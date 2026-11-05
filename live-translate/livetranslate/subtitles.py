"""Ghi phụ đề SRT (song ngữ) tăng dần."""
from __future__ import annotations

from typing import Optional


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    if ms == 1000:
        s += 1
        ms = 0
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def srt_block(index: int, start: float, end: float, translation: str, source: Optional[str] = None, bilingual: bool = True) -> str:
    lines = [str(index), f"{fmt_time(start)} --> {fmt_time(max(end, start + 0.5))}"]
    if bilingual and source:
        lines.append(source.strip())
    lines.append((translation or "").strip())
    return "\n".join(lines) + "\n\n"


class SrtWriter:
    def __init__(self, path: str, bilingual: bool = True):
        self.path = path
        self.bilingual = bilingual
        self._f = open(path, "w", encoding="utf-8")
        self._n = 0

    def add(self, start: float, end: float, translation: str, source: Optional[str] = None) -> None:
        if not (translation or "").strip():
            return
        self._n += 1
        self._f.write(srt_block(self._n, start, end, translation, source, self.bilingual))
        self._f.flush()

    def close(self) -> None:
        try:
            self._f.close()
        except Exception:
            pass
