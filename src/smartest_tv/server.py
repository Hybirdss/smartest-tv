"""smartest-tv MCP Server — unified TV control across platforms."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from smartest_tv.apps import resolve_app
from smartest_tv.config import get_tv_config
from smartest_tv.drivers.base import TVDriver

# ---------------------------------------------------------------------------
# Driver management
# ---------------------------------------------------------------------------
_driver: TVDriver | None = None
_driver_lock = asyncio.Lock()


def _create_driver() -> TVDriver:
    """Create a driver from config file (with env var overrides)."""
    tv = get_tv_config()
    platform = tv.get("platform", "")
    ip = tv.get("ip", "")
    mac = tv.get("mac", "")

    if platform == "lg":
        from smartest_tv.drivers.lg import LGDriver
        return LGDriver(ip=ip, mac=mac)
    elif platform == "samsung":
        from smartest_tv.drivers.samsung import SamsungDriver
        return SamsungDriver(ip=ip, mac=mac)
    elif platform in ("android", "firetv"):
        from smartest_tv.drivers.android import AndroidDriver
        return AndroidDriver(ip=ip)
    elif platform == "roku":
        from smartest_tv.drivers.roku import RokuDriver
        return RokuDriver(ip=ip)
    else:
        raise ValueError(f"No TV configured. Run: stv setup")


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


# -- Resolve & Play ----------------------------------------------------------


@mcp.tool()
async def tv_resolve(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve a content name to a platform-specific ID.

    Finds the streaming ID without launching anything.
    Uses local cache (instant) with HTTP scraping fallback.

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name (e.g. "Frieren", "baby shark").
        season: Season number (Netflix TV shows only).
        episode: Episode number (Netflix TV shows only).
        title_id: Netflix title ID if known (e.g. 81726714). Skips search.

    Returns:
        Content ID string (e.g. "82656797" for Netflix, "dQw4w9WgXcQ" for YouTube).
    """
    from smartest_tv.resolve import resolve
    return resolve(platform, query, season, episode, title_id)


@mcp.tool()
async def tv_play_content(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Find content by name and play it on TV in one step.

    Resolves the content ID, then launches it. For Netflix, automatically
    closes the app first (required for deep links to work).

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name (e.g. "Frieren", "baby shark").
        season: Season number (Netflix TV shows only).
        episode: Episode number (Netflix TV shows only).
        title_id: Netflix title ID if known (e.g. 81726714). Skips search.
    """
    from smartest_tv.resolve import resolve

    content_id = resolve(platform, query, season, episode, title_id)

    d = await _get_driver()
    app_id, name = resolve_app(platform, d.platform)

    if platform.lower() == "netflix":
        try:
            await d.close_app(app_id)
            await asyncio.sleep(2)
        except Exception:
            pass

    await d.launch_app_deep(app_id, content_id)

    # Record to history
    from smartest_tv import cache as _cache
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season and episode:
        desc += f" S{season}E{episode}"
    return f"Playing {desc} on {name} (content: {content_id})"


@mcp.tool()
async def tv_history(limit: int = 10) -> list[dict]:
    """Show recent play history.

    Returns the last N items played on the TV.
    """
    from smartest_tv import cache as _cache
    return _cache.get_history(limit)


@mcp.tool()
async def tv_next(query: str | None = None) -> str:
    """Play the next episode of a Netflix show.

    Continues from where the user left off. If no query given,
    continues the most recently watched Netflix show.

    Args:
        query: Show name (optional). If omitted, uses most recent.
    """
    from smartest_tv import cache as _cache
    from smartest_tv.resolve import resolve

    if not query:
        last = _cache.get_last_played(platform="netflix")
        if not last:
            return "No Netflix history. Play something first."
        query = last["query"]

    result = _cache.get_next_episode(query)
    if not result:
        return f"No next episode for '{query}'. Finished or not in history."

    q, season, episode = result
    content_id = resolve("netflix", q, season, episode)

    d = await _get_driver()
    app_id, name = resolve_app("netflix", d.platform)

    try:
        await d.close_app(app_id)
        await asyncio.sleep(2)
    except Exception:
        pass

    await d.launch_app_deep(app_id, content_id)
    _cache.record_play("netflix", q, content_id, season, episode)
    return f"Playing {q} S{season}E{episode} on Netflix (content: {content_id})"
