"""Driver factory for smartest-tv.

Creates TVDriver instances from config. Raises ValueError on failure
(never calls sys.exit) so it is safe to use from both CLI and MCP server.
"""

from __future__ import annotations

from typing import NoReturn

from smartest_tv.config import get_tv_config
from smartest_tv.drivers.base import TVDriver


def _walk_import_chain(exc: BaseException) -> tuple[str, BaseException]:
    """Find (module name, exception) of the deepest ImportError in a chain.

    Engine drivers re-raise their own ImportError (``name=None``) chained
    to the original failure, so the informative name usually lives one
    or two ``__cause__`` levels down.
    """
    probe: BaseException | None = exc
    seen: set[int] = set()
    while probe is not None and id(probe) not in seen:
        seen.add(id(probe))
        if isinstance(probe, ImportError) and probe.name:
            return probe.name, probe
        probe = probe.__cause__ or probe.__context__
    return "", exc


def root_import_name(exc: BaseException) -> str:
    """Module name of the deepest ImportError in a cause chain ("")."""
    return _walk_import_chain(exc)[0]


def _driver_import_error(
    platform: str, package: str, extra: str, exc: ImportError
) -> NoReturn:
    """Build a helpful ImportError for a failed driver import.

    Two very different failure modes look identical to a bare ``except
    ImportError`` (issue #14):

    1. The driver package itself is missing → tell the user how to
       install it (pipx for CLI installs, ``stv[extra]`` otherwise).
    2. A *transitive* dependency fails to import (e.g. a broken/partially
       upgraded ``aiofiles`` in Home Assistant's site-packages) → the
       install advice is wrong and actively misleading; what the user
       needs is the name of the actually-broken module.

    ``ImportError.name`` (Python 3.3+) tells us which module failed, so
    we can pick the right message. The original exception is always
    chained so the full traceback stays visible.

    The name usually lives deeper than the caught exception: engine
    drivers re-raise their own ImportError (``name=None``) chained to
    the original, so we walk the cause chain for the first ImportError
    carrying a module name.
    """
    root, root_exc = _walk_import_chain(exc)
    root_pkg = root.split(".")[0]

    if root_pkg and root_pkg not in (package, "smartest_tv"):
        # The driver is installed; something it imports is broken.
        raise ImportError(
            f"The {platform} driver is installed, but its dependency "
            f"'{root_pkg}' failed to import: {root_exc}\n"
            f"This usually means a broken or partially upgraded install of "
            f"'{root_pkg}' (mixed file versions in site-packages), not a "
            f"missing {package} install.\n"
            f"Reinstall/repair '{root_pkg}' in the environment stv runs in:\n"
            f"  pip install --force-reinstall '{root_pkg}'\n"
            f"Home Assistant users: the chained traceback below shows the "
            f"real cause — repair that package in HA, then reload this "
            f"integration."
        ) from exc

    raise ImportError(
        f"{platform.capitalize()} driver requires {package}.\n"
        f"  pipx inject stv '{package}'             (recommended, pipx installs)\n"
        f"  pip install 'stv[{extra}]'              (alternative)\n"
        f"  Home Assistant: requirements are installed automatically — "
        f"reload the integration or check the log for the chained cause."
    ) from exc


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
        except ImportError as exc:
            _driver_import_error("LG", "aiowebostv", "lg", exc)
        return LGDriver(ip=ip, mac=mac)

    elif platform == "samsung":
        try:
            from smartest_tv._engine.drivers.samsung import SamsungDriver
        except ImportError as exc:
            _driver_import_error("Samsung", "samsungtvws", "samsung", exc)
        return SamsungDriver(ip=ip, mac=mac)

    elif platform in ("android", "firetv"):
        try:
            from smartest_tv._engine.drivers.android import AndroidDriver
        except ImportError as exc:
            _driver_import_error("Android", "androidtvremote2", "android", exc)
        return AndroidDriver(ip=ip)

    elif platform == "roku":
        try:
            from smartest_tv._engine.drivers.roku import RokuDriver
        except ImportError as exc:
            _driver_import_error("Roku", "aiohttp", "roku", exc)
        return RokuDriver(ip=ip)

    elif platform == "browser":
        from smartest_tv.drivers.browser import BrowserDriver
        return BrowserDriver()

    else:
        raise ValueError(f"Unknown platform: {platform}. Run: stv setup")
