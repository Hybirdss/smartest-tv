"""api server concurrency (v1.3.0).

ThreadingHTTPServer lets /api/ping answer while a slow TV command runs;
`_run_driver` serializes driver-touching execution so two request
threads never drive one driver instance on two event loops at once.
"""

from __future__ import annotations

import asyncio
import threading

import pytest

from smartest_tv import api


@pytest.fixture()
def no_cached_driver(monkeypatch):
    monkeypatch.setattr(api, "_driver", None)


def test_run_driver_serializes_execution(no_cached_driver, monkeypatch):
    """Two _run_driver calls must never overlap, regardless of threads."""
    active = 0
    max_active = 0
    lock = threading.Lock()

    def make_coro(delay: float):
        async def _do():
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            await asyncio.sleep(delay)
            with lock:
                active -= 1
            return "ok"

        return _do

    results: list = []

    def worker(delay: float):
        results.append(api._run_driver(make_coro(delay)))

    threads = [threading.Thread(target=worker, args=(0.05,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert results == ["ok"] * 4
    assert max_active == 1  # strictly serialized


def test_ping_handler_does_not_take_driver_lock(no_cached_driver, monkeypatch):
    """A slow driver command (holding _driver_exec_lock) must not block
    /api/ping — that head-of-line blocking is the v1.3.0 fix."""
    import json
    from io import BytesIO

    api._driver_exec_lock.acquire()
    try:
        handler = api.ApiHandler.__new__(api.ApiHandler)

        def fake_get_tv_config():
            return {"name": "lr", "platform": "lg"}

        monkeypatch.setattr(api, "get_tv_config", fake_get_tv_config)

        class _W:
            def write(self, data):
                handler._written = data

        handler.wfile = _W()
        handler.rfile = BytesIO()
        handler.path = "/api/ping"
        handler.headers = {"Content-Length": "0"}

        def fake_send_response(code):
            handler._code = code

        def fake_send_header(k, v):
            pass

        def fake_end_headers():
            pass

        handler.send_response = fake_send_response
        handler.send_header = fake_send_header
        handler.end_headers = fake_end_headers

        done = threading.Event()

        def run_ping():
            handler.do_GET()
            done.set()

        t = threading.Thread(target=run_ping, daemon=True)
        t.start()
        assert done.wait(timeout=2.0), "ping blocked behind driver lock!"
        assert handler._code == 200
        assert json.loads(handler._written)["status"] == "ok"
    finally:
        api._driver_exec_lock.release()


def test_start_api_server_refuses_wildcard_without_key(monkeypatch):
    monkeypatch.setattr(api, "_api_key", None)
    with pytest.raises(ValueError):
        api.start_api_server(host="0.0.0.0", port=0)
