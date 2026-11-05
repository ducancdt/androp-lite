from __future__ import annotations

from ..config import Settings
from .base import Translator, TranslationContext
from .prompts import build_system_prompt, build_user_prompt, clean_translation, load_glossary


def make_translator(s: Settings) -> Translator:
    kind = (s.translator or "gemini").lower()
    glossary = load_glossary(s.glossary) if s.glossary else {}
    if kind == "none":
        from .base import PassthroughTranslator

        return PassthroughTranslator()
    if kind == "gemini":
        from .gemini import GeminiTranslator

        return GeminiTranslator(s.gemini_api_key, s.gemini_model, s.target_lang, s.source_lang, glossary)
    if kind in ("openai", "openai-compatible", "groq", "openrouter", "ollama", "deepseek"):
        from .openai_compat import OpenAICompatTranslator

        return OpenAICompatTranslator(
            s.openai_api_key, s.openai_base_url, s.openai_model, s.target_lang, s.source_lang, glossary
        )
    if kind in ("anthropic", "claude"):
        from .anthropic import AnthropicTranslator

        return AnthropicTranslator(s.anthropic_api_key, s.anthropic_model, s.target_lang, s.source_lang, glossary)
    raise ValueError(f"Nhà cung cấp dịch không hỗ trợ: {s.translator}")


__all__ = [
    "Translator",
    "TranslationContext",
    "make_translator",
    "build_system_prompt",
    "build_user_prompt",
    "clean_translation",
    "load_glossary",
]
