"""Multi-platform TV discovery via SSDP and ADB port scan."""

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
    Android/Fire TV ADB (port 5555).

    Returns a list of dicts with 'ip', 'name', 'platform', 'raw' keys.
    """
    results = await asyncio.gather(
        _ssdp_discover(timeout=timeout),
        _adb_scan(timeout=timeout),
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


async def _adb_scan(timeout: float = 3.0) -> list[dict]:
    """Scan common subnets for Android/Fire TV ADB port (5555)."""
    local_ip = _get_local_ip()
    if not local_ip:
        return []

    prefix = ".".join(local_ip.split(".")[:3])
    candidates = [f"{prefix}.{i}" for i in range(1, 255)]

    connect_timeout = min(1.0, timeout / 2)

    async def _check(ip: str) -> dict | None:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 5555),
                timeout=connect_timeout,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return {"ip": ip, "name": f"Android TV ({ip})", "platform": "android", "raw": ""}
        except Exception:
            return None

    # Run in batches of 50 to avoid too many open sockets
    found = []
    for i in range(0, len(candidates), 50):
        batch = candidates[i : i + 50]
        results = await asyncio.gather(*[_check(ip) for ip in batch])
        found.extend(r for r in results if r is not None)
        if found:
            break  # Stop after first batch that finds something

    return found


def _extract_name(text: str, ip: str, platform: str) -> str:
    """Extract a human-readable TV name from SSDP response text."""
    # LG-specific header
    m = re.search(r"DLNADeviceName\.lge\.com:\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Generic friendly name
    m = re.search(r"friendlyName:\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Server header fallback
    m = re.search(r"SERVER:\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:40]

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
