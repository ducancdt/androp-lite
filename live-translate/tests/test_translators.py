import livetranslate.http as http
from livetranslate.http import ApiError
from livetranslate.translate.anthropic import AnthropicTranslator
from livetranslate.translate.base import TranslationContext
from livetranslate.translate.gemini import GeminiClient, GeminiTranslator
from livetranslate.translate.openai_compat import OpenAICompatTranslator


class FakePost:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, payload, headers=None, **kw):
        self.calls.append((url, payload, headers))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def gemini_resp(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_gemini_translate(monkeypatch):
    fake = FakePost([gemini_resp(" Xin chào thế giới ")])
    monkeypatch.setattr("livetranslate.translate.gemini.post_json", fake)
    tr = GeminiTranslator("key", "gemini-2.5-flash", "vi", "en")
    ctx = TranslationContext()
    assert tr.translate("Hello world", ctx) == "Xin chào thế giới"
    url, payload, headers = fake.calls[0]
    assert url.endswith("models/gemini-2.5-flash:generateContent")
    assert headers["x-goog-api-key"] == "key"
    assert "Hello world" in payload["contents"][0]["parts"][0]["text"]
    assert payload["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}


def test_gemini_retries_without_thinking(monkeypatch):
    fake = FakePost([ApiError(400, "thinking is not supported"), gemini_resp("ok")])
    monkeypatch.setattr("livetranslate.translate.gemini.post_json", fake)
    c = GeminiClient("k", "gemini-2.5-flash")
    assert GeminiClient.text_of(c.generate([{"text": "x"}])) == "ok"
    assert "thinkingConfig" not in fake.calls[1][1]["generationConfig"]


def test_gemini_falls_back_when_model_missing(monkeypatch):
    fake = FakePost([ApiError(404, "not found"), gemini_resp("fallback ok")])
    monkeypatch.setattr("livetranslate.translate.gemini.post_json", fake)
    monkeypatch.setattr(
        "livetranslate.translate.gemini.get_json",
        lambda url, headers=None, **kw: {
            "models": [
                {"name": "models/gemini-9-pro", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-9-flash-tts", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-9-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-9-flash-lite", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/embedding-1", "supportedGenerationMethods": ["embedContent"]},
            ]
        },
    )
    c = GeminiClient("k", "gemini-old")
    assert GeminiClient.text_of(c.generate([{"text": "x"}])) == "fallback ok"
    assert c.model == "gemini-9-flash"
    assert fake.calls[1][0].endswith("models/gemini-9-flash:generateContent")


def test_openai_compat(monkeypatch):
    fake = FakePost([{"choices": [{"message": {"content": "Bonjour"}}]}])
    monkeypatch.setattr("livetranslate.translate.openai_compat.post_json", fake)
    tr = OpenAICompatTranslator("k", "https://api.groq.com/openai/v1/", "llama", "fr", "en")
    assert tr.translate("Hello") == "Bonjour"
    url, payload, headers = fake.calls[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert payload["messages"][0]["role"] == "system"
    assert headers["Authorization"] == "Bearer k"


def test_anthropic(monkeypatch):
    fake = FakePost([{"content": [{"type": "text", "text": "こんにちは"}]}])
    monkeypatch.setattr("livetranslate.translate.anthropic.post_json", fake)
    tr = AnthropicTranslator("k", "claude-x", "ja", "en")
    assert tr.translate("Hello") == "こんにちは"
    url, payload, headers = fake.calls[0]
    assert headers["anthropic-version"] == "2023-06-01"
    assert payload["system"]


def test_context_window():
    ctx = TranslationContext(max_lines=2)
    for i in range(4):
        ctx.add(f"s{i}", f"t{i}")
    assert ctx.pairs() == [("s2", "t2"), ("s3", "t3")]


def test_post_json_retries_on_503(monkeypatch):
    calls = {"n": 0}

    class R:
        def __init__(self, code, body):
            self.status_code = code
            self.text = body

        def json(self):
            import json

            return json.loads(self.text)

    def fake_post(url, headers=None, json=None, files=None, data=None, timeout=None):
        calls["n"] += 1
        return R(503, "busy") if calls["n"] == 1 else R(200, '{"ok": true}')

    monkeypatch.setattr(http.requests, "post", fake_post)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)
    assert http.post_json("https://x/y", {}) == {"ok": True}
    assert calls["n"] == 2
