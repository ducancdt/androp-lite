from __future__ import annotations

from ..config import Settings
from .base import TextToSpeech, SilentTTS


def make_tts(s: Settings) -> TextToSpeech:
    kind = (s.tts or "vieneu").lower()
    if kind in ("none", "off", "subtitle"):
        return SilentTTS()
    if kind == "vieneu":
        from .vieneu_tts import VieNeuTTS

        return VieNeuTTS(voice=s.voice, voice_ref=s.voice_ref, mode=s.vieneu_mode, precision=s.vieneu_precision)
    if kind == "gemini":
        from .gemini_tts import GeminiTTS

        return GeminiTTS(s.gemini_api_key, s.gemini_tts_model, s.gemini_tts_voice)
    raise ValueError(f"TTS không hỗ trợ: {s.tts}")


__all__ = ["TextToSpeech", "SilentTTS", "make_tts"]
