"""Gemini qua REST (generateContent). Tự chọn model dự phòng khi model cấu hình không còn."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..http import ApiError, get_json, post_json
from .base import Translator

log = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    """Gọi generateContent, hỗ trợ text + audio inline. Dùng chung cho dịch, STT và TTS."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY (lấy tại https://aistudio.google.com/apikey)")
        self.api_key = api_key
        self.model = model
        self._fallback_done = False
        self._no_thinking_config = False

    # ------------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

    def _url(self, model: str, method: str = "generateContent") -> str:
        return f"{GEMINI_BASE}/models/{model}:{method}"

    def pick_fallback_model(self) -> Optional[str]:
        """Liệt kê model và chọn một bản 'flash' hỗ trợ generateContent."""
        try:
            data = get_json(f"{GEMINI_BASE}/models?pageSize=200", headers=self._headers())
        except Exception as e:
            log.warning("Không liệt kê được model Gemini: %s", e)
            return None
        names: List[str] = []
        for m in data.get("models", []):
            name = str(m.get("name", "")).replace("models/", "")
            methods = m.get("supportedGenerationMethods") or m.get("supported_generation_methods") or []
            if "generateContent" not in methods:
                continue
            low = name.lower()
            if any(x in low for x in ("tts", "live", "image", "embedding", "audio", "veo", "imagen", "transcribe")):
                continue
            names.append(name)

        def score(n: str) -> tuple:
            low = n.lower()
            return (
                0 if "flash" in low else 1,
                1 if "lite" in low else 0,
                1 if ("preview" in low or "exp" in low) else 0,
                -_version_key(low),
            )

        names.sort(key=score)
        return names[0] if names else None

    def generate(
        self,
        parts: List[Dict[str, Any]],
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        extra_config: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        model = model or self.model
        body: Dict[str, Any] = {"contents": [{"role": "user", "parts": parts}]}
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}
        cfg: Dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if extra_config:
            cfg.update(extra_config)
        if not self._no_thinking_config and "flash" in model.lower() and not extra_config:
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
        body["generationConfig"] = cfg
        try:
            return post_json(self._url(model), body, headers=self._headers(), timeout=timeout)
        except ApiError as e:
            if e.status == 400 and "thinking" in e.message.lower() and "thinkingConfig" in cfg:
                self._no_thinking_config = True
                cfg.pop("thinkingConfig", None)
                return post_json(self._url(model), body, headers=self._headers(), timeout=timeout)
            if e.status == 404 and not self._fallback_done and model == self.model:
                self._fallback_done = True
                fb = self.pick_fallback_model()
                if fb and fb != model:
                    log.warning("Model Gemini '%s' không khả dụng; chuyển sang '%s'", model, fb)
                    self.model = fb
                    return self.generate(parts, system, temperature, max_tokens, extra_config, fb, timeout)
            raise

    @staticmethod
    def text_of(resp: Dict[str, Any]) -> str:
        cands = resp.get("candidates") or []
        if not cands:
            fb = resp.get("promptFeedback", {})
            if fb.get("blockReason"):
                log.warning("Gemini chặn nội dung: %s", fb.get("blockReason"))
            return ""
        content = cands[0].get("content") or {}
        texts = [p.get("text", "") for p in content.get("parts", []) if isinstance(p, dict) and p.get("text")]
        return "".join(texts).strip()


def _version_key(name: str) -> float:
    import re

    m = re.search(r"(\d+)(?:\.(\d+))?", name)
    if not m:
        return 0.0
    major = int(m.group(1))
    minor = int(m.group(2) or 0)
    return major + minor / 100.0


class GeminiTranslator(Translator):
    name = "gemini"

    def __init__(self, api_key: str, model: str, target_lang: str, source_lang: Optional[str], glossary=None):
        super().__init__(target_lang, source_lang, glossary)
        self.client = GeminiClient(api_key, model)

    def _complete(self, system: str, user: str) -> str:
        resp = self.client.generate([{"text": user}], system=system, temperature=0.2, max_tokens=512)
        return GeminiClient.text_of(resp)
