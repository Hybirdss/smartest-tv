"""Media player platform for Smartest TV."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IP, CONF_PLATFORM, CONF_TV_NAME, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
)

# Parse "netflix:Frieren:s2e8" → ("netflix", "Frieren", 2, 8)
_MEDIA_ID_RE = re.compile(
    r"^(?P<platform>\w+):(?P<query>.+?)(?::s(?P<season>\d+)e(?P<episode>\d+))?$"
)


_ACTIVATE_STATES = {"on", "ringing", "active"}
_DEACTIVATE_STATES = {"off", "idle"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smartest TV media player from a config entry."""
    driver = hass.data[DOMAIN][entry.entry_id]
    entity = StvMediaPlayer(entry, driver)
    async_add_entities([entity], update_before_add=True)

    interrupt_sensors: list[dict] = entry.options.get("interrupt_sensors", [])
    for cfg in interrupt_sensors:
        entity_id = cfg.get("entity_id")
        action = cfg.get("action", "pause")
        duck_volume = cfg.get("duck_volume", 0.1)
        if not entity_id:
            continue

        def _make_handler(eid: str, act: str, dvol: float):
            async def _handler(event):
                if event.data.get("entity_id") != eid:
                    return
                new_state = event.data.get("new_state")
                if new_state is None:
                    return
                state_val = new_state.state if hasattr(new_state, "state") else str(new_state)

                if state_val in _ACTIVATE_STATES:
                    if act == "pause":
                        if entity._attr_state == MediaPlayerState.PLAYING:
                            entity._interrupt_was_playing = True
                        await entity.async_media_pause()
                    elif act == "duck":
                        entity._interrupt_prior_volume = entity._attr_volume_level
                        await entity.async_set_volume_level(dvol)
                elif state_val in _DEACTIVATE_STATES:
                    if act == "pause" and getattr(entity, "_interrupt_was_playing", False):
                        entity._interrupt_was_playing = False
                        await entity.async_media_play()
                    elif act == "duck":
                        prior = getattr(entity, "_interrupt_prior_volume", None)
                        if prior is not None:
                            entity._interrupt_prior_volume = None
                            await entity.async_set_volume_level(prior)

            return _handler

        unsub = hass.bus.async_listen("state_changed", _make_handler(entity_id, action, duck_volume))
        entity._interrupt_unsubs.append(unsub)


