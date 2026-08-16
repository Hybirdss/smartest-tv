"""http.curl() pure-Python fallback (v1.3.0).

Home Assistant slim containers ship without the curl binary; before
v1.3.0 every resolve / RemoteDriver / community-cache call failed
silently there. When curl is absent, curl() must transparently use
urllib with equivalent semantics: redirects, gzip/deflate, POST+JSON,
and HTTP-error bodies still returned with ok=True (curl -s parity).
"""

from __future__ import annotations

import gzip
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import smartest_tv.http as http_mod
from smartest_tv.http import curl, curl_json


@pytest.fixture()
def no_curl(monkeypatch):
    """Force the urllib fallback regardless of the host having curl."""
    monkeypatch.setattr(http_mod.shutil, "which", lambda name: None if name == "curl" else name)
    # curl() caches the which() result — every test starts from a clean probe
    monkeypatch.setattr(http_mod, "_have_curl", None)


@pytest.fixture()
def local_server():
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str = "application/json",
                  extra: dict[str, str] | None = None):
            try:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # Client (e.g. a timed-out /slow request) is gone — that
                # is the scenario under test, not a failure.
                pass

        def do_GET(self):
            if self.path == "/deflate":
                import zlib
                payload = zlib.compress(json.dumps({"msg": "deflated"}).encode())
                self._send(200, payload, extra={"Content-Encoding": "deflate"})
            elif self.path == "/deflate-raw":
                import zlib
                c = zlib.compressobj(wbits=-zlib.MAX_WBITS)
                payload = c.compress(json.dumps({"msg": "raw deflate"}).encode()) + c.flush()
                self._send(200, payload, extra={"Content-Encoding": "deflate"})
            elif self.path == "/slow":
                time.sleep(2.5)
                self._send(200, b"{}")
            elif self.path == "/hello":
                self._send(200, json.dumps({"msg": "hi"}).encode())
            elif self.path == "/gz":
                payload = gzip.compress(json.dumps({"msg": "compressed"}).encode())
                self._send(200, payload, extra={"Content-Encoding": "gzip"})
            elif self.path == "/redir":
                self.send_response(301)
                self.send_header("Location", "/hello")
                self.send_header("Content-Length", "0")
                self.end_headers()
            elif self.path == "/missing":
                self._send(404, b'{"error": "not found"}')
            elif self.path == "/gz-truncated":
                # gzip header claims a body twice this size
                payload = gzip.compress(b'{"msg": "never fully arriv')
                self._send(200, payload[: len(payload) // 2],
                           extra={"Content-Encoding": "gzip"})
            elif self.path == "/gz-missing":
                payload = gzip.compress(b'{"error": "gone"}')
                self._send(404, payload, extra={"Content-Encoding": "gzip"})
            else:
                self._send(400, b"bad")

        def do_POST(self):
            if self.path == "/echo":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                hits.append(self.headers.get("Content-Type", ""))
                self._send(200, body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", hits
    finally:
        server.shutdown()
        server.server_close()


def test_fallback_get(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/hello")
    assert r.ok
    assert r.status_code == 200
    assert json.loads(r.body)["msg"] == "hi"


def test_fallback_follows_redirects(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/redir")
    assert r.ok
    assert json.loads(r.body)["msg"] == "hi"


def test_fallback_gzip(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/gz")
    assert r.ok
    assert json.loads(r.body)["msg"] == "compressed"


def test_fallback_post_json_default_content_type(no_curl, local_server):
    base, hits = local_server
    r = curl(f"{base}/echo", method="POST", data=json.dumps({"a": 1}))
    assert r.ok
    assert json.loads(r.body) == {"a": 1}
    assert hits and hits[0].startswith("application/json")


def test_fallback_deflate_zlib_stream(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/deflate")
    assert r.ok
    assert json.loads(r.body)["msg"] == "deflated"


def test_fallback_deflate_raw_stream(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/deflate-raw")
    assert r.ok
    assert json.loads(r.body)["msg"] == "raw deflate"


def test_fallback_timeout_returns_error(no_curl, local_server):
    base, _ = local_server
    r = curl(f"{base}/slow", timeout=1)
    assert not r.ok
    assert r.error  # surfaced reason, not an empty failure


def test_fallback_gzipped_http_error_body_decompresses(no_curl, local_server):
    """curl --compressed decompresses error bodies too; so must the fallback."""
    base, _ = local_server
    r = curl(f"{base}/gz-missing")
    assert r.ok and r.status_code == 404
    assert json.loads(r.body)["error"] == "gone"


def test_fallback_truncated_gzip_does_not_raise(no_curl, local_server):
    """A truncated gzip body must return undecoded bytes, never raise."""
    base, _ = local_server
    r = curl(f"{base}/gz-truncated")
    assert r.ok  # transport succeeded; body simply stays compressed
    # And it really stayed compressed: the plaintext never appears, and
    # a regression that returned an empty body would fail here too.
    assert "never fully arriv" not in r.body
    assert r.body


def test_fallback_http_error_returns_body_like_curl(no_curl, local_server):
    # curl -s (without -f) exits 0 on 404 and prints the body.
    base, _ = local_server
    r = curl(f"{base}/missing")
    assert r.ok
    assert r.status_code == 404
    assert "not found" in r.body


def test_fallback_connection_error_is_not_ok(no_curl):
    r = curl("http://127.0.0.1:1/nope", timeout=2)
    assert not r.ok
    assert r.error


def test_fallback_curl_json_roundtrip(no_curl, local_server):
    base, _ = local_server
    assert curl_json(f"{base}/hello") == {"msg": "hi"}


def test_curl_path_still_used_when_available(local_server, monkeypatch):
    """With curl on PATH the subprocess path is chosen (smoke: no fallback)."""
    calls = []
    real_run = http_mod.subprocess.run

    def fake_run(args, **kwargs):
        calls.append(args)
        return real_run(args, **kwargs)

    monkeypatch.setattr(http_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(http_mod, "_have_curl", True)  # cached, like production
    base, _ = local_server
    r = curl(f"{base}/hello")
    assert calls and calls[0][0] == "curl"
    assert r.ok


def test_curl_vanishing_midprocess_falls_back(local_server, monkeypatch):
    """Cached "curl present" + binary gone at exec time -> urllib, not an error."""
    def boom(args, **kwargs):
        raise FileNotFoundError("curl")

    monkeypatch.setattr(http_mod.subprocess, "run", boom)
    monkeypatch.setattr(http_mod.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(http_mod, "_have_curl", True)

    base, _ = local_server
    r = curl(f"{base}/hello")
    assert r.ok and json.loads(r.body)["msg"] == "hi"
    assert http_mod._have_curl is False  # cache flipped; next call skips subprocess
