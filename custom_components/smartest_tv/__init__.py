"""The Smartest TV integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_TV_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smartest TV from a config entry."""
    from smartest_tv.drivers.factory import create_driver

    tv_name = entry.data[CONF_TV_NAME]

    try:
        driver = await hass.async_add_executor_job(create_driver, tv_name)
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
