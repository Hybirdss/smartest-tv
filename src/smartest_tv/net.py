"""Shared TCP probing.

Used by subnet discovery (`_engine/discovery.py`) and manual-IP platform
probing (`setup.py`) so connect/close semantics live in exactly one
place. Kept outside `_engine` — it is a public utility with no TV
driver dependencies.
"""

from __future__ import annotations

import asyncio


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
