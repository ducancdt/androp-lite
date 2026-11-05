from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Transcript:
    text: str
    language: Optional[str] = None
    translation: Optional[str] = None  # có khi STT dịch thẳng (Gemini audio)

    @property
    def empty(self) -> bool:
        return not (self.text or "").strip() and not (self.translation or "").strip()


# Các câu Whisper hay "bịa" khi gặp im lặng / nhạc
_HALLUCINATIONS = [
    "subtitles by",
    "subscribe",
    "hãy subscribe",
    "đăng ký kênh",
    "cảm ơn các bạn đã theo dõi",
    "thanks for watching",
    "thank you for watching",
    "amara.org",
    "ご視聴ありがとうございました",
    "字幕",
    "♪",
]
_ONLY_PUNCT = re.compile(r"^[\s\W_]*$")


def looks_like_hallucination(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t or _ONLY_PUNCT.match(t):
        return True
    if len(t) <= 2:
        return True
    for h in _HALLUCINATIONS:
        if h in t and len(t) < len(h) + 25:
            return True
    # lặp từ bất thường ("you you you you")
    words = t.split()
    if len(words) >= 6 and len(set(words)) <= 2:
        return True
    return False


class SpeechToText:
    """Giao diện STT: ``transcribe(audio float32 16 kHz) -> Transcript``."""

    name = "stt"
    translates_directly = False

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16_000) -> Transcript:  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:
        pass
