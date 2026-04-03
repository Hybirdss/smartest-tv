"""smartest-tv MCP Server — unified TV control across platforms."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from smartest_tv.apps import resolve_app
from smartest_tv.drivers.base import TVDriver

# ---------------------------------------------------------------------------
# Driver management
# ---------------------------------------------------------------------------
_driver_cache: dict[str | None, TVDriver] = {}
_driver_lock = asyncio.Lock()


def _create_driver(tv_name: str | None = None) -> TVDriver:
    """Create a driver from config file (with env var overrides)."""
    from smartest_tv.drivers.factory import create_driver
    return create_driver(tv_name)


async def _get_driver(tv_name: str | None = None) -> TVDriver:
    async with _driver_lock:
        if tv_name not in _driver_cache:
            _driver_cache[tv_name] = _create_driver(tv_name)
            await _driver_cache[tv_name].connect()
        return _driver_cache[tv_name]


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
async def tv_on(tv_name: str | None = None) -> str:
    """Turn on the TV (Wake-on-LAN or platform equivalent).

    Args:
        tv_name: Target TV name (default: primary TV). Use stv multi list to see names.
    """
    d = await _get_driver(tv_name)
    await d.power_on()
    return "TV turning on."


@mcp.tool()
async def tv_off(tv_name: str | None = None) -> str:
    """Turn off the TV (standby).

    Args:
        tv_name: Target TV name (default: primary TV). Use stv multi list to see names.
    """
    d = await _get_driver(tv_name)
    await d.power_off()
    return "TV turned off."


# -- Volume ------------------------------------------------------------------


@mcp.tool()
async def tv_volume(tv_name: str | None = None) -> dict:
    """Get current volume and mute status.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    return {"volume": await d.get_volume(), "muted": await d.get_muted()}


@mcp.tool()
async def tv_set_volume(level: int, tv_name: str | None = None) -> str:
    """Set volume (0-100).

    Args:
        level: Volume level 0-100.
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.set_volume(level)
    return f"Volume set to {level}."


@mcp.tool()
async def tv_volume_up(tv_name: str | None = None) -> str:
    """Increase volume by one step.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.volume_up()
    return "Volume increased."


@mcp.tool()
async def tv_volume_down(tv_name: str | None = None) -> str:
    """Decrease volume by one step.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.volume_down()
    return "Volume decreased."


@mcp.tool()
async def tv_mute(mute: bool | None = None, tv_name: str | None = None) -> str:
    """Mute, unmute, or toggle.

    Args:
        mute: True to mute, False to unmute, None to toggle.
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    if mute is None:
        mute = not await d.get_muted()
    await d.set_mute(mute)
    return f"TV {'muted' if mute else 'unmuted'}."


# -- Apps & Deep Linking -----------------------------------------------------


@mcp.tool()
async def tv_launch(app: str, content_id: str | None = None, tv_name: str | None = None) -> str:
    """Launch an app, optionally deep linking to specific content.

    Args:
        app: App name (netflix, youtube, spotify, disney, prime, etc.) or raw app ID.
        content_id: Content identifier for deep linking.
            - Netflix: episode/movie ID (e.g. "82656797")
            - YouTube: video ID (e.g. "dQw4w9WgXcQ") or full URL
            - Spotify: URI (e.g. "spotify:album:5poA9SAx0Xiz1cd17fWBLS")
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    app_id, name = resolve_app(app, d.platform)

    if content_id:
        await d.launch_app_deep(app_id, content_id)
        return f"Launched {name} with content: {content_id}"
    else:
        await d.launch_app(app_id)
        return f"Launched {name}."


@mcp.tool()
async def tv_close(app: str, tv_name: str | None = None) -> str:
    """Close a running app.

    Args:
        app: App name or ID.
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    app_id, name = resolve_app(app, d.platform)
    await d.close_app(app_id)
    return f"Closed {name}."


@mcp.tool()
async def tv_apps(tv_name: str | None = None) -> list[dict[str, str]]:
    """List all installed apps.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    apps = await d.list_apps()
    return [{"id": a.id, "name": a.name} for a in apps]


# -- Media Playback ----------------------------------------------------------


@mcp.tool()
async def tv_play(tv_name: str | None = None) -> str:
    """Resume media playback.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.play()
    return "Playing."


