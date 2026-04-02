"""smartest-tv MCP Server — unified TV control across platforms."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fastmcp import FastMCP

from smartest_tv.apps import resolve_app
from smartest_tv.drivers.base import TVDriver

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TV_PLATFORM = os.environ.get("TV_PLATFORM", "lg")
TV_IP = os.environ.get("TV_IP", "")
TV_MAC = os.environ.get("TV_MAC", "")
TV_KEY_FILE = os.environ.get("TV_KEY_FILE", "")

# ---------------------------------------------------------------------------
# Driver management
# ---------------------------------------------------------------------------
_driver: TVDriver | None = None
_driver_lock = asyncio.Lock()


def _create_driver() -> TVDriver:
    """Create a driver based on TV_PLATFORM env var."""
    if TV_PLATFORM == "lg":
        from smartest_tv.drivers.lg import LGDriver

        return LGDriver(ip=TV_IP, mac=TV_MAC, key_file=TV_KEY_FILE)
    elif TV_PLATFORM == "samsung":
        from smartest_tv.drivers.samsung import SamsungDriver

        return SamsungDriver(ip=TV_IP, mac=TV_MAC)
    elif TV_PLATFORM in ("android", "firetv"):
        from smartest_tv.drivers.android import AndroidDriver

        return AndroidDriver(ip=TV_IP)
    elif TV_PLATFORM == "roku":
        from smartest_tv.drivers.roku import RokuDriver

        return RokuDriver(ip=TV_IP)
    else:
        raise ValueError(f"Unknown TV platform: {TV_PLATFORM}. Use: lg, samsung, android, roku")


async def _get_driver() -> TVDriver:
    global _driver
    async with _driver_lock:
        if _driver is None:
            _driver = _create_driver()
            await _driver.connect()
        return _driver


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "smartest-tv",
    instructions=(
        "Control a smart TV (LG, Samsung, Android TV, Roku). "
        "Supports power, volume, app launching with deep linking, "
        "media playback, input switching, and notifications.\n\n"
        "**Deep Linking:** Pass a content_id to tv_launch to open specific content:\n"
        "- Netflix: numeric episode/movie ID (e.g. 82656797)\n"
        "- YouTube: video ID (e.g. dQw4w9WgXcQ)\n"
        "- Spotify: URI (e.g. spotify:album:5poA9SAx0Xiz1cd17fWBLS)\n\n"
        "Content IDs are the same across all TV platforms. "
        "The server auto-formats deep links for each platform.\n\n"
        "For Netflix: close the app first with tv_close, then tv_launch with content_id."
    ),
)


# -- Power -------------------------------------------------------------------


@mcp.tool()
async def tv_on() -> str:
    """Turn on the TV (Wake-on-LAN or platform equivalent)."""
    d = await _get_driver()
    await d.power_on()
    return "TV turning on."


@mcp.tool()
async def tv_off() -> str:
    """Turn off the TV (standby)."""
    d = await _get_driver()
    await d.power_off()
    return "TV turned off."


# -- Volume ------------------------------------------------------------------


@mcp.tool()
async def tv_volume() -> dict:
    """Get current volume and mute status."""
    d = await _get_driver()
    return {"volume": await d.get_volume(), "muted": await d.get_muted()}


@mcp.tool()
async def tv_set_volume(level: int) -> str:
    """Set volume (0-100)."""
    d = await _get_driver()
    await d.set_volume(level)
    return f"Volume set to {level}."


@mcp.tool()
async def tv_volume_up() -> str:
    """Increase volume by one step."""
    d = await _get_driver()
    await d.volume_up()
    return "Volume increased."


@mcp.tool()
async def tv_volume_down() -> str:
    """Decrease volume by one step."""
    d = await _get_driver()
    await d.volume_down()
    return "Volume decreased."


@mcp.tool()
async def tv_mute(mute: bool | None = None) -> str:
    """Mute, unmute, or toggle."""
    d = await _get_driver()
    if mute is None:
        mute = not await d.get_muted()
    await d.set_mute(mute)
    return f"TV {'muted' if mute else 'unmuted'}."


# -- Apps & Deep Linking -----------------------------------------------------


@mcp.tool()
async def tv_launch(app: str, content_id: str | None = None) -> str:
    """Launch an app, optionally deep linking to specific content.

    Args:
        app: App name (netflix, youtube, spotify, disney, prime, etc.) or raw app ID.
        content_id: Content identifier for deep linking.
            - Netflix: episode/movie ID (e.g. "82656797")
            - YouTube: video ID (e.g. "dQw4w9WgXcQ") or full URL
            - Spotify: URI (e.g. "spotify:album:5poA9SAx0Xiz1cd17fWBLS")
    """
    d = await _get_driver()
    app_id, name = resolve_app(app, d.platform)

    if content_id:
        await d.launch_app_deep(app_id, content_id)
        return f"Launched {name} with content: {content_id}"
    else:
        await d.launch_app(app_id)
        return f"Launched {name}."


@mcp.tool()
async def tv_close(app: str) -> str:
    """Close a running app."""
    d = await _get_driver()
    app_id, name = resolve_app(app, d.platform)
    await d.close_app(app_id)
    return f"Closed {name}."


@mcp.tool()
async def tv_apps() -> list[dict[str, str]]:
    """List all installed apps."""
    d = await _get_driver()
    apps = await d.list_apps()
    return [{"id": a.id, "name": a.name} for a in apps]


# -- Media Playback ----------------------------------------------------------


@mcp.tool()
async def tv_play() -> str:
    """Resume media playback."""
    d = await _get_driver()
    await d.play()
    return "Playing."


@mcp.tool()
async def tv_pause() -> str:
    """Pause media playback."""
    d = await _get_driver()
    await d.pause()
    return "Paused."


@mcp.tool()
async def tv_stop() -> str:
    """Stop media playback."""
    d = await _get_driver()
    await d.stop()
    return "Stopped."


# -- Status & Info -----------------------------------------------------------


@mcp.tool()
async def tv_status() -> dict:
    """Get TV status (current app, volume, mute)."""
    d = await _get_driver()
    s = await d.status()
    return {
        "platform": d.platform,
        "current_app": s.current_app,
        "volume": s.volume,
        "muted": s.muted,
        "sound_output": s.sound_output,
    }


@mcp.tool()
async def tv_info() -> dict:
    """Get TV system info (model, firmware, platform)."""
    d = await _get_driver()
    i = await d.info()
    return {
        "platform": i.platform,
        "model": i.model,
        "firmware": i.firmware,
        "ip": i.ip,
        "name": i.name,
    }


# -- Notifications -----------------------------------------------------------


@mcp.tool()
async def tv_notify(message: str) -> str:
    """Show a toast notification on the TV screen."""
    d = await _get_driver()
    await d.notify(message)
    return f"Notification sent: {message}"


# -- Screen ------------------------------------------------------------------


@mcp.tool()
async def tv_screen_off() -> str:
    """Turn off screen (audio continues)."""
    d = await _get_driver()
    await d.screen_off()
    return "Screen off."


@mcp.tool()
async def tv_screen_on() -> str:
    """Turn screen back on."""
    d = await _get_driver()
    await d.screen_on()
    return "Screen on."
