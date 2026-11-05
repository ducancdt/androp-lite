"""Tiện ích âm thanh thuần numpy: PCM16 <-> float32, resample, WAV, RMS."""
from __future__ import annotations

import io
import wave

import numpy as np

SAMPLE_RATE = 16_000  # tần số chuẩn cho STT


def pcm16_to_float32(data: bytes) -> np.ndarray:
    if len(data) % 2:
        data = data[:-1]
    return np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0


def float32_to_pcm16(audio: np.ndarray) -> bytes:
    clipped = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


def to_mono(audio: np.ndarray) -> np.ndarray:
    a = np.asarray(audio, dtype=np.float32)
    if a.ndim == 2:
        return a.mean(axis=1)
    return a


def resample_linear(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Resample tuyến tính. Đủ tốt cho phát lại; STT dùng 16k trực tiếp từ ffmpeg."""
    audio = to_mono(audio)
    if src_rate == dst_rate or audio.size == 0:
        return audio
    n_out = int(round(audio.size * dst_rate / src_rate))
    if n_out <= 1:
        return audio[:1]
    x_old = np.linspace(0.0, 1.0, num=audio.size, endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(float32_to_pcm16(audio))
    return buf.getvalue()


def read_wav_bytes(data: bytes) -> tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(data), "rb") as w:
        rate = w.getframerate()
        ch = w.getnchannels()
        width = w.getsampwidth()
        frames = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError(f"Chỉ hỗ trợ WAV 16-bit, nhận {width * 8}-bit")
    audio = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        audio = audio.reshape(-1, ch).mean(axis=1)
    return audio, rate


def rms(audio: np.ndarray) -> float:
    a = np.asarray(audio, dtype=np.float32)
    if a.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(a * a)))


def time_stretch(audio: np.ndarray, rate: float, sample_rate: int) -> np.ndarray:
    """Tăng tốc giọng đọc (rate > 1 = nhanh hơn) giữ cao độ. Cần librosa; nếu không có thì trả nguyên."""
    if rate <= 1.0 or audio.size == 0:
        return audio
    try:
        import librosa  # type: ignore

        return librosa.effects.time_stretch(np.asarray(audio, dtype=np.float32), rate=rate)
    except Exception:
        return audio


class WavWriter:
    """Ghi WAV 16-bit mono tăng dần (để lưu bản dịch đã đọc)."""

    def __init__(self, path: str, sample_rate: int):
        self.sample_rate = sample_rate
        self._w = wave.open(path, "wb")
        self._w.setnchannels(1)
        self._w.setsampwidth(2)
        self._w.setframerate(sample_rate)

    def write(self, audio: np.ndarray, src_rate: int | None = None) -> None:
        if src_rate and src_rate != self.sample_rate:
            audio = resample_linear(audio, src_rate, self.sample_rate)
        self._w.writeframes(float32_to_pcm16(audio))

    def close(self) -> None:
        try:
            self._w.close()
        except Exception:
            pass
