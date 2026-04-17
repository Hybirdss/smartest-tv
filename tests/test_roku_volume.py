"""Roku volume delta-tracking — verifies set_volume does not re-issue
100 VolumeDown keypresses on every call once state is known."""
from __future__ import annotations

import pytest

pytest.importorskip("aiohttp")

from smartest_tv._engine.drivers.roku import RokuDriver


@pytest.fixture
def driver(monkeypatch):
    """A RokuDriver with _keypress mocked — we just count calls."""
    d = RokuDriver(ip="10.0.0.1")
    calls: list[str] = []

    async def fake_keypress(key: str) -> None:
        calls.append(key)

    monkeypatch.setattr(d, "_keypress", fake_keypress)
    return d, calls


@pytest.mark.asyncio
async def test_first_set_volume_does_full_reset(driver):
    d, calls = driver
    await d.set_volume(40)
    # 100 down + 40 up
    assert calls.count("VolumeDown") == 100
    assert calls.count("VolumeUp") == 40
    assert d._known_volume == 40


@pytest.mark.asyncio
async def test_subsequent_set_volume_uses_delta_not_full_reset(driver):
    d, calls = driver
    await d.set_volume(40)
    calls.clear()

    # 40 -> 60: should send exactly 20 VolumeUp keypresses, zero VolumeDown
    await d.set_volume(60)
    assert calls.count("VolumeUp") == 20
    assert calls.count("VolumeDown") == 0
    assert d._known_volume == 60

    # 60 -> 30: 30 VolumeDown, zero VolumeUp
    calls.clear()
    await d.set_volume(30)
    assert calls.count("VolumeDown") == 30
    assert calls.count("VolumeUp") == 0
    assert d._known_volume == 30


@pytest.mark.asyncio
async def test_set_volume_same_level_no_keypresses(driver):
    d, calls = driver
    await d.set_volume(50)
    calls.clear()
    await d.set_volume(50)
    assert calls == []


@pytest.mark.asyncio
async def test_volume_up_down_update_known_state(driver):
    d, calls = driver
    await d.set_volume(20)
    calls.clear()

    await d.volume_up()
    await d.volume_up()
    await d.volume_down()
    assert d._known_volume == 21

    # Delta from 21 -> 25 should now be just 4 up presses.
    calls.clear()
    await d.set_volume(25)
    assert calls.count("VolumeUp") == 4
    assert calls.count("VolumeDown") == 0


@pytest.mark.asyncio
async def test_set_volume_clamps_to_valid_range(driver):
    d, calls = driver
    await d.set_volume(200)  # out of range
    # Should clamp to 100 — 100 down, then 100 up.
    assert calls.count("VolumeUp") == 100
    assert d._known_volume == 100
