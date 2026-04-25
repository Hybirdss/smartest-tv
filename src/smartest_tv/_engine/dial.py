"""DIAL (Discovery and Launch) helpers — RFC-style SSDP + REST app launch.

DIAL is the protocol Chromecast uses to launch Netflix, YouTube, and a few
other co-developed apps over HTTP. It bypasses Tizen's ``ed.apps.launch``
WebSocket pipe entirely, so it survives even when a TV firmware ignores
``DEEP_LINK metaTag`` (issue #8).

The flow is:

1. SSDP M-SEARCH for ``urn:dial-multiscreen-org:service:dial:1`` →
   the TV responds with an ``Application-URL`` header pointing at the
   DIAL REST endpoint (typically ``http://<ip>:<port>/ws/app/``).
2. ``POST {Application-URL}/{AppName}`` with launch parameters in the
   body. ``AppName`` is the canonical DIAL name, e.g. ``Netflix`` or
   ``YouTube``. A ``2xx`` response means the TV accepted the launch.

Discovery is the slow part (multicast round-trip), so callers should
cache the resolved ``Application-URL`` per-TV.
"""

from __future__ import annotations

import asyncio
import re
import socket
from typing import Final

import aiohttp

_SSDP_ADDR: Final = "239.255.255.250"
_SSDP_PORT: Final = 1900
_DIAL_ST: Final = "urn:dial-multiscreen-org:service:dial:1"


def _build_msearch(mx: int = 2) -> bytes:
    return (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {_SSDP_ADDR}:{_SSDP_PORT}\r\n"
        'MAN: "ssdp:discover"\r\n'
        f"MX: {mx}\r\n"
        f"ST: {_DIAL_ST}\r\n"
        "\r\n"
    ).encode("ascii")


def parse_application_url(response: str) -> str | None:
    """Extract the ``Application-URL`` header value from an SSDP response.

    Header names are case-insensitive per RFC 7230. Trailing CRLF and
    inline whitespace are stripped. Returns ``None`` when the header is
    absent or empty.
    """
    m = re.search(r"^Application-URL\s*:\s*(\S[^\r\n]*)", response, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    url = m.group(1).strip()
    if not url:
        return None
    # DIAL spec recommends but doesn't mandate a trailing slash; normalize away.
    return url.rstrip("/")


async def discover_application_url(host_ip: str, timeout: float = 3.0) -> str | None:
    """Find the DIAL ``Application-URL`` of the TV at ``host_ip``.

    Sends a single M-SEARCH for the DIAL service type and filters
    responses to those originating from ``host_ip``. Returns the URL
    (no trailing slash) or ``None`` if nothing answered in time.
    """
    msg = _build_msearch(mx=int(timeout))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    try:
        sock.sendto(msg, (_SSDP_ADDR, _SSDP_PORT))
        loop = asyncio.get_running_loop()
        end = loop.time() + timeout
        while loop.time() < end:
            remaining = max(0.05, end - loop.time())
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 4096), timeout=remaining
                )
            except (TimeoutError, asyncio.TimeoutError):
                return None
            if addr[0] != host_ip:
                continue
            url = parse_application_url(data.decode(errors="ignore"))
            if url:
                return url
        return None
    except OSError:
        return None
    finally:
        sock.close()


async def launch(
    application_url: str,
    app_name: str,
    body: str,
    *,
    session: aiohttp.ClientSession,
    timeout: float = 10.0,
) -> bool:
    """POST DIAL launch payload to ``{application_url}/{app_name}``.

    Returns ``True`` for any ``2xx`` (DIAL spec uses ``201 Created`` for
    successful launches with a ``LOCATION`` header pointing at the
    running instance — we don't need the instance URL for fire-and-forget
    deep linking, so we just check status). Returns ``False`` on
    network/HTTP failure so the caller can fall back to another launch
    path.
    """
    url = application_url.rstrip("/") + "/" + app_name
    try:
        async with session.post(
            url,
            data=body.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            return 200 <= resp.status < 300
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
        return False


def netflix_body(content_id: str) -> str:
    """Build the Netflix DIAL launch body for a content id or URL.

    Accepts a numeric Netflix title id (``"80100172"``), a full
    ``netflix.com/watch/...`` URL, or a pre-built ``m=...`` query string
    (passed through unchanged). The output matches the format Netflix's
    launch handler expects regardless of transport (DIAL or webOS WAM),
    which is why the LG driver uses the same string.
    """
    if content_id.startswith("m="):
        return content_id
    numeric = content_id
    if "netflix.com" in content_id:
        m = re.search(r"/(?:watch|title)/(\d+)", content_id)
        if m:
            numeric = m.group(1)
    return f"m=https://www.netflix.com/watch/{numeric}&source_type=4"


def youtube_body(content_id: str) -> str:
    """Build the YouTube DIAL launch body for a video id or URL.

    Accepts a raw 11-char video id, a ``youtube.com/watch?v=...`` URL,
    or a ``youtu.be/...`` short link. DIAL bodies use plain
    ``v=<videoId>`` form-encoded.
    """
    video_id = content_id
    if "youtube.com" in content_id or "youtu.be" in content_id:
        m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", content_id)
        if m:
            video_id = m.group(1)
    return f"v={video_id}"
