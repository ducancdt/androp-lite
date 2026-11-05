"""Web overlay phụ đề (thuần stdlib) — mở trong trình duyệt hoặc làm Browser Source cho OBS."""
from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, List, Optional

log = logging.getLogger(__name__)

_HTML_PATH = Path(__file__).resolve().parent / "web" / "overlay.html"


def _load_html() -> str:
    try:
        return _HTML_PATH.read_text(encoding="utf-8")
    except Exception:
        return "<html><body><pre id='x'></pre><script>setInterval(async()=>{const r=await fetch('/api/state');document.getElementById('x').textContent=JSON.stringify(await r.json(),null,1)},500)</script></body></html>"


class SubtitleServer:
    def __init__(self, port: int, snapshot: Callable[[int], List[dict]], status: Optional[Callable[[], dict]] = None, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.snapshot = snapshot
        self.status = status or (lambda: {})
        html = _load_html()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # noqa: D401 - tắt log truy cập
                log.debug("web: " + fmt, *args)

            def _send(self, code: int, body: bytes, ctype: str) -> None:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                path = self.path.split("?", 1)[0]
                if path in ("/", "/index.html", "/overlay"):
                    self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                elif path == "/api/state":
                    payload = {"lines": outer.snapshot(10), "status": outer.status()}
                    self._send(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
                else:
                    self._send(404, b"not found", "text/plain")

        self._server = ThreadingHTTPServer((host, port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="web", daemon=True)

    def start(self) -> "SubtitleServer":
        self._thread.start()
        log.info("Phụ đề web: http://%s:%d/  (OBS Browser Source: thêm ?bg=0 để nền trong suốt)", self.host, self.port)
        return self

    def close(self) -> None:
        try:
            self._server.shutdown()
            self._server.server_close()
        except Exception:
            pass
