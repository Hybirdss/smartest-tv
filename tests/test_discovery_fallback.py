"""Discovery fallback scan & Cast friendly-name enrichment tests."""

from __future__ import annotations

import pytest

pytest.importorskip("aiohttp")

from smartest_tv._engine import discovery  # noqa: E402


@pytest.mark.asyncio
async def test_discover_finds_lg_and_enriches_cast_name_when_ssdp_blocked(monkeypatch):
    """Blocked SSDP still surfaces LG TVs via port fallback + Cast name."""
    local_ip = "192.168.1.50"
    lg_ip = "192.168.1.140"
    android_ip = "192.168.1.151"

    async def no_ssdp(timeout: float = 3.0):
        return []

    async def fake_probe(ip: str, port: int, connect_timeout: float = 2.0):
        return (
            (ip == lg_ip and port in (3000, 3001))
            or (ip == android_ip and port == 6466)
            # Local dev server on port 3000 on local_ip must be ignored.
            or (ip == local_ip and port == 3000)
        )

    async def fake_cast_name(ip: str, timeout: float = 0.4):
        return {
            lg_ip: "[LG] webOS TV UR8250KNA",
            android_ip: "Hello tv Pro",
        }.get(ip)

    monkeypatch.setattr(discovery, "_get_local_ip", lambda: local_ip)
    monkeypatch.setattr(discovery, "_ssdp_discover", no_ssdp)
    monkeypatch.setattr(discovery, "probe_port", fake_probe)
    monkeypatch.setattr(discovery, "_fetch_cast_name", fake_cast_name)

    found = {tv["ip"]: tv for tv in await discovery.discover(timeout=1.0)}
    assert local_ip not in found
    assert found[lg_ip]["platform"] == "lg"
    assert found[lg_ip]["raw"] == "port:3001"
    assert found[lg_ip]["name"] == "LG webOS TV UR8250KNA"
    assert found[android_ip]["platform"] == "android"
    assert found[android_ip]["name"] == "Hello tv Pro"
