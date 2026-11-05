"""STT streaming: nhận âm thanh liên tục, tự chốt câu (không cần bộ cắt câu VAD của ta).

Backend đầu tiên: WhisperLiveKit (https://github.com/QuentinFuxa/WhisperLiveKit, Apache-2.0)
— server tự host với SimulStreaming/LocalAgreement, độ trễ thấp hơn cách "chờ hết câu rồi mới nhận dạng".

Chạy server (máy này hoặc máy khác có GPU):

    pip install whisperlivekit
    wlk --model small --language en --pcm-input --port 8000

rồi:

    livetranslate --source <url> --stt wlk --wlk-url ws://127.0.0.1:8000/asr
"""
from __future__ import annotations

import asyncio
import json
import logging
import queue
import re
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from ..audio import float32_to_pcm16
from .base import SpeechToText, Transcript, looks_like_hallucination

log = logging.getLogger(__name__)


@dataclass
class StreamLine:
    """Một câu đã chốt từ STT streaming, kèm thời gian (giây kể từ đầu luồng)."""

    text: str
    start: float
    end: float
    language: Optional[str] = None
    translation: Optional[str] = None  # khi server tự dịch (WLK --target-language)

    def to_transcript(self) -> Transcript:
        return Transcript(text=self.text, language=self.language, translation=self.translation)


class StreamingSTT(SpeechToText):
    """Giao diện STT streaming: ``feed(audio)`` liên tục, ``poll()`` lấy câu đã chốt."""

    name = "streaming"
    streaming = True

    def start(self) -> None:  # pragma: no cover - interface
        pass

    def feed(self, audio: np.ndarray, sample_rate: int = 16_000) -> None:  # pragma: no cover
        raise NotImplementedError

    def poll(self, timeout: float = 0.2) -> Optional[StreamLine]:  # pragma: no cover
        raise NotImplementedError

    def finish(self) -> None:
        """Báo hết âm thanh; server xả nốt phần còn lại."""

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16_000) -> Transcript:
        raise RuntimeError("StreamingSTT dùng feed()/poll(), không dùng transcribe()")


# ----------------------------------------------------------------------------
_TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2})(?:\.(\d+))?$")


