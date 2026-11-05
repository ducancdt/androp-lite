"""Prompt dịch dùng chung cho mọi nhà cung cấp."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import lang_name


def load_glossary(path: str) -> Dict[str, str]:
    """Đọc thuật ngữ: mỗi dòng ``thuật ngữ = bản dịch`` (bỏ qua # và dòng trống)."""
    out: Dict[str, str] = {}
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Không thấy file thuật ngữ: {path}")
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sep = "=" if "=" in line else ("\t" if "\t" in line else None)
        if not sep:
            continue
        k, _, v = line.partition(sep)
        if k.strip():
            out[k.strip()] = v.strip()
    return out


def build_system_prompt(target_lang: str, source_lang: Optional[str], glossary: Optional[Dict[str, str]] = None) -> str:
    tgt = lang_name(target_lang)
    src = lang_name(source_lang)
    lines = [
        "You are a professional simultaneous interpreter for a live broadcast.",
        f"Translate each utterance from {src} into {tgt}.",
        "Rules:",
        "- Output ONLY the translation. No quotes, no explanations, no notes, no language labels.",
        "- Keep it natural and spoken, as a human interpreter would say it aloud. Keep sentence meaning and tone.",
        "- Keep proper names, brand names, numbers and units. Do not add information.",
        "- The text comes from automatic speech recognition: fix obvious recognition errors from context, ignore filler words.",
        "- If the input is empty, only noise, or not real speech (e.g. music, laughter, random letters), output exactly: [skip]",
        "- Use the earlier lines only as context for consistency; never translate them again.",
    ]
    if target_lang.lower() == "vi":
        lines.append("- Dịch sang tiếng Việt tự nhiên, xưng hô phù hợp ngữ cảnh, không dịch word-by-word.")
    if glossary:
        lines.append("Glossary (always use these translations):")
        for k, v in glossary.items():
            lines.append(f"- {k} => {v}")
    return "\n".join(lines)


def build_user_prompt(text: str, history: List[Tuple[str, str]]) -> str:
    parts: List[str] = []
    if history:
        parts.append("Previous lines (context only, already translated):")
        for src, tr in history:
            parts.append(f"  source: {src}\n  translation: {tr}")
        parts.append("")
    parts.append("Translate this utterance:")
    parts.append(text)
    return "\n".join(parts)


_SKIP_RE = re.compile(r"^\s*\[?\s*skip\s*\]?\s*[.。]?\s*$", re.IGNORECASE)
_LABEL_RE = re.compile(r"^\s*(translation|bản dịch)\s*[:：]\s*", re.IGNORECASE)


def clean_translation(raw: str) -> str:
    """Bỏ nhãn, dấu ngoặc kép thừa, phát hiện [skip]."""
    t = (raw or "").strip()
    if not t or _SKIP_RE.match(t):
        return ""
    t = _LABEL_RE.sub("", t)
    # bỏ code fence nếu mô hình lỡ thêm
    if t.startswith("```"):
        t = t.strip("`").strip()
        if "\n" in t:
            t = t.split("\n", 1)[1].strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"“”'«»":
        t = t[1:-1].strip()
    if _SKIP_RE.match(t):
        return ""
    return t
