"""Micro / loopback qua sounddevice (PortAudio)."""
from __future__ import annotations

import queue
from typing import Iterator, Optional

import numpy as np

from ..audio import SAMPLE_RATE, resample_linear, to_mono
from .base import AudioSource


def _parse_device(device: Optional[str]):
    if device is None or device == "":
        return None
    try:
        return int(device)
    except ValueError:
        return device


def list_devices() -> str:
    import sounddevice as sd  # type: ignore

    return str(sd.query_devices())


class MicSource(AudioSource):
    name = "mic"

    def __init__(self, device: Optional[str] = None, block_ms: int = 100):
        self.device = _parse_device(device)
        self.block_ms = block_ms
        self._q: "queue.Queue[Optional[np.ndarray]]" = queue.Queue(maxsize=200)
        self._stream = None
        self._closed = False

    def frames(self) -> Iterator[np.ndarray]:
        try:
            import sounddevice as sd  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Cần 'sounddevice' để thu mic: pip install sounddevice") from e

        info = sd.query_devices(self.device, "input")
        rate = int(info["default_samplerate"]) or SAMPLE_RATE
        channels = 1 if info["max_input_channels"] >= 1 else 2
        blocksize = int(rate * self.block_ms / 1000)

        def callback(indata, frames, time_info, status):  # noqa: ARG001
            if self._closed:
                return
            try:
                self._q.put_nowait(np.array(indata, dtype=np.float32, copy=True))
            except queue.Full:
                pass

        self._stream = sd.InputStream(
            device=self.device,
            samplerate=rate,
            channels=min(channels, int(info["max_input_channels"]) or 1),
            dtype="float32",
            blocksize=blocksize,
            callback=callback,
        )
        self._stream.start()
        try:
            while not self._closed:
                try:
                    block = self._q.get(timeout=0.5)
                except queue.Empty:
                    continue
                if block is None:
                    break
                yield resample_linear(to_mono(block), rate, SAMPLE_RATE)
        finally:
            self.close()

    def close(self) -> None:
        self._closed = True
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
