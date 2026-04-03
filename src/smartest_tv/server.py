"""smartest-tv MCP Server — unified TV control across platforms.

Optimized for AI agents: fewer tools, each does more.
"""

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
        "Control smart TVs (LG, Samsung, Android TV, Roku) with natural language. "
        "Play Netflix/YouTube/Spotify by name, cast URLs, queue content, get recommendations, "
        "run scene presets, sync across multiple TVs.\n\n"
        "Key tools:\n"
        "- tv_play: search + play content by name (most common)\n"
        "- tv_cast: play a URL directly\n"
        "- tv_next: continue watching\n"
        "- tv_whats_on: trending content\n"
        "- tv_recommend: personalized suggestions\n"
        "- tv_scene: run presets (movie-night, kids, sleep)\n"
        "- tv_queue: manage play queue\n"
        "- tv_sync: play on multiple TVs at once"
    ),
)


# -- Play Content (most important tool) -------------------------------------


@mcp.tool()
async def tv_play(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
    tv_name: str | None = None,
) -> str:
    """Find content by name and play it on TV.

    This is the primary tool. Resolves the content ID automatically,
    then deep-links into the app on your TV.

    Args:
        platform: "netflix", "youtube", or "spotify".
        query: Content name (e.g. "Stranger Things", "baby shark", "Ye White Lines").
        season: Season number (Netflix series only).
        episode: Episode number (Netflix series only).
        title_id: Netflix title ID if already known (skips search).
        tv_name: Target TV name. Omit for default TV.

    Examples:
        tv_play("netflix", "Stranger Things", season=4, episode=7)
        tv_play("youtube", "baby shark")
        tv_play("spotify", "Ye White Lines")
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

    from smartest_tv import cache as _cache
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season is not None and episode is not None:
        desc += f" S{season}E{episode}"
    return f"Playing {desc} on {name} (content: {content_id})"


# -- Cast URL ----------------------------------------------------------------


@mcp.tool()
async def tv_cast(url: str, tv_name: str | None = None) -> str:
    """Cast a Netflix/YouTube/Spotify URL to the TV.

    Paste any streaming URL. stv parses the platform and content ID automatically.

    Args:
        url: Any Netflix, YouTube, or Spotify URL.
        tv_name: Target TV name. Omit for default TV.

    Examples:
        tv_cast("https://youtube.com/watch?v=dQw4w9WgXcQ")
        tv_cast("https://netflix.com/watch/82656797")
        tv_cast("https://open.spotify.com/track/3bbjDFVu...")
    """
    from smartest_tv.cli import _parse_cast_url
    from smartest_tv.resolve import resolve

    try:
        platform, content_id = _parse_cast_url(url)
    except ValueError as exc:
        return f"Error: {exc}"

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

    return f"Casting on {name} (content: {content_id})"


# -- Continue Watching -------------------------------------------------------


@mcp.tool()
async def tv_next(query: str | None = None, tv_name: str | None = None) -> str:
    """Play the next episode. Continues from watch history.

    Args:
        query: Show name. Omit to continue the most recent Netflix show.
        tv_name: Target TV name. Omit for default TV.
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
        return f"No next episode for '{query}'."

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
    return f"Playing {q} S{season}E{episode}"


# -- Discovery: Trending + Recommend ----------------------------------------


@mcp.tool()
async def tv_whats_on(platform: str | None = None, limit: int = 10) -> str:
    """Show trending content on Netflix and/or YouTube.

    Args:
        platform: "netflix", "youtube", or omit for both.
        limit: Number of results per platform (default 10).
    """
    from smartest_tv.resolve import fetch_netflix_trending, fetch_youtube_trending

    parts: list[str] = []

    if platform in (None, "netflix"):
        items = fetch_netflix_trending(limit)
        lines = ["Netflix Top 10:"]
        for item in items:
            r = item.get("rank", "")
            t = item.get("title", "")
            c = item.get("category", "")
            lines.append(f"  {r:>2}. {t}" + (f"  — {c}" if c else ""))
        if not items:
            lines.append("  (unavailable)")
        parts.append("\n".join(lines))

    if platform in (None, "youtube"):
        items = fetch_youtube_trending(limit)
        lines = ["YouTube Trending:"]
        for item in items:
            r = item.get("rank", "")
            t = item.get("title", "")
            ch = item.get("channel", "")
            lines.append(f"  {r:>2}. [{ch}] {t}" if ch else f"  {r:>2}. {t}")
        if not items:
            lines.append("  (unavailable)")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


@mcp.tool()
async def tv_recommend(mood: str | None = None, limit: int = 5) -> str:
    """Get personalized recommendations based on watch history + trending.

    Args:
        mood: "chill", "action", "kids", "random", or omit for auto.
        limit: Number of recommendations (default 5).
    """
    from smartest_tv.resolve import get_recommendations
    from smartest_tv import cache as _cache

    recent = _cache.analyze_history()["recent_shows"]
    results = get_recommendations(mood=mood, limit=limit)

    if not results:
        return "No recommendations. Try tv_whats_on for trending."

    lines = []
    if recent:
        lines.append(f"Based on: {', '.join(recent[:3])}\n")
    for i, rec in enumerate(results, 1):
        lines.append(f"  {i}. {rec['title']:<30s} {rec['platform']:<8s} — {rec['reason']}")
    return "\n".join(lines)