@mcp.tool()
async def tv_pause(tv_name: str | None = None) -> str:
    """Pause media playback.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.pause()
    return "Paused."


@mcp.tool()
async def tv_stop(tv_name: str | None = None) -> str:
    """Stop media playback.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.stop()
    return "Stopped."


# -- Status & Info -----------------------------------------------------------


@mcp.tool()
async def tv_status(tv_name: str | None = None) -> dict:
    """Get TV status (current app, volume, mute).

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    s = await d.status()
    return {
        "platform": d.platform,
        "current_app": s.current_app,
        "volume": s.volume,
        "muted": s.muted,
        "sound_output": s.sound_output,
    }


@mcp.tool()
async def tv_info(tv_name: str | None = None) -> dict:
    """Get TV system info (model, firmware, platform).

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
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
async def tv_notify(message: str, tv_name: str | None = None) -> str:
    """Show a toast notification on the TV screen.

    Args:
        message: Notification text.
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.notify(message)
    return f"Notification sent: {message}"


# -- Screen ------------------------------------------------------------------


@mcp.tool()
async def tv_screen_off(tv_name: str | None = None) -> str:
    """Turn off screen (audio continues).

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.screen_off()
    return "Screen off."


@mcp.tool()
async def tv_screen_on(tv_name: str | None = None) -> str:
    """Turn screen back on.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    d = await _get_driver(tv_name)
    await d.screen_on()
    return "Screen on."


# -- Resolve & Play ----------------------------------------------------------


@mcp.tool()
async def tv_cast(url: str, tv_name: str | None = None) -> str:
    """Cast a URL to the TV. Accepts Netflix, YouTube, Spotify links.

    Parses the URL to extract the platform and content ID, then launches
    the appropriate app with deep linking. For Netflix, closes the app first
    (required for deep links to work).

    Args:
        url: Streaming URL. Supported formats:
            - https://www.netflix.com/watch/82656797
            - https://www.netflix.com/title/81726714
            - https://www.youtube.com/watch?v=dQw4w9WgXcQ
            - https://youtu.be/dQw4w9WgXcQ
            - https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
            - https://open.spotify.com/album/xxx
            - https://open.spotify.com/playlist/xxx
        tv_name: Target TV name (default: primary TV).
    """
    from smartest_tv.cli import _parse_cast_url
    from smartest_tv.resolve import resolve

    try:
        platform, content_id = _parse_cast_url(url)
    except ValueError as exc:
        return f"Error: {exc}"

    # Netflix title URL → resolve to actual video ID
    if platform == "netflix" and content_id.startswith("title:"):
        title_id = int(content_id.split(":", 1)[1])
        try:
            content_id = resolve("netflix", str(title_id), title_id=title_id)
        except ValueError as exc:
            return f"Error: {exc}"

    d = await _get_driver(tv_name)
    app_id, name = resolve_app(platform, d.platform)

    if platform == "netflix":
        try:
            await d.close_app(app_id)
            await asyncio.sleep(2)
        except Exception:
            pass

    await d.launch_app_deep(app_id, content_id)

    from smartest_tv import cache as _cache
    _cache.record_play(platform, url, content_id, None, None)

    return f"Casting {url} on {name} (content: {content_id})"


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
    tv_name: str | None = None,
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
        tv_name: Target TV name (default: primary TV).
    """
    from smartest_tv.resolve import resolve

    content_id = resolve(platform, query, season, episode, title_id)

    d = await _get_driver(tv_name)
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
async def tv_whats_on(platform: str | None = None, limit: int = 10) -> str:
    """Show trending content on Netflix or YouTube.

    Args:
        platform: "netflix", "youtube", or None for both.
        limit: Number of results per platform (default 10).

    Returns:
        Formatted list of trending titles.
    """
    from smartest_tv.resolve import fetch_netflix_trending, fetch_youtube_trending

    def _fmt_views(n) -> str:
        if n is None:
            return ""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M views"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K views"
        return f"{n} views"

    parts: list[str] = []
    show_netflix = platform in (None, "netflix")
    show_youtube = platform in (None, "youtube")

    if show_netflix:
        items = fetch_netflix_trending(limit)
        lines = ["Netflix Top 10:"]
        if items:
            for item in items:
                rank = item.get("rank", "")
                title = item.get("title", "")
                cat = item.get("category", "")
                cat_str = f"  — {cat}" if cat else ""
                lines.append(f"  {rank:>2}. {title}{cat_str}")
        else:
            lines.append("  (Could not fetch trending data)")
        parts.append("\n".join(lines))

    if show_youtube:
        items = fetch_youtube_trending(limit)
        lines = ["YouTube Trending:"]
        if items:
            for item in items:
                rank = item.get("rank", "")
                title = item.get("title", "")
                channel = item.get("channel", "")
                views = _fmt_views(item.get("view_count"))
                channel_str = f"[{channel}] " if channel else ""
                views_str = f"  — {views}" if views else ""
                lines.append(f"  {rank:>2}. {channel_str}{title}{views_str}")
        else:
            lines.append("  (Could not fetch trending data)")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


