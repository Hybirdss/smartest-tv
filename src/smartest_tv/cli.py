"""smartest-tv CLI — talk to your TV.

Usage:
    stv setup                          # First time? Start here.
    stv status
    stv launch netflix 82656797
    stv volume 30
    stv off
"""

from __future__ import annotations

import asyncio
import json
import sys

import click

from smartest_tv.apps import resolve_app
from smartest_tv.cast import parse_cast_url
from smartest_tv.config import (
    get_tv_config, list_tvs, add_tv, remove_tv, set_default_tv,
    get_all_tv_names, get_group_members, get_groups, save_group, delete_group,
)
from smartest_tv.drivers.base import TVDriver
from smartest_tv.playback import launch_content
from smartest_tv.sync import broadcast, connect_all
from smartest_tv.ui import console as _ui_console
from smartest_tv.ui import render as _ui


def _get_driver(tv_name: str | None = None) -> TVDriver:
    """Create driver from config file (or env var overrides)."""
    from smartest_tv.drivers.factory import create_driver
    try:
        return create_driver(tv_name)
    except (ValueError, ImportError) as e:
        raise click.ClickException(str(e))


def _run(coro):
    """Run an async function."""
    return asyncio.run(coro)


def _output(data, fmt: str):
    """Print data in the requested format (JSON or fallback text)."""
    if fmt == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                click.echo(f"{k}: {v}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    click.echo("  ".join(f"{k}={v}" for k, v in item.items()))
                else:
                    click.echo(item)
        else:
            click.echo(data)


def _print(renderable):
    """Print a Rich renderable through the themed console."""
    _ui_console.print(renderable)


def _success(message: str):
    """Short success line with a green check."""
    from smartest_tv.ui.theme import ICONS
    _ui_console.print(f"[success]{ICONS['ok']}  {message}[/success]")


def _fail(message: str, hint: str = "", exit_code: int = 1):
    """Red-bordered error panel. Exits with non-zero by default."""
    _ui_console.print(_ui.render_error(message, hint))
    if exit_code is not None:
        sys.exit(exit_code)


def _info(message: str, icon: str = ""):
    """Dim info/status line."""
    prefix = f"{icon}  " if icon else ""
    _ui_console.print(f"[info]{prefix}{message}[/info]")


@click.group()
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              help="Output format")
@click.option("--tv", "tv_name", default=None, help="Target TV name (default: primary TV)")
@click.option("--all", "all_tvs", is_flag=True, help="Target all configured TVs")
@click.option("--group", "-g", "group_name", default=None, help="Target a TV group")
@click.pass_context
def main(ctx, fmt, tv_name, all_tvs, group_name):
    """stv — Talk to your TV. It listens."""
    ctx.ensure_object(dict)
    ctx.obj["fmt"] = fmt
    ctx.obj["tv_name"] = tv_name
    ctx.obj["all_tvs"] = all_tvs
    ctx.obj["group_name"] = group_name


def _get_targets(ctx) -> list[str]:
    """Resolve --all / --group / --tv into a list of TV names.

    Returns [None] for single default TV, otherwise named TV list.
    """
    if ctx.obj.get("all_tvs"):
        names = get_all_tv_names()
        if not names:
            raise click.ClickException("No TVs configured. Run: stv setup")
        return names
    if ctx.obj.get("group_name"):
        try:
            return get_group_members(ctx.obj["group_name"])
        except KeyError as e:
            raise click.ClickException(str(e))
    return [ctx.obj.get("tv_name")]


def _is_multi(ctx) -> bool:
    """True if targeting multiple TVs."""
    return bool(ctx.obj.get("all_tvs") or ctx.obj.get("group_name"))


async def _broadcast_action(targets: list[str], action_fn):
    """Run an async action on multiple TVs concurrently."""
    drivers, failures = await connect_all(targets, _get_driver)
    broadcast_results = await broadcast(drivers, action_fn)
    result_by_tv = {result["tv"]: result for result in failures + broadcast_results}
    return [result_by_tv[tv_name] for tv_name in targets if tv_name in result_by_tv]


def _print_results(results, fmt: str = "text"):
    """Print multi-TV broadcast results."""
    if fmt == "json":
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return
    _print(_ui.render_broadcast_results(results))


# -- Remote MCP Server -------------------------------------------------------


@main.command()
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--port", default=8910, type=int, help="Port")
@click.option(
    "--transport",
    default="sse",
    type=click.Choice(["sse", "streamable-http"]),
    help="Transport protocol",
)
def serve(host, port, transport):
    """Start stv as a remote MCP server (+ REST API for party mode)."""
    from smartest_tv.server import mcp
    from smartest_tv.api import start_api_server
    from smartest_tv.ui.common import kv_table, boxed
    from smartest_tv.ui.theme import ICONS
    from rich.console import Group
    from rich.text import Text

    api_port = port + 1
    start_api_server(host, api_port)

    path = "sse" if transport == "sse" else "mcp"
    content = Group(
        kv_table({
            "MCP server": f"http://{host}:{port}/{path}",
            "REST API":   f"http://{host}:{api_port}/api/ping",
        }),
        Text(""),
        Text("Friends can add your TV:", style="accent"),
        Text(f"  stv multi add friend --platform remote --url http://YOUR_IP:{api_port}", style="primary"),
        Text(""),
        Text("Press Ctrl+C to stop.", style="muted"),
    )
    _print(boxed(content, title=f"{ICONS['cast']} stv server"))
    mcp.run(transport=transport, host=host, port=port)


# -- Setup & Diagnostics ----------------------------------------------------


@main.command()
@click.option("--ip", default=None, help="TV IP address (skip auto-discovery)")
def setup(ip):
    """Set up your TV. Discovers, pairs, and configures everything."""
    from smartest_tv.setup import run_setup
    run_setup(ip=ip)


