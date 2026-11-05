"""Nguồn âm thanh: URL (yt-dlp + ffmpeg), file, mic, thiết bị ffmpeg. Tất cả trả float32 mono 16 kHz."""
from __future__ import annotations

from .base import AudioSource
from .ffmpeg_source import FfmpegDeviceSource, FileSource, UrlSource
from .mic import MicSource


def make_source(spec: str, *, realtime_file: bool = False, verbose: bool = False) -> AudioSource:
    """Phân giải chuỗi nguồn:

    - ``mic`` hoặc ``mic:<tên/chỉ số thiết bị>``  → micro / loopback qua sounddevice
    - ``device:<tham số ffmpeg>``                  → ví dụ ``device:-f dshow -i audio=Stereo Mix``
    - ``file:<đường dẫn>`` hoặc đường dẫn tồn tại   → tệp video/audio bất kỳ
    - ``http(s)://...``                            → YouTube, Twitch, Facebook, TikTok... (yt-dlp)
    """
    import os

    s = spec.strip()
    low = s.lower()
    if low == "mic" or low.startswith("mic:"):
        device = s[4:] if low.startswith("mic:") else None
        return MicSource(device=device or None)
    if low.startswith("device:"):
        return FfmpegDeviceSource(s[len("device:") :])
    if low.startswith("file:"):
        return FileSource(s[len("file:") :], realtime=realtime_file)
    if low.startswith("http://") or low.startswith("https://"):
        return UrlSource(s, verbose=verbose)
    if os.path.exists(s):
        return FileSource(s, realtime=realtime_file)
    raise ValueError(f"Không hiểu nguồn: {spec!r}")


__all__ = ["AudioSource", "UrlSource", "FileSource", "FfmpegDeviceSource", "MicSource", "make_source"]
