"""Giọng đọc tiếng Việt VieNeu-TTS (https://github.com/pnnbao97/VieNeu-TTS, Apache-2.0).

- CPU: ONNX, không cần torch. ``precision="int8"`` nhanh hơn ~1.6x (cần CPU hỗ trợ VNNI).
- GPU: ``pip install "vieneu[cuda]"``.
- Nhân bản giọng: truyền ``voice_ref`` = file wav/mp3 3-10 giây giọng mẫu.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from .base import TextToSpeech

log = logging.getLogger(__name__)


class VieNeuTTS(TextToSpeech):
    name = "vieneu"

    def __init__(
        self,
        voice: str = "Mai Anh",
        voice_ref: Optional[str] = None,
        mode: str = "v3turbo",
        precision: str = "fp32",
        backend: str = "auto",
    ):
        try:
            from vieneu import Vieneu  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Cần VieNeu-TTS: pip install vieneu   (GPU: pip install \"vieneu[cuda]\")") from e
        kwargs = {}
        if mode == "v3turbo":
            kwargs["precision"] = precision
            kwargs["backend"] = backend
        log.info("Đang tải VieNeu-TTS (%s)... lần đầu sẽ tải model từ HuggingFace", mode)
        self.engine = Vieneu(mode=mode, **kwargs)
        self.sample_rate = int(getattr(self.engine, "sample_rate", 48_000))
        self.voice = voice
        if voice_ref:
            self.voice = self.add_voice(voice_ref)
        else:
            self._check_voice(voice)
        log.info("VieNeu-TTS sẵn sàng: giọng '%s', %d Hz", self.voice, self.sample_rate)

    # ------------------------------------------------------------------
    def list_voices(self) -> list:
        try:
            return [name for (_label, name) in self.engine.list_preset_voices()]
        except Exception:
            return []

    def _check_voice(self, voice: str) -> None:
        voices = self.list_voices()
        if voices and voice not in voices:
            resolver = getattr(self.engine, "resolve_voice_name", None)
            if resolver and resolver(voice):
                return
            log.warning("Giọng '%s' không có trong preset; các giọng có sẵn: %s", voice, ", ".join(voices))

    def add_voice(self, ref_path: str, name: Optional[str] = None) -> str:
        p = Path(ref_path)
        if not p.is_file():
            raise FileNotFoundError(f"Không thấy file giọng mẫu: {ref_path}")
        name = name or f"custom:{p.stem}"
        log.info("Đang nhân bản giọng từ %s ...", p.name)
        self.engine.add_voice(name, str(p), denoise=True)
        return name

    def synthesize(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(0, dtype=np.float32)
        kwargs = {"voice": self.voice}
        try:
            wav = self.engine.infer(text, show_progress=False, **kwargs)
        except TypeError:
            wav = self.engine.infer(text, **kwargs)
        return np.asarray(wav, dtype=np.float32).reshape(-1)


def default_voice_dir() -> str:
    return os.path.join(os.getcwd(), "voices")