@main.command()
@click.pass_context
def doctor(ctx):
    """Check if everything is working."""
    tv_name = ctx.obj["tv_name"]
    try:
        tv = get_tv_config(tv_name)
    except KeyError as e:
        _fail(str(e))
        return
    if not tv.get("platform"):
        _fail("No TV configured.", hint="Run: stv setup")
        return

    tv_label = f"{tv.get('name', 'TV')} ({tv['platform'].upper()}, {tv['ip']})"
    checks: list[dict] = []

    d = _get_driver(tv_name)
    try:
        _run(d.connect())
        checks.append({"name": "TV reachable", "status": "ok", "detail": tv['ip']})
    except Exception as e:
        checks.append({"name": "TV reachable", "status": "fail", "detail": str(e)[:60]})
        _print(_ui.render_doctor(checks, tv_label=tv_label))
        return

    try:
        s = _run(d.status())
        detail = f"{s.current_app or 'idle'}, vol {s.volume}"
        checks.append({"name": "Status query", "status": "ok", "detail": detail})
    except Exception:
        checks.append({"name": "Status query", "status": "warn", "detail": "failed"})

    try:
        apps = _run(d.list_apps())
        app_names = {a.name.lower() for a in apps}
        for service in ["Netflix", "YouTube", "Spotify"]:
            found = any(service.lower() in n for n in app_names)
            checks.append({
                "name": service,
                "status": "ok" if found else "warn",
                "detail": "installed" if found else "not found",
            })
    except Exception:
        checks.append({"name": "App list", "status": "warn", "detail": "unavailable"})

    _print(_ui.render_doctor(checks, tv_label=tv_label))


# -- Power -------------------------------------------------------------------


@main.command()
@click.pass_context
def on(ctx):
    """Turn on the TV (or all TVs with --all / --group)."""
    from smartest_tv.ui.theme import ICONS
    if _is_multi(ctx):
        targets = _get_targets(ctx)
        results = _run(_broadcast_action(targets, lambda d: d.power_on() or "turning on"))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])
        _run(d.connect())
        _run(d.power_on())
        _success(f"{ICONS['on']} TV turning on.")


@main.command()
@click.pass_context
def off(ctx):
    """Turn off the TV (or all TVs with --all / --group)."""
    from smartest_tv.ui.theme import ICONS
    if _is_multi(ctx):
        targets = _get_targets(ctx)
        results = _run(_broadcast_action(targets, lambda d: d.power_off() or "turned off"))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            await d.power_off()

        _run(_do())
        _success(f"{ICONS['off']} TV turned off.")


# -- Volume ------------------------------------------------------------------


@main.command()
@click.argument("level", required=False, type=int)
@click.pass_context
def volume(ctx, level):
    """Get or set volume. No argument = show current. Supports --all / --group."""
    if _is_multi(ctx) and level is not None:
        targets = _get_targets(ctx)

        async def _set_vol(d):
            await d.set_volume(level)
            return f"volume → {level}"

        results = _run(_broadcast_action(targets, _set_vol))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            if level is not None:
                await d.set_volume(level)
                return {"volume": level, "action": "set"}
            else:
                return {"volume": await d.get_volume(), "muted": await d.get_muted()}

        result = _run(_do())
        if ctx.obj["fmt"] == "json":
            _output(result, "json")
        elif level is not None:
            _success(f"Volume set to {level}.")
        else:
            _print(_ui.render_volume(int(result.get("volume", 0)), muted=bool(result.get("muted", False))))


@main.command()
@click.pass_context
def mute(ctx):
    """Toggle mute. Supports --all / --group."""
    from smartest_tv.ui.theme import ICONS
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _toggle_mute(d):
            current = await d.get_muted()
            await d.set_mute(not current)
            return "muted" if not current else "unmuted"

        results = _run(_broadcast_action(targets, _toggle_mute))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            current = await d.get_muted()
            await d.set_mute(not current)
            return not current

        muted = _run(_do())
        icon = ICONS['mute'] if muted else ICONS['volume']
        _success(f"{icon} TV {'muted' if muted else 'unmuted'}.")


# -- Apps & Deep Linking -----------------------------------------------------


@main.command()
@click.argument("app")
@click.argument("content_id", required=False)
@click.pass_context
def launch(ctx, app, content_id):
    """Launch an app, optionally with deep link content ID."""
    from smartest_tv.ui.theme import ICONS, app_icon
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        app_id, name = resolve_app(app, d.platform)
        if content_id:
            await d.launch_app_deep(app_id, content_id)
            return name, app_id, content_id
        else:
            await d.launch_app(app_id)
            return name, app_id, None

    name, app_id, content = _run(_do())
    icon = app_icon(app_id)
    if content:
        _success(f"{icon} Launched {name} → {content}")
    else:
        _success(f"{icon} Launched {name}")


@main.command()
@click.argument("app")
@click.pass_context
def close(ctx, app):
    """Close a running app."""
    from smartest_tv.ui.theme import app_icon
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        app_id, name = resolve_app(app, d.platform)
        await d.close_app(app_id)
        return name, app_id

    name, app_id = _run(_do())
    _success(f"{app_icon(app_id)} Closed {name}.")


@main.command()
@click.pass_context
def apps(ctx):
    """List installed apps."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        return [{"id": a.id, "name": a.name} for a in await d.list_apps()]

    result = _run(_do())
    if ctx.obj["fmt"] == "json":
        _output(result, "json")
    else:
        _print(_ui.render_apps(result))


# -- Media -------------------------------------------------------------------


@main.command()
@click.pass_context
def play(ctx):
    """Resume playback."""
    from smartest_tv.ui.theme import ICONS
    d = _get_driver(ctx.obj["tv_name"])
    _run(d.connect())
    _run(d.play())
    _success(f"{ICONS['play']} Playing.")


@main.command()
@click.pass_context
def pause(ctx):
    """Pause playback."""
    from smartest_tv.ui.theme import ICONS
    d = _get_driver(ctx.obj["tv_name"])
    _run(d.connect())
    _run(d.pause())
    _success(f"{ICONS['pause']} Paused.")


# -- Status ------------------------------------------------------------------


@main.command()
@click.pass_context
def status(ctx):
    """Show TV status."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        s = await d.status()
        return {
            "platform": d.platform,
            "current_app": s.current_app,
            "volume": s.volume,
            "muted": s.muted,
            "sound_output": s.sound_output,
        }

    data = _run(_do())
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        tv_label = ctx.obj.get("tv_name") or "TV"
        try:
            cfg = get_tv_config(tv_label if ctx.obj.get("tv_name") else None)
            tv_label = cfg.get("name", tv_label)
        except Exception:
            pass
        _print(_ui.render_status(data, tv_name=tv_label))


