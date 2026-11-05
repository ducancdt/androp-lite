"""Gemini nghe trực tiếp audio: trả transcript, và (tuỳ chọn) bản dịch luôn trong một lần gọi."""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Optional

import numpy as np

from ..audio import wav_bytes
from ..config import lang_name
from ..translate.gemini import GeminiClient
from ..translate.prompts import load_glossary
from .base import SpeechToText, Transcript, looks_like_hallucination

log = logging.getLogger(__name__)


class GeminiAudio(SpeechToText):
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        glossary_path: Optional[str] = None,
    ):
        self.client = GeminiClient(api_key, model)
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translates_directly = bool(target_lang)
        glossary = load_glossary(glossary_path) if glossary_path else {}
        self.system = self._build_system(source_lang, target_lang, glossary)

    @staticmethod
    def _build_system(source_lang, target_lang, glossary) -> str:
        src = lang_name(source_lang)
        lines = [
            "You are a live-broadcast interpreter. You receive a short audio clip of speech.",
            f"The speech is in {src}." if source_lang else "Detect the spoken language.",
            "Return ONLY a compact JSON object, no markdown, with keys:",
            '  "text": the verbatim transcript of what was said (same language as the audio),',
        ]
        if target_lang:
            lines.append(f'  "translation": a natural spoken-style translation into {lang_name(target_lang)},')
        lines += [
            '  "lang": ISO 639-1 code of the spoken language.',
            'If the clip has no real speech (music, noise, silence), return {"text": "", "translation": "", "lang": ""}.',
            "Do not add commentary. Keep names and numbers.",
        ]
        if glossary:
            lines.append("Glossary (always use these translations):")
            lines += [f"- {k} => {v}" for k, v in glossary.items()]
        return "\n".join(lines)

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16_000) -> Transcript:
        wav = wav_bytes(audio, sample_rate)
        parts = [
            {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav).decode("ascii")}},
            {"text": "Transcribe" + (" and translate" if self.target_lang else "") + " this clip as instructed."},
        ]
        resp = self.client.generate(
            parts,
            system=self.system,
            temperature=0.1,
            max_tokens=1024,
            extra_config={"responseMimeType": "application/json", "thinkingConfig": {"thinkingBudget": 0}}
            if not self.client._no_thinking_config
            else {"responseMimeType": "application/json"},
        )
        raw = GeminiClient.text_of(resp)
        data = _parse_json(raw)
        text = (data.get("text") or "").strip()
        translation = (data.get("translation") or "").strip() if self.target_lang else None
        if looks_like_hallucination(text) and not translation:
            return Transcript(text="", language=None)
        return Transcript(text=text, language=(data.get("lang") or None), translation=translation or None)


def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                pass
    # không phải JSON: coi như transcript thô
    return {"text": raw}
