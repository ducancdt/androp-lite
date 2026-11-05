import numpy as np

from livetranslate.pipeline import Pipeline
from livetranslate.segmenter import Segmenter
from livetranslate.stt.base import SpeechToText, Transcript
from livetranslate.subtitles import SrtWriter, fmt_time, srt_block
from livetranslate.translate.base import Translator
from livetranslate.tts.base import TextToSpeech

SR = 16_000


def tone(seconds, amp=0.3):
    t = np.arange(int(seconds * SR)) / SR
    return (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


class FakeSTT(SpeechToText):
    name = "fake-stt"

    def __init__(self):
        self.n = 0

    def transcribe(self, audio, sample_rate=16_000):
        self.n += 1
        if self.n == 2:
            return Transcript(text="")  # câu không có lời
        return Transcript(text=f"hello {self.n}", language="en")


class FakeTranslator(Translator):
    name = "fake-mt"

    def _complete(self, system, user):
        return "xin chào " + user.rsplit("hello ", 1)[-1]


class FakeTTS(TextToSpeech):
    name = "fake-tts"
    sample_rate = 8_000

    def __init__(self):
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)
        return np.ones(800, dtype=np.float32) * 0.1


class FakePlayer:
    def __init__(self):
        self.chunks = []

    def enqueue(self, audio, rate):
        self.chunks.append((audio.size, rate))

    def wait_idle(self, timeout=None):
        pass


def frames(audio, chunk=1600):
    for i in range(0, audio.size, chunk):
        yield audio[i : i + chunk]


def test_pipeline_end_to_end(tmp_path):
    audio = np.concatenate([tone(1.0), np.zeros(SR, np.float32), tone(1.0), np.zeros(SR, np.float32), tone(1.0), np.zeros(SR, np.float32)])
    stt, mt, tts, player = FakeSTT(), FakeTranslator("vi", "en"), FakeTTS(), FakePlayer()
    lines = []
    srt_path = tmp_path / "out.srt"
    srt = SrtWriter(str(srt_path))
    p = Pipeline(frames(audio), Segmenter(silence_ms=500, min_speech_ms=300), stt, mt, tts, player=player, on_line=lines.append, srt=srt)
    p.run()
    srt.close()
    assert stt.n == 3
    assert [l.translation for l in lines] == ["xin chào 1", "xin chào 3"]
    assert tts.texts == ["xin chào 1", "xin chào 3"]
    assert player.chunks == [(800, 8000), (800, 8000)]
    assert p.errors == 0
    content = srt_path.read_text(encoding="utf-8")
    assert "1\n00:00:00" in content and "hello 1\nxin chào 1" in content
    assert p.snapshot(1)[0]["translation"] == "xin chào 3"


def test_pipeline_uses_direct_translation_from_stt():
    class DirectSTT(SpeechToText):
        name = "direct"
        translates_directly = True

        def transcribe(self, audio, sample_rate=16_000):
            return Transcript(text="hi", language="en", translation="chào")

    class BoomTranslator(Translator):
        def _complete(self, system, user):
            raise AssertionError("không được gọi")

    lines = []
    p = Pipeline(frames(tone(1.0)), Segmenter(min_speech_ms=300), DirectSTT(), BoomTranslator(), FakeTTS(), on_line=lines.append)
    p.run()
    assert [l.translation for l in lines] == ["chào"]


def test_pipeline_survives_stage_errors():
    class FlakySTT(SpeechToText):
        def transcribe(self, audio, sample_rate=16_000):
            raise RuntimeError("api down")

    lines = []
    p = Pipeline(frames(tone(1.0)), Segmenter(min_speech_ms=300), FlakySTT(), FakeTranslator(), FakeTTS(), on_line=lines.append)
    p.run()
    assert lines == [] and p.errors == 1


def test_srt_format():
    assert fmt_time(3661.5) == "01:01:01,500"
    block = srt_block(1, 0.0, 1.2, "xin chào", "hello")
    assert block == "1\n00:00:00,000 --> 00:00:01,200\nhello\nxin chào\n\n"
