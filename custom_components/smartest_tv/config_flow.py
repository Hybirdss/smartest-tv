"""Config flow for Smartest TV integration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow

from .const import CONF_IP, CONF_MAC, CONF_PLATFORM, CONF_TV_NAME, DOMAIN, TV_PLATFORMS

_LOGGER = logging.getLogger(__name__)


class SmarTestTVConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smartest TV."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry) -> SmarTestTVOptionsFlow:
        return SmarTestTVOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered: list[dict[str, str]] = []
        self._pending_tv: dict[str, str] = {}
        self._pair_driver = None
        self._pair_remote = None

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

            return await self._async_finish_setup(
                tv_name=tv_name,
                platform=user_input[CONF_PLATFORM],
                ip=user_input[CONF_IP],
                mac=user_input.get(CONF_MAC, ""),
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

            return await self._async_finish_setup(
                tv_name=tv_name,
                platform=tv["platform"],
                ip=tv["ip"],
                mac=tv.get("mac", ""),
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

    async def _async_finish_setup(
        self, tv_name: str, platform: str, ip: str, mac: str
    ) -> ConfigFlowResult:
        """Register the TV and, when needed, run on-screen pairing.

        Android TV / Fire TV require an explicit pairing handshake with a
        PIN shown on the TV screen (issue #15): without it every command
        fails with "Not paired with this TV. Run: stv setup" — impossible
        advice inside a Home Assistant container.
        """
        self._pending_tv = {
            CONF_TV_NAME: tv_name,
            CONF_PLATFORM: platform,
            CONF_IP: ip,
            CONF_MAC: mac,
        }

        if platform in ("android", "firetv"):
            return await self.async_step_pair()

        await self.hass.async_add_executor_job(_register_tv, tv_name, platform, ip, mac)
        return self._async_create_entry()

    def _async_create_entry(self) -> ConfigFlowResult:
        tv = self._pending_tv
        return self.async_create_entry(
            title=tv[CONF_TV_NAME],
            data={
                CONF_TV_NAME: tv[CONF_TV_NAME],
                CONF_PLATFORM: tv[CONF_PLATFORM],
                CONF_IP: tv[CONF_IP],
                CONF_MAC: tv[CONF_MAC],
            },
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pair with an Android TV / Fire TV.

        First entry: starts pairing — the TV shows a 6-digit PIN.
        With user_input: completes pairing with the entered PIN, then
        creates the config entry.
        """
        from smartest_tv._engine.drivers.android import (
            AndroidDriver,
            CannotConnect,
            InvalidAuth,
        )

        errors: dict[str, str] = {}

        if user_input is not None:
            pin = str(user_input.get("pin", "")).strip()
            try:
                await self._pair_driver.finish_pairing(self._pair_remote, pin)
            except InvalidAuth:
                errors["pin"] = "invalid_pin"
            except (CannotConnect, ConnectionError, asyncio.TimeoutError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 — anything else: retry once
                _LOGGER.exception("Unexpected pairing error for %s", self._pending_tv.get(CONF_IP))
                errors["base"] = "unknown"
            else:
                try:
                    await self._pair_driver.disconnect()
                except Exception:  # noqa: BLE001
                    pass
                self._pair_driver = None
                self._pair_remote = None
                tv = self._pending_tv
                await self.hass.async_add_executor_job(
                    _register_tv, tv[CONF_TV_NAME], tv[CONF_PLATFORM], tv[CONF_IP], tv[CONF_MAC]
                )
                return self._async_create_entry()
        else:
            # Start (or resume) pairing: TV displays the PIN prompt.
            ip = self._pending_tv[CONF_IP]
            try:
                self._pair_driver = AndroidDriver(ip=ip)
                # Already paired? start_pairing() returns a connected
                # remote — skip straight to entry creation.
                try:
                    await self._pair_driver.connect()
                except RuntimeError:
                    pass  # not paired — expected on first setup
                if self._pair_driver.paired:
                    try:
                        await self._pair_driver.disconnect()
                    except Exception:  # noqa: BLE001
                        pass
                    self._pair_driver = None
                    await self.hass.async_add_executor_job(
                        _register_tv,
                        self._pending_tv[CONF_TV_NAME],
                        self._pending_tv[CONF_PLATFORM],
                        ip,
                        self._pending_tv[CONF_MAC],
                    )
                    return self._async_create_entry()
                self._pair_remote = await self._pair_driver.start_pairing()
            except (CannotConnect, ConnectionError, asyncio.TimeoutError, OSError) as exc:
                _LOGGER.warning("Cannot reach Android TV at %s: %s", ip, exc)
                # TV unreachable — register anyway; pairing can be redone
                # by removing/re-adding the entry. Better than a dead end.
                await self.hass.async_add_executor_job(
                    _register_tv,
                    self._pending_tv[CONF_TV_NAME],
                    self._pending_tv[CONF_PLATFORM],
                    ip,
                    self._pending_tv[CONF_MAC],
                )
                return self._async_create_entry()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to start pairing with %s", ip)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({vol.Required("pin"): str}),
            errors=errors,
            description_placeholders={"name": self._pending_tv.get(CONF_TV_NAME, "TV")},
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
