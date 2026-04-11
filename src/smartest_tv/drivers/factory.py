"""Driver factory for smartest-tv.

Creates TVDriver instances from config. Raises ValueError on failure
(never calls sys.exit) so it is safe to use from both CLI and MCP server.
"""

from __future__ import annotations

from smartest_tv.config import get_tv_config
from smartest_tv.drivers.base import TVDriver


def create_driver(tv_name: str | None = None) -> TVDriver:
    """Create a TVDriver from config.

    Args:
        tv_name: Target TV name. None selects the default TV.

    Returns:
        An unconnected TVDriver instance.

    Raises:
        ValueError: TV not found, not configured, or unknown platform.
        ImportError: Required driver package is not installed.
    """
    # --tv browser: skip config lookup, go straight to browser
    if tv_name == "browser":
        from smartest_tv.drivers.browser import BrowserDriver
        return BrowserDriver()

    try:
        tv = get_tv_config(tv_name)
    except KeyError as e:
        raise ValueError(str(e)) from e

    platform = tv.get("platform", "")

    if not platform:
        from smartest_tv.drivers.browser import BrowserDriver
        return BrowserDriver()

    ip = tv.get("ip", "")
    mac = tv.get("mac", "")

    if platform == "remote":
        from smartest_tv.drivers.remote import RemoteDriver
        url = tv.get("url", "")
        if not url:
            raise ValueError(
                f"Remote TV '{tv_name or 'default'}' has no url. "
                f"Set url in config, e.g.: stv multi add friend --platform remote --url http://ip:8911"
            )
        api_key = tv.get("api_key", "")
        return RemoteDriver(url=url, api_key=api_key or None)

    elif platform == "lg":
        try:
            from smartest_tv._engine.drivers.lg import LGDriver
        except ImportError:
            raise ImportError(
                "LG driver requires bscpylgtv.\n"
                "  pipx inject stv bscpylgtv         (recommended)\n"
                "  pip install 'stv[lg]'             (alternative)"
            )
        return LGDriver(ip=ip, mac=mac)

    elif platform == "samsung":
        try:
            from smartest_tv._engine.drivers.samsung import SamsungDriver
        except ImportError:
            raise ImportError(
                "Samsung driver requires samsungtvws.\n"
                "  pipx inject stv 'samsungtvws[encrypted]'\n"
                "  pip install 'stv[samsung]'"
            )
        return SamsungDriver(ip=ip, mac=mac)

    elif platform in ("android", "firetv"):
        try:
            from smartest_tv._engine.drivers.android import AndroidDriver
        except ImportError:
            raise ImportError(
                "Android driver requires adb-shell.\n"
                "  pipx inject stv adb-shell\n"
                "  pip install 'stv[android]'"
            )
        return AndroidDriver(ip=ip)

    elif platform == "roku":
        try:
            from smartest_tv._engine.drivers.roku import RokuDriver
        except ImportError:
            raise ImportError(
                "Roku driver requires aiohttp.\n"
                "  pipx inject stv aiohttp\n"
                "  pip install 'stv[roku]'"
            )
        return RokuDriver(ip=ip)

    elif platform == "browser":
        from smartest_tv.drivers.browser import BrowserDriver
        return BrowserDriver()

    else:
        raise ValueError(f"Unknown platform: {platform}. Run: stv setup")
