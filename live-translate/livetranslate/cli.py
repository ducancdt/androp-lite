"""Dòng lệnh: livetranslate --source <URL|mic|file:...> [tuỳ chọn]."""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import Optional

from . import __version__
from .config import Settings, load_dotenv

log = logging.getLogger("livetranslate")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="livetranslate",
        description="Dịch trực tiếp YouTube / livestream / mic sang tiếng Việt và đọc bằng giọng VieNeu-TTS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ví dụ:\n"
            "  livetranslate --source https://www.youtube.com/watch?v=XXXX\n"
            "  livetranslate --source mic --source-lang en\n"
            '  livetranslate --source "device:-f dshow -i audio=Stereo Mix (Realtek(R) Audio)"\n'
            "  livetranslate --source file:video.mp4 --save-srt out.srt --save-audio out.wav --no-play\n"
            "  livetranslate --source <url> --stt gemini            # Gemini nghe + dịch trong 1 lần gọi\n"
            "  livetranslate --source <url> --stt wlk               # streaming qua server WhisperLiveKit (độ trễ thấp nhất)\n"
            "  livetranslate --source <url> --translator openai     # OpenAI/Groq/OpenRouter/Ollama\n"
        ),
    )
    p.add_argument("--source", "-s", help="URL (YouTube, Twitch, Facebook, TikTok...), 'mic', 'mic:<thiết bị>', 'device:<ffmpeg args>', 'file:<đường dẫn>'")
    p.add_argument("--source-lang", help="Mã ngôn ngữ nguồn (en, ja, ko, zh...). Bỏ trống = tự nhận dạng")
    p.add_argument("--target", "-t", dest="target_lang", help="Ngôn ngữ đích (mặc định vi)")
    p.add_argument("--stt", choices=["whisper", "gemini", "openai", "wlk"], help="Nhận dạng giọng nói: whisper (offline, theo câu), gemini, openai, wlk (streaming qua server WhisperLiveKit)")
    p.add_argument("--wlk-url", help="WebSocket của server WhisperLiveKit (mặc định ws://127.0.0.1:8000/asr)")
    p.add_argument("--wlk-settle", type=float, dest="wlk_settle_s", help="Giây dòng cuối đứng yên để chốt câu (mặc định 1.2)")
    p.add_argument("--whisper-model", help="tiny/base/small/medium/large-v3 hoặc tên model faster-whisper (mặc định small)")
    p.add_argument("--whisper-device", help="cpu hoặc cuda")
    p.add_argument("--translator", choices=["gemini", "openai", "anthropic", "none"], help="Nhà cung cấp dịch")
    p.add_argument("--model", help="Ghi đè tên model của nhà cung cấp dịch đã chọn")
    p.add_argument("--glossary", help="File thuật ngữ: mỗi dòng 'từ = bản dịch'")
    p.add_argument("--tts", choices=["vieneu", "gemini", "none"], help="Giọng đọc (mặc định vieneu)")
    p.add_argument("--voice", help="Tên giọng VieNeu (vd 'Mai Anh', 'Hải Đăng') hoặc giọng Gemini TTS")
    p.add_argument("--voice-ref", help="File wav/mp3 3-10 giây để nhân bản giọng (VieNeu)")
    p.add_argument("--vieneu-mode", choices=["v3turbo", "v3nano"], help="v3turbo (48 kHz, chất lượng) hoặc v3nano (nhẹ, nhanh)")
    p.add_argument("--vieneu-precision", choices=["fp32", "int8"], help="int8 nhanh hơn trên CPU hỗ trợ VNNI")
    p.add_argument("--fit-duration", action="store_true", help="Tăng tốc giọng đọc khi dài hơn câu gốc (cần librosa)")
    p.add_argument("--silence-ms", type=int, help="Im lặng (ms) để kết thúc câu, mặc định 700")
    p.add_argument("--max-segment", type=float, help="Độ dài tối đa một câu (giây), mặc định 15")
    p.add_argument("--vad-threshold", type=float, help="Ngưỡng năng lượng phát hiện tiếng nói (0.005-0.05), mặc định 0.012")
    p.add_argument("--no-play", action="store_true", help="Không phát ra loa")
    p.add_argument("--output-device", help="Tên/chỉ số thiết bị phát (vd VB-Cable để đưa vào OBS/Zoom)")
    p.add_argument("--save-srt", help="Ghi phụ đề song ngữ .srt")
    p.add_argument("--save-audio", help="Ghi giọng đọc bản dịch .wav")
    p.add_argument("--web", type=int, metavar="PORT", help="Bật trang phụ đề web tại http://127.0.0.1:PORT/")
    p.add_argument("--web-host", default="127.0.0.1", help="Địa chỉ lắng nghe cho web (0.0.0.0 để máy khác xem)")
    p.add_argument("--realtime", action="store_true", help="Với file: xử lý theo thời gian thực thay vì nhanh nhất có thể")
    p.add_argument("--max-queue", type=int, help="Số câu tối đa chờ xử lý trước khi bỏ bớt (mặc định 6)")
    p.add_argument("--env", help="Đường dẫn file .env (mặc định ./.env)")
    p.add_argument("--list-voices", action="store_true", help="Liệt kê giọng VieNeu rồi thoát")
    p.add_argument("--list-devices", action="store_true", help="Liệt kê thiết bị âm thanh rồi thoát")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--version", action="version", version=f"livetranslate {__version__}")
    return p