# -- Power -------------------------------------------------------------------


@mcp.tool()
async def tv_power(on: bool, tv_name: str | None = None) -> str:
    """Turn TV on or off.

    Args:
        on: True = turn on, False = turn off.
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)
    if on:
        await d.power_on()
        return "TV turning on."
    else:
        await d.power_off()
        return "TV turned off."


# -- Volume ------------------------------------------------------------------


@mcp.tool()
async def tv_volume(
    level: int | None = None,
    direction: str | None = None,
    mute: bool | None = None,
    tv_name: str | None = None,
) -> str:
    """Get or set volume, step up/down, or toggle mute. All in one tool.

    - No args: returns current volume + mute status
    - level=25: set volume to 25
    - direction="up"/"down": step volume
    - mute=True/False/None: mute, unmute, or toggle

    Args:
        level: Volume level 0-100.
        direction: "up" or "down" for one step.
        mute: True=mute, False=unmute, None=toggle.
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)

    if level is not None:
        await d.set_volume(level)
        return f"Volume set to {level}."

    if direction == "up":
        await d.volume_up()
        return "Volume up."
    if direction == "down":
        await d.volume_down()
        return "Volume down."

    if mute is not None:
        if mute is True:
            await d.set_mute(True)
            return "Muted."
        elif mute is False:
            await d.set_mute(False)
            return "Unmuted."
    elif mute is None and level is None and direction is None:
        # No args = get current status
        vol = await d.get_volume()
        muted = await d.get_muted()
        return f"Volume: {vol}, Muted: {muted}"

    # Toggle mute as default action
    current = await d.get_muted()
    await d.set_mute(not current)
    return f"{'Muted' if not current else 'Unmuted'}."


# -- Status ------------------------------------------------------------------


@mcp.tool()
async def tv_status(tv_name: str | None = None) -> dict:
    """Get TV status: current app, volume, mute, model, firmware.

    Args:
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)
    s = await d.status()
    i = await d.info()
    return {
        "platform": d.platform,
        "model": i.model,
        "current_app": s.current_app,
        "volume": s.volume,
        "muted": s.muted,
    }


# -- Screen ------------------------------------------------------------------


@mcp.tool()
async def tv_screen(on: bool, tv_name: str | None = None) -> str:
    """Turn screen on or off (audio continues when off).

    Args:
        on: True = screen on, False = screen off (audio continues).
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)
    if on:
        await d.screen_on()
        return "Screen on."
    else:
        await d.screen_off()
        return "Screen off."


# -- Apps & Launching -------------------------------------------------------


@mcp.tool()
async def tv_launch(app: str, content_id: str | None = None, tv_name: str | None = None) -> str:
    """Launch an app, optionally with a deep link.

    Use tv_play instead if you have a content name (not ID).
    Use this when you already have the exact content ID.

    Args:
        app: App name (netflix, youtube, spotify) or raw app ID.
        content_id: Platform-specific content ID for deep linking.
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)
    app_id, name = resolve_app(app, d.platform)

    if content_id:
        await d.launch_app_deep(app_id, content_id)
        return f"Launched {name} with: {content_id}"
    else:
        await d.launch_app(app_id)
        return f"Launched {name}."


@mcp.tool()
async def tv_notify(message: str, tv_name: str | None = None) -> str:
    """Show a toast notification on the TV screen.

    Args:
        message: Text to display.
        tv_name: Target TV name. Omit for default TV.
    """
    d = await _get_driver(tv_name)
    await d.notify(message)
    return f"Sent: {message}"


# -- Queue -------------------------------------------------------------------


@mcp.tool()
async def tv_queue(
    action: str,
    platform: str | None = None,
    query: str | None = None,
    season: int | None = None,
    episode: int | None = None,
    tv_name: str | None = None,
) -> str:
    """Manage the play queue. Actions: add, show, play, skip, clear.

    Args:
        action: "add", "show", "play", "skip", or "clear".
        platform: Required for "add". netflix/youtube/spotify.
        query: Required for "add". Content name.
        season: For "add" — Netflix season number.
        episode: For "add" — Netflix episode number.
        tv_name: For "play" — target TV.

    Examples:
        tv_queue("add", "youtube", "Gangnam Style")
        tv_queue("add", "netflix", "Dark", season=1, episode=1)
        tv_queue("show")
        tv_queue("play")
        tv_queue("clear")
    """
    from smartest_tv import cache as _cache

    if action == "add":
        if not platform or not query:
            return "Error: 'add' requires platform and query."
        item = _cache.queue_add(platform, query, season, episode)
        desc = item["query"]
        if item.get("season") is not None:
            desc += f" S{item['season']}E{item.get('episode', '?')}"
        return f"Added: [{platform}] {desc}"

    if action == "show":
        items = _cache.queue_show()
        if not items:
            return "Queue is empty."
        lines = []
        for i, item in enumerate(items, 1):
            desc = f"[{item['platform']}] {item['query']}"
            if item.get("season") is not None:
                desc += f" S{item['season']}E{item.get('episode', '?')}"
            lines.append(f"  {i}. {desc}")
        return "Queue:\n" + "\n".join(lines)

    if action == "play":
        from smartest_tv.resolve import resolve
        item = _cache.queue_pop()
        if not item:
            return "Queue is empty."
        p, q = item["platform"], item["query"]
        s, e = item.get("season"), item.get("episode")
        content_id = resolve(p, q, s, e)
        d = await _get_driver(tv_name)
        app_id, name = resolve_app(p, d.platform)
        if p.lower() == "netflix":
            try:
                await d.close_app(app_id)
                await asyncio.sleep(2)
            except Exception:
                pass
        await d.launch_app_deep(app_id, content_id)
        _cache.record_play(p, q, content_id, s, e)
        return f"Playing {q} on {name}"

    if action == "skip":
        _cache.queue_skip()
        return "Skipped."

    if action == "clear":
        _cache.queue_clear()
        return "Queue cleared."

    return f"Unknown action: {action}. Use add/show/play/skip/clear."


# -- History -----------------------------------------------------------------


@mcp.tool()
async def tv_history(limit: int = 10) -> list[dict]:
    """Show recent play history."""
    from smartest_tv import cache as _cache
    return _cache.get_history(limit)


# -- Resolve (advanced) -----------------------------------------------------


@mcp.tool()
async def tv_resolve(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve a content name to its platform ID without playing.

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name.
        season: Season number (Netflix).
        episode: Episode number (Netflix).
        title_id: Netflix title ID if known.

    Returns:
        Content ID string.
    """
    from smartest_tv.resolve import resolve
    return resolve(platform, query, season, episode, title_id)


