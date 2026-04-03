"""Tests for sync broadcast engine."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from smartest_tv.drivers.base import TVDriver, TVStatus
from smartest_tv.sync import broadcast, connect_all


class FakeDriver(TVDriver):
    """Minimal fake driver for testing."""

    platform = "fake"

    def __init__(self, name: str = "fake", fail_on: str | None = None):
        self.name = name
        self.fail_on = fail_on
        self.connected = False
        self.actions: list[str] = []

    async def connect(self):
        if self.fail_on == "connect":
            raise ConnectionError(f"{self.name} unreachable")
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def power_on(self):
        self.actions.append("power_on")

    async def power_off(self):
        if self.fail_on == "power_off":
            raise RuntimeError(f"{self.name} power_off failed")
        self.actions.append("power_off")

    async def get_volume(self) -> int:
        return 20

    async def set_volume(self, level: int):
        self.actions.append(f"set_volume:{level}")

    async def volume_up(self):
        self.actions.append("volume_up")

    async def volume_down(self):
        self.actions.append("volume_down")

    async def set_mute(self, mute: bool):
        self.actions.append(f"set_mute:{mute}")

    async def get_muted(self) -> bool:
        return False

    async def launch_app(self, app_id: str):
        self.actions.append(f"launch:{app_id}")

    async def launch_app_deep(self, app_id: str, content_id: str):
        self.actions.append(f"deep_link:{app_id}:{content_id}")

    async def close_app(self, app_id: str):
        self.actions.append(f"close:{app_id}")

    async def list_apps(self):
        return []

    async def play(self):
        self.actions.append("play")

    async def pause(self):
        self.actions.append("pause")

    async def stop(self):
        self.actions.append("stop")

    async def status(self) -> TVStatus:
        return TVStatus(current_app="test", volume=20, muted=False)

    async def info(self):
        from smartest_tv.drivers.base import TVInfo
        return TVInfo(platform="fake", name=self.name)

    async def notify(self, message: str):
        self.actions.append(f"notify:{message}")


# ---------------------------------------------------------------------------
# broadcast()
# ---------------------------------------------------------------------------


def test_broadcast_all_succeed():
    d1 = FakeDriver("tv1")
    d2 = FakeDriver("tv2")

    async def action(d):
        await d.power_off()
        return "turned off"

    results = asyncio.run(broadcast({"tv1": d1, "tv2": d2}, action))
    assert len(results) == 2
    assert all(r["status"] == "ok" for r in results)
    assert d1.actions == ["power_off"]
    assert d2.actions == ["power_off"]


def test_broadcast_partial_failure():
    d1 = FakeDriver("tv1")
    d2 = FakeDriver("tv2", fail_on="power_off")

    async def action(d):
        await d.power_off()
        return "done"

    results = asyncio.run(broadcast({"tv1": d1, "tv2": d2}, action))
    ok = [r for r in results if r["status"] == "ok"]
    err = [r for r in results if r["status"] == "error"]
    assert len(ok) == 1
    assert len(err) == 1
    assert err[0]["tv"] == "tv2"


def test_broadcast_deep_link():
    d1 = FakeDriver("living-room")
    d2 = FakeDriver("bedroom")

    async def action(d):
        await d.launch_app_deep("netflix", "82656797")
        return "playing"

    results = asyncio.run(broadcast({"living-room": d1, "bedroom": d2}, action))
    assert d1.actions == ["deep_link:netflix:82656797"]
    assert d2.actions == ["deep_link:netflix:82656797"]


def test_broadcast_volume():
    d1 = FakeDriver("tv1")
    d2 = FakeDriver("tv2")
    d3 = FakeDriver("tv3")

    async def action(d):
        await d.set_volume(25)
        return "vol 25"

    results = asyncio.run(broadcast({"tv1": d1, "tv2": d2, "tv3": d3}, action))
    assert all(r["status"] == "ok" for r in results)
    for d in [d1, d2, d3]:
        assert d.actions == ["set_volume:25"]


def test_broadcast_notify():
    d1 = FakeDriver("tv1")
    d2 = FakeDriver("tv2")

    async def action(d):
        await d.notify("Dinner's ready!")
        return "sent"

    results = asyncio.run(broadcast({"tv1": d1, "tv2": d2}, action))
    assert d1.actions == ["notify:Dinner's ready!"]
    assert d2.actions == ["notify:Dinner's ready!"]


# ---------------------------------------------------------------------------
# connect_all()
# ---------------------------------------------------------------------------


def test_connect_all_success():
    created = {}

    def factory(name):
        d = FakeDriver(name)
        created[name] = d
        return d

    drivers = asyncio.run(connect_all(["tv1", "tv2"], factory))
    assert set(drivers.keys()) == {"tv1", "tv2"}
    assert all(d.connected for d in drivers.values())


def test_connect_all_partial_failure():
    def factory(name):
        return FakeDriver(name, fail_on="connect" if name == "tv2" else None)

    drivers = asyncio.run(connect_all(["tv1", "tv2", "tv3"], factory))
    assert "tv1" in drivers
    assert "tv2" not in drivers  # failed to connect
    assert "tv3" in drivers


def test_broadcast_empty_drivers():
    async def action(d):
        return "done"

    results = asyncio.run(broadcast({}, action))
    assert results == []
