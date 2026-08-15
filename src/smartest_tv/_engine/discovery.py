"""Multi-platform TV discovery via SSDP and Android remote-service port scan."""

from __future__ import annotations

import asyncio
import re
import socket

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 3

_SSDP_TARGETS = [
    ("urn:lge-com:service:webos-second-screen:1", "lg"),
    ("urn:samsung.com:device:RemoteControlReceiver:1", "samsung"),
    ("roku:ecp", "roku"),
]


async def discover(timeout: float = 3.0) -> list[dict]:
    """Discover smart TVs on the local network.

    Sends SSDP M-SEARCH for LG, Samsung, and Roku. Also port-scans for
    the Android TV Remote Protocol v2 service (port 6466 — what the
    driver actually connects to), with legacy ADB 5555 as a fallback
    probe for old setups.

    Returns a list of dicts with 'ip', 'name', 'platform', 'raw' keys.
    """
    results = await asyncio.gather(
        _ssdp_discover(timeout=timeout),
        _android_scan(timeout=timeout),
        return_exceptions=True,
    )

    found: dict[str, dict] = {}
    for r in results:
        if isinstance(r, list):
            for tv in r:
                ip = tv["ip"]
                if ip not in found:
                    found[ip] = tv

    return list(found.values())


async def _ssdp_discover(timeout: float = 3.0) -> list[dict]:
    """Send SSDP M-SEARCH for all known TV service types."""
    found: dict[str, dict] = {}

    for st, platform in _SSDP_TARGETS:
        msg = (
            "M-SEARCH * HTTP/1.1\r\n"
            f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
            'MAN: "ssdp:discover"\r\n'
            f"MX: {SSDP_MX}\r\n"
            f"ST: {st}\r\n"
            "\r\n"
        )
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            sock.sendto(msg.encode(), (SSDP_ADDR, SSDP_PORT))

            loop = asyncio.get_event_loop()
            end = loop.time() + timeout

            while loop.time() < end:
                try:
                    data, addr = await asyncio.wait_for(
                        loop.run_in_executor(None, sock.recvfrom, 4096),
                        timeout=max(0.1, end - loop.time()),
                    )
                    ip = addr[0]
                    if ip in found:
                        continue
                    text = data.decode(errors="ignore")
                    name = _extract_name(text, ip, platform)
                    found[ip] = {
                        "ip": ip,
                        "name": name,
                        "platform": platform,
                        "raw": text,
                    }
                except (TimeoutError, asyncio.TimeoutError, OSError):
                    break
        except OSError:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

    return list(found.values())


# Android TV Remote Protocol v2 — the service the AndroidDriver talks to
# (TLS on 6466; 6467 is its pairing port). Discovery only needs a TCP
# connect signal, no handshake. Before v1.3.0 this scan probed ADB 5555
# only, which the driver stopped using when it migrated from adb-shell
# to the Remote Protocol — so stock Android TVs (no ADB debugging) were
# invisible to `stv setup` and the HA discovery flow (issue #15 reports).
_ANDROID_REMOTE_PORT = 6466
_ANDROID_LEGACY_ADB_PORT = 5555


async def _probe_port(ip: str, port: int, connect_timeout: float) -> bool:
    """TCP-connect probe one port. True if something is listening."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=connect_timeout,
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


async def _android_scan(timeout: float = 3.0) -> list[dict]:
    """Scan the local /24 for the Android TV remote service (6466).

    Port order matters: 6466 first — it is what the driver connects to.
    Legacy ADB 5555 is kept as a second-wave fallback for devices from
    pre-migration setups; note a 5555-only device cannot actually be
    driven by the Remote-Protocol driver (it will fail at pairing with a
    clear error), but surfacing it is still more helpful than silence.
    """
    local_ip = _get_local_ip()
    if not local_ip:
        return []

    prefix = ".".join(local_ip.split(".")[:3])
    candidates = [f"{prefix}.{i}" for i in range(1, 255)]

    connect_timeout = min(1.0, timeout / 2)
    found: dict[str, dict] = {}
    remaining = list(candidates)

    # Run in batches of 50 to avoid too many open sockets. Scan every
    # batch: stopping at the first hit hid additional Android TVs on the
    # same network (multi-TV households got partial discovery results).
    for port in (_ANDROID_REMOTE_PORT, _ANDROID_LEGACY_ADB_PORT):
        still_remaining: list[str] = []
        for i in range(0, len(remaining), 50):
            batch = remaining[i : i + 50]
            results = await asyncio.gather(
                *[_probe_port(ip, port, connect_timeout) for ip in batch]
            )
            for ip, hit in zip(batch, results):
                if hit:
                    found[ip] = {
                        "ip": ip,
                        "name": f"Android TV ({ip})",
                        "platform": "android",
                        "raw": f"port:{port}",
                    }
                else:
                    still_remaining.append(ip)
        remaining = still_remaining
        if not remaining:
            break

    return list(found.values())


def _sanitize_name(raw: str, max_len: int = 64) -> str:
    """Scrub an SSDP-supplied name before it lands in config / UI.

    SSDP responses come from any device on the LAN; a malicious neighbour
    can craft a friendlyName with Rich-markup control chars ("[red]...[/]")
    or shell-escapes that later break the terminal. Keep letters, digits,
    spaces, and the common punctuation one expects in a TV name; drop the
    rest.
    """
    # Strip CR/LF first (SSDP headers are delimited by CRLF — a second
    # header leaked into group(1) would otherwise be stored).
    cleaned = raw.split("\r")[0].split("\n")[0]
    cleaned = re.sub(r"[^\w .()\-']", "", cleaned, flags=re.UNICODE)
    cleaned = cleaned.strip()
    return cleaned[:max_len]


def _extract_name(text: str, ip: str, platform: str) -> str:
    """Extract a human-readable TV name from SSDP response text."""
    # LG-specific header
    m = re.search(r"DLNADeviceName\.lge\.com:\s*(.+)", text, re.IGNORECASE)
    if m:
        name = _sanitize_name(m.group(1))
        if name:
            return name

    # Generic friendly name
    m = re.search(r"friendlyName:\s*(.+)", text, re.IGNORECASE)
    if m:
        name = _sanitize_name(m.group(1))
        if name:
            return name

    # Server header fallback
    m = re.search(r"SERVER:\s*(.+)", text, re.IGNORECASE)
    if m:
        name = _sanitize_name(m.group(1), max_len=40)
        if name:
            return name

    brand = {"lg": "LG", "samsung": "Samsung", "roku": "Roku"}.get(platform, "Smart")
    return f"{brand} TV ({ip})"


def _get_local_ip() -> str:
    """Get the local machine's primary IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""