@main.command()
@click.pass_context
def info(ctx):
    """Show TV system info."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        i = await d.info()
        return {
            "platform": i.platform,
            "model": i.model,
            "firmware": i.firmware,
            "ip": i.ip,
            "name": i.name,
        }

    data = _run(_do())
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        _print(_ui.render_info(data))


# -- Notifications -----------------------------------------------------------


@main.command()
@click.argument("message")
@click.pass_context
def notify(ctx, message):
    """Show a notification on the TV. Supports --all / --group."""
    from smartest_tv.ui.theme import ICONS
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _send(d):
            await d.notify(message)
            return f"sent: {message}"

        results = _run(_broadcast_action(targets, _send))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            await d.notify(message)

        _run(_do())
        _success(f"{ICONS['info']} Sent: {message}")


# -- What's On ---------------------------------------------------------------


@main.command("whats-on")
@click.argument("platform", required=False, default=None,
                type=click.Choice(["netflix", "youtube"]))
@click.option("--limit", "-n", default=10, type=int, help="Number of results")
@click.pass_context
def whats_on(ctx, platform, limit):
    """Show trending content on Netflix or YouTube.

    Examples:
        stv whats-on
        stv whats-on netflix
        stv whats-on youtube
        stv whats-on netflix -n 5
    """
    from smartest_tv.resolve import fetch_netflix_trending, fetch_youtube_trending

    fmt = ctx.obj["fmt"]
    show_netflix = platform in (None, "netflix")
    show_youtube = platform in (None, "youtube")

    result: dict = {}
    if show_netflix:
        result["netflix"] = fetch_netflix_trending(limit)
    if show_youtube:
        result["youtube"] = fetch_youtube_trending(limit)

    if fmt == "json":
        _output(result, "json")
    else:
        _print(_ui.render_trending(
            netflix=result.get("netflix") if show_netflix else None,
            youtube=result.get("youtube") if show_youtube else None,
        ))


# -- Search ------------------------------------------------------------------


@main.command()
@click.argument("platform")
@click.argument("query", nargs=-1, required=True)
@click.pass_context
def search(ctx, platform, query):
    """Search for content and show what stv found.

    Examples:
        stv search netflix Frieren
        stv search spotify "Ye White Lines"
        stv search youtube "baby shark"
    """
    from smartest_tv.resolve import (
        _search_netflix_title_id, _scrape_netflix_all_seasons,
        _search_spotify, _slugify,
    )

    query_str = " ".join(query)
    p = platform.lower()

    if p == "netflix":
        title_id = _search_netflix_title_id(query_str)
        if not title_id:
            _fail(f"No Netflix results for: {query_str}")
            return

        result = {"title_id": title_id, "url": f"https://www.netflix.com/title/{title_id}"}
        try:
            seasons = _scrape_netflix_all_seasons(title_id)
            result["seasons"] = len(seasons)
            result["episodes"] = {
                f"S{i}": f"{s[0]}–{s[-1]} ({len(s)} eps)"
                for i, s in enumerate(seasons, 1)
            }
        except Exception:
            pass

        if ctx.obj["fmt"] == "json":
            _output(result, "json")
        else:
            _print(_ui.render_netflix_search(query_str, result))

    elif p == "spotify":
        uri = _search_spotify(query_str)
        if not uri:
            _fail(f"No Spotify results for: {query_str}")
            return
        if ctx.obj["fmt"] == "json":
            _output({"uri": uri}, "json")
        else:
            _print(_ui.render_spotify_search(query_str, uri))

    elif p == "youtube":
        import shutil, subprocess as sp
        if not shutil.which("yt-dlp"):
            _fail("yt-dlp not found")
            return
        r = sp.run(
            ["yt-dlp", f"ytsearch3:{query_str}", "--get-id", "--get-title", "--no-download"],
            capture_output=True, text=True, timeout=30,
        )
        lines = r.stdout.strip().split("\n")
        if len(lines) < 2:
            _fail(f"No YouTube results for: {query_str}")
            return
        results = []
        for i in range(0, len(lines) - 1, 2):
            results.append({"title": lines[i], "id": lines[i + 1]})
        if ctx.obj["fmt"] == "json":
            _output(results, "json")
        else:
            _print(_ui.render_youtube_search(query_str, results))
    else:
        _fail(f"Unsupported: {platform}")


# -- Cast --------------------------------------------------------------------


_parse_cast_url = parse_cast_url


@main.command()
@click.argument("url")
@click.pass_context
def cast(ctx, url):
    """Cast a URL to your TV. Supports Netflix, YouTube, Spotify links.

    Examples:
        stv cast https://www.netflix.com/watch/82656797
        stv cast https://www.netflix.com/title/81726714
        stv cast https://www.youtube.com/watch?v=dQw4w9WgXcQ
        stv cast https://youtu.be/dQw4w9WgXcQ
        stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
    """
    from smartest_tv.ui.theme import ICONS
    try:
        platform, content_id = _parse_cast_url(url)
    except ValueError as exc:
        _fail(str(exc))
        return

    # Netflix title URL → resolve to an actual video/episode ID
    if platform == "netflix" and content_id.startswith("title:"):
        title_id = int(content_id.split(":", 1)[1])
        from smartest_tv.resolve import resolve as do_resolve
        try:
            content_id = do_resolve("netflix", str(title_id), title_id=title_id)
        except ValueError as exc:
            _fail(str(exc))
            return

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app(platform, d.platform)

    async def _do():
        await d.connect()
        await launch_content(d, platform, app_id, content_id)

    _run(_do())

    from smartest_tv import cache as _cache
    _cache.record_play(platform, url, content_id, None, None)

    _success(f"{ICONS['cast']} Casting {url} → {name} ({content_id})")


# -- Resolve & Play ----------------------------------------------------------


def _parse_season_episode(text: str) -> tuple[int | None, int | None]:
    """Parse season/episode from strings like 's2e8', 'S02E08', '2x8'."""
    import re

    m = re.match(r"[sS](\d+)[eExX](\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"(\d+)[xX](\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


@main.command()
@click.argument("platform")
@click.argument("query", nargs=-1, required=True)
@click.option("--season", "-s", type=int, help="Season number")
@click.option("--episode", "-e", type=int, help="Episode number")
@click.option("--title-id", type=int, help="Netflix title ID (skips search)")
@click.pass_context
def resolve(ctx, platform, query, season, episode, title_id):
    """Resolve content to a platform-specific ID.

    Examples:
        stv resolve netflix Frieren -s 2 -e 8
        stv resolve netflix Frieren s2e8
        stv resolve youtube "baby shark"
        stv resolve netflix "The Glory" --title-id 81519223 -s 1 -e 1
    """
    from smartest_tv.resolve import resolve as do_resolve

    query_parts = list(query)

    # Try to parse s2e8 from the last argument
    if query_parts and not season and not episode:
        s, e = _parse_season_episode(query_parts[-1])
        if s is not None:
            season, episode = s, e
            query_parts = query_parts[:-1]

    query_str = " ".join(query_parts)
    if not query_str:
        _fail("No query provided.")
        return

    try:
        content_id = do_resolve(platform, query_str, season, episode, title_id)
    except ValueError as exc:
        _fail(str(exc))
        return

    if ctx.obj["fmt"] == "json":
        _output(content_id, "json")
    else:
        from smartest_tv.ui.theme import app_icon
        _success(f"{app_icon(platform)} {platform}: {content_id}")


@main.command()
@click.argument("platform")
@click.argument("query", nargs=-1, required=True)
@click.option("--season", "-s", type=int, help="Season number")
@click.option("--episode", "-e", type=int, help="Episode number")
@click.option("--title-id", type=int, help="Netflix title ID (skips search)")
@click.pass_context
def play(ctx, platform, query, season, episode, title_id):
    """Find content and play it on TV in one step.

    Resolves the content ID, then launches it. For Netflix, automatically
    closes the app first (required for deep links).

    Examples:
        stv play netflix Frieren s2e8
        stv play netflix Frieren -s 2 -e 8 --title-id 81726714
        stv play youtube "baby shark"
        stv play spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS
    """
    from smartest_tv.resolve import resolve as do_resolve

    query_parts = list(query)

    # Parse s2e8 from last argument
    if query_parts and not season and not episode:
        s, e = _parse_season_episode(query_parts[-1])
        if s is not None:
            season, episode = s, e
            query_parts = query_parts[:-1]

    query_str = " ".join(query_parts)
    if not query_str:
        _fail("No query provided.")
        return

    from smartest_tv.ui.theme import ICONS, app_icon

    # Step 1: Resolve content ID (once — works for all TVs)
    try:
        content_id = do_resolve(platform, query_str, season, episode, title_id)
    except ValueError as exc:
        _fail(str(exc))
        return

    desc = f"{query_str}"
    if season and episode:
        desc += f" S{season}E{episode}"

    icon = app_icon(platform)

    # Step 2: Launch on TV(s)
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _play_on(d):
            app_id, name = resolve_app(platform, d.platform)
            await launch_content(d, platform, app_id, content_id)
            return f"{ICONS['play']} {desc} on {name} ({content_id})"

        results = _run(_broadcast_action(targets, _play_on))
        _print_results(results, ctx.obj["fmt"])
    else:
        d = _get_driver(ctx.obj["tv_name"])
        app_id, name = resolve_app(platform, d.platform)

        async def _do():
            await d.connect()
            await launch_content(d, platform, app_id, content_id)

        _run(_do())
        _success(f"{icon} Playing {desc} on {name}  ({content_id})")

    # Record to history
    from smartest_tv import cache as _cache
    _cache.record_play(platform, query_str, content_id, season, episode)


# -- History -----------------------------------------------------------------


@main.command()
@click.option("--limit", "-n", default=10, help="Number of entries")
@click.pass_context
def history(ctx, limit):
    """Show recent play history.

    Examples:
        stv history
        stv history -n 5
    """
    from smartest_tv import cache as _cache

    entries = _cache.get_history(limit)
    if ctx.obj["fmt"] == "json":
        _output(entries, "json")
    else:
        _print(_ui.render_history(entries))


@main.command()
@click.option("--mood", "-m", default=None,
              type=click.Choice(["chill", "action", "kids", "random"]),
              help="Filter by mood")
@click.option("--limit", "-n", default=5, type=int, help="Number of results")
@click.pass_context
def recommend(ctx, mood, limit):
    """Get personalized content recommendations.

    Uses watch history + trending to suggest what to watch.
    Set STV_LLM_URL to enable AI-powered reasons (e.g. http://localhost:11434/api/generate).

    Examples:
        stv recommend
        stv recommend --mood chill
        stv recommend --mood action -n 3
    """
    from smartest_tv.resolve import get_recommendations
    from smartest_tv import cache as _cache

    history_data = _cache.analyze_history()
    recent = history_data["recent_shows"]

    results = get_recommendations(mood=mood, limit=limit)

    if ctx.obj["fmt"] == "json":
        _output(results, "json")
    else:
        _print(_ui.render_recommendations(results, recent_shows=recent))


@main.command()
@click.argument("query", nargs=-1)
@click.pass_context
def next(ctx, query):
    """Play the next episode of a Netflix show.

    Uses play history to determine where you left off.

    Examples:
        stv next Frieren        # → plays next episode after last watched
        stv next                # → continues the most recent Netflix show
    """
    from smartest_tv import cache as _cache
    from smartest_tv.resolve import resolve as do_resolve

    query_str = " ".join(query) if query else None

    from smartest_tv.ui.theme import ICONS
    if not query_str:
        # Find most recent Netflix play
        last = _cache.get_last_played(platform="netflix")
        if not last:
            _fail("No Netflix history. Play something first.")
            return
        query_str = last["query"]

    result = _cache.get_next_episode(query_str)
    if not result:
        _fail(f"No next episode for '{query_str}'. Finished or not in history.")
        return

    q, season, episode = result

    try:
        content_id = do_resolve("netflix", q, season, episode)
    except ValueError as exc:
        _fail(str(exc))
        return

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app("netflix", d.platform)

    async def _do():
        await d.connect()
        await launch_content(d, "netflix", app_id, content_id)

    _run(_do())
    _cache.record_play("netflix", q, content_id, season, episode)
    _success(f"{ICONS['netflix']} Playing {q} S{season}E{episode} on Netflix  ({content_id})")


# -- Queue -------------------------------------------------------------------


@main.group("queue")
def queue_group():
    """Manage the play queue."""


@queue_group.command("add")
@click.argument("platform", type=click.Choice(["netflix", "youtube", "spotify"]))
@click.argument("query")
@click.option("-s", "--season", type=int, help="Season number")
@click.option("-e", "--episode", type=int, help="Episode number")
def queue_add_cmd(platform, query, season, episode):
    """Add content to the play queue.

    Examples:
        stv queue add netflix "Bridgerton" -s 3 -e 4
        stv queue add youtube "Despacito"
        stv queue add spotify "Ye White Lines"
    """
    from smartest_tv import cache as _cache
    from smartest_tv.ui.theme import ICONS, app_icon
    item = _cache.queue_add(platform, query, season, episode)
    desc = item["query"]
    if item.get("season") and item.get("episode"):
        desc += f" S{item['season']}E{item['episode']}"
    _success(f"{ICONS['queue']}  Added  {app_icon(platform)} {platform}  —  {desc}")


@queue_group.command("show")
@click.pass_context
def queue_show_cmd(ctx):
    """Show the current play queue."""
    from smartest_tv import cache as _cache
    items = _cache.queue_show()
    if ctx.obj["fmt"] == "json":
        _output(items, "json")
    else:
        _print(_ui.render_queue(items))


@queue_group.command("play")
@click.pass_context
def queue_play_cmd(ctx):
    """Play the next item in the queue."""
    from smartest_tv import cache as _cache
    from smartest_tv.resolve import resolve as do_resolve
    from smartest_tv.ui.theme import ICONS, app_icon

    item = _cache.queue_pop()
    if not item:
        _info("Queue is empty.", icon=ICONS['queue'])
        return

    platform = item["platform"]
    query = item["query"]
    season = item.get("season")
    episode = item.get("episode")

    try:
        content_id = do_resolve(platform, query, season, episode)
    except ValueError as exc:
        _fail(str(exc))
        return

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app(platform, d.platform)

    async def _do():
        await d.connect()
        await launch_content(d, platform, app_id, content_id)

    _run(_do())
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season and episode:
        desc += f" S{season}E{episode}"
    _success(f"{app_icon(platform)} Playing {desc} on {name}  ({content_id})")


@queue_group.command("skip")
def queue_skip_cmd():
    """Skip the current queue item (remove without playing)."""
    from smartest_tv import cache as _cache
    from smartest_tv.ui.theme import ICONS, app_icon
    items = _cache.queue_show()
    if not items:
        _info("Queue is empty.", icon=ICONS['queue'])
        return
    skipped = items[0]
    _cache.queue_skip()
    desc = skipped["query"]
    if skipped.get("season") and skipped.get("episode"):
        desc += f" S{skipped['season']}E{skipped['episode']}"
    _success(f"{ICONS['next']} Skipped  {app_icon(skipped['platform'])} {skipped['platform']}  —  {desc}")

    remaining = _cache.queue_show()
    if remaining:
        next_item = remaining[0]
        next_desc = next_item["query"]
        if next_item.get("season") and next_item.get("episode"):
            next_desc += f" S{next_item['season']}E{next_item['episode']}"
        _info(
            f"Next: {next_item['platform']} — {next_desc}",
            icon=app_icon(next_item['platform']),
        )
    else:
        _info("Queue is now empty.", icon=ICONS['queue'])


@queue_group.command("clear")
def queue_clear_cmd():
    """Clear the entire play queue."""
    from smartest_tv import cache as _cache
    from smartest_tv.ui.theme import ICONS
    _cache.queue_clear()
    _success(f"{ICONS['queue']} Queue cleared.")


# -- Cache -------------------------------------------------------------------


@main.group("cache")
def cache_group():
    """Manage the content ID cache."""


@cache_group.command("set")
@click.argument("platform")
@click.argument("query")
@click.option("--season", "-s", type=int, help="Season number (Netflix)")
@click.option("--first-ep-id", type=int, help="First episode videoId of the season")
@click.option("--count", type=int, help="Number of episodes in the season")
@click.option("--title-id", type=int, help="Netflix title ID")
@click.option("--content-id", type=str, help="Direct content ID (YouTube/Spotify)")
def cache_set(platform, query, season, first_ep_id, count, title_id, content_id):
    """Save a content ID to the local cache.

    For Netflix episodes (AI or user discovers IDs once, instant forever):
        stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714

    For YouTube/Spotify:
        stv cache set youtube "baby shark" --content-id dQw4w9WgXcQ
        stv cache set spotify "Ye Vultures" --content-id spotify:album:xxx
    """
    from smartest_tv import cache
    from smartest_tv.resolve import _slugify

    slug = _slugify(query)
    p = platform.lower()

    from smartest_tv.ui.theme import ICONS
    if p == "netflix" and season and first_ep_id and count:
        cache.put_netflix_show(slug, title_id or 0, season, first_ep_id, count)
        last_ep_id = first_ep_id + count - 1
        _success(f"{ICONS['cache']} Cached  {query} S{season}  eps {first_ep_id}–{last_ep_id}  ({count} eps)")
    elif content_id:
        cache.put(p, slug, content_id)
        _success(f"{ICONS['cache']} Cached  {query} → {content_id}")
    else:
        _fail("Need --content-id or (--season + --first-ep-id + --count)")


@cache_group.command("get")
@click.argument("platform")
@click.argument("query")
@click.option("--season", "-s", type=int)
@click.option("--episode", "-e", type=int)
@click.pass_context
def cache_get(ctx, platform, query, season, episode):
    """Look up a cached content ID.

    Examples:
        stv cache get netflix Frieren -s 2 -e 8
        stv cache get youtube "baby shark"
    """
    from smartest_tv import cache
    from smartest_tv.resolve import _slugify

    slug = _slugify(query)

    if platform.lower() == "netflix" and season and episode:
        result = cache.get_netflix_episode(slug, season, episode)
    else:
        result = cache.get(platform.lower(), slug)

    if result:
        if ctx.obj["fmt"] == "json":
            _output(result, "json")
        else:
            from smartest_tv.ui.theme import ICONS
            _success(f"{ICONS['cache']} {result}")
    else:
        _fail("(not cached)")


@cache_group.command("show")
@click.pass_context
def cache_show(ctx):
    """Show all cached content IDs."""
    from smartest_tv import cache

    data = cache._load()
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        _print(_ui.render_cache_show(data))


@cache_group.command("contribute")
def cache_contribute():
    """Show your local cache as community-cache.json format.

    Copy the output and submit as a PR or GitHub Issue to share
    your resolved content IDs with all stv users.

    Example:
        stv cache contribute > my-cache.json
        # Then open a PR adding entries to community-cache.json
    """
    from smartest_tv import cache

    data = cache._load()
    # Strip private data (_history)
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    if not clean:
        _fail("Nothing to contribute. Play some content first.")
        return

    # stdout: raw JSON so users can pipe to a file (no Rich markup)
    click.echo(json.dumps(clean, ensure_ascii=False, indent=2))
    # stderr: themed instructions
    _ui_console.print(
        "\n[muted]☝  Copy this and submit a PR:[/muted]\n"
        "  [accent]https://github.com/Hybirdss/smartest-tv[/accent]\n"
        "  [dim]Add entries to community-cache.json[/dim]",
        file=sys.stderr,
    )


# -- Scene Presets -----------------------------------------------------------


@main.group("scene")
def scene_group():
    """Run or manage scene presets (movie-night, kids, sleep, music, ...)."""


@scene_group.command("list")
@click.pass_context
def scene_list_cmd(ctx):
    """List all available scenes (built-in and custom).

    Example:
        stv scene list
    """
    from smartest_tv.scenes import list_scenes, BUILTIN_SCENES

    scenes = list_scenes()
    if ctx.obj["fmt"] == "json":
        _output(scenes, "json")
        return

    _print(_ui.render_scenes(scenes, set(BUILTIN_SCENES.keys()) if isinstance(BUILTIN_SCENES, dict) else set(BUILTIN_SCENES)))


@scene_group.command("run")
@click.argument("name")
@click.pass_context
def scene_run_cmd(ctx, name):
    """Run a scene preset.

    Examples:
        stv scene run movie-night
        stv scene run sleep
        stv scene run my-custom-scene
    """
    from smartest_tv.scenes import run_scene

    tv_name = ctx.obj["tv_name"]

    async def _do():
        return await run_scene(name, tv_name)

    try:
        results = _run(_do())
    except KeyError as exc:
        _fail(str(exc))
        return

    _print(_ui.render_scene_run(name, results))


@scene_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Short description")
def scene_create_cmd(name, description):
    """Create a custom scene interactively.

    Example:
        stv scene create my-scene --description "My custom scene"
    """
    from smartest_tv.scenes import BUILTIN_SCENES, save_custom_scene

    if name in BUILTIN_SCENES:
        _fail(f"'{name}' is a built-in scene. Choose a different name.")
        return

    click.echo(f"Creating scene '{name}'. Add steps one by one (empty action to finish).")
    click.echo("Actions: volume, notify, screen_off, screen_on, play, webhook")
    click.echo()

    steps = []
    while True:
        action = click.prompt("  action", default="", show_default=False).strip()
        if not action:
            break

        step: dict = {"action": action}

        if action == "volume":
            step["value"] = click.prompt("  value (0-100)", type=int)
        elif action == "notify":
            step["message"] = click.prompt("  message")
        elif action == "play":
            step["platform"] = click.prompt("  platform (netflix/youtube/spotify)")
            step["query"] = click.prompt("  query")
            season = click.prompt("  season (optional)", default="", show_default=False).strip()
            if season:
                step["season"] = int(season)
                step["episode"] = click.prompt("  episode", type=int)
        elif action == "webhook":
            step["url"] = click.prompt("  url")
        elif action in ("screen_off", "screen_on"):
            pass  # no extra fields
        else:
            click.echo(f"  Unknown action '{action}' — adding as-is.")

        steps.append(step)
        click.echo(f"  Step added: {step}")

    if not steps:
        _info("No steps added. Scene not saved.")
        return

    save_custom_scene(name, description, steps)
    from smartest_tv.ui.theme import ICONS
    _success(f"{ICONS['scene']} Scene '{name}' saved with {len(steps)} step(s).")


@scene_group.command("delete")
@click.argument("name")
def scene_delete_cmd(name):
    """Delete a custom scene.

    Example:
        stv scene delete my-scene
    """
    from smartest_tv.scenes import delete_custom_scene
    from smartest_tv.ui.theme import ICONS

    try:
        delete_custom_scene(name)
        _success(f"{ICONS['scene']} Scene '{name}' deleted.")
    except KeyError as exc:
        _fail(str(exc))


# -- Multi TV Management -----------------------------------------------------


@main.group("multi")
def multi_group():
    """Manage multiple TVs."""


@multi_group.command("list")
@click.pass_context
def multi_list(ctx):
    """List all configured TVs and their status."""
    tvs = list_tvs()
    if ctx.obj["fmt"] == "json":
        _output(tvs, "json")
    else:
        _print(_ui.render_tv_list(tvs))


@multi_group.command("add")
@click.argument("name")
@click.option("--platform", required=True,
              type=click.Choice(["lg", "samsung", "android", "firetv", "roku", "remote"]),
              help="TV platform (use 'remote' for a friend's stv)")
@click.option("--ip", default="", help="TV IP address (local TVs)")
@click.option("--url", default="", help="Remote stv API URL (e.g. http://friend:8911)")
@click.option("--mac", default="", help="MAC address for Wake-on-LAN")
@click.option("--default", "is_default", is_flag=True, help="Set as default TV")
def multi_add(name, platform, ip, url, mac, is_default):
    """Add a TV to the config.

    Examples:
        stv multi add bedroom --platform samsung --ip 192.168.1.101
        stv multi add living-room --platform lg --ip 192.168.1.100 --default
        stv multi add friend --platform remote --url http://203.0.113.50:8911
    """
    from smartest_tv.ui.theme import ICONS
    if platform == "remote" and not url:
        _fail("Remote TVs require --url.", hint="Example: --url http://friend-ip:8911")
        return
    if platform != "remote" and not ip:
        _fail("Local TVs require --ip.")
        return

    try:
        add_tv(name, platform, ip or url, mac=mac, default=is_default)
        if platform == "remote":
            _success(f"{ICONS['tv']} Added remote TV '{name}' → {url}")
        else:
            default_str = "  (default)" if is_default else ""
            _success(f"{ICONS['tv']} Added TV '{name}': {platform.upper()} @ {ip}{default_str}")
    except Exception as e:
        _fail(str(e))


@multi_group.command("remove")
@click.argument("name")
def multi_remove(name):
    """Remove a TV from the config.

    Example:
        stv multi remove bedroom
    """
    from smartest_tv.ui.theme import ICONS
    try:
        remove_tv(name)
        _success(f"{ICONS['tv']} Removed TV '{name}'.")
    except KeyError as e:
        _fail(str(e))


@multi_group.command("default")
@click.argument("name")
def multi_default(name):
    """Set the default TV.

    Example:
        stv multi default living-room
    """
    from smartest_tv.ui.theme import ICONS
    try:
        set_default_tv(name)
        _success(f"{ICONS['star']}  Default TV set to '{name}'.")
    except KeyError as e:
        _fail(str(e))


# -- Group Management --------------------------------------------------------


@main.group("group")
def group_group():
    """Manage TV groups for sync playback and party mode."""


@group_group.command("list")
@click.pass_context
def group_list_cmd(ctx):
    """List all TV groups.

    Example:
        stv group list
    """
    groups = get_groups()
    if ctx.obj["fmt"] == "json":
        _output(groups, "json")
    else:
        _print(_ui.render_group_list(groups))


@group_group.command("create")
@click.argument("name")
@click.argument("members", nargs=-1, required=True)
def group_create_cmd(name, members):
    """Create a TV group.

    Examples:
        stv group create party living-room bedroom
        stv group create everywhere living-room bedroom friend-tv
    """
    from smartest_tv.ui.theme import ICONS
    try:
        save_group(name, list(members))
        _success(f"{ICONS['group']} Group '{name}' created: {', '.join(members)}")
    except (ValueError, KeyError) as e:
        _fail(str(e))


@group_group.command("delete")
@click.argument("name")
def group_delete_cmd(name):
    """Delete a TV group.

    Example:
        stv group delete party
    """
    from smartest_tv.ui.theme import ICONS
    try:
        delete_group(name)
        _success(f"{ICONS['group']} Group '{name}' deleted.")
    except KeyError as e:
        _fail(str(e))


# -- Insights ----------------------------------------------------------------


@main.command("insights")
@click.option("--period", default="week", type=click.Choice(["day", "week", "month"]),
              help="Time period for the report")
@click.pass_context
def insights_cmd(ctx, period):
    """View your watching insights and screen time.

    Examples:
        stv insights                   # weekly report
        stv insights --period day      # today's viewing
        stv insights --period month    # monthly overview
    """
    from smartest_tv.insights import get_insights

    data = get_insights(period)
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        _print(_ui.render_insights(data))


@main.command("screen-time")
@click.option("--period", default="day", type=click.Choice(["day", "week", "month"]),
              help="Time period")
@click.pass_context
def screen_time_cmd(ctx, period):
    """Check screen time (great for kids tracking).

    Examples:
        stv screen-time                # today
        stv screen-time --period week  # this week
    """
    from smartest_tv.insights import get_screen_time

    data = get_screen_time(period)
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        _print(_ui.render_screen_time(period, data))


@main.command("sub-value")
@click.argument("platform", default="netflix")
@click.option("--cost", default=17.99, help="Monthly subscription cost")
@click.pass_context
def sub_value_cmd(ctx, platform, cost):
    """Is your streaming subscription worth it?

    Examples:
        stv sub-value netflix --cost 17.99
        stv sub-value youtube --cost 13.99
    """
    from smartest_tv.insights import get_subscription_value

    data = get_subscription_value(platform, cost)
    if ctx.obj["fmt"] == "json":
        _output(data, "json")
    else:
        _print(_ui.render_sub_value(platform, cost, data))


# -- Display -----------------------------------------------------------------


@main.group("display")
def display_group():
    """Use your TV as a display — dashboards, messages, clocks."""


@display_group.command("message")
@click.argument("text")
@click.option("--bg", default="#000", help="Background color")
@click.option("--color", default="#fff", help="Text color")
@click.pass_context
def display_message(ctx, text, bg, color):
    """Show a persistent message on TV.

    Example:
        stv display message "Dinner's ready!"
        stv display message "Welcome home" --bg "#1a1a2e" --color "#e94560"
    """
    from smartest_tv.display import generate_html, serve

    html = generate_html("message", {"text": text, "bg": bg, "color": color})
    _cast_html(ctx, html)


@display_group.command("clock")
@click.option("--format", "fmt", default="24h", type=click.Choice(["12h", "24h"]),
              help="Clock format")
@click.pass_context
def display_clock(ctx, fmt):
    """Show a full-screen clock on TV.

    Example:
        stv display clock
        stv display clock --format 12h
    """
    from smartest_tv.display import generate_html, serve

    html = generate_html("clock", {"format": fmt})
    _cast_html(ctx, html)


@display_group.command("dashboard")
@click.argument("cards", nargs=-1, required=True)
@click.option("--title", default="Dashboard", help="Dashboard title")
@click.pass_context
def display_dashboard(ctx, cards, title):
    """Show an info dashboard on TV. Cards are label:value pairs.

    Example:
        stv display dashboard "Time:21:30" "Weather:18°C" "WiFi:Connected"
    """
    from smartest_tv.display import generate_html, serve

    parsed = []
    for card in cards:
        if ":" in card:
            label, value = card.split(":", 1)
            parsed.append({"label": label.strip(), "value": value.strip()})
        else:
            parsed.append({"label": card, "value": ""})
    html = generate_html("dashboard", {"title": title, "cards": parsed})
    _cast_html(ctx, html)


@display_group.command("url")
@click.argument("url")
@click.pass_context
def display_url(ctx, url):
    """Show any URL on the TV in fullscreen.

    Example:
        stv display url https://grafana.local/d/my-dashboard
    """
    from smartest_tv.display import generate_html, serve

    html = generate_html("iframe", {"url": url, "fullscreen": True})
    _cast_html(ctx, html)


def _cast_html(ctx, html: str, port: int = 8765):
    """Helper: serve HTML and open on TV via browser app."""
    from smartest_tv.display import serve
    from smartest_tv.ui.theme import ICONS

    url, stop = serve(html, port)
    tv_name = ctx.obj.get("tv_name")
    _info(f"Serving at {url}", icon=ICONS['cast'])

    try:
        d = _get_driver(tv_name)
        _run(d.connect())

        # Try to open URL in TV browser
        browser_ids = {
            "lg": "com.webos.app.browser",
            "samsung": "org.tizen.browser",
            "roku": "",  # Roku doesn't have a general browser
            "android": "com.android.chrome",
        }
        browser_id = browser_ids.get(d.platform, "")
        if browser_id:
            _run(d.launch_app_deep(browser_id, url))
            _success(f"{ICONS['tv']} Opened on TV. Press Ctrl+C to stop serving.")
        else:
            _info(f"Open {url} on your TV's browser. Press Ctrl+C to stop.")

        # Keep serving until interrupted
        import signal
        signal.signal(signal.SIGINT, lambda *_: None)
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        stop()
        _info("Server stopped.")


# -- Audio Mode --------------------------------------------------------------


@main.group("audio")
def audio_group():
    """Multi-room audio — play music with screens off (Sonos-killer mode)."""


@audio_group.command("play")
@click.argument("query")
@click.option("--platform", "-p", default="youtube", help="Platform (youtube/spotify)")
@click.option("--rooms", "-r", default=None, help="Comma-separated room names")
@click.pass_context
def audio_play_cmd(ctx, query, platform, rooms):
    """Play audio on TVs with screens off.

    Examples:
        stv audio play "lo-fi beats"                     # all TVs
        stv audio play "chill vibes" -p spotify          # Spotify
        stv audio play "jazz" -r kitchen,bedroom         # specific rooms
    """
    from smartest_tv.audio import audio_play

    room_list = rooms.split(",") if rooms else None
    results = _run(audio_play(query, platform, room_list))
    _print(_ui.render_broadcast_results(results))


@audio_group.command("stop")
@click.option("--rooms", "-r", default=None, help="Comma-separated room names")
def audio_stop_cmd(rooms):
    """Stop audio mode — screens back on.

    Examples:
        stv audio stop
        stv audio stop -r kitchen
    """
    from smartest_tv.audio import audio_stop

    room_list = rooms.split(",") if rooms else None
    results = _run(audio_stop(room_list))
    _print(_ui.render_broadcast_results(results))


@audio_group.command("volume")
@click.argument("room")
@click.argument("level", type=int)
def audio_volume_cmd(room, level):
    """Set volume for a specific room.

    Example:
        stv audio volume kitchen 30
        stv audio volume bedroom 15
    """
    from smartest_tv.audio import audio_volume
    from smartest_tv.ui.theme import ICONS

    result = _run(audio_volume(room, level))
    _success(f"{ICONS['volume']} {room} → {level}  ({result})")


# -- License Management ------------------------------------------------------


@main.group("license")
def license_group():
    """Manage license key."""


@license_group.command("set")
@click.argument("key")
def license_set(key):
    """Save a license key for unlimited API resolves.

    Example:
        stv license set XXXX-XXXX-XXXX-XXXX
    """
    from smartest_tv.config import CONFIG_DIR

    license_file = CONFIG_DIR / "license.key"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    license_file.write_text(key.strip())
    from smartest_tv.ui.theme import ICONS
    _success(f"{ICONS['bolt']} License key saved. Pro features activated.")
    _info(f"Stored: {license_file}")


@license_group.command("status")
def license_status():
    """Check your current license status.

    Example:
        stv license status
    """
    import os
    from smartest_tv.config import CONFIG_DIR

    # Check env var first, then file
    key = os.environ.get("STV_LICENSE_KEY", "")
    source = "env (STV_LICENSE_KEY)"

    if not key:
        license_file = CONFIG_DIR / "license.key"
        if license_file.exists():
            key = license_file.read_text().strip()
            source = str(license_file)

    _print(_ui.render_license_status(key or None, source))


@license_group.command("remove")
def license_remove():
    """Remove your license key.

    Example:
        stv license remove
    """
    from smartest_tv.config import CONFIG_DIR
    from smartest_tv.ui.theme import ICONS

    license_file = CONFIG_DIR / "license.key"
    if license_file.exists():
        license_file.unlink()
        _success(f"{ICONS['bolt']} License key removed. Reverted to free tier.")
    else:
        _info("No license key found.")


if __name__ == "__main__":
    main()
