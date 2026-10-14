"""Minimal HTTP client (standard library only), injectable for tests."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from . import __version__

USER_AGENT = f"discover-anything/{__version__} (+https://github.com/karangupta8/discover-anything)"
DEFAULT_TIMEOUT = 60


class HttpError(RuntimeError):
    def __init__(self, status: int, url: str, body: str = "") -> None:
        super().__init__(f"HTTP {status} from {url}: {body[:200]}")
        self.status = status
        self.url = url


class HttpClient:
    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout

    def _send(self, request: urllib.request.Request) -> bytes:
        request.add_header("User-Agent", USER_AGENT)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if exc.fp else ""
            raise HttpError(exc.code, request.full_url, body) from exc

    def get_text(self, url: str, params: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None) -> str:
        full = f"{url}?{urllib.parse.urlencode(params)}" if params else url
        return self._send(urllib.request.Request(full, headers=headers or {})).decode("utf-8")

    def get_json(self, url: str, params: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None) -> Any:
        return json.loads(self.get_text(url, params, headers))

    def post_form(self, url: str, form: dict[str, Any],
                  headers: dict[str, str] | None = None) -> str:
        data = urllib.parse.urlencode(form).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
        return self._send(request).decode("utf-8")

    def post_json(self, url: str, payload: Any, headers: dict[str, str] | None = None) -> Any:
        data = json.dumps(payload).encode("utf-8")
        merged = {"Content-Type": "application/json", **(headers or {})}
        request = urllib.request.Request(url, data=data, headers=merged, method="POST")
        return json.loads(self._send(request).decode("utf-8"))

    def put_bytes(self, url: str, body: bytes, headers: dict[str, str] | None = None) -> Any:
        merged = {"Content-Type": "application/octet-stream", **(headers or {})}
        request = urllib.request.Request(url, data=body, headers=merged, method="PUT")
        raw = self._send(request).decode("utf-8")
        return json.loads(raw) if raw.strip() else None
