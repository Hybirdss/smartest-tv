"""ADB discovery must scan every subnet batch (regression).

The old loop stopped at the first batch that found an Android TV, so a
second TV in a later batch window was invisible to `stv setup` and the
HA discovery flow.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("aiohttp")  # engine discovery pulls driver deps

from smartest_tv._engine import discovery  # noqa: E402


class _FakeWriter:
    def close(self):
        pass

    async def wait_closed(self):
        pass


@pytest.mark.asyncio
async def test_adb_scan_finds_tvs_across_all_batches(monkeypatch):
    local_ip = "192.168.1.100"
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: local_ip)

    hits = {"192.168.1.3", "192.168.1.254"}  # first batch + last batch

    async def fake_open_connection(ip, port):
        assert port == 5555
        if ip in hits:
            return None, _FakeWriter()
        raise OSError("refused")

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

    found = await discovery._adb_scan(timeout=1.0)
    ips = {tv["ip"] for tv in found}
    assert ips == hits  # old code returned only {"192.168.1.3"}
