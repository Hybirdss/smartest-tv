"""ARP-cache MAC→IP lookup (stale-IP self-heal support).

``lookup_ip_by_mac`` is the recovery primitive behind the LG driver's
DHCP self-heal: when a router re-leases the TV's address (measured
2026-10-01: .101 → .107 overnight), the kernel ARP cache is the one
source that knows the new binding without a network scan. These tests
pin the parsers for every platform shape and the fallback order.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import smartest_tv.net as net_mod
from smartest_tv.net import (
    _parse_arp_a,
    _parse_ip_neigh,
    _parse_proc_net_arp,
    lookup_ip_by_mac,
)


class TestParsers:
    def test_ip_neigh_stale_and_reachable(self):
        out = (
            "192.168.200.107 dev enp6s0 lladdr a4:36:c7:dc:f7:8c STALE\n"
            "192.168.200.254 dev enp6s0 lladdr 14:4d:67:f1:17:54 REACHABLE\n"
        )
        assert _parse_ip_neigh(out) == [
            ("192.168.200.107", "a4:36:c7:dc:f7:8c"),
            ("192.168.200.254", "14:4d:67:f1:17:54"),
        ]

    def test_ip_neigh_skips_failed_and_macless(self):
        out = (
            "192.168.200.101 dev enp6s0  FAILED\n"
            "fe80::1 dev enp6s0 lladdr a4:36:c7:dc:f7:8c STALE\n"
            "192.168.200.1 dev enp6s0 lladdr 00:00:00:00:00:00 INCOMPLETE\n"
        )
        assert _parse_ip_neigh(out) == [("192.168.200.1", "00:00:00:00:00:00")]

    def test_proc_net_arp(self):
        text = (
            "IP address       HW type     Flags       HW address            Mask     Device\n"
            "192.168.200.107  0x1         0x2         a4:36:c7:dc:f7:8c     *        enp6s0\n"
            "192.168.200.101  0x1         0x0         00:00:00:00:00:00     *        enp6s0\n"
        )
        assert _parse_proc_net_arp(text) == [
            ("192.168.200.107", "a4:36:c7:dc:f7:8c"),
            ("192.168.200.101", "00:00:00:00:00:00"),
        ]

    def test_arp_a_linux_shape(self):
        out = "? (192.168.1.5) at a4:36:c7:dc:f7:8c [ether]  on enp6s0\n"
        assert _parse_arp_a(out) == [("192.168.1.5", "a4:36:c7:dc:f7:8c")]

    def test_arp_a_macos_shape(self):
        out = "? (192.168.1.5) at a4:36:c7:dc:f7:8c on en0 ifscope [ethernet]\n"
        assert _parse_arp_a(out) == [("192.168.1.5", "a4:36:c7:dc:f7:8c")]

    def test_arp_a_windows_shape(self):
        out = (
            "Interface: 192.168.1.2 --- 0x3\n"
            "  Internet Address      Physical Address      Type\n"
            "  192.168.1.5           a4-36-c7-dc-f7-8c     dynamic\n"
        )
        assert _parse_arp_a(out) == [("192.168.1.5", "a4-36-c7-dc-f7-8c")]


class TestLookupIpByMac:
    def test_rejects_garbage_mac(self):
        assert lookup_ip_by_mac("") is None
        assert lookup_ip_by_mac("not-a-mac") is None
        assert lookup_ip_by_mac("a4:36:c7:dc:f7") is None

    @pytest.fixture()
    def no_proc_arp(self, monkeypatch):
        """Force the subprocess path by hiding /proc/net/arp."""

        class _HiddenPath:
            def __init__(self, *_a):
                pass

            def exists(self):
                return False

        monkeypatch.setattr(net_mod, "Path", _HiddenPath)

    def test_finds_match_from_ip_neigh(self, monkeypatch, no_proc_arp):
        def fake_run(cmd, **kwargs):
            m = MagicMock()
            m.stdout = "192.168.200.107 dev enp6s0 lladdr a4:36:c7:dc:f7:8c STALE\n"
            return m

        monkeypatch.setattr(net_mod.subprocess, "run", fake_run)
        assert lookup_ip_by_mac("a4:36:c7:dc:f7:8c") == "192.168.200.107"

    def test_normalizes_dash_and_case(self, monkeypatch, no_proc_arp):
        def fake_run(cmd, **kwargs):
            m = MagicMock()
            m.stdout = "192.168.200.107 dev enp6s0 lladdr a4:36:c7:dc:f7:8c STALE\n"
            return m

        monkeypatch.setattr(net_mod.subprocess, "run", fake_run)
        assert lookup_ip_by_mac("A4-36-C7-DC-F7-8C") == "192.168.200.107"

    def test_falls_through_to_arp_an(self, monkeypatch, no_proc_arp):
        def fake_run(cmd, **kwargs):
            m = MagicMock()
            if cmd[:2] == ["ip", "neigh"]:
                m.stdout = "192.168.200.182 dev enp6s0 lladdr 98:39:10:c2:0a:2a STALE\n"
            else:
                m.stdout = "? (192.168.200.107) at a4:36:c7:dc:f7:8c [ether]  on enp6s0\n"
            return m

        monkeypatch.setattr(net_mod.subprocess, "run", fake_run)
        assert lookup_ip_by_mac("a4:36:c7:dc:f7:8c") == "192.168.200.107"

    def test_subprocess_failure_returns_none(self, monkeypatch, no_proc_arp):
        def fake_run(cmd, **kwargs):
            raise OSError("no such command")

        monkeypatch.setattr(net_mod.subprocess, "run", fake_run)
        assert lookup_ip_by_mac("a4:36:c7:dc:f7:8c") is None

    def test_proc_net_arp_short_circuits(self, monkeypatch):
        class _FakeProcFile:
            def __init__(self, *_a):
                pass

            def exists(self):
                return True

            def read_text(self):
                return (
                    "IP address       HW type     Flags       HW address            Mask     Device\n"
                    "192.168.200.107  0x1         0x2         a4:36:c7:dc:f7:8c     *        enp6s0\n"
                )

        monkeypatch.setattr(net_mod, "Path", _FakeProcFile)

        def explode(cmd, **kwargs):  # pragma: no cover — must not be reached
            raise AssertionError("subprocess must not run when /proc/net/arp hits")

        monkeypatch.setattr(net_mod.subprocess, "run", explode)
        assert lookup_ip_by_mac("a4:36:c7:dc:f7:8c") == "192.168.200.107"
