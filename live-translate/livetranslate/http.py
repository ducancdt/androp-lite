"""HTTP nhỏ gọn dùng chung cho các nhà cung cấp AI (requests + retry)."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

log = logging.getLogger(__name__)


class ApiError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


def post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 60.0,
    retries: int = 2,
    files: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """POST JSON (hoặc multipart khi có ``files``) với retry cho 429/5xx/lỗi mạng."""
    last: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            if files is not None:
                r = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)
            else:
                r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 1.5 * (attempt + 1)
                log.warning("API %s -> %s, thử lại sau %.1fs", url.split("?")[0], r.status_code, wait)
                time.sleep(wait)
                continue
            if r.status_code >= 400:
                raise ApiError(r.status_code, r.text[:1000])
            return r.json()
        except requests.RequestException as e:
            last = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"Lỗi mạng khi gọi {url.split('?')[0]}: {e}") from e
    raise RuntimeError(str(last))


def get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 30.0) -> Dict[str, Any]:
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code >= 400:
        raise ApiError(r.status_code, r.text[:1000])
    return r.json()
