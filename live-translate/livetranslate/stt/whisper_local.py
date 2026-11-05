"""faster-whisper chạy offline trên CPU/GPU."""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from .base import SpeechToText, Transcript, looks_like_hallucination

log = logging.getLogger(__name__)


class WhisperLocal(SpeechToText):
    name = "whisper"

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8", language: Optional[str] = None):
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Cần faster-whisper: pip install faster-whisper") from e
        log.info("Đang tải Whisper '%s' (%s/%s)...", model_size, device, compute_type)
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.language = language
        log.info("Whisper sẵn sàng")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16_000) -> Transcript:
        audio = np.asarray(audio, dtype=np.float32)
        segments, info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
            without_timestamps=True,
        )
        texts = []
        for seg in segments:
            t = (seg.text or "").strip()
            if not t:
                continue
            no_speech = getattr(seg, "no_speech_prob", 0.0) or 0.0
            logprob = getattr(seg, "avg_logprob", 0.0) or 0.0
            if no_speech > 0.7 and logprob < -1.0:
                continue
            texts.append(t)
        text = " ".join(texts).strip()
        if looks_like_hallucination(text):
            return Transcript(text="", language=getattr(info, "language", None))
        return Transcript(text=text, language=getattr(info, "language", None))
