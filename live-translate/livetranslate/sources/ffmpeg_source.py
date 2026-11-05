"""Nguồn dựa trên ffmpeg: URL qua yt-dlp, tệp, thiết bị thu."""
from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
import sys
import threading
import time
from typing import Iterator, List, Optional

import numpy as np

from ..audio import SAMPLE_RATE, pcm16_to_float32
from .base import AudioSource

log = logging.getLogger(__name__)

CHUNK_BYTES = SAMPLE_RATE * 2 // 10  # 100 ms PCM16


def require_binary(name: str, hint: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Không tìm thấy '{name}' trong PATH. {hint}")
    return path


def _ffmpeg_decode_cmd(input_args: List[str]) -> List[str]:
    ffmpeg = require_binary("ffmpeg", "Cài ffmpeg: https://ffmpeg.org/download.html")
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        *input_args,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "-",
    ]


def _pump_stderr(proc: subprocess.Popen, label: str) -> None:
    def run() -> None:
        try:
            for line in iter(proc.stderr.readline, b""):
                txt = line.decode("utf-8", "replace").rstrip()
                if txt:
                    log.debug("[%s] %s", label, txt)
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


class _FfmpegPipeSource(AudioSource):
    def __init__(self) -> None:
        self._procs: List[subprocess.Popen] = []
        self._closed = False

    def _read_pcm(self, proc: subprocess.Popen, realtime: bool = False) -> Iterator[np.ndarray]:
        assert proc.stdout is not None
        t0 = time.monotonic()
        produced = 0.0
        while not self._closed:
            data = proc.stdout.read(CHUNK_BYTES)
            if not data:
                break
            audio = pcm16_to_float32(data)
            if realtime:
                produced += audio.size / SAMPLE_RATE
                lag = produced - (time.monotonic() - t0)
                if lag > 0.05:
                    time.sleep(lag)
            yield audio

    def close(self) -> None:
        self._closed = True
        for p in self._procs:
            try:
                p.kill()
            except Exception:
                pass


class FileSource(_FfmpegPipeSource):
    """Giải mã tệp video/audio bất kỳ bằng ffmpeg."""

    name = "file"

    def __init__(self, path: str, realtime: bool = False):
        super().__init__()
        self.path = path
        self.realtime = realtime

    def frames(self) -> Iterator[np.ndarray]:
        cmd = _ffmpeg_decode_cmd(["-i", self.path])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._procs.append(proc)
        _pump_stderr(proc, "ffmpeg")
        yield from self._read_pcm(proc, realtime=self.realtime)


class FfmpegDeviceSource(_FfmpegPipeSource):
    """Thu từ thiết bị hệ thống qua ffmpeg, ví dụ:

    - Windows:  ``-f dshow -i audio=Stereo Mix (Realtek(R) Audio)``
    - Linux:    ``-f pulse -i default`` (hoặc ``alsa_output.<...>.monitor`` để lấy âm thanh loa)
    - macOS:    ``-f avfoundation -i :0`` (cần BlackHole/Loopback để lấy âm thanh hệ thống)
    """

    name = "device"

    def __init__(self, ffmpeg_args: str):
        super().__init__()
        self.args = shlex.split(ffmpeg_args, posix=(sys.platform != "win32"))

    def frames(self) -> Iterator[np.ndarray]:
        cmd = _ffmpeg_decode_cmd(self.args)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._procs.append(proc)
        _pump_stderr(proc, "ffmpeg")
        yield from self._read_pcm(proc)


class UrlSource(_FfmpegPipeSource):
    """YouTube / Twitch / Facebook / TikTok / Kick / bất kỳ trang yt-dlp hỗ trợ, kể cả livestream.

    Cách 1 (mặc định): ``yt-dlp -g`` lấy URL luồng trực tiếp rồi ffmpeg đọc (độ trễ thấp, hợp live HLS).
    Cách 2 (dự phòng): ``yt-dlp -o - | ffmpeg`` khi trang cần cookie/header đặc biệt.
    """

    name = "url"

    def __init__(self, url: str, verbose: bool = False, pipe_mode: bool = False, ytdlp_args: Optional[List[str]] = None):
        super().__init__()
        self.url = url
        self.verbose = verbose
        self.pipe_mode = pipe_mode
        self.ytdlp_args = ytdlp_args or []

    def _ytdlp(self) -> str:
        return require_binary("yt-dlp", "Cài: pip install yt-dlp")

    def resolve_stream_url(self) -> tuple[str, dict]:
        """Trả (url_luồng, headers) tốt nhất cho audio."""
        cmd = [
            self._ytdlp(),
            "-f",
            "bestaudio[protocol!=http_dash_segments]/bestaudio/best",
            "-g",
            "--no-playlist",
            "--print",
            "http_headers",
            *self.ytdlp_args,
            self.url,
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            raise RuntimeError(f"yt-dlp lỗi: {out.stderr.strip()[-800:]}")
        lines = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
        headers: dict = {}
        stream = None
        for ln in lines:
            if ln.startswith("{"):
                try:
                    import ast

                    headers = ast.literal_eval(ln)
                except Exception:
                    headers = {}
            elif ln.startswith("http"):
                stream = ln
        if not stream:
            raise RuntimeError("yt-dlp không trả URL luồng")
        return stream, headers

    def frames(self) -> Iterator[np.ndarray]:
        if self.pipe_mode:
            yield from self._frames_pipe()
            return
        try:
            stream, headers = self.resolve_stream_url()
        except Exception as e:
            log.warning("Không lấy được URL trực tiếp (%s); chuyển sang chế độ pipe yt-dlp", e)
            yield from self._frames_pipe()
            return

        input_args: List[str] = ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5"]
        if headers:
            hdr = "".join(f"{k}: {v}\r\n" for k, v in headers.items() if k.lower() != "accept-encoding")
            input_args += ["-headers", hdr]
            ua = headers.get("User-Agent")
            if ua:
                input_args += ["-user_agent", ua]
        input_args += ["-i", stream]
        cmd = _ffmpeg_decode_cmd(input_args)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._procs.append(proc)
        _pump_stderr(proc, "ffmpeg")
        got_any = False
        for chunk in self._read_pcm(proc):
            got_any = True
            yield chunk
        if not got_any and not self._closed:
            log.warning("ffmpeg không đọc được luồng trực tiếp; thử chế độ pipe yt-dlp")
            yield from self._frames_pipe()

    def _frames_pipe(self) -> Iterator[np.ndarray]:
        ytdlp_cmd = [
            self._ytdlp(),
            "-f",
            "bestaudio/best",
            "--no-playlist",
            "-q",
            "-o",
            "-",
            *self.ytdlp_args,
            self.url,
        ]
        dl = subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._procs.append(dl)
        _pump_stderr(dl, "yt-dlp")
        cmd = _ffmpeg_decode_cmd(["-i", "pipe:0"])
        proc = subprocess.Popen(cmd, stdin=dl.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._procs.append(proc)
        _pump_stderr(proc, "ffmpeg")
        if dl.stdout:
            dl.stdout.close()
        yield from self._read_pcm(proc)
