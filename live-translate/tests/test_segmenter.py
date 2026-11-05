import numpy as np

from livetranslate.segmenter import Segmenter

SR = 16_000


def tone(seconds: float, amp: float = 0.3, freq: float = 220.0) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SR), dtype=np.float32)


def feed(seg: Segmenter, audio: np.ndarray, chunk: int = 1600):
    out = []
    for i in range(0, audio.size, chunk):
        out.extend(seg.push(audio[i : i + chunk]))
    return out


def test_splits_on_silence():
    seg = Segmenter(silence_ms=500, min_speech_ms=300, max_segment_s=10)
    audio = np.concatenate([silence(0.5), tone(1.0), silence(0.8), tone(1.5), silence(1.0)])
    segs = feed(seg, audio)
    assert len(segs) == 2
    assert abs(segs[0].start - 0.2) < 0.1  # pre-roll 300ms trước khi nói
    assert 1.0 <= segs[0].duration <= 2.0
    assert segs[1].start > segs[0].end
    assert segs[0].index == 1 and segs[1].index == 2


def test_ignores_short_blips():
    seg = Segmenter(silence_ms=400, min_speech_ms=500)
    audio = np.concatenate([tone(0.1), silence(1.0)])
    assert feed(seg, audio) == []


def test_force_cut_on_max_length():
    seg = Segmenter(silence_ms=700, min_speech_ms=300, max_segment_s=2.0)
    audio = tone(5.0)
    segs = feed(seg, audio)
    assert len(segs) == 2
    for s in segs:
        assert s.duration <= 2.05


def test_flush_returns_tail():
    seg = Segmenter(silence_ms=700, min_speech_ms=300)
    segs = feed(seg, tone(1.0))
    assert segs == []
    tail = seg.flush()
    assert tail is not None and tail.duration >= 1.0
    assert seg.flush() is None


def test_adaptive_noise_floor_ignores_hum():
    seg = Segmenter(silence_ms=500, min_speech_ms=300, threshold=0.003)
    hum = tone(6.0, amp=0.004, freq=50)
    segs = feed(seg, hum)
    # nền ồn nhỏ liên tục không được coi là lời nói mãi: tối đa 1 câu ban đầu trước khi ngưỡng thích nghi
    assert len(segs) <= 1
