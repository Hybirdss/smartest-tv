"""Regression tests for the LG driver's aiowebostv subclass.

webOS 24/25 rejects subscribe_media_foreground_app with
401 insufficient permissions because aiowebostv's registration manifest
does not include the com.webos.media/* permission. The vanilla
_get_states_and_subscribe_state_updates fires that subscription during
connect() and only suppresses WebOsTvServiceNotFoundError, so the
WebOsTvCommandError propagates and kills connect.

These tests pin the workaround: _SmarTestWebOsClient swallows
WebOsTvCommandError from that single subscription and returns {}.
"""
from __future__ import annotations

import pytest

pytest.importorskip("aiowebostv")

from aiowebostv.exceptions import WebOsTvCommandError  # noqa: E402

from smartest_tv._engine.drivers.lg import _SmarTestWebOsClient  # noqa: E402


def _fresh_client() -> _SmarTestWebOsClient:
    """Return an instance without running WebOsClient.__init__ (no sockets)."""
    return _SmarTestWebOsClient.__new__(_SmarTestWebOsClient)


@pytest.mark.asyncio
async def test_media_sub_swallows_command_error(monkeypatch):
    async def boom(self, callback):  # bound method → self + callback
        raise WebOsTvCommandError("401 insufficient permissions")

    monkeypatch.setattr(
        "aiowebostv.WebOsClient.subscribe_media_foreground_app",
        boom,
    )
    result = await _fresh_client().subscribe_media_foreground_app(
        lambda *_: None
    )
    assert result == {}


@pytest.mark.asyncio
async def test_media_sub_passes_through_on_success(monkeypatch):
    async def ok(self, callback):
        return {"subscribed": True}

    monkeypatch.setattr(
        "aiowebostv.WebOsClient.subscribe_media_foreground_app",
        ok,
    )
    result = await _fresh_client().subscribe_media_foreground_app(
        lambda *_: None
    )
    assert result == {"subscribed": True}


@pytest.mark.asyncio
async def test_media_sub_does_not_swallow_unrelated_exceptions(monkeypatch):
    async def kaboom(self, callback):
        raise RuntimeError("bus is on fire")

    monkeypatch.setattr(
        "aiowebostv.WebOsClient.subscribe_media_foreground_app",
        kaboom,
    )
    with pytest.raises(RuntimeError, match="bus is on fire"):
        await _fresh_client().subscribe_media_foreground_app(lambda *_: None)
