"""Anthropic Claude qua REST Messages API."""
from __future__ import annotations

from typing import Optional

from ..http import post_json
from .base import Translator

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class AnthropicTranslator(Translator):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, target_lang: str, source_lang: Optional[str], glossary=None):
        super().__init__(target_lang, source_lang, glossary)
        if not api_key:
            raise RuntimeError("Thiếu ANTHROPIC_API_KEY")
        self.api_key = api_key
        self.model = model

    def _complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": 512,
            "temperature": 0.2,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        resp = post_json(ANTHROPIC_URL, body, headers=headers)
        blocks = resp.get("content") or []
        return "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text").strip()
