"""Shared TCP probing.

Used by subnet discovery (`_engine/discovery.py`) and manual-IP platform
probing (`setup.py`) so connect/close semantics live in exactly one
place. Kept outside `_engine` — it is a public utility with no TV
driver dependencies.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


async def probe_port(ip: str, port: int, connect_timeout: float) -> bool:
    """TCP-connect probe one port. True if something is listening.

    Only network/timeout conditions count as "no listener" — programming
    errors propagate instead of being masked as a closed port.
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=connect_timeout,
        )
    except (asyncio.TimeoutError, OSError):
        return False
    try:
        writer.close()
        await writer.wait_closed()
    except (asyncio.TimeoutError, OSError):
        # Transport already gone mid-close — the listener was still there.
        pass
    return True


# ---------------------------------------------------------------------------
# MAC → IP resolution (ARP cache)
# ---------------------------------------------------------------------------

_Parser = Callable[[str], "list[tuple[str, str]]"]
_IPv4_RE = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
_MAC_RE = re.compile(r"[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5}")


def _norm_mac(mac: str) -> str:
    """Normalize a MAC to bare lowercase hex (``aa:bb:cc:dd:ee:ff`` → ``aabbccddeeff``)."""
    return re.sub(r"[:\-]", "", mac.strip().lower())


def _is_mac(mac: str) -> bool:
    bare = _norm_mac(mac)
    return len(bare) == 12 and all(c in "0123456789abcdef" for c in bare)


def _parse_ip_neigh(out: str) -> list[tuple[str, str]]:
    """Parse ``ip neigh show`` output → [(ip, mac), ...]."""
    pairs: list[tuple[str, str]] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5 or not _IPv4_RE.fullmatch(parts[0]):
            continue
        try:
            idx = parts.index("lladdr")
        except ValueError:
            continue
        if idx + 1 < len(parts) and _is_mac(parts[idx + 1]):
            pairs.append((parts[0], parts[idx + 1]))
    return pairs


def _parse_proc_net_arp(text: str) -> list[tuple[str, str]]:
    """Parse ``/proc/net/arp`` contents → [(ip, mac), ...]."""
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines()[1:]:  # skip header
        parts = line.split()
        if len(parts) >= 4 and _IPv4_RE.fullmatch(parts[0]) and _is_mac(parts[3]):
            pairs.append((parts[0], parts[3]))
    return pairs


def _parse_arp_a(out: str) -> list[tuple[str, str]]:
    """Parse ``arp -a``/``-an`` output (Linux, macOS, Windows) → [(ip, mac), ...].

    Covers the three shapes seen in the wild::

        ? (192.168.1.5) at a4:36:c7:dc:f7:8c [ether] on enp6s0   # Linux/macOS
        ? (192.168.1.5) at a4:36:c7:dc:f7:8c on en0 ifscope [ethernet]
          192.168.1.5        a4-36-c7-dc-f7-8c     dynamic       # Windows
    """
    pairs: list[tuple[str, str]] = []
    for line in out.splitlines():
        m_ip = _IPv4_RE.search(line)
        m_mac = _MAC_RE.search(line)
        if m_ip and m_mac:
            pairs.append((m_ip.group(0), m_mac.group(0)))
    return pairs


def lookup_ip_by_mac(mac: str) -> str | None:
    """Resolve a MAC address to its current IPv4 via the local ARP cache.

    DHCP routers routinely re-lease TV addresses (measured 2026-10-01:
    living-room webOS TV moved 192.168.200.101 → .107 overnight), which
    bricks a statically configured TV. The ARP cache is the one source
    that needs no extra privileges, no root, and no network scan — the
    kernel already knows the MAC↔IP binding from routine traffic.

    Order: ``/proc/net/arp`` (zero-cost read) → ``ip neigh`` (Linux) →
    ``arp -a`` (macOS/BSD/Windows fallback). Returns the first matching
    IPv4, or None when the MAC is absent from every source.
    """
    if not _is_mac(mac):
        return None
    want = _norm_mac(mac)
    candidates: list[tuple[str, str]] = []

    def _found() -> str | None:
        return next(
            (c_ip for c_ip, c_mac in candidates if _norm_mac(c_mac) == want), None
        )

    proc_arp = Path("/proc/net/arp")
    if proc_arp.exists():
        try:
            candidates.extend(_parse_proc_net_arp(proc_arp.read_text()))
        except OSError:
            pass
        ip = _found()
        if ip:
            return ip

    if sys.platform == "win32":
        commands: list[tuple[list[str], _Parser]] = [(["arp", "-a"], _parse_arp_a)]
    else:
        commands = [
            (["ip", "neigh", "show"], _parse_ip_neigh),
            (["arp", "-an"], _parse_arp_a),
        ]

    for cmd, parse in commands:
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        candidates.extend(parse(proc.stdout or ""))
        ip = _found()
        if ip:
            return ip
    return None
