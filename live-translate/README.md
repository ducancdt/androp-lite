# Live Translate — dịch trực tiếp YouTube / livestream / mic sang tiếng Việt, đọc bằng giọng VieNeu-TTS

Chương trình nghe âm thanh từ **YouTube, Twitch, Facebook, TikTok, Kick… (mọi trang yt-dlp hỗ trợ, kể cả livestream)**, từ **mic**, từ **âm thanh hệ thống** (Zoom, Teams, game, trình duyệt) hoặc từ **tệp video**, rồi:

```
nguồn âm thanh → cắt câu (VAD) → nhận dạng (STT) → dịch bằng AI → đọc bằng giọng Việt → loa / OBS / phụ đề
```

- **Dịch bằng AI tuỳ chọn**: chỉ cần gắn API key của **Gemini** (mặc định), hoặc **bất kỳ API tương thích OpenAI** (OpenAI, Groq, OpenRouter, DeepSeek, Together, Ollama/LM Studio chạy local…), hoặc **Anthropic Claude**.
- **Giọng đọc tiếng Việt mã nguồn mở**: [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (Apache-2.0) chạy **offline trên CPU** (không cần torch), 25 giọng có sẵn ba miền, **nhân bản giọng bất kỳ** từ 3–10 giây audio mẫu.
- **Nhận dạng giọng nói offline** bằng [faster-whisper](https://github.com/SYSTRAN/faster-whisper), hoặc để **Gemini nghe và dịch thẳng** trong một lần gọi (ít độ trễ hơn, không cần Whisper), hoặc Whisper API của OpenAI/Groq.
- Phụ đề song ngữ **web overlay** (dùng làm Browser Source trong OBS), ghi **.srt** và **.wav**.
- Mọi tầng chạy song song, tự bỏ câu cũ khi máy quá tải để độ trễ không tăng dần.

## Cài đặt

Yêu cầu: Python ≥ 3.10, [ffmpeg](https://ffmpeg.org/download.html) trong PATH.

```bash
cd live-translate
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[all]"            # = faster-whisper + vieneu + sounddevice + yt-dlp
```

Cài tối thiểu nếu không cần hết (ví dụ chỉ dùng Gemini nghe + Gemini đọc):

```bash
pip install -e ".[url,audio]"
```

GPU NVIDIA cho VieNeu: `pip install "vieneu[cuda]"`; cho Whisper: `--whisper-device cuda` (cần CUDA + cuDNN).

### Khóa API

```bash
cp .env.example .env     # rồi điền một trong các khóa
```

| Nhà cung cấp | Biến môi trường | Ghi chú |
|---|---|---|
| Gemini (mặc định) | `GEMINI_API_KEY`, `GEMINI_MODEL` | Lấy khóa miễn phí tại https://aistudio.google.com/apikey. Nếu model cấu hình không còn, chương trình tự chọn một model *flash* đang khả dụng. |
| OpenAI-compatible | `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | Groq: `https://api.groq.com/openai/v1`; OpenRouter: `https://openrouter.ai/api/v1`; Ollama: `http://localhost:11434/v1` (khóa để trống). |
| Anthropic | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | |

Chọn nhà cung cấp bằng `--translator gemini|openai|anthropic`; nếu không chỉ định, chương trình chọn theo khóa có trong `.env`.

## Dùng

```bash
# YouTube (video thường hoặc livestream), tự nhận dạng ngôn ngữ, đọc bằng giọng "Mai Anh"
livetranslate --source "https://www.youtube.com/watch?v=XXXX"

# Chỉ định ngôn ngữ nguồn (chính xác và nhanh hơn), chọn giọng khác
livetranslate --source "https://www.twitch.tv/abc" --source-lang en --voice "Hải Đăng"

# Gemini nghe audio và dịch thẳng (1 lần gọi API, không cần Whisper)
livetranslate --source "https://..." --stt gemini

# Dùng Groq (nhanh, rẻ) để dịch, Whisper offline để nghe
livetranslate --source "https://..." --translator openai --model llama-3.3-70b-versatile

# Mic
livetranslate --source mic --source-lang ja
livetranslate --list-devices            # xem chỉ số thiết bị, rồi --source mic:3

# Âm thanh hệ thống (dịch Zoom/Teams/game/bất kỳ app nào)
#   Windows: bật "Stereo Mix" trong Sound settings, hoặc cài VB-Cable
livetranslate --source "device:-f dshow -i audio=Stereo Mix (Realtek(R) Audio)"
#   Linux (PulseAudio/PipeWire): pactl list short sources | grep monitor
livetranslate --source "device:-f pulse -i alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
#   macOS: cài BlackHole, chọn nó làm output rồi:
livetranslate --source "device:-f avfoundation -i :1"

# Tệp video: xuất phụ đề song ngữ + giọng đọc, không phát loa
livetranslate --source file:phim.mp4 --save-srt phim.vi.srt --save-audio phim.vi.wav --no-play

# Phụ đề web cho OBS (Browser Source: http://127.0.0.1:8765/?bg=0&n=2&size=36)
livetranslate --source "https://..." --web 8765

# Nhân bản giọng từ mẫu 5 giây
livetranslate --source "https://..." --voice-ref giong_mau.wav

# Giọng đọc đi vào OBS/Discord qua VB-Cable thay vì loa
livetranslate --source "https://..." --output-device "CABLE Input"
```

Liệt kê giọng VieNeu: `livetranslate --list-voices`. Giọng v3 Turbo có sẵn: Adam bựa, Trúc Ly, Thiện Minh, Mai Anh, Hải Đăng, Thùy Dung, Thiền Tâm Đức, Ngọc Huyền, Quang Sơn, Ngọc Trân, Minh Đức, Phạm Tuyên, Xuân Vĩnh, Thanh Bình, Ngọc Linh, Đoan Trang, Quỳnh Anh, Quốc Tuấn, Adam, Thái Sơn, Thục Đoan, Minh Triết, Mỹ Duyên, Đức Trí, Kim Thanh.

### Tuỳ chọn hay dùng

| Tuỳ chọn | Ý nghĩa |
|---|---|
| `--target ja` | Dịch sang ngôn ngữ khác (mặc định `vi`). TTS VieNeu đọc tốt tiếng Việt và tiếng Anh. |
| `--whisper-model base\|small\|medium\|large-v3` | Càng lớn càng chính xác, càng chậm. `small` hợp CPU thường. |
| `--silence-ms 500` | Khoảng im lặng kết thúc câu. Giảm để phản ứng nhanh hơn, tăng nếu bị cắt câu. |
| `--max-segment 10` | Câu dài tối đa (giây) trước khi buộc cắt. |
| `--vad-threshold 0.02` | Tăng nếu nhạc nền bị coi là lời nói, giảm nếu bỏ sót giọng nhỏ. |
| `--glossary tu_dien.txt` | Thuật ngữ cố định, mỗi dòng `GPU = card đồ hoạ`. |
| `--vieneu-precision int8` | VieNeu nhanh hơn ~1.6× trên CPU hỗ trợ VNNI. |
| `--vieneu-mode v3nano` | Model nhẹ 282 MB, nhanh hơn trên máy yếu. |
| `--fit-duration` | Tăng tốc giọng đọc (tối đa 1.6×) khi dài hơn câu gốc, để bám kịp hình. |
| `--tts gemini` | Dùng giọng Gemini TTS (đám mây) nếu không cài được VieNeu. |
| `--tts none` | Chỉ phụ đề, không đọc. |

## Độ trễ và cấu hình gợi ý

Độ trễ ≈ khoảng im lặng kết thúc câu (0,7 s) + STT + dịch + TTS. Trên CPU 4–8 nhân:

| Cấu hình | Độ trễ điển hình sau khi người nói dứt câu |
|---|---|
| `--stt gemini` (Gemini nghe + dịch) + VieNeu int8 | ~2–4 s |
| Whisper `small` + Gemini/Groq + VieNeu fp32 | ~3–6 s |
| Whisper `medium` + bất kỳ + VieNeu | ~6–10 s (nên dùng GPU) |

Nếu log báo `Quá tải: bỏ câu…`, giảm `--whisper-model`, dùng `--stt gemini`, hoặc `--vieneu-precision int8`.

## Kiến trúc

```
livetranslate/
  sources/     URL (yt-dlp + ffmpeg, livestream HLS), file, device (ffmpeg), mic (sounddevice) → float32 16 kHz
  segmenter.py VAD năng lượng thích nghi, cắt theo im lặng / độ dài tối đa, giữ pre-roll
  stt/         faster-whisper (offline) | Gemini audio (nghe + dịch thẳng) | OpenAI-compatible /audio/transcriptions
  translate/   Gemini | OpenAI-compatible | Anthropic — chung prompt phiên dịch, ngữ cảnh 3 câu trước, glossary
  tts/         VieNeu-TTS (preset / nhân bản giọng) | Gemini TTS | none
  player.py    hàng đợi phát sounddevice (chọn thiết bị ra), ghi WAV
  pipeline.py  3 luồng nối bằng hàng đợi giới hạn; bỏ câu cũ khi quá tải; ghi SRT; callback hiển thị
  webui.py     HTTP stdlib: trang overlay (web/overlay.html) + /api/state cho OBS
```

Thêm nhà cung cấp dịch mới: kế thừa `translate.base.Translator` và cài `_complete(system, user) -> str` (xem `openai_compat.py`, ~40 dòng).

## Kiểm thử

```bash
pip install -e ".[dev]"
pytest -q
```

Bộ test mô phỏng STT/dịch/TTS nên không cần khóa API hay model; kiểm tra bộ cắt câu, prompt, các client API (Gemini kể cả fallback model và tắt thinking, OpenAI-compatible, Anthropic), pipeline, SRT, CLI.

## Giấy phép & ghi công

- Mã nguồn: Apache-2.0.
- [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (Apache-2.0) — giọng đọc tiếng Việt, model `pnnbao-ump/VieNeu-TTS-v3-Turbo`.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT), [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense), [ffmpeg](https://ffmpeg.org) (LGPL/GPL), [sounddevice](https://github.com/spatialaudio/python-sounddevice) (MIT).
- Một lựa chọn TTS Việt mã nguồn mở khác: [VietTTS](https://github.com/dangvansam/viet-tts) (code Apache-2.0 nhưng model CC BY-NC, không dùng thương mại) — chưa tích hợp.

Tôn trọng điều khoản của nền tảng bạn lấy luồng (YouTube/Twitch…) và bản quyền nội dung; công cụ này dành cho sử dụng cá nhân/phi thương mại trừ khi bạn có quyền phát lại.
