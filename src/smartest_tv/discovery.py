"""SSDP auto-discovery for LG webOS TVs on the local network."""

from __future__ import annotations

import asyncio
import re
import socket


SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 3
SSDP_ST = "urn:lge-com:service:webos-second-screen:1"

SEARCH_MSG = (
    "M-SEARCH * HTTP/1.1\r\n"
    f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
    'MAN: "ssdp:discover"\r\n'
    f"MX: {SSDP_MX}\r\n"
    f"ST: {SSDP_ST}\r\n"
    "\r\n"
)


async def discover(timeout: float = 5.0) -> list[dict]:
    """Discover LG webOS TVs on the local network via SSDP.

    Returns a list of dicts with 'ip' and 'name' keys.
    """
    found: dict[str, dict] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    sock.sendto(SEARCH_MSG.encode(), (SSDP_ADDR, SSDP_PORT))

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
            name_match = re.search(
                r"DLNADeviceName\.lge\.com:\s*(.+)", text, re.IGNORECASE
            )
            name = name_match.group(1).strip() if name_match else f"LG TV ({ip})"
            found[ip] = {"ip": ip, "name": name}
        except (TimeoutError, asyncio.TimeoutError, OSError):
            break

    sock.close()
    return list(found.values())
