from __future__ import annotations

from typing import Optional

import numpy as np


class TextToSpeech:
    """Giao diện TTS: ``synthesize(text) -> float32 mono`` ở ``sample_rate``."""

    name = "tts"
    sample_rate = 24_000

    def synthesize(self, text: str) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

    def list_voices(self) -> list:
        return []

    def close(self) -> None:
        pass


class SilentTTS(TextToSpeech):
    """Không đọc, chỉ phụ đề."""

    name = "none"

    def synthesize(self, text: str) -> np.ndarray:
        return np.zeros(0, dtype=np.float32)
