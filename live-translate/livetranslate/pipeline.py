"""Chuỗi xử lý: nguồn → cắt câu → STT → dịch → TTS → phát / phụ đề.

Mỗi tầng chạy trên luồng riêng, nối bằng hàng đợi có giới hạn. Khi tầng sau chậm hơn tầng trước
(ví dụ CPU yếu), câu cũ nhất bị bỏ để độ trễ không tăng mãi.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

from .audio import SAMPLE_RATE, time_stretch
from .segmenter import Segment, Segmenter
from .stt.base import SpeechToText, Transcript
from .subtitles import SrtWriter
from .translate.base import TranslationContext, Translator
from .tts.base import TextToSpeech

log = logging.getLogger(__name__)


@dataclass
class Line:
    """Một câu đã xử lý xong (để hiển thị phụ đề / web)."""

    index: int
    start: float
    end: float
    source: str
    translation: str
    language: Optional[str] = None
    created: float = field(default_factory=time.time)
    stt_ms: int = 0
    mt_ms: int = 0
    tts_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "source": self.source,
            "translation": self.translation,
            "language": self.language,
            "latency_ms": self.stt_ms + self.mt_ms + self.tts_ms,
        }


class _DropOldestQueue(queue.Queue):
    def put_drop(self, item, on_drop: Optional[Callable] = None) -> None:
        while True:
            try:
                self.put_nowait(item)
                return
            except queue.Full:
                try:
                    dropped = self.get_nowait()
                    if on_drop:
                        on_drop(dropped)
                except queue.Empty:
                    pass


class Pipeline:
    def __init__(
        self,
        source_frames,  # iterator float32 16 kHz
        segmenter: Segmenter,
        stt: SpeechToText,
        translator: Translator,
        tts: TextToSpeech,
        player=None,
        on_line: Optional[Callable[[Line], None]] = None,
        srt: Optional[SrtWriter] = None,
        max_queue: int = 6,
        context_lines: int = 3,
        fit_duration: bool = False,
    ):
        self.source_frames = source_frames
        self.segmenter = segmenter
        self.stt = stt
        self.translator = translator
        self.tts = tts
        self.player = player
        self.on_line = on_line
        self.srt = srt
        self.fit_duration = fit_duration
        self.context = TranslationContext(max_lines=context_lines)

        self._seg_q: _DropOldestQueue = _DropOldestQueue(maxsize=max_queue)
        self._tts_q: _DropOldestQueue = _DropOldestQueue(maxsize=max_queue)
        self._stop = threading.Event()
        self._stream_done = threading.Event()
        self._seg_count = 0
        self.stream_drain_s = 8.0  # chờ STT streaming xả nốt sau khi hết âm thanh
        self._threads: List[threading.Thread] = []
        self.lines: List[Line] = []
        self.dropped = 0
        self.errors = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    @property
    def streaming(self) -> bool:
        """STT streaming (vd WhisperLiveKit) tự chốt câu; bỏ qua bộ cắt câu VAD."""
        return bool(getattr(self.stt, "streaming", False))

    def run(self) -> None:
        """Chạy chặn đến khi nguồn kết thúc hoặc ``stop()``."""
        if self.streaming:
            self.stt.start()
            first = threading.Thread(target=self._stream_worker, name="stt-stream-mt", daemon=True)
        else:
            first = threading.Thread(target=self._stt_worker, name="stt-mt", daemon=True)
        workers = [first, threading.Thread(target=self._tts_worker, name="tts", daemon=True)]
        for t in workers:
            t.start()
        self._threads = workers
        try:
            if self.streaming:
                self._ingest_streaming()
            else:
                self._ingest()
        finally:
            if self.streaming:
                self._stream_done.set()
            else:
                self._seg_q.put(None)
            workers[0].join()
            self._tts_q.put(None)
            workers[1].join()
            if self.player is not None:
                self.player.wait_idle(timeout=120)

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------
    def _ingest(self) -> None:
        for chunk in self.source_frames:
            if self._stop.is_set():
                break
            for seg in self.segmenter.push(chunk):
                self._enqueue_segment(seg)
        if not self._stop.is_set():
            tail = self.segmenter.flush()
            if tail is not None:
                self._enqueue_segment(tail)

    def _ingest_streaming(self) -> None:
        for chunk in self.source_frames:
            if self._stop.is_set():
                break
            self.stt.feed(chunk, SAMPLE_RATE)
        self.stt.finish()

    def _stream_worker(self) -> None:
        """Lấy câu đã chốt từ STT streaming rồi dịch/đọc như đường thường."""
        idle_after_done = 0.0
        while not self._stop.is_set():
            try:
                line = self.stt.poll(timeout=0.2)
            except Exception as e:
                self.errors += 1
                log.error("Lỗi STT streaming: %s", e)
                if self._stream_done.is_set():
                    return
                time.sleep(0.5)
                continue
            if line is None:
                if self._stream_done.is_set():
                    idle_after_done += 0.2
                    if idle_after_done >= self.stream_drain_s:
                        return
                continue
            idle_after_done = 0.0
            self._seg_count += 1
            try:
                self._handle_transcript(
                    line.to_transcript(), index=self._seg_count, start=line.start, end=line.end, stt_ms=0
                )
            except Exception as e:
                self.errors += 1
                log.error("Lỗi xử lý câu #%d: %s", self._seg_count, e, exc_info=log.isEnabledFor(logging.DEBUG))

    def _enqueue_segment(self, seg: Segment) -> None:
        def on_drop(old):
            self.dropped += 1
            log.warning("Quá tải: bỏ câu #%d (%.1fs) để giữ độ trễ", old.index, old.duration)

        self._seg_q.put_drop(seg, on_drop)

    def _stt_worker(self) -> None:
        while True:
            seg = self._seg_q.get()
            if seg is None:
                return
            if self._stop.is_set():
                continue
            try:
                self._process_segment(seg)
            except Exception as e:  # không để một câu lỗi làm dừng cả chương trình
                self.errors += 1
                log.error("Lỗi xử lý câu #%d: %s", seg.index, e, exc_info=log.isEnabledFor(logging.DEBUG))

    def _process_segment(self, seg: Segment) -> None:
        t0 = time.monotonic()
        tr: Transcript = self.stt.transcribe(seg.audio, SAMPLE_RATE)
        stt_ms = int((time.monotonic() - t0) * 1000)
        self._handle_transcript(tr, index=seg.index, start=seg.start, end=seg.end, stt_ms=stt_ms)

    def _handle_transcript(self, tr: Transcript, *, index: int, start: float, end: float, stt_ms: int) -> None:
        if tr.empty:
            log.debug("Câu #%d: không có lời", index)
            return
        t1 = time.monotonic()
        source = (tr.text or "").strip()
        if tr.translation is not None:
            translation = tr.translation.strip()
        else:
            translation = self.translator.translate(source, self.context)
        t2 = time.monotonic()
        if not translation:
            log.debug("Câu #%d: bỏ qua (%r)", index, source[:40])
            return
        self.context.add(source or translation, translation)
        line = Line(
            index=index,
            start=start,
            end=end,
            source=source,
            translation=translation,
            language=tr.language,
            stt_ms=stt_ms,
            mt_ms=int((t2 - t1) * 1000),
        )
        with self._lock:
            self.lines.append(line)
            if len(self.lines) > 500:
                del self.lines[: len(self.lines) - 500]
        if self.srt is not None:
            self.srt.add(start, end, translation, source)
        if self.on_line:
            try:
                self.on_line(line)
            except Exception:
                pass
        self._tts_q.put_drop(line, lambda old: log.warning("Quá tải TTS: bỏ đọc câu #%d", old.index))

    def _tts_worker(self) -> None:
        while True:
            line = self._tts_q.get()
            if line is None:
                return
            if self._stop.is_set():
                continue
            try:
                t0 = time.monotonic()
                audio = self.tts.synthesize(line.translation)
                line.tts_ms = int((time.monotonic() - t0) * 1000)
                if audio.size == 0:
                    continue
                if self.fit_duration:
                    src_dur = max(0.3, line.end - line.start)
                    out_dur = audio.size / float(self.tts.sample_rate)
                    ratio = out_dur / src_dur
                    if ratio > 1.05:
                        audio = time_stretch(audio, min(ratio, 1.6), self.tts.sample_rate)
                if self.player is not None:
                    self.player.enqueue(audio, self.tts.sample_rate)
            except Exception as e:
                self.errors += 1
                log.error("Lỗi TTS câu #%d: %s", line.index, e)

    # ------------------------------------------------------------------
    def snapshot(self, n: int = 8) -> List[dict]:
        with self._lock:
            return [ln.to_dict() for ln in self.lines[-n:]]
