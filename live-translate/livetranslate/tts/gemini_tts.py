"""Giọng đọc Gemini TTS (đám mây) — dự phòng khi không cài được VieNeu."""
from __future__ import annotations

import base64
import logging
import re

import numpy as np

from ..audio import pcm16_to_float32, read_wav_bytes
from ..translate.gemini import GeminiClient
from .base import TextToSpeech

log = logging.getLogger(__name__)


class GeminiTTS(TextToSpeech):
    name = "gemini-tts"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview-tts", voice: str = "Kore"):
        self.client = GeminiClient(api_key, model)
        self.voice = voice
        self.sample_rate = 24_000

    def synthesize(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(0, dtype=np.float32)
        resp = self.client.generate(
            [{"text": text}],
            temperature=1.0,
            max_tokens=8192,
            extra_config={
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": self.voice}}},
            },
            timeout=120,
        )
        cands = resp.get("candidates") or []
        if not cands:
            return np.zeros(0, dtype=np.float32)
        for part in (cands[0].get("content") or {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if not blob:
                continue
            data = base64.b64decode(blob.get("data", ""))
            mime = blob.get("mimeType") or blob.get("mime_type") or ""
            if "wav" in mime:
                audio, rate = read_wav_bytes(data)
                self.sample_rate = rate
                return audio
            m = re.search(r"rate=(\d+)", mime)
            self.sample_rate = int(m.group(1)) if m else 24_000
            return pcm16_to_float32(data)
        return np.zeros(0, dtype=np.float32)
