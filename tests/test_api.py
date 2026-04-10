"""Unit tests for smartest_tv.api."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from smartest_tv import api


def test_get_driver_uses_factory_and_caches(monkeypatch):
    calls: list[None] = []
    sentinel = object()

    monkeypatch.setattr(api, "_driver", None)

    def fake_create_driver():
        calls.append(None)
        return sentinel

    monkeypatch.setattr(api, "create_driver", fake_create_driver)

    first = api._get_driver()
    second = api._get_driver()

    assert first is sentinel
    assert second is sentinel
    assert calls == [None]


def test_generate_api_key():
    key = api.generate_api_key()
    assert key.startswith("stv_")
    assert len(key) > 20


# ---------------------------------------------------------------------------
# ApiHandler tests — using a minimal request mock
# ---------------------------------------------------------------------------

class FakeRequest:
    """Minimal mock for BaseHTTPRequestHandler input."""

    def __init__(self, method: str, path: str, body: dict | None = None,
                 headers: dict | None = None):
        self.method = method
        self.path = path
        self.body = json.dumps(body).encode() if body else b""
        self.headers = headers or {}

    def makefile(self, mode, bufsize=-1):
        if "r" in mode:
            # Build raw HTTP request
            lines = [f"{self.method} {self.path} HTTP/1.1"]
            self.headers["Content-Length"] = str(len(self.body))
            for k, v in self.headers.items():
                lines.append(f"{k}: {v}")
            lines.append("")
            header_bytes = "\r\n".join(lines).encode() + b"\r\n"
            return BytesIO(header_bytes + self.body)
        return BytesIO()


def _make_handler(method: str, path: str, body: dict | None = None,
                  headers: dict | None = None, api_key: str | None = None):
    """Create an ApiHandler with a fake request, capture the response."""
    req = FakeRequest(method, path, body, headers or {})

    # Patch _api_key
    with patch.object(api, "_api_key", api_key):
        handler = api.ApiHandler.__new__(api.ApiHandler)
        handler.request = req
        handler.client_address = ("127.0.0.1", 12345)
        handler.server = MagicMock()
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.command = method
        handler.path = path

        # Parse headers from raw request
        import http.client
        handler.rfile = BytesIO(req.body)
        handler.headers = http.client.HTTPMessage()
        if headers:
            for k, v in headers.items():
                handler.headers[k] = v
        handler.headers["Content-Length"] = str(len(req.body))

        # Capture response
        handler.wfile = BytesIO()
        handler._headers_buffer = []
        handler.responses = {200: ("OK",), 401: ("Unauthorized",), 404: ("Not Found",), 500: ("Error",)}

        # Override send_response to not write to wfile directly
        response_data = {}

        def capture_respond(code, data):
            response_data["code"] = code
            response_data["data"] = data

        handler._respond = capture_respond

        def capture_error(code, msg):
            response_data["code"] = code
            response_data["data"] = {"error": msg}

        handler._error = capture_error

        return handler, response_data


class TestApiAuth:
    """Test authentication checks."""

    def test_no_api_key_allows_all(self):
        handler, resp = _make_handler("GET", "/api/ping", api_key=None)
        handler.do_GET()
        assert resp["code"] == 200

    def test_api_key_rejects_no_auth(self):
        handler, resp = _make_handler("GET", "/api/ping", api_key="secret123")
        with patch.object(api, "_api_key", "secret123"):
            handler.do_GET()
        assert resp["code"] == 401

    def test_api_key_accepts_correct_bearer(self):
        handler, resp = _make_handler(
            "GET", "/api/ping",
            headers={"Authorization": "Bearer secret123"},
            api_key="secret123",
        )
        with patch.object(api, "_api_key", "secret123"):
            handler.do_GET()
        assert resp["code"] == 200

    def test_api_key_rejects_wrong_bearer(self):
        handler, resp = _make_handler(
            "GET", "/api/ping",
            headers={"Authorization": "Bearer wrong"},
            api_key="secret123",
        )
        with patch.object(api, "_api_key", "secret123"):
            handler.do_GET()
        assert resp["code"] == 401


class TestApiEndpoints:
    """Test API endpoint routing."""

    def test_ping(self):
        handler, resp = _make_handler("GET", "/api/ping")
        handler.do_GET()
        assert resp["code"] == 200
        assert resp["data"]["status"] == "ok"

    def test_unknown_get(self):
        handler, resp = _make_handler("GET", "/api/nonexistent")
        handler.do_GET()
        assert resp["code"] == 404

    def test_unknown_post(self):
        handler, resp = _make_handler("POST", "/api/nonexistent", body={})
        with patch.object(api, "_get_driver", return_value=MagicMock()):
            handler.do_POST()
        assert resp["code"] == 404

    def test_options_cors(self):
        handler, resp = _make_handler("OPTIONS", "/api/ping")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_OPTIONS()
        handler.send_response.assert_called_with(200)
        cors_headers = {call[0][0]: call[0][1] for call in handler.send_header.call_args_list}
        assert "Access-Control-Allow-Origin" in cors_headers
        assert "Access-Control-Allow-Methods" in cors_headers


class TestApiServerStart:
    """Test server startup."""

    def test_refuses_open_bind_without_key(self, monkeypatch):
        monkeypatch.setattr(api, "_api_key", None)
        with pytest.raises(ValueError, match="STV_API_KEY"):
            api.start_api_server(host="0.0.0.0", port=0)
