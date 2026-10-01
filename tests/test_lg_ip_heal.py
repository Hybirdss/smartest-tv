"""LG driver stale-IP self-heal (DHCP re-lease recovery).

Regression tests for the 2026-10-01 incident class: the TV's DHCP lease
changed (.101 → .107) and every ``stv`` command died with a raw
``OSError: [Errno 113]`` traceback. ``LGDriver.connect`` now catches
unreachable-host errors, re-resolves the TV by MAC via the ARP cache,
confirms a webOS port is listening at the candidate IP, retries once,
and persists the healed IP back to config.
"""

from __future__ import annotations

import pytest

pytest.importorskip("aiowebostv")

import smartest_tv.net as net_mod
from smartest_tv._engine.drivers.lg import LGDriver

STALE_IP = "192.168.200.101"
HEALED_IP = "192.168.200.107"
TV_MAC = "a4:36:c7:dc:f7:8c"


class _FakeClient:
    """Records every construction; fails connect() on the stale IP."""

    instances: list["_FakeClient"] = []

    def __init__(self, host: str, client_key: str | None = None, **_kw):
        self.host = host
        self.client_key = client_key
        self.connected = False
        self.fail_connect: bool = host == STALE_IP
        _FakeClient.instances.append(self)

    def is_connected(self) -> bool:
        return self.connected

    async def connect(self) -> bool:
        if self.fail_connect:
            raise OSError(113, f"Connect call failed ({self.host}, 3001)")
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.connected = False


@pytest.fixture()
def fake_client(monkeypatch):
    import smartest_tv._engine.drivers.lg as lg_mod

    _FakeClient.instances = []
    monkeypatch.setattr(lg_mod, "_SmarTestWebOsClient", _FakeClient)
    return _FakeClient


@pytest.fixture()
def arp_says_healed(monkeypatch):
    async def fake_probe(ip, port, connect_timeout=2.0):
        return ip == HEALED_IP

    monkeypatch.setattr(net_mod, "lookup_ip_by_mac", lambda mac: HEALED_IP)
    monkeypatch.setattr(net_mod, "probe_port", fake_probe)


def _driver(tmp_path, mac: str = TV_MAC) -> LGDriver:
    return LGDriver(
        ip=STALE_IP, mac=mac, key_file=str(tmp_path / "lg_key.json"), tv_name=""
    )


async def test_connect_heals_stale_ip_and_retries(
    tmp_path, fake_client, arp_says_healed, monkeypatch, capsys
):
    calls: list[tuple] = []
    monkeypatch.setattr(
        "smartest_tv.config.update_tv_ip",
        lambda name, old, new: calls.append((name, old, new)) or True,
    )

    d = _driver(tmp_path)
    await d.connect()

    assert d.ip == HEALED_IP
    assert len(fake_client.instances) == 2  # stale attempt, healed retry
    assert fake_client.instances[0].host == STALE_IP
    assert fake_client.instances[1].host == HEALED_IP
    assert fake_client.instances[1].connected
    assert calls == [(None, STALE_IP, HEALED_IP)]
    assert "TV IP changed" in capsys.readouterr().err


async def test_heal_survives_config_write_failure(
    tmp_path, fake_client, arp_says_healed, monkeypatch
):
    def explode(name, old, new):
        raise OSError("read-only config dir")

    monkeypatch.setattr("smartest_tv.config.update_tv_ip", explode)

    d = _driver(tmp_path)
    await d.connect()  # playback must not die on a config write failure
    assert d.ip == HEALED_IP


async def test_no_mac_means_no_heal(tmp_path, fake_client, monkeypatch):
    monkeypatch.setattr(
        net_mod, "lookup_ip_by_mac", lambda mac: pytest.fail("must not be called")
    )
    d = _driver(tmp_path, mac="")
    with pytest.raises(OSError):
        await d.connect()
    assert d.ip == STALE_IP


async def test_mac_not_in_arp_cache_propagates(tmp_path, fake_client, monkeypatch):
    monkeypatch.setattr(net_mod, "lookup_ip_by_mac", lambda mac: None)
    d = _driver(tmp_path)
    with pytest.raises(OSError):
        await d.connect()
    assert d.ip == STALE_IP


async def test_candidate_without_webos_port_is_rejected(
    tmp_path, fake_client, monkeypatch
):
    async def closed_port(ip, port, connect_timeout=2.0):
        return False

    monkeypatch.setattr(net_mod, "lookup_ip_by_mac", lambda mac: HEALED_IP)
    monkeypatch.setattr(net_mod, "probe_port", closed_port)
    persisted: list[tuple] = []
    monkeypatch.setattr(
        "smartest_tv.config.update_tv_ip",
        lambda name, old, new: persisted.append((name, old, new)) or True,
    )

    d = _driver(tmp_path)
    with pytest.raises(OSError):
        await d.connect()
    assert d.ip == STALE_IP  # did NOT adopt the stranger at HEALED_IP
    assert persisted == []


async def test_retry_failure_propagates_without_looping(
    tmp_path, fake_client, arp_says_healed, monkeypatch
):
    class _AlwaysDown(_FakeClient):
        def __init__(self, host: str, client_key: str | None = None, **_kw):
            super().__init__(host, client_key)
            self.fail_connect = True

    import smartest_tv._engine.drivers.lg as lg_mod

    monkeypatch.setattr(lg_mod, "_SmarTestWebOsClient", _AlwaysDown)
    _FakeClient.instances = []  # subclass __init__ appends to the parent list

    d = _driver(tmp_path)
    with pytest.raises(OSError):
        await d.connect()
    assert len(_FakeClient.instances) == 2  # one heal retry, no infinite loop


async def test_successful_connect_skips_heal_entirely(
    tmp_path, fake_client, monkeypatch
):
    d = LGDriver(
        ip=HEALED_IP, mac=TV_MAC, key_file=str(tmp_path / "lg_key.json")
    )
    monkeypatch.setattr(
        net_mod, "lookup_ip_by_mac", lambda mac: pytest.fail("must not be called")
    )
    await d.connect()
    assert d.ip == HEALED_IP
    assert len(fake_client.instances) == 1
