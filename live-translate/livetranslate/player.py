"""Phát âm thanh tuần tự qua sounddevice; tuỳ chọn ghi WAV."""
from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import numpy as np

from .audio import WavWriter, resample_linear

log = logging.getLogger(__name__)


def _parse_device(device: Optional[str]):
    if device is None or device == "":
        return None
    try:
        return int(device)
    except ValueError:
        return device


class AudioPlayer:
    """Hàng đợi phát. ``enqueue(audio, rate)`` không chặn; phát theo thứ tự trên luồng riêng."""

    def __init__(self, play: bool = True, device: Optional[str] = None, save_path: Optional[str] = None, save_rate: int = 48_000):
        self.play = play
        self.device = _parse_device(device)
        self._q: "queue.Queue[Optional[tuple]]" = queue.Queue()
        self._writer = WavWriter(save_path, save_rate) if save_path else None
        self._stream = None
        self._stream_rate: Optional[int] = None
        self._thread = threading.Thread(target=self._run, name="player", daemon=True)
        self._stopped = threading.Event()
        self.playing = threading.Event()
        self._thread.start()

    def enqueue(self, audio: np.ndarray, sample_rate: int) -> None:
        if audio is None or audio.size == 0:
            return
        self._q.put((np.asarray(audio, dtype=np.float32), int(sample_rate)))

    def pending(self) -> int:
        return self._q.qsize()

    def _open_stream(self, rate: int):
        import sounddevice as sd  # type: ignore

        if self._stream is not None and self._stream_rate == rate:
            return self._stream
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        try:
            self._stream = sd.OutputStream(samplerate=rate, channels=1, dtype="float32", device=self.device)
            self._stream.start()
            self._stream_rate = rate
        except Exception as e:
            # thiết bị không nhận tần số này → dùng tần số mặc định và resample
            info = sd.query_devices(self.device, "output")
            fallback = int(info["default_samplerate"])
            log.warning("Không mở được loa ở %d Hz (%s); dùng %d Hz", rate, e, fallback)
            self._stream = sd.OutputStream(samplerate=fallback, channels=1, dtype="float32", device=self.device)
            self._stream.start()
            self._stream_rate = fallback
        return self._stream

    def _run(self) -> None:
        while not self._stopped.is_set():
            item = self._q.get()
            if item is None:
                break
            audio, rate = item
            self.playing.set()
            try:
                if self._writer is not None:
                    self._writer.write(audio, rate)
                if self.play:
                    stream = self._open_stream(rate)
                    if self._stream_rate != rate:
                        audio = resample_linear(audio, rate, self._stream_rate or rate)
                    stream.write(audio.reshape(-1, 1))
            except Exception as e:
                log.error("Lỗi phát âm thanh: %s", e)
                if "sounddevice" in str(type(e).__module__) or "PortAudio" in str(e):
                    self.play = False
            finally:
                if self._q.empty():
                    self.playing.clear()

    def wait_idle(self, timeout: Optional[float] = None) -> None:
        import time

        t0 = time.monotonic()
        while (not self._q.empty() or self.playing.is_set()) and not self._stopped.is_set():
            if timeout is not None and time.monotonic() - t0 > timeout:
                break
            time.sleep(0.05)

    def close(self, drain: bool = True) -> None:
        if drain:
            self.wait_idle(timeout=120)
        self._stopped.set()
        self._q.put(None)
        self._thread.join(timeout=5)
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        if self._writer is not None:
            self._writer.close()