def parse_wlk_time(value) -> float:
    """WLK gửi 'H:MM:SS.cc'; chấp nhận cả số."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    m = _TIME_RE.match(str(value).strip())
    if not m:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    h = int(m.group(1) or 0)
    mnt = int(m.group(2))
    s = int(m.group(3))
    frac = m.group(4) or "0"
    return h * 3600 + mnt * 60 + s + int(frac) / (10 ** len(frac))


class LineCommitter:
    """Biến danh sách ``lines`` mà WLK gửi lại liên tục thành các câu chốt chỉ phát một lần.

    WLK trả toàn bộ trạng thái mỗi lần cập nhật: ``lines`` là phần đã chốt (ổn định), dòng cuối
    có thể còn dài thêm. Quy tắc chốt:
    - dòng không còn là dòng cuối → chốt phần chưa phát;
    - dòng cuối không đổi trong ``settle_s`` giây và kết thúc bằng dấu câu → chốt;
    - dòng cuối không đổi trong ``max_wait_s`` giây → chốt dù chưa có dấu câu;
    - server báo im lặng (speaker == -2) sau dòng → chốt.
    Phần đã phát của một dòng được nhớ để chỉ phát phần nối thêm.
    """

    SENTENCE_END = re.compile(r"[.!?。！？…]\s*[\"”’)]?$")

    def __init__(self, settle_s: float = 1.2, max_wait_s: float = 4.0):
        self.settle_s = settle_s
        self.max_wait_s = max_wait_s
        self._emitted: Dict[int, int] = {}  # index dòng → số ký tự đã phát
        self._last_text: Dict[int, str] = {}
        self._last_change: Dict[int, float] = {}
        self._pruned = 0  # số dòng server đã cắt khỏi đầu danh sách

    def update(self, lines: List[dict], now: Optional[float] = None, final: bool = False) -> List[StreamLine]:
        now = time.monotonic() if now is None else now
        out: List[StreamLine] = []
        # loại dòng im lặng nhưng ghi nhớ vị trí để chốt dòng trước nó
        speech: List[tuple] = []  # (global_index, line, silence_after)
        gi = self._pruned
        for ln in lines:
            if ln.get("speaker") == -2 or not (ln.get("text") or "").strip():
                if speech:
                    speech[-1] = (speech[-1][0], speech[-1][1], True)
                continue
            speech.append((gi, ln, False))
            gi += 1
        n = len(speech)
        for pos, (idx, ln, silence_after) in enumerate(speech):
            text = (ln.get("text") or "").strip()
            if self._last_text.get(idx) != text:
                self._last_text[idx] = text
                self._last_change[idx] = now
            emitted = self._emitted.get(idx, 0)
            if emitted >= len(text):
                continue
            is_last = pos == n - 1
            idle = now - self._last_change[idx]
            commit = (
                final
                or not is_last
                or silence_after
                or (idle >= self.settle_s and bool(self.SENTENCE_END.search(text)))
                or idle >= self.max_wait_s
            )
            if not commit:
                continue
            new_text = text[emitted:].strip()
            self._emitted[idx] = len(text)
            if not new_text or looks_like_hallucination(new_text):
                continue
            start, end = parse_wlk_time(ln.get("start")), parse_wlk_time(ln.get("end"))
            tr = (ln.get("translation") or "").strip() or None
            out.append(StreamLine(text=new_text, start=start, end=end, language=ln.get("detected_language"), translation=tr if emitted == 0 else None))
        return out

    def note_pruned(self, count: int) -> None:
        self._pruned += max(0, int(count))


class WhisperLiveKitStream(StreamingSTT):
    """Client WebSocket tới server WhisperLiveKit (``wlk --pcm-input``)."""

    name = "wlk"

    def __init__(
        self,
        url: str = "ws://127.0.0.1:8000/asr",
        language: Optional[str] = None,
        target_language: Optional[str] = None,
        api_token: Optional[str] = None,
        settle_s: float = 1.2,
        max_wait_s: float = 4.0,
        connect_timeout: float = 15.0,
    ):
        try:
            import websockets  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Cần thư viện websockets: pip install websockets") from e
        self.url = url
        self.language = language
        self.target_language = target_language
        self.api_token = api_token
        self.translates_directly = bool(target_language)
        self.connect_timeout = connect_timeout
        self.committer = LineCommitter(settle_s=settle_s, max_wait_s=max_wait_s)
        self._send_q: "queue.Queue[Optional[bytes]]" = queue.Queue(maxsize=400)
        self._out_q: "queue.Queue[StreamLine]" = queue.Queue()
        self._lines: List[dict] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stopped = threading.Event()
        self._ready = threading.Event()
        self._error: Optional[BaseException] = None
        self._finished = False

    # ------------------------------------------------------------------
    def _full_url(self) -> str:
        params = []
        if self.language:
            params.append(f"language={self.language}")
        if self.target_language:
            params.append(f"target_language={self.target_language}")
        if self.api_token:
            params.append(f"token={self.api_token}")
        if not params:
            return self.url
        return self.url + ("&" if "?" in self.url else "?") + "&".join(params)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="wlk-ws", daemon=True)
        self._thread.start()
        if not self._ready.wait(self.connect_timeout):
            err = self._error or RuntimeError(f"Không kết nối được WhisperLiveKit tại {self.url}")
            raise RuntimeError(str(err))
        if self._error:
            raise RuntimeError(str(self._error))
        log.info("Đã kết nối WhisperLiveKit: %s", self.url)

    def feed(self, audio: np.ndarray, sample_rate: int = 16_000) -> None:
        if self._finished or self._stopped.is_set():
            return
        data = float32_to_pcm16(audio)
        try:
            self._send_q.put(data, timeout=2.0)
        except queue.Full:
            log.warning("WLK: hàng đợi gửi đầy, bỏ 1 khối âm thanh")

    def finish(self) -> None:
        if not self._finished:
            self._finished = True
            self._send_q.put(b"")

    def poll(self, timeout: float = 0.2) -> Optional[StreamLine]:
        try:
            return self._out_q.get(timeout=timeout)
        except queue.Empty:
            if self._error and self._out_q.empty():
                raise RuntimeError(f"WLK lỗi: {self._error}")
            # chốt theo thời gian (dòng cuối đứng yên) ngay cả khi server không gửi gì mới
            with self._lock:
                for ln in self.committer.update(self._lines):
                    self._out_q.put(ln)
            try:
                return self._out_q.get_nowait()
            except queue.Empty:
                return None

    def close(self) -> None:
        self._stopped.set()
        self._send_q.put(None)
        if self._thread is not None:
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    def _run(self) -> None:
        try:
            asyncio.run(self._session())
        except BaseException as e:  # noqa: BLE001
            self._error = e
            log.error("WLK: %s", e)
        finally:
            self._ready.set()

    async def _session(self) -> None:
        import websockets

        async with websockets.connect(self._full_url(), max_size=None, open_timeout=self.connect_timeout) as ws:
            self._ready.set()
            sender = asyncio.create_task(self._sender(ws))
            try:
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue
                    self._handle_message(raw)
                    if self._stopped.is_set():
                        break
            finally:
                sender.cancel()
                await asyncio.gather(sender, return_exceptions=True)
            # kết thúc: chốt mọi dòng còn lại
            with self._lock:
                for ln in self.committer.update(self._lines, final=True):
                    self._out_q.put(ln)

    async def _sender(self, ws) -> None:
        loop = asyncio.get_running_loop()
        while not self._stopped.is_set():
            item = await loop.run_in_executor(None, self._send_q.get)
            if item is None:
                return
            await ws.send(item)  # b"" = EOF theo giao thức WLK

    def _handle_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return
        kind = msg.get("type")
        if kind in ("config", "ready_to_stop"):
            if kind == "ready_to_stop":
                self._stopped.set()
            return
        if kind == "error" or msg.get("error"):
            self._error = RuntimeError(msg.get("error") or "server error")
            return
        if kind == "diff":
            pruned = int(msg.get("lines_pruned") or 0)
            with self._lock:
                if pruned:
                    self._lines = self._lines[pruned:]
                    self.committer.note_pruned(pruned)
                new_lines = msg.get("new_lines") or []
                n_lines = msg.get("n_lines")
                if new_lines and isinstance(n_lines, int):
                    keep = max(0, n_lines - len(new_lines))
                    self._lines = self._lines[:keep] + list(new_lines)
                elif new_lines:
                    self._lines = self._lines + list(new_lines)
                lines = list(self._lines)
        else:  # "snapshot" hoặc trạng thái đầy đủ (mode=full)
            lines = msg.get("lines")
            if not isinstance(lines, list):
                return
            with self._lock:
                self._lines = list(lines)
        with self._lock:
            for ln in self.committer.update(lines):
                self._out_q.put(ln)
