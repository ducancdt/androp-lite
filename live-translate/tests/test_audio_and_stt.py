import json

import numpy as np

from livetranslate.audio import float32_to_pcm16, pcm16_to_float32, read_wav_bytes, resample_linear, wav_bytes
from livetranslate.config import Settings, load_dotenv
from livetranslate.stt.base import looks_like_hallucination
from livetranslate.stt.gemini_stt import GeminiAudio, _parse_json


def test_pcm_roundtrip():
    a = np.linspace(-0.9, 0.9, 100).astype(np.float32)
    b = pcm16_to_float32(float32_to_pcm16(a))
    assert np.allclose(a, b, atol=1e-4)


def test_wav_roundtrip():
    a = np.sin(np.arange(1600) / 10).astype(np.float32) * 0.5
    audio, rate = read_wav_bytes(wav_bytes(a, 16_000))
    assert rate == 16_000 and audio.size == 1600
    assert np.allclose(a, audio, atol=1e-3)


def test_resample():
    a = np.zeros(48_000, np.float32)
    assert resample_linear(a, 48_000, 16_000).size == 16_000
    assert resample_linear(a, 16_000, 16_000) is a


def test_hallucination_filter():
    assert looks_like_hallucination("")
    assert looks_like_hallucination("...")
    assert looks_like_hallucination("Thanks for watching!")
    assert looks_like_hallucination("you you you you you you")
    assert not looks_like_hallucination("Thanks for watching, now let's look at the next chart of the quarter.")
    assert not looks_like_hallucination("The weather is nice today.")


def test_parse_json_variants():
    assert _parse_json('{"text": "a", "translation": "b"}') == {"text": "a", "translation": "b"}
    assert _parse_json('```json\n{"text": "a"}\n```') == {"text": "a"}
    assert _parse_json('noise {"text": "x"} tail') == {"text": "x"}
    assert _parse_json("plain words") == {"text": "plain words"}


def test_gemini_audio_direct(monkeypatch):
    calls = []

    def fake_post(url, payload, headers=None, **kw):
        calls.append(payload)
        return {"candidates": [{"content": {"parts": [{"text": json.dumps({"text": "hello", "translation": "xin chào", "lang": "en"})}]}}]}

    monkeypatch.setattr("livetranslate.translate.gemini.post_json", fake_post)
    stt = GeminiAudio("k", "gemini-2.5-flash", source_lang="en", target_lang="vi")
    assert stt.translates_directly
    tr = stt.transcribe(np.zeros(16_000, np.float32))
    assert (tr.text, tr.translation, tr.language) == ("hello", "xin chào", "en")
    parts = calls[0]["contents"][0]["parts"]
    assert parts[0]["inline_data"]["mime_type"] == "audio/wav"
    assert calls[0]["generationConfig"]["responseMimeType"] == "application/json"


def test_dotenv_and_settings(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('GEMINI_API_KEY="abc"\n# c\nLT_VOICE=Hải Đăng\nOPENAI_BASE_URL=https://x/v1/\n', encoding="utf-8")
    for k in ("GEMINI_API_KEY", "LT_VOICE", "OPENAI_BASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LT_TRANSLATOR"):
        monkeypatch.delenv(k, raising=False)
    load_dotenv(str(env))
    s = Settings.from_env()
    assert s.gemini_api_key == "abc" and s.voice == "Hải Đăng" and s.openai_base_url == "https://x/v1"
    assert s.translator == "gemini"
    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert Settings.from_env().translator == "openai"
