"""The Smartest TV integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_PLATFORM, CONF_TV_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smartest TV from a config entry."""
    from smartest_tv.drivers.factory import create_driver

    tv_name = entry.data[CONF_TV_NAME]

    try:
        driver = await hass.async_add_executor_job(create_driver, tv_name)
    except ImportError as exc:
        # Driver package missing, or — more commonly — one of its
        # dependencies is broken in this HA install (issue #14: a mixed
        # aiofiles install surfaced as "install adb-shell", which was
        # nonsense). Log the actionable path, keep the chained traceback.
        from smartest_tv.drivers.factory import root_import_name

        root_pkg = root_import_name(exc).split(".")[0]
        if root_pkg and root_pkg not in ("smartest_tv", "androidtvremote2", "aiowebostv", "samsungtvws", "aiohttp"):
            _LOGGER.error(
                "Failed to set up %s: a dependency of the %s driver (%s) is "
                "broken in this Home Assistant environment — see the chained "
                "traceback below. Repair it with: pip install --force-reinstall %s "
                "(in the HA environment), then reload this integration.",
                tv_name,
                entry.data.get(CONF_PLATFORM, "TV"),
                root_pkg,
                root_pkg,
            )
        else:
            _LOGGER.error(
                "Failed to set up %s: driver requirements are missing or "
                "broken — see the chained traceback below. Reload the "
                "integration to reinstall requirements; if it persists, "
                "check the dependency named in the traceback.",
                tv_name,
            )
        _LOGGER.exception("Driver import error for %s", tv_name)
        return False
    except Exception:
        _LOGGER.exception("Failed to create driver for %s", tv_name)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = driver

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        driver = hass.data[DOMAIN].pop(entry.entry_id, None)
        if driver:
            try:
                await driver.disconnect()
            except Exception:
                pass
    return unload_ok