# -- Scene Presets -----------------------------------------------------------


@mcp.tool()
async def tv_scene(action: str = "list", name: str | None = None, tv_name: str | None = None) -> str:
    """Run or list scene presets. Built-in: movie-night, kids, sleep, music.

    Args:
        action: "list" or "run".
        name: Scene name (required for "run").
        tv_name: Target TV (for "run").

    Examples:
        tv_scene("list")
        tv_scene("run", "movie-night")
        tv_scene("run", "kids", tv_name="kids-room")
    """
    from smartest_tv.scenes import list_scenes, run_scene

    if action == "list":
        scenes = list_scenes()
        lines = []
        for sname, s in scenes.items():
            desc = s.get("description", "")
            lines.append(f"  {sname}: {desc}")
        return "Scenes:\n" + "\n".join(lines)

    if action == "run":
        if not name:
            return "Error: specify scene name. Use tv_scene('list') to see options."
        try:
            results = await run_scene(name, tv_name)
        except KeyError as exc:
            return f"Error: {exc}"
        return "\n".join(results) + f"\nScene '{name}' done."

    return f"Unknown action: {action}. Use 'list' or 'run'."


# -- Multi-TV & Sync --------------------------------------------------------


@mcp.tool()
async def tv_list_tvs() -> list[dict]:
    """List all configured TVs with name, platform, IP, and default status."""
    from smartest_tv.config import list_tvs
    return list_tvs()


@mcp.tool()
async def tv_sync(
    platform: str,
    query: str,
    tv_names: list[str] | None = None,
    group: str | None = None,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Play content on multiple TVs simultaneously (party mode).

    Resolves once, launches on all targets via asyncio.gather.

    Args:
        platform: netflix, youtube, or spotify.
        query: Content name.
        tv_names: List of TV names. Or use group.
        group: TV group name (e.g. "party").
        season: Netflix season number.
        episode: Netflix episode number.
        title_id: Netflix title ID if known.
    """
    from smartest_tv.config import get_all_tv_names, get_group_members
    from smartest_tv.resolve import resolve

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

    try:
        content_id = resolve(platform, query, season, episode, title_id)
    except ValueError as e:
        return f"Error: {e}"

    async def _play_one(name: str) -> dict:
        try:
            d = await _get_driver(name)
            app_id, app_name = resolve_app(platform, d.platform)
            if platform.lower() == "netflix":
                try:
                    await d.close_app(app_id)
                    await asyncio.sleep(2)
                except Exception:
                    pass
            await d.launch_app_deep(app_id, content_id)
            return {"tv": name, "status": "ok", "message": f"Playing on {app_name}"}
        except Exception as e:
            return {"tv": name, "status": "error", "message": str(e)}

    results = await asyncio.gather(*[_play_one(n) for n in targets])

    from smartest_tv import cache as _cache
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season is not None and episode is not None:
        desc += f" S{season}E{episode}"

    lines = [f"Sync: {desc}"]
    for r in results:
        icon = "ok" if r["status"] == "ok" else "FAIL"
        lines.append(f"  [{icon}] {r['tv']}: {r['message']}")
    return "\n".join(lines)


@mcp.tool()
async def tv_groups() -> list[dict]:
    """List all TV groups and their members."""
    from smartest_tv.config import get_groups
    return [{"name": n, "members": m} for n, m in get_groups().items()]
