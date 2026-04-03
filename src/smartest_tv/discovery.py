"""TV discovery — find smart TVs on the local network.

Delegates to _engine for SSDP and ADB scanning.
"""

from __future__ import annotations


async def discover(timeout: float = 3.0) -> list[dict]:
    """Discover smart TVs on the local network.

    Returns list of dicts with keys: ip, platform, name, port.
    """
    try:
        from smartest_tv._engine.discovery import discover as _discover
        return await _discover(timeout)
    except ImportError:
        raise ImportError(
            "TV discovery requires the full install. "
            "Install from PyPI: pip install stv"
        )
