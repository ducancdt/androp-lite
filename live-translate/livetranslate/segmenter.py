"""Cắt luồng âm thanh thành từng câu dựa trên năng lượng (VAD đơn giản, thuần numpy)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional

import numpy as np

from .audio import SAMPLE_RATE, rms


@dataclass
class Segment:
    audio: np.ndarray  # float32 mono 16 kHz
    start: float  # giây kể từ đầu luồng
    end: float
    index: int = 0

    @property
    def duration(self) -> float:
        return self.end - self.start


class Segmenter:
    """Nhận audio float32 16 kHz theo từng khối bất kỳ, trả ra Segment khi phát hiện hết câu.

    - Ngưỡng thích nghi: ``max(threshold, noise_floor * 3)`` với noise_floor là EMA RMS của các khung im lặng.
    - Kết thúc câu khi im lặng liên tục >= ``silence_ms`` hoặc câu dài quá ``max_segment_s``.
    - Bỏ qua câu ngắn hơn ``min_speech_ms``. Giữ ``pre_roll_ms`` âm thanh trước lúc bắt đầu nói.
    """

    FRAME_MS = 20
    KEEP_TAIL_FRAMES = 5  # 100 ms im lặng giữ lại cuối câu

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        silence_ms: int = 700,
        min_speech_ms: int = 500,
        max_segment_s: float = 15.0,
        threshold: float = 0.012,
        pre_roll_ms: int = 300,
    ):
        self.sr = sample_rate
        self.frame = int(sample_rate * self.FRAME_MS / 1000)
        self.silence_frames = max(1, silence_ms // self.FRAME_MS)
        self.min_speech_frames = max(1, min_speech_ms // self.FRAME_MS)
        self.max_frames = max(self.min_speech_frames + 1, int(max_segment_s * 1000 / self.FRAME_MS))
        self.threshold = threshold
        self.pre_roll_frames = max(0, pre_roll_ms // self.FRAME_MS)

        self._pending = np.zeros(0, dtype=np.float32)
        self._frames_seen = 0
        self._noise_floor = threshold
        self._pre_roll: List[np.ndarray] = []
        self._speech: List[np.ndarray] = []
        self._speech_frames = 0
        self._silence_run = 0
        self._in_speech = False
        self._start_frame = 0
        self._count = 0

    # ------------------------------------------------------------------
    def push(self, audio: np.ndarray) -> Iterator[Segment]:
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if audio.size == 0:
            return
        self._pending = np.concatenate([self._pending, audio]) if self._pending.size else audio
        while self._pending.size >= self.frame:
            frame = self._pending[: self.frame]
            self._pending = self._pending[self.frame :]
            seg = self._process_frame(frame)
            if seg is not None:
                yield seg

    def flush(self) -> Optional[Segment]:
        """Trả câu đang dang dở khi nguồn kết thúc."""
        if self._in_speech and self._speech_frames >= self.min_speech_frames:
            seg = self._emit()
            self._reset_speech()
            return seg
        self._reset_speech()
        return None

    # ------------------------------------------------------------------
    def _current_threshold(self) -> float:
        return max(self.threshold, self._noise_floor * 3.0)

    def _process_frame(self, frame: np.ndarray) -> Optional[Segment]:
        idx = self._frames_seen
        self._frames_seen += 1
        level = rms(frame)
        is_speech = level >= self._current_threshold()

        if not is_speech:
            # cập nhật nền ồn chậm, chỉ từ khung im lặng
            self._noise_floor = 0.98 * self._noise_floor + 0.02 * level

        if not self._in_speech:
            if is_speech:
                self._in_speech = True
                self._start_frame = idx - len(self._pre_roll)
                self._speech = list(self._pre_roll)
                self._speech.append(frame)
                self._speech_frames = 1
                self._silence_run = 0
            else:
                self._pre_roll.append(frame)
                if len(self._pre_roll) > self.pre_roll_frames:
                    self._pre_roll.pop(0)
            return None

        # đang trong câu
        self._speech.append(frame)
        self._speech_frames += 1
        if is_speech:
            self._silence_run = 0
        else:
            self._silence_run += 1

        end_of_sentence = self._silence_run >= self.silence_frames
        too_long = self._speech_frames >= self.max_frames
        if end_of_sentence or too_long:
            seg = None
            if self._speech_frames - self._silence_run >= self.min_speech_frames:
                # bỏ phần im lặng đuôi, giữ lại ~100 ms để STT không bị cụt
                keep = max(0, self._silence_run - self.KEEP_TAIL_FRAMES)
                seg = self._emit(trim_frames=keep)
            self._reset_speech()
            return seg
        return None

    def _emit(self, trim_frames: int = 0) -> Segment:
        frames = self._speech[: len(self._speech) - trim_frames] if trim_frames else self._speech
        audio = np.concatenate(frames) if frames else np.zeros(0, dtype=np.float32)
        start = self._start_frame * self.frame / self.sr
        end = start + audio.size / self.sr
        self._count += 1
        return Segment(audio=audio, start=max(0.0, start), end=end, index=self._count)

    def _reset_speech(self) -> None:
        self._in_speech = False
        self._speech = []
        self._speech_frames = 0
        self._silence_run = 0
        self._pre_roll = []
