"""Cấu hình: đọc .env + biến môi trường + tham số dòng lệnh."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def load_dotenv(path: Optional[str] = None) -> dict:
    """Đọc file .env đơn giản (KEY=VALUE, bỏ qua # và dòng trống). Không ghi đè biến đã có."""
    p = Path(path or ".env")
    loaded: dict = {}
    if not p.is_file():
        return loaded
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
        loaded[key] = value
    return loaded


LANG_NAMES = {
    "vi": "Vietnamese (tiếng Việt)",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "th": "Thai",
    "ru": "Russian",
    "id": "Indonesian",
    "pt": "Portuguese",
    "it": "Italian",
    "ar": "Arabic",
    "hi": "Hindi",
}


def lang_name(code: Optional[str]) -> str:
    if not code:
        return "the source language"
    return LANG_NAMES.get(code.lower(), code)


@dataclass
class Settings:
    # Nguồn âm thanh: URL (YouTube, Twitch, ...), "mic", "mic:<device>", "device:<ffmpeg args>", "file:<path>"
    source: str = "mic"
    source_lang: Optional[str] = None  # None = tự nhận dạng
    target_lang: str = "vi"

    # Nhận dạng giọng nói
    stt: str = "whisper"  # whisper | gemini | openai
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute: str = "int8"

    # Dịch
    translator: str = "gemini"  # gemini | openai | anthropic | none
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_stt_model: str = "whisper-1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    glossary: Optional[str] = None
    context_lines: int = 3

    # Giọng đọc
    tts: str = "vieneu"  # vieneu | gemini | none
    voice: str = "Mai Anh"
    voice_ref: Optional[str] = None  # file wav 3-10s để nhân bản giọng
    vieneu_mode: str = "v3turbo"  # v3turbo | v3nano
    vieneu_precision: str = "fp32"  # fp32 | int8 (CPU)
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_tts_voice: str = "Kore"
    fit_duration: bool = False  # tăng tốc giọng đọc nếu dài hơn câu gốc

    # Cắt câu
    silence_ms: int = 700
    min_speech_ms: int = 500
    max_segment_s: float = 15.0
    vad_threshold: float = 0.012

    # Đầu ra
    play: bool = True
    output_device: Optional[str] = None
    save_srt: Optional[str] = None
    save_audio: Optional[str] = None
    web_port: Optional[int] = None
    max_queue: int = 6
    realtime_file: bool = False  # phát file theo thời gian thực thay vì chạy nhanh nhất có thể
    verbose: bool = False

    extra: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "Settings":
        s = cls()
        env = os.environ.get
        s.gemini_api_key = env("GEMINI_API_KEY", "") or env("GOOGLE_API_KEY", "")
        s.gemini_model = env("GEMINI_MODEL", s.gemini_model)
        s.openai_api_key = env("OPENAI_API_KEY", "")
        s.openai_base_url = env("OPENAI_BASE_URL", s.openai_base_url).rstrip("/")
        s.openai_model = env("OPENAI_MODEL", s.openai_model)
        s.openai_stt_model = env("OPENAI_STT_MODEL", s.openai_stt_model)
        s.anthropic_api_key = env("ANTHROPIC_API_KEY", "")
        s.anthropic_model = env("ANTHROPIC_MODEL", s.anthropic_model)
        s.target_lang = env("LT_TARGET_LANG", s.target_lang)
        s.voice = env("LT_VOICE", s.voice)
        s.gemini_tts_model = env("GEMINI_TTS_MODEL", s.gemini_tts_model)
        s.gemini_tts_voice = env("GEMINI_TTS_VOICE", s.gemini_tts_voice)
        if env("LT_TRANSLATOR"):
            s.translator = env("LT_TRANSLATOR", s.translator)
        elif not s.gemini_api_key:
            # Tự chọn nhà cung cấp theo khóa có sẵn
            if s.openai_api_key:
                s.translator = "openai"
            elif s.anthropic_api_key:
                s.translator = "anthropic"
        return s
