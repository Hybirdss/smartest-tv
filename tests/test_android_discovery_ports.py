"""Android discovery must scan the right ports and every subnet batch.

Two regressions pinned here:
  1. Before v1.3.0 the scan probed only ADB 5555 — a port the driver
     stopped using when it migrated to Remote Protocol v2 (6466). Stock
     Android TVs were invisible to `stv setup` and HA discovery.
  2. Before v1.2.1 the scan stopped at the first batch that found a TV,
     hiding additional TVs in later batches.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("aiohttp")  # engine discovery pulls driver deps

from smartest_tv._engine import discovery  # noqa: E402


def _install_fake_connect(monkeypatch, hits: dict[int, set[str]]):
    """open_connection succeeds only for (port in hits, ip in hits[port])."""

    async def fake_open_connection(ip, port):
        if port in hits and ip in hits[port]:
            return None, _NullWriter()
        raise OSError("refused")

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)


class _NullWriter:
    def close(self):
        pass

    async def wait_closed(self):
        pass


@pytest.mark.asyncio
async def test_discovers_remote_protocol_6466(monkeypatch):
    local_ip = "192.168.1.100"
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: local_ip)
    _install_fake_connect(monkeypatch, {6466: {"192.168.1.42"}})

    found = await discovery._android_scan(timeout=1.0)
    assert [tv["ip"] for tv in found] == ["192.168.1.42"]
    assert found[0]["platform"] == "android"
    assert "6466" in found[0]["raw"]


@pytest.mark.asyncio
async def test_legacy_5555_still_discovered(monkeypatch):
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: "192.168.1.100")
    _install_fake_connect(monkeypatch, {5555: {"192.168.1.42"}})

    found = await discovery._android_scan(timeout=1.0)
    assert [tv["ip"] for tv in found] == ["192.168.1.42"]
    assert "5555" in found[0]["raw"]


@pytest.mark.asyncio
async def test_finds_tvs_across_all_batches(monkeypatch):
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: "192.168.1.100")
    # first batch window + last batch window, mixed port generations
    _install_fake_connect(
        monkeypatch,
        {6466: {"192.168.1.3", "192.168.1.254"}, 5555: {"192.168.1.130"}},
    )

    found = await discovery._android_scan(timeout=1.0)
    ips = {tv["ip"] for tv in found}
    assert ips == {"192.168.1.3", "192.168.1.130", "192.168.1.254"}


@pytest.mark.asyncio
async def test_6466_wins_over_legacy_5555(monkeypatch):
    """A TV with both ports open is reported once, primary port first."""
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: "192.168.1.100")
    _install_fake_connect(monkeypatch, {6466: {"192.168.1.5"}, 5555: {"192.168.1.5"}})

    found = await discovery._android_scan(timeout=1.0)
    assert len(found) == 1
    assert "6466" in found[0]["raw"]


@pytest.mark.asyncio
async def test_no_local_ip_returns_empty(monkeypatch):
    monkeypatch.setattr(discovery, "_get_local_ip", lambda: None)
    assert await discovery._android_scan(timeout=1.0) == []


@pytest.mark.asyncio
async def test_real_socket_6466_listener_is_discovered(monkeypatch):
    """End-to-end with a real TCP listener (loopback only, no LAN traffic).

    _get_local_ip is faked to 127.0.0.1 so the /24 candidates become
    127.0.0.1-254; only our listener on :6466 answers.
    """
    import socket as _socket

    server = _socket.socket()
    server.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 6466))
    server.listen(5)
    try:
        monkeypatch.setattr(discovery, "_get_local_ip", lambda: "127.0.0.1")
        found = await discovery._android_scan(timeout=2.0)
        assert any(tv["ip"] == "127.0.0.1" and "6466" in tv["raw"] for tv in found)
    finally:
        server.close()