class StvMediaPlayer(MediaPlayerEntity):
    """Representation of a TV controlled by stv."""

    _attr_has_entity_name = True
    _attr_supported_features = SUPPORT_FLAGS

    # Expose the integration-wide poll cadence to HA so the TV is not
    # hammered by the default 10 s scan interval.
    scan_interval = SCAN_INTERVAL

    # After this many consecutive polling failures we stop retrying
    # every scan and back off; a TV that has been off for an hour
    # should not reopen a WebSocket each minute.
    _MAX_CONSECUTIVE_FAILURES = 3

    def __init__(self, entry: ConfigEntry, driver: Any) -> None:
        """Initialize the media player."""
        self._driver = driver
        self._entry = entry
        self._tv_name: str = entry.data[CONF_TV_NAME]
        self._platform: str = entry.data[CONF_PLATFORM]
        self._connected = False
        self._consecutive_failures = 0

        self._attr_unique_id = f"stv_{entry.data[CONF_IP]}_{self._tv_name}"
        self._attr_name = self._tv_name
        self._attr_state = MediaPlayerState.OFF
        self._attr_available = True
        self._attr_volume_level: float | None = None
        self._attr_is_volume_muted: bool | None = None
        self._attr_app_name: str | None = None

        # Interruption listener state
        self._interrupt_unsubs: list = []
        self._interrupt_was_playing: bool = False
        self._interrupt_prior_volume: float | None = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for the TV."""
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._tv_name,
            "manufacturer": self._platform.capitalize(),
            "model": f"{self._platform} TV",
        }

    async def async_update(self) -> None:
        """Poll the TV for current state.

        A single failed poll no longer forces the entity to OFF — a
        momentary Wi-Fi blip would otherwise make the dashboard flicker
        and force a full LG 8-subscription reconnect on the next cycle.
        We keep the previous state visible, tag the entity unavailable,
        and only flip to OFF once several consecutive polls have failed
        (strong signal that the TV is actually off / removed from the
        network).
        """
        try:
            if not self._connected:
                await self._driver.connect()
                self._connected = True

            status = await self._driver.status()
            self._consecutive_failures = 0
            self._attr_available = True
            self._attr_state = (
                MediaPlayerState.ON if status.powered else MediaPlayerState.OFF
            )
            if status.volume is not None:
                self._attr_volume_level = status.volume / 100.0
            self._attr_is_volume_muted = status.muted
            self._attr_app_name = status.current_app
        except Exception as exc:  # noqa: BLE001 — driver raises OSError, asyncio.TimeoutError, WebOsTv*Error, …
            self._connected = False
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._MAX_CONSECUTIVE_FAILURES:
                # Sustained failure — TV is probably off or off-network.
                self._attr_state = MediaPlayerState.OFF
                self._attr_available = True
            else:
                # Transient glitch — retain last-known state, mark
                # unavailable so the UI shows "?" instead of flapping.
                self._attr_available = False
            _LOGGER.debug(
                "Poll %d/%d failed for %s (%s: %s); will retry",
                self._consecutive_failures,
                self._MAX_CONSECUTIVE_FAILURES,
                self._tv_name,
                type(exc).__name__,
                exc,
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the TV on (Wake-on-LAN if MAC configured)."""
        try:
            await self._driver.power_on()
        except ValueError as exc:
            # LG/Samsung power_on raises ValueError("MAC address required")
            # when no MAC is configured. Turning this into a user-visible
            # notification via a warning log beats surfacing a raw
            # traceback through the HA UI.
            _LOGGER.warning(
                "Cannot power on %s without a MAC address — "
                "re-run setup and add the MAC for Wake-on-LAN. (%s)",
                self._tv_name,
                exc,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the TV off."""
        await self._driver.power_off()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        await self._driver.set_volume(int(volume * 100))

    async def async_volume_up(self) -> None:
        """Turn volume up."""
        await self._driver.volume_up()

    async def async_volume_down(self) -> None:
        """Turn volume down."""
        await self._driver.volume_down()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute."""
        await self._driver.set_mute(mute)

    async def async_media_play(self) -> None:
        """Send play command."""
        await self._driver.play()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self._driver.pause()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self._driver.stop()

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media by content name.

        media_id format: "netflix:Frieren:s2e8" or "youtube:lofi beats" or "spotify:track name"
        """
        match = _MEDIA_ID_RE.match(media_id)
        if not match:
            _LOGGER.error("Invalid media_id format: %s (expected platform:query[:sNeN])", media_id)
            return

        platform = match.group("platform")
        query = match.group("query")
        season = int(match.group("season")) if match.group("season") else None
        episode = int(match.group("episode")) if match.group("episode") else None

        try:
            from smartest_tv.apps import resolve_app
            from smartest_tv.playback import launch_content
            from smartest_tv.resolve import resolve

            content_id = await self.hass.async_add_executor_job(
                resolve, platform, query, season, episode
            )
            app_id, _ = resolve_app(platform, self._platform)

            if not self._connected:
                await self._driver.connect()
                self._connected = True

            await launch_content(self._driver, platform, app_id, content_id)
            _LOGGER.info("Playing %s on %s", media_id, self._tv_name)
        except Exception:
            _LOGGER.exception("Failed to play %s on %s", media_id, self._tv_name)

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect driver and cancel interruption listeners when entity is removed."""
        for unsub in self._interrupt_unsubs:
            unsub()
        self._interrupt_unsubs.clear()
        if self._connected:
            try:
                await self._driver.disconnect()
            except Exception:
                pass
