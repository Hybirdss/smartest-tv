"""Unit tests for smartest_tv.audio — no TV, no network required."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import smartest_tv.audio as audio_module
from smartest_tv.audio import audio_play, audio_stop, audio_volume


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_driver(name: str = "tv1") -> MagicMock:
    """Return a minimal async mock driver."""
    d = AsyncMock()
    d.platform = "lg"
    d.name = name
    d.connect = AsyncMock()
    d.launch_app_deep = AsyncMock()
    d.screen_off = AsyncMock()
    d.screen_on = AsyncMock()
    d.set_volume = AsyncMock()
    return d


# ---------------------------------------------------------------------------
# audio_play
# ---------------------------------------------------------------------------


def test_audio_play_calls_sync_and_screen_off(monkeypatch):
    """audio_play launches content AND turns screens off on all target TVs."""
    driver = _make_driver("living-room")

    async def fake_connect(names, factory):
        return {"living-room": driver}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["living-room"])
    monkeypatch.setattr(audio_module, "resolve", lambda platform, query: "dQw4w9WgXcQ")
    monkeypatch.setattr(audio_module, "resolve_app", lambda name, plat: ("youtube.leanback.v4", "youtube"))
    monkeypatch.setattr(audio_module, "connect_all", fake_connect)

    results = asyncio.run(audio_play("lo-fi beats", platform="youtube"))

    driver.launch_app_deep.assert_awaited_once()
    driver.screen_off.assert_awaited_once()
    assert len(results) >= 1


def test_audio_play_broadcasts_to_multiple_tvs(monkeypatch):
    """audio_play targets all TVs when rooms=None."""
    d1 = _make_driver("tv1")
    d2 = _make_driver("tv2")

    async def fake_connect(names, factory):
        return {"tv1": d1, "tv2": d2}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["tv1", "tv2"])
    monkeypatch.setattr(audio_module, "resolve", lambda platform, query: "abc123")
    monkeypatch.setattr(audio_module, "resolve_app", lambda name, plat: ("youtube.leanback.v4", "youtube"))
    monkeypatch.setattr(audio_module, "connect_all", fake_connect)

    results = asyncio.run(audio_play("chill music"))

    d1.launch_app_deep.assert_awaited_once()
    d2.launch_app_deep.assert_awaited_once()
    d1.screen_off.assert_awaited_once()
    d2.screen_off.assert_awaited_once()


def test_audio_stop_calls_screen_on(monkeypatch):
    """audio_stop turns screens back on for all target TVs."""
    driver = _make_driver("living-room")

    async def fake_connect(names, factory):
        return {"living-room": driver}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["living-room"])
    monkeypatch.setattr(audio_module, "connect_all", fake_connect)

    results = asyncio.run(audio_stop())

    driver.screen_on.assert_awaited_once()
    assert any(r["status"] == "ok" for r in results)


def test_audio_volume_single_room(monkeypatch):
    """audio_volume sets volume on a specific TV."""
    driver = _make_driver("bedroom")

    monkeypatch.setattr(audio_module, "create_driver", lambda name: driver)

    result = asyncio.run(audio_volume("bedroom", 30))

    driver.connect.assert_awaited_once()
    driver.set_volume.assert_awaited_once_with(30)
    assert "30" in result
    assert "bedroom" in result


def test_audio_play_default_platform_is_youtube(monkeypatch):
    """When no platform is specified, audio_play defaults to 'youtube'."""
    driver = _make_driver("tv1")

    called_platform: list[str] = []

    def fake_resolve(platform, query):
        called_platform.append(platform)
        return "vid123"

    async def fake_connect(names, factory):
        return {"tv1": driver}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["tv1"])
    monkeypatch.setattr(audio_module, "resolve", fake_resolve)
    monkeypatch.setattr(audio_module, "resolve_app", lambda name, plat: ("youtube.leanback.v4", "youtube"))
    monkeypatch.setattr(audio_module, "connect_all", fake_connect)

    asyncio.run(audio_play("relaxing music"))

    assert called_platform == ["youtube"]


def test_audio_rooms_filter(monkeypatch):
    """audio_play only targets the specified rooms, not all TVs."""
    d_bedroom = _make_driver("bedroom")
    d_living = _make_driver("living-room")

    connected_names: list[str] = []

    async def fake_connect_all(names, factory):
        connected_names.extend(names)
        return {"bedroom": d_bedroom}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["living-room", "bedroom"])
    monkeypatch.setattr(audio_module, "resolve", lambda platform, query: "spotify:track:abc")
    monkeypatch.setattr(audio_module, "resolve_app", lambda name, plat: ("spotify-beehive", "spotify"))
    monkeypatch.setattr(audio_module, "connect_all", fake_connect_all)

    asyncio.run(audio_play("jazz music", platform="spotify", rooms=["bedroom"]))

    assert "bedroom" in connected_names
    assert "living-room" not in connected_names
    d_bedroom.launch_app_deep.assert_awaited_once()
    d_living.launch_app_deep.assert_not_called()


def test_audio_stop_specific_rooms(monkeypatch):
    """audio_stop only restores screens for specified rooms."""
    d_bedroom = _make_driver("bedroom")
    d_living = _make_driver("living-room")

    connected_names: list[str] = []

    async def fake_connect_all(names, factory):
        connected_names.extend(names)
        return {"bedroom": d_bedroom}, []

    monkeypatch.setattr(audio_module, "get_all_tv_names", lambda: ["living-room", "bedroom"])
    monkeypatch.setattr(audio_module, "connect_all", fake_connect_all)

    asyncio.run(audio_stop(rooms=["bedroom"]))

    assert connected_names == ["bedroom"]
    d_bedroom.screen_on.assert_awaited_once()
    d_living.screen_on.assert_not_called()