@mcp.tool()
async def tv_queue_add(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
) -> str:
    """Add content to the play queue.

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name (e.g. "Bridgerton", "Despacito").
        season: Season number (Netflix TV shows only).
        episode: Episode number (Netflix TV shows only).
    """
    from smartest_tv import cache as _cache
    item = _cache.queue_add(platform, query, season, episode)
    desc = item["query"]
    if item.get("season") and item.get("episode"):
        desc += f" S{item['season']}E{item['episode']}"
    return f"Added to queue: [{platform}] {desc}"


@mcp.tool()
async def tv_queue_show() -> list[dict]:
    """Show the current play queue."""
    from smartest_tv import cache as _cache
    return _cache.queue_show()


@mcp.tool()
async def tv_queue_play(tv_name: str | None = None) -> str:
    """Play the next item in the queue.

    Pops the first item, resolves its content ID, and plays it on TV.

    Args:
        tv_name: Target TV name (default: primary TV).
    """
    from smartest_tv import cache as _cache
    from smartest_tv.resolve import resolve

    item = _cache.queue_pop()
    if not item:
        return "Queue is empty."

    platform = item["platform"]
    query = item["query"]
    season = item.get("season")
    episode = item.get("episode")

    content_id = resolve(platform, query, season, episode)

    d = await _get_driver(tv_name)
    app_id, name = resolve_app(platform, d.platform)

    if platform.lower() == "netflix":
        try:
            await d.close_app(app_id)
            await asyncio.sleep(2)
        except Exception:
            pass

    await d.launch_app_deep(app_id, content_id)
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season and episode:
        desc += f" S{season}E{episode}"
    return f"Playing {desc} on {name} (content: {content_id})"


@mcp.tool()
async def tv_queue_clear() -> str:
    """Clear the entire play queue."""
    from smartest_tv import cache as _cache
    _cache.queue_clear()
    return "Queue cleared."


