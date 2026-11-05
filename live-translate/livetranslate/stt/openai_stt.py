"""STT qua endpoint /audio/transcriptions tương thích OpenAI (OpenAI whisper-1, Groq whisper-large-v3-turbo...)."""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..audio import wav_bytes
from ..http import post_json
from .base import SpeechToText, Transcript, looks_like_hallucination


class OpenAITranscribe(SpeechToText):
    name = "openai-stt"

    def __init__(self, api_key: str, base_url: str, model: str = "whisper-1", language: Optional[str] = None):
        if not api_key:
            raise RuntimeError("Thiếu OPENAI_API_KEY cho STT")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16_000) -> Transcript:
        wav = wav_bytes(audio, sample_rate)
        data = {"model": self.model, "response_format": "json", "temperature": "0"}
        if self.language:
            data["language"] = self.language
        resp = post_json(
            f"{self.base_url}/audio/transcriptions",
            payload={},
            headers={"Authorization": f"Bearer {self.api_key}"},
            files={"file": ("clip.wav", wav, "audio/wav")},
            data=data,
        )
        text = (resp.get("text") or "").strip()
        if looks_like_hallucination(text):
            text = ""
        return Transcript(text=text, language=resp.get("language") or self.language)
