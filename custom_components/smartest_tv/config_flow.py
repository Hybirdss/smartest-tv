"""Config flow for Smartest TV integration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant

from .const import CONF_IP, CONF_MAC, CONF_PLATFORM, CONF_TV_NAME, DOMAIN, TV_PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def _try_connect(hass: HomeAssistant, platform: str, ip: str) -> bool:
    """Test if we can connect to the TV."""
    try:
        from smartest_tv.config import add_tv
        from smartest_tv.drivers.factory import create_driver

        # Register temporarily so create_driver can find it
        await hass.async_add_executor_job(
            add_tv, "__ha_test__", platform, ip, "", False
        )
        driver = await hass.async_add_executor_job(create_driver, "__ha_test__")
        await driver.connect()
        await driver.disconnect()
        return True
    except Exception:
        _LOGGER.debug("Connection test failed for %s at %s", platform, ip)
        return False


class SmarTestTVConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smartest TV."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry) -> SmarTestTVOptionsFlow:
        return SmarTestTVOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — choose discover or manual."""
        if user_input is not None:
            # Manual entry submitted
            tv_name = user_input[CONF_TV_NAME]

            # Check not already configured
            await self.async_set_unique_id(f"{user_input[CONF_IP]}_{tv_name}")
            self._abort_if_unique_id_configured()

            # Register in stv config so the driver can find it
            await self.hass.async_add_executor_job(
                _register_tv,
                tv_name,
                user_input[CONF_PLATFORM],
                user_input[CONF_IP],
                user_input.get(CONF_MAC, ""),
            )

            return self.async_create_entry(
                title=tv_name,
                data={
                    CONF_TV_NAME: tv_name,
                    CONF_PLATFORM: user_input[CONF_PLATFORM],
                    CONF_IP: user_input[CONF_IP],
                    CONF_MAC: user_input.get(CONF_MAC, ""),
                },
            )

        # Try auto-discovery first
        try:
            self._discovered = await self._async_discover()
        except Exception:
            self._discovered = []

        if self._discovered:
            return await self.async_step_discover()

        # No TVs found — show manual form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TV_NAME): str,
                    vol.Required(CONF_PLATFORM): vol.In(TV_PLATFORMS),
                    vol.Required(CONF_IP): str,
                    vol.Optional(CONF_MAC, default=""): str,
                }
            ),
        )

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle discovery step — select from found TVs."""
        if user_input is not None:
            idx = int(user_input["tv_index"])
            tv = self._discovered[idx]
            tv_name = tv.get("name", f"{tv['platform']}_{tv['ip']}")

            await self.async_set_unique_id(f"{tv['ip']}_{tv_name}")
            self._abort_if_unique_id_configured()

            await self.hass.async_add_executor_job(
                _register_tv,
                tv_name,
                tv["platform"],
                tv["ip"],
                tv.get("mac", ""),
            )

            return self.async_create_entry(
                title=tv_name,
                data={
                    CONF_TV_NAME: tv_name,
                    CONF_PLATFORM: tv["platform"],
                    CONF_IP: tv["ip"],
                    CONF_MAC: tv.get("mac", ""),
                },
            )

        # Build selection list
        tv_options = {
            str(i): f"{tv.get('name', 'TV')} ({tv['platform']}, {tv['ip']})"
            for i, tv in enumerate(self._discovered)
        }

        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema(
                {vol.Required("tv_index"): vol.In(tv_options)}
            ),
            description_placeholders={"count": str(len(self._discovered))},
        )

    async def _async_discover(self) -> list[dict[str, str]]:
        """Run stv SSDP discovery."""
        from smartest_tv.discovery import discover

        return await asyncio.wait_for(discover(timeout=5.0), timeout=10.0)


class SmarTestTVOptionsFlow(OptionsFlow):
    """Options flow for configuring interruption sensors."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage interrupt_sensors option."""
        if user_input is not None:
            raw = user_input.get("interrupt_sensors", "[]").strip()
            try:
                sensors = json.loads(raw) if raw else []
                if not isinstance(sensors, list):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(raw),
                    errors={"interrupt_sensors": "invalid_json"},
                )
            return self.async_create_entry(
                title="",
                data={"interrupt_sensors": sensors},
            )

        current = self.config_entry.options.get("interrupt_sensors", [])
        return self.async_show_form(
            step_id="init",
            data_schema=self._schema(json.dumps(current, indent=2) if current else "[]"),
        )

    @staticmethod
    def _schema(default: str) -> vol.Schema:
        return vol.Schema(
            {vol.Optional("interrupt_sensors", default=default): str}
        )


def _register_tv(name: str, platform: str, ip: str, mac: str) -> None:
    """Register a TV in stv's config file (runs in executor)."""
    from smartest_tv.config import add_tv

    add_tv(name=name, platform=platform, ip=ip, mac=mac, default=False)