@mcp.tool()
async def tv_next(query: str | None = None, tv_name: str | None = None) -> str:
    """Play the next episode of a Netflix show.

    Continues from where the user left off. If no query given,
    continues the most recently watched Netflix show.

    Args:
        query: Show name (optional). If omitted, uses most recent.
        tv_name: Target TV name (default: primary TV).
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

    d = await _get_driver(tv_name)
    app_id, name = resolve_app("netflix", d.platform)

    try:
        await d.close_app(app_id)
        await asyncio.sleep(2)
    except Exception:
        pass

    await d.launch_app_deep(app_id, content_id)
    _cache.record_play("netflix", q, content_id, season, episode)
    return f"Playing {q} S{season}E{episode} on Netflix (content: {content_id})"


# -- Multi TV Management -----------------------------------------------------


@mcp.tool()
async def tv_recommend(mood: str | None = None, limit: int = 5) -> str:
    """Get personalized content recommendations based on watch history.

    Combines watch history patterns with trending content.
    Set STV_LLM_URL env var to enable AI-powered reasons.

    Args:
        mood: Optional filter — "chill", "action", "kids", or "random".
        limit: Number of recommendations (default 5).

    Returns:
        Formatted list of recommendations with title, platform, and reason.
    """
    from smartest_tv.resolve import get_recommendations
    from smartest_tv import cache as _cache

    history_data = _cache.analyze_history()
    recent = history_data["recent_shows"]
    results = get_recommendations(mood=mood, limit=limit)

    if not results:
        return "No recommendations available. Try tv_whats_on for trending content."

    lines: list[str] = []
    if recent:
        lines.append(f"Based on your recent watching ({', '.join(recent[:3])}):\n")
    else:
        lines.append("Trending now (no watch history yet):\n")

    for i, rec in enumerate(results, 1):
        title = rec["title"]
        platform = rec["platform"].capitalize()
        reason = rec["reason"]
        lines.append(f"  {i}. {title:<30s}  {platform:<8s}  — {reason}")

    return "\n".join(lines)


@mcp.tool()
async def tv_list_tvs() -> list[dict]:
    """List all configured TVs.

    Returns a list of all configured TVs with their name, platform, IP, and default status.
    Use tv_name parameter in other tools to target a specific TV.
    """
    from smartest_tv.config import list_tvs
    return list_tvs()


# -- Scene Presets -----------------------------------------------------------


@mcp.tool()
async def tv_scene_list() -> list[dict]:
    """List all available scene presets (built-in and custom).

    Returns a list of scenes with name, description, and steps.
    Built-in scenes: movie-night, kids, sleep, music.
    """
    from smartest_tv.scenes import list_scenes
    scenes = list_scenes()
    return [
        {"name": name, "description": s.get("description", ""), "steps": s.get("steps", [])}
        for name, s in scenes.items()
    ]


@mcp.tool()
async def tv_scene_run(name: str, tv_name: str | None = None) -> str:
    """Run a scene preset — executes all steps in order.

    Built-in scenes: movie-night, kids, sleep, music.
    Custom scenes are defined in ~/.config/smartest-tv/scenes.json.

    Args:
        name: Scene name (e.g. "movie-night", "sleep").
        tv_name: Target TV name (default: primary TV).
    """
    from smartest_tv.scenes import run_scene
    try:
        results = await run_scene(name, tv_name)
    except KeyError as exc:
        return f"Error: {exc}"
    return "\n".join(results) + f"\nScene '{name}' done."


# -- Sync / Party Mode -------------------------------------------------------


@mcp.tool()
async def tv_sync_play(
    platform: str,
    query: str,
    tv_names: list[str] | None = None,
    group: str | None = None,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Play content on multiple TVs simultaneously (party mode).

    Resolves the content ID once, then launches on all target TVs at the same time.
    Works with both local TVs and remote friends' TVs.

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name (e.g. "Squid Game", "lo-fi beats").
        tv_names: List of TV names to play on. If omitted, uses group.
        group: TV group name (e.g. "party", "home"). If omitted, uses tv_names.
        season: Season number (Netflix TV shows only).
        episode: Episode number (Netflix TV shows only).
        title_id: Netflix title ID if known.
    """
    from smartest_tv.config import get_all_tv_names, get_group_members
    from smartest_tv.resolve import resolve
    from smartest_tv.sync import broadcast

    # Determine targets
    if tv_names:
        targets = tv_names
    elif group:
        try:
            targets = get_group_members(group)
        except KeyError as e:
            return f"Error: {e}"
    else:
        targets = get_all_tv_names()

    if not targets:
        return "No TVs to play on."

    # Resolve content once
    try:
        content_id = resolve(platform, query, season, episode, title_id)
    except ValueError as e:
        return f"Error resolving content: {e}"

    # Connect all drivers
    drivers: dict[str, TVDriver] = {}
    for name in targets:
        try:
            d = await _get_driver(name)
            drivers[name] = d
        except Exception as e:
            pass  # Skip unreachable TVs

    if not drivers:
        return "Could not connect to any target TVs."

    # Play on all simultaneously
    async def _play(d: TVDriver) -> str:
        app_id, app_name = resolve_app(platform, d.platform)
        if platform.lower() == "netflix":
            try:
                await d.close_app(app_id)
                await asyncio.sleep(2)
            except Exception:
                pass
        await d.launch_app_deep(app_id, content_id)
        return f"Playing on {app_name}"

    results = await broadcast(drivers, _play)

    # Record to history
    from smartest_tv import cache as _cache
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season and episode:
        desc += f" S{season}E{episode}"

    lines = [f"Sync play: {desc} ({content_id})"]
    for r in results:
        icon = "✓" if r["status"] == "ok" else "✗"
        lines.append(f"  {icon} [{r['tv']}] {r['message']}")
    return "\n".join(lines)


@mcp.tool()
async def tv_group_list() -> list[dict]:
    """List all configured TV groups.

    Returns groups with their member TV names.
    """
    from smartest_tv.config import get_groups
    groups = get_groups()
    return [{"name": name, "members": members} for name, members in groups.items()]
