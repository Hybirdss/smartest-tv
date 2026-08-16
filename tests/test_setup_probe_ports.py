"""setup._probe_ip port table (v1.3.0 — driver-matching ports).

Probed ports must match what the drivers actually connect to:
Samsung wss 8002 before legacy 8001, Android remote 6466 before legacy
ADB 5555. Before v1.3.0 android probed only 5555 and samsung only 8001,
so current-generation TVs failed platform detection on manual IP entry.
"""

from __future__ import annotations

import asyncio

import pytest

from smartest_tv import setup as setup_mod


class _NullWriter:
    def close(self):
        pass

    async def wait_closed(self):
        pass


def _only_port(monkeypatch, port: int):
    async def fake_open(ip, p):
        if p == port:
            return None, _NullWriter()
        raise OSError("refused")

    monkeypatch.setattr(asyncio, "open_connection", fake_open)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("port", "platform"),
    [
        (3000, "lg"),
        (8002, "samsung"),   # primary wss
        (8001, "samsung"),   # legacy ws
        (8060, "roku"),
        (6466, "android"),   # Remote Protocol v2 (the driver's port)
        (5555, "android"),   # legacy ADB
    ],
)
async def test_probe_matches_driver_ports(monkeypatch, port, platform):
    _only_port(monkeypatch, port)
    result = await setup_mod._probe_ip("10.0.0.7")
    assert result == [{
        "ip": "10.0.0.7",
        "name": setup_mod._make_name(platform, "10.0.0.7"),
        "platform": platform,
        "raw": f"port:{port}",
    }]


@pytest.mark.asyncio
async def test_probe_nothing_open(monkeypatch):
    _only_port(monkeypatch, -1)
    assert await setup_mod._probe_ip("10.0.0.7") == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("primary", "legacy", "platform"),
    [
        (8002, 8001, "samsung"),  # wss beats legacy ws
        (6466, 5555, "android"),  # Remote Protocol v2 beats legacy ADB
    ],
)
async def test_primary_port_wins_when_both_open(monkeypatch, primary, legacy, platform):
    """Both generations of the service running: the driver's port is reported."""

    async def fake_open(ip, p):
        if p in (primary, legacy):
            return None, _NullWriter()
        raise OSError("refused")

    monkeypatch.setattr(asyncio, "open_connection", fake_open)
    result = await setup_mod._probe_ip("10.0.0.7")
    assert result == [{
        "ip": "10.0.0.7",
        "name": setup_mod._make_name(platform, "10.0.0.7"),
        "platform": platform,
        "raw": f"port:{primary}",
    }]
