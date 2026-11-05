import asyncio
import json
import threading

import numpy as np
import pytest

from livetranslate.pipeline import Pipeline
from livetranslate.segmenter import Segmenter
from livetranslate.stt.streaming import LineCommitter, StreamLine, StreamingSTT, WhisperLiveKitStream, parse_wlk_time
from livetranslate.translate.base import Translator
from livetranslate.tts.base import TextToSpeech


def test_parse_wlk_time():
    assert parse_wlk_time("0:00:01.50") == pytest.approx(1.5)
    assert parse_wlk_time("1:02:03.25") == pytest.approx(3723.25)
    assert parse_wlk_time(4.5) == 4.5
    assert parse_wlk_time(None) == 0.0


def line(text, start="0:00:00.00", end="0:00:01.00", speaker=1):
    return {"speaker": speaker, "text": text, "start": start, "end": end}


def test_committer_commits_previous_line_when_new_line_appears():
    c = LineCommitter(settle_s=1.0, max_wait_s=4.0)
    assert c.update([line("Hello there")], now=0.0) == []
    out = c.update([line("Hello there"), line("Next one", "0:00:01.00", "0:00:02.00")], now=0.1)
    assert [o.text for o in out] == ["Hello there"]
    assert out[0].start == 0.0 and out[0].end == 1.0
    # dòng cuối chưa chốt, lặp lại không phát lại dòng đầu
    assert c.update([line("Hello there"), line("Next one")], now=0.2) == []


def test_committer_settles_on_punctuation_and_max_wait():
    c = LineCommitter(settle_s=1.0, max_wait_s=4.0)
    assert c.update([line("I think so.")], now=0.0) == []
    assert c.update([line("I think so.")], now=0.5) == []
    assert [o.text for o in c.update([line("I think so.")], now=1.1)] == ["I think so."]
    # không dấu câu: chờ max_wait
    assert c.update([line("I think so."), line("and then we")], now=1.2) == []
    assert c.update([line("I think so."), line("and then we")], now=3.0) == []
    assert [o.text for o in c.update([line("I think so."), line("and then we")], now=5.3)] == ["and then we"]


def test_committer_emits_only_appended_tail():
    c = LineCommitter(settle_s=1.0, max_wait_s=4.0)
    c.update([line("First part.")], now=0.0)
    assert [o.text for o in c.update([line("First part.")], now=1.5)] == ["First part."]
    # cùng dòng dài thêm → chỉ phát phần mới
    out = c.update([line("First part. Second part.")], now=1.6)
    assert out == []
    out = c.update([line("First part. Second part.")], now=3.0)
    assert [o.text for o in out] == ["Second part."]


def test_committer_silence_marker_and_final():
    c = LineCommitter(settle_s=5.0, max_wait_s=50.0)
    out = c.update([line("Quick."), {"speaker": -2, "text": "", "start": "0:00:01.00", "end": "0:00:02.00"}], now=0.0)
    assert [o.text for o in out] == ["Quick."]
    c2 = LineCommitter(settle_s=5.0, max_wait_s=50.0)
    assert [o.text for o in c2.update([line("unfinished")], now=0.0, final=True)] == ["unfinished"]


# ----------------------------------------------------------------------------
async def _fake_wlk_server(received, stop_event, host="127.0.0.1"):
    import websockets

    async def handler(ws):
        await ws.send(json.dumps({"type": "config", "useAudioWorklet": True, "mode": "full"}))
        total = 0
        async for msg in ws:
            if isinstance(msg, bytes):
                if not msg:
                    break
                total += len(msg)
                received.append(len(msg))
                if total >= 3200:
                    state = {"status": "active", "lines": [line("hello world."), line("second line", "0:00:01.00", "0:00:02.50")], "buffer_transcription": ""}
                    await ws.send(json.dumps(state))
        await ws.send(json.dumps({"status": "active", "lines": [line("hello world."), line("second line.", "0:00:01.00", "0:00:02.50")]}))
        await ws.send(json.dumps({"type": "ready_to_stop"}))

    async with websockets.serve(handler, host, 0) as server:
        port = server.sockets[0].getsockname()[1]
        stop_event.port = port
        stop_event.ready.set()
        await stop_event.done.wait()


class _Ctl:
    def __init__(self):
        self.ready = threading.Event()
        self.port = None
        self.done = None


def _start_server(received):
    ctl = _Ctl()

    def run():
        async def main():
            ctl.done = asyncio.Event()
            await _fake_wlk_server(received, ctl)

        asyncio.run(main())

    t = threading.Thread(target=run, daemon=True)
    t.start()
    assert ctl.ready.wait(5)
    return ctl


def test_wlk_client_end_to_end():
    pytest.importorskip("websockets")
    received = []
    ctl = _start_server(received)
    stt = WhisperLiveKitStream(url=f"ws://127.0.0.1:{ctl.port}/asr", language="en", settle_s=0.3, max_wait_s=1.0)
    assert stt._full_url().endswith("/asr?language=en")
    stt.start()
    chunk = np.zeros(1600, np.float32)  # 100 ms
    for _ in range(3):
        stt.feed(chunk)
    stt.finish()
    got = []
    for _ in range(50):
        ln = stt.poll(timeout=0.2)
        if ln is not None:
            got.append(ln)
        if len(got) >= 2:
            break
    stt.close()
    assert [g.text for g in got] == ["hello world.", "second line."]
    assert got[1].start == 1.0 and got[1].end == 2.5
    assert received == [3200, 3200, 3200]


# ----------------------------------------------------------------------------
class FakeStream(StreamingSTT):
    name = "fake-stream"

    def __init__(self):
        self.fed = 0
        self.started = False
        self.finished = False
        self._lines = [StreamLine("one.", 0.0, 1.0, "en"), StreamLine("two.", 1.0, 2.0, "en")]

    def start(self):
        self.started = True

    def feed(self, audio, sample_rate=16000):
        self.fed += audio.size

    def finish(self):
        self.finished = True

    def poll(self, timeout=0.2):
        if self.fed >= 1600 and self._lines:
            return self._lines.pop(0)
        return None


class FakeTranslator(Translator):
    def _complete(self, system, user):
        return "vi:" + user.rsplit("\n", 1)[-1]


class FakeTTS(TextToSpeech):
    sample_rate = 8000

    def __init__(self):
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)
        return np.zeros(80, np.float32)


def test_pipeline_streaming_path():
    stt, tts, lines = FakeStream(), FakeTTS(), []
    p = Pipeline(iter([np.zeros(1600, np.float32)] * 2), Segmenter(), stt, FakeTranslator(), tts, on_line=lines.append)
    p.stream_drain_s = 0.6
    p.run()
    assert stt.started and stt.finished and stt.fed == 3200
    assert [l.translation for l in lines] == ["vi:one.", "vi:two."]
    assert [l.start for l in lines] == [0.0, 1.0]
    assert tts.texts == ["vi:one.", "vi:two."]
    assert p.errors == 0
