"""Bất kỳ API tương thích OpenAI: OpenAI, Groq, OpenRouter, DeepSeek, Together, Ollama, LM Studio, vLLM..."""
from __future__ import annotations

from typing import Dict, Optional

from ..http import post_json
from .base import Translator


class OpenAICompatTranslator(Translator):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        target_lang: str,
        source_lang: Optional[str],
        glossary=None,
    ):
        super().__init__(target_lang, source_lang, glossary)
        self.api_key = api_key or "none"  # Ollama/LM Studio không cần khóa
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = post_json(f"{self.base_url}/chat/completions", body, headers=self._headers())
        choices = resp.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):  # một số server trả mảng phần
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return (content or "").strip()
