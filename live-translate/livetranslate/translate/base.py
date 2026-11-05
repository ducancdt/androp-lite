from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple

from .prompts import build_system_prompt, build_user_prompt, clean_translation


@dataclass
class TranslationContext:
    """Giữ vài câu gần nhất để bản dịch mạch lạc."""

    max_lines: int = 3
    history: Deque[Tuple[str, str]] = field(default_factory=deque)

    def add(self, source: str, translation: str) -> None:
        self.history.append((source, translation))
        while len(self.history) > self.max_lines:
            self.history.popleft()

    def pairs(self):
        return list(self.history)


class Translator:
    """Giao diện dịch. Lớp con chỉ cần cài ``_complete(system, user) -> str``."""

    name = "translator"

    def __init__(self, target_lang: str = "vi", source_lang: Optional[str] = None, glossary: Optional[Dict[str, str]] = None):
        self.target_lang = target_lang
        self.source_lang = source_lang
        self.glossary = glossary or {}
        self.system_prompt = build_system_prompt(target_lang, source_lang, self.glossary)

    def translate(self, text: str, context: Optional[TranslationContext] = None) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        user = build_user_prompt(text, context.pairs() if context else [])
        raw = self._complete(self.system_prompt, user)
        return clean_translation(raw)

    def _complete(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class PassthroughTranslator(Translator):
    """Không dịch (dùng khi STT đã trả thẳng bản dịch, hoặc chỉ muốn phụ đề gốc)."""

    name = "none"

    def translate(self, text: str, context: Optional[TranslationContext] = None) -> str:
        return (text or "").strip()