def apply_args(s: Settings, a: argparse.Namespace) -> Settings:
    for key in (
        "source", "source_lang", "target_lang", "stt", "whisper_model", "whisper_device", "translator",
        "glossary", "tts", "voice", "voice_ref", "vieneu_mode", "vieneu_precision", "silence_ms",
        "vad_threshold", "output_device", "save_srt", "save_audio", "max_queue", "wlk_url", "wlk_settle_s",
    ):
        v = getattr(a, key, None)
        if v is not None:
            setattr(s, key, v)
    if a.max_segment is not None:
        s.max_segment_s = a.max_segment
    if a.model:
        if s.translator == "gemini":
            s.gemini_model = a.model
        elif s.translator == "openai":
            s.openai_model = a.model
        elif s.translator == "anthropic":
            s.anthropic_model = a.model
    if a.fit_duration:
        s.fit_duration = True
    if a.no_play:
        s.play = False
    if a.web is not None:
        s.web_port = a.web
    s.realtime_file = bool(a.realtime)
    s.verbose = bool(a.verbose)
    s.extra["web_host"] = a.web_host
    return s


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s" if verbose else "%(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("urllib3", "requests", "huggingface_hub", "filelock"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    a = parser.parse_args(argv)
    setup_logging(a.verbose)
    load_dotenv(a.env)
    s = apply_args(Settings.from_env(), a)

    if a.list_devices:
        from .sources.mic import list_devices

        print(list_devices())
        return 0
    if a.list_voices:
        from .tts.vieneu_tts import VieNeuTTS

        tts = VieNeuTTS(voice=s.voice, mode=s.vieneu_mode, precision=s.vieneu_precision)
        print("\n".join(tts.list_voices()))
        return 0
    if not s.source:
        parser.error("cần --source (URL, mic, device:..., file:...)")

    return run(s)


def run(s: Settings) -> int:
    from .pipeline import Pipeline
    from .player import AudioPlayer
    from .segmenter import Segmenter
    from .sources import make_source
    from .stt import make_stt
    from .subtitles import SrtWriter
    from .translate import make_translator
    from .tts import make_tts

    log.info("livetranslate %s — nguồn: %s", __version__, s.source)
    source = make_source(s.source, realtime_file=s.realtime_file, verbose=s.verbose)
    stt = make_stt(s)
    translator = make_translator(s) if not getattr(stt, "translates_directly", False) else None
    if translator is None:
        from .translate.base import PassthroughTranslator

        translator = PassthroughTranslator()
        log.info("STT '%s' trả thẳng bản dịch; bỏ qua tầng dịch riêng", stt.name)
    tts = make_tts(s)
    player = AudioPlayer(play=s.play and tts.name != "none", device=s.output_device, save_path=s.save_audio, save_rate=tts.sample_rate)
    srt = SrtWriter(s.save_srt) if s.save_srt else None
    segmenter = Segmenter(
        silence_ms=s.silence_ms,
        min_speech_ms=s.min_speech_ms,
        max_segment_s=s.max_segment_s,
        threshold=s.vad_threshold,
    )

    def on_line(line) -> None:
        src = f"  [{line.language or '?'}] {line.source}\n" if line.source and line.source != line.translation else ""
        print(f"{src}  → {line.translation}   ({line.stt_ms + line.mt_ms} ms)", flush=True)

    pipeline = Pipeline(
        source.frames(),
        segmenter,
        stt,
        translator,
        tts,
        player=player,
        on_line=on_line,
        srt=srt,
        max_queue=s.max_queue,
        context_lines=s.context_lines,
        fit_duration=s.fit_duration,
    )

    web = None
    if s.web_port:
        from .webui import SubtitleServer

        def status() -> dict:
            last = pipeline.lines[-1] if pipeline.lines else None
            return {
                "source": s.source[:60],
                "stt": stt.name,
                "translator": translator.name,
                "tts": tts.name,
                "lines": len(pipeline.lines),
                "dropped": pipeline.dropped,
                "last_latency_ms": (last.stt_ms + last.mt_ms + last.tts_ms) if last else None,
            }

        web = SubtitleServer(s.web_port, pipeline.snapshot, status, host=s.extra.get("web_host", "127.0.0.1")).start()

    def handle_sig(signum, frame):  # noqa: ARG001
        log.info("Đang dừng...")
        pipeline.stop()
        source.close()

    signal.signal(signal.SIGINT, handle_sig)
    try:
        signal.signal(signal.SIGTERM, handle_sig)
    except Exception:
        pass

    t0 = time.monotonic()
    log.info("Sẵn sàng. STT=%s | dịch=%s | giọng=%s. Nhấn Ctrl+C để dừng.", stt.name, translator.name, tts.name)
    try:
        pipeline.run()
    finally:
        source.close()
        player.close(drain=not pipeline._stop.is_set())
        if srt:
            srt.close()
        if web:
            web.close()
        stt.close()
        tts.close()
        log.info(
            "Kết thúc sau %.0fs: %d câu, %d bỏ qua do quá tải, %d lỗi.",
            time.monotonic() - t0,
            len(pipeline.lines),
            pipeline.dropped,
            pipeline.errors,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
