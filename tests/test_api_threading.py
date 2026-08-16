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


# -- DriverBusyError / lock timeout (v1.3.2) -------------------------------


def test_run_driver_raises_busy_when_lock_held(monkeypatch):
    """A stuck command must surface DriverBusyError, not hang the caller."""
    monkeypatch.setattr(api, "_driver_lock_timeout", lambda: 0.05)
    api._driver_exec_lock.acquire()
    try:
        box = {}

        def call():
            try:
                api._run_driver(_never_runs)
            except api.DriverBusyError as e:
                box["err"] = str(e)
            except BaseException as e:  # pragma: no cover — bug guard
                box["other"] = repr(e)

        th = threading.Thread(target=call, daemon=True)
        th.start()
        th.join(timeout=2)
        assert "err" in box, f"expected DriverBusyError, got {box}"
        assert "busy" in box["err"].lower()
    finally:
        api._driver_exec_lock.release()


async def _never_runs():
    raise AssertionError("coroutine must not run while lock is held")


def test_run_driver_recovers_after_release(monkeypatch):
    monkeypatch.setattr(api, "_driver_lock_timeout", lambda: 0.05)
    api._driver_exec_lock.acquire()
    api._driver_exec_lock.release()
    assert api._run_driver(_ok_coro) == "ok"


async def _ok_coro():
    return "ok"


def test_lock_timeout_env_parsing(monkeypatch):
    monkeypatch.setenv("STV_DRIVER_LOCK_TIMEOUT", "7.5")
    assert api._driver_lock_timeout() == 7.5
    monkeypatch.setenv("STV_DRIVER_LOCK_TIMEOUT", "not-a-number")
    assert api._driver_lock_timeout() == 30.0  # invalid falls back


def _make_handler():
    h = api.ApiHandler.__new__(api.ApiHandler)
    h._out = []
    h._code = None

    class _W:
        def write(self, data):
            h._out.append(data)

    h.wfile = _W()
    h.rfile = None
    h.send_response = lambda code: setattr(h, "_code", code)
    h.send_header = lambda k, v: None
    h.end_headers = lambda: None
    return h


def test_respond_driver_maps_busy_to_503(monkeypatch):
    def busy(_):
        raise api.DriverBusyError("TV driver busy for over 30s")

    h = _make_handler()
    monkeypatch.setattr(api, "_run_driver", busy)
    h._respond_driver(None)
    assert h._code == 503
    assert "busy" in h._out[0].decode()


def test_respond_driver_maps_generic_to_500(monkeypatch):
    def boom(_):
        raise ValueError("driver exploded")

    h = _make_handler()
    monkeypatch.setattr(api, "_run_driver", boom)
    h._respond_driver(None)
    assert h._code == 500
    assert "driver exploded" in h._out[0].decode()
