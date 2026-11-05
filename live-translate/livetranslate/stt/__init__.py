from __future__ import annotations

from ..config import Settings
from .base import SpeechToText, Transcript


def make_stt(s: Settings) -> SpeechToText:
    kind = (s.stt or "whisper").lower()
    if kind in ("whisper", "faster-whisper", "local"):
        from .whisper_local import WhisperLocal

        return WhisperLocal(s.whisper_model, s.whisper_device, s.whisper_compute, s.source_lang)
    if kind == "gemini":
        from .gemini_stt import GeminiAudio

        direct = (s.translator or "").lower() in ("gemini", "none") and s.extra.get("direct", True)
        return GeminiAudio(
            s.gemini_api_key,
            s.gemini_model,
            source_lang=s.source_lang,
            target_lang=s.target_lang if direct else None,
            glossary_path=s.glossary,
        )
    if kind in ("openai", "groq", "whisper-api"):
        from .openai_stt import OpenAITranscribe

        return OpenAITranscribe(s.openai_api_key, s.openai_base_url, s.openai_stt_model, s.source_lang)
    raise ValueError(f"STT không hỗ trợ: {s.stt}")


__all__ = ["SpeechToText", "Transcript", "make_stt"]
