from livetranslate.cli import apply_args, build_parser
from livetranslate.config import Settings


def test_cli_overrides():
    a = build_parser().parse_args(
        ["--source", "mic", "--translator", "openai", "--model", "gpt-x", "--no-play", "--web", "8765", "--max-segment", "9", "--voice", "Adam"]
    )
    s = apply_args(Settings(), a)
    assert s.source == "mic" and s.translator == "openai" and s.openai_model == "gpt-x"
    assert s.play is False and s.web_port == 8765 and s.max_segment_s == 9 and s.voice == "Adam"


def test_make_source_parsing(tmp_path):
    from livetranslate.sources import make_source
    from livetranslate.sources.ffmpeg_source import FfmpegDeviceSource, FileSource, UrlSource
    from livetranslate.sources.mic import MicSource

    assert isinstance(make_source("https://youtu.be/abc"), UrlSource)
    assert isinstance(make_source("mic:2"), MicSource) and make_source("mic:2").device == 2
    d = make_source("device:-f pulse -i default")
    assert isinstance(d, FfmpegDeviceSource) and d.args == ["-f", "pulse", "-i", "default"]
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert isinstance(make_source(str(f)), FileSource)
    assert isinstance(make_source("file:nope.mp4"), FileSource)
