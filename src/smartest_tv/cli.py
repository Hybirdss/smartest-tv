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
from smartest_tv.config import (
    get_tv_config, list_tvs, add_tv, remove_tv, set_default_tv,
    get_all_tv_names, get_group_members, get_groups, save_group, delete_group,
)
from smartest_tv.drivers.base import TVDriver


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
    """Print data in the requested format."""
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
    """Run an async action on multiple TVs concurrently.

    action_fn(driver) -> str | None
    Returns list of (tv_name, success: bool, message: str)
    """
    async def _one(tv_name):
        try:
            d = _get_driver(tv_name)
            await d.connect()
            result = await action_fn(d)
            return (tv_name or "default", True, str(result or "done"))
        except Exception as e:
            return (tv_name or "default", False, str(e))

    return list(await asyncio.gather(*[_one(n) for n in targets]))


def _print_results(results):
    """Print multi-TV broadcast results."""
    for name, success, msg in results:
        icon = "✅" if success else "❌"
        click.echo(f"  [{name}] {icon} {msg}")


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

    api_port = port + 1
    start_api_server(host, api_port)

    path = "sse" if transport == "sse" else "mcp"
    click.echo(f"MCP server:  http://{host}:{port}/{path}")
    click.echo(f"REST API:    http://{host}:{api_port}/api/ping")
    click.echo()
    click.echo("Friends can add your TV:  stv multi add friend --platform remote --url http://YOUR_IP:" + str(api_port))
    click.echo("Press Ctrl+C to stop.")
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
        click.echo(f"❌ {e}")
        return
    if not tv.get("platform"):
        click.echo("❌ No TV configured. Run: stv setup")
        return

    click.echo(f"📺 {tv.get('name', 'TV')} ({tv['platform'].upper()}, {tv['ip']})")
    click.echo()

    d = _get_driver(tv_name)
    try:
        _run(d.connect())
        click.echo("✅ TV reachable")
    except Exception as e:
        click.echo(f"❌ Can't connect: {e}")
        return

    try:
        s = _run(d.status())
        click.echo(f"✅ Status OK — {s.current_app or 'idle'}, vol {s.volume}")
    except Exception:
        click.echo("⚠️  Status query failed")

    try:
        apps = _run(d.list_apps())
        app_names = {a.name.lower() for a in apps}
        for service in ["Netflix", "YouTube", "Spotify"]:
            found = any(service.lower() in n for n in app_names)
            click.echo(f"{'✅' if found else '⚠️ '} {service} {'found' if found else 'not found'}")
    except Exception:
        click.echo("⚠️  App list unavailable")

    click.echo()
    click.echo("All good! 🎉" if True else "")


# -- Power -------------------------------------------------------------------


@main.command()
@click.pass_context
def on(ctx):
    """Turn on the TV (or all TVs with --all / --group)."""
    if _is_multi(ctx):
        targets = _get_targets(ctx)
        results = _run(_broadcast_action(targets, lambda d: d.power_on() or "turning on"))
        _print_results(results)
    else:
        d = _get_driver(ctx.obj["tv_name"])
        _run(d.connect())
        _run(d.power_on())
        click.echo("TV turning on.")


@main.command()
@click.pass_context
def off(ctx):
    """Turn off the TV (or all TVs with --all / --group)."""
    if _is_multi(ctx):
        targets = _get_targets(ctx)
        results = _run(_broadcast_action(targets, lambda d: d.power_off() or "turned off"))
        _print_results(results)
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            await d.power_off()

        _run(_do())
        click.echo("TV turned off.")


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
        _print_results(results)
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
        if level is not None:
            click.echo(f"Volume set to {level}.")
        else:
            _output(result, ctx.obj["fmt"])


@main.command()
@click.pass_context
def mute(ctx):
    """Toggle mute. Supports --all / --group."""
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _toggle_mute(d):
            current = await d.get_muted()
            await d.set_mute(not current)
            return "muted" if not current else "unmuted"

        results = _run(_broadcast_action(targets, _toggle_mute))
        _print_results(results)
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            current = await d.get_muted()
            await d.set_mute(not current)
            return not current

        muted = _run(_do())
        click.echo(f"TV {'muted' if muted else 'unmuted'}.")


# -- Apps & Deep Linking -----------------------------------------------------


@main.command()
@click.argument("app")
@click.argument("content_id", required=False)
@click.pass_context
def launch(ctx, app, content_id):
    """Launch an app, optionally with deep link content ID."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        app_id, name = resolve_app(app, d.platform)
        if content_id:
            await d.launch_app_deep(app_id, content_id)
            return f"Launched {name} with content: {content_id}"
        else:
            await d.launch_app(app_id)
            return f"Launched {name}."

    click.echo(_run(_do()))


@main.command()
@click.argument("app")
@click.pass_context
def close(ctx, app):
    """Close a running app."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        app_id, name = resolve_app(app, d.platform)
        await d.close_app(app_id)
        return name

    name = _run(_do())
    click.echo(f"Closed {name}.")


@main.command()
@click.pass_context
def apps(ctx):
    """List installed apps."""
    d = _get_driver(ctx.obj["tv_name"])

    async def _do():
        await d.connect()
        return [{"id": a.id, "name": a.name} for a in await d.list_apps()]

    _output(_run(_do()), ctx.obj["fmt"])


# -- Media -------------------------------------------------------------------


@main.command()
@click.pass_context
def play(ctx):
    """Resume playback."""
    d = _get_driver(ctx.obj["tv_name"])
    _run(d.connect())
    _run(d.play())
    click.echo("Playing.")


@main.command()
@click.pass_context
def pause(ctx):
    """Pause playback."""
    d = _get_driver(ctx.obj["tv_name"])
    _run(d.connect())
    _run(d.pause())
    click.echo("Paused.")


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

    _output(_run(_do()), ctx.obj["fmt"])


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

    _output(_run(_do()), ctx.obj["fmt"])


# -- Notifications -----------------------------------------------------------


@main.command()
@click.argument("message")
@click.pass_context
def notify(ctx, message):
    """Show a notification on the TV. Supports --all / --group."""
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _send(d):
            await d.notify(message)
            return f"sent: {message}"

        results = _run(_broadcast_action(targets, _send))
        _print_results(results)
    else:
        d = _get_driver(ctx.obj["tv_name"])

        async def _do():
            await d.connect()
            await d.notify(message)

        _run(_do())
        click.echo(f"Sent: {message}")


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

    def _fmt_views(n) -> str:
        if n is None:
            return ""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M views"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K views"
        return f"{n} views"

    fmt = ctx.obj["fmt"]
    show_netflix = platform in (None, "netflix")
    show_youtube = platform in (None, "youtube")

    result = {}

    if show_netflix:
        items = fetch_netflix_trending(limit)
        result["netflix"] = items
        if fmt != "json":
            click.echo("Netflix Top 10:")
            if items:
                for item in items:
                    rank = item.get("rank", "")
                    title = item.get("title", "")
                    cat = item.get("category", "")
                    cat_str = f"  — {cat}" if cat else ""
                    click.echo(f"  {rank:>2}. {title}{cat_str}")
            else:
                click.echo("  (Could not fetch trending data)")
            if show_youtube:
                click.echo()

    if show_youtube:
        items = fetch_youtube_trending(limit)
        result["youtube"] = items
        if fmt != "json":
            click.echo("YouTube Trending:")
            if items:
                for item in items:
                    rank = item.get("rank", "")
                    title = item.get("title", "")
                    channel = item.get("channel", "")
                    views = _fmt_views(item.get("view_count"))
                    channel_str = f"[{channel}] " if channel else ""
                    views_str = f"  — {views}" if views else ""
                    click.echo(f"  {rank:>2}. {channel_str}{title}{views_str}")
            else:
                click.echo("  (Could not fetch trending data)")

    if fmt == "json":
        _output(result, "json")


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
            click.echo(f"❌ No Netflix results for: {query_str}", err=True)
            sys.exit(1)

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
            click.echo(f"📺 {query_str}")
            click.echo(f"   Netflix ID: {title_id}")
            click.echo(f"   URL: https://www.netflix.com/title/{title_id}")
            if "seasons" in result:
                click.echo(f"   {result['seasons']} seasons:")
                for sn, info in result["episodes"].items():
                    click.echo(f"     {sn}: {info}")

    elif p == "spotify":
        uri = _search_spotify(query_str)
        if not uri:
            click.echo(f"❌ No Spotify results for: {query_str}", err=True)
            sys.exit(1)
        if ctx.obj["fmt"] == "json":
            _output({"uri": uri}, "json")
        else:
            click.echo(f"🎵 {query_str}")
            click.echo(f"   URI: {uri}")

    elif p == "youtube":
        import shutil, subprocess as sp
        if not shutil.which("yt-dlp"):
            click.echo("❌ yt-dlp not found", err=True)
            sys.exit(1)
        r = sp.run(
            ["yt-dlp", f"ytsearch3:{query_str}", "--get-id", "--get-title", "--no-download"],
            capture_output=True, text=True, timeout=30,
        )
        lines = r.stdout.strip().split("\n")
        if len(lines) < 2:
            click.echo(f"❌ No YouTube results for: {query_str}", err=True)
            sys.exit(1)
        # yt-dlp alternates: title, id, title, id, ...
        results = []
        for i in range(0, len(lines) - 1, 2):
            results.append({"title": lines[i], "id": lines[i + 1]})
        if ctx.obj["fmt"] == "json":
            _output(results, "json")
        else:
            click.echo(f"🔍 YouTube: {query_str}")
            for r in results:
                click.echo(f"   {r['id']}  {r['title']}")
    else:
        click.echo(f"❌ Unsupported: {platform}", err=True)
        sys.exit(1)


# -- Cast --------------------------------------------------------------------


def _parse_cast_url(url: str) -> tuple[str, str]:
    """Parse a streaming URL into (platform, content_id).

    Supported:
      netflix.com/watch/12345        → ("netflix", "12345")
      netflix.com/title/12345        → ("netflix", "title:12345")  # needs resolve
      youtube.com/watch?v=ID         → ("youtube", "ID")
      youtu.be/ID                    → ("youtube", "ID")
      open.spotify.com/track/ID      → ("spotify", "spotify:track:ID")
      open.spotify.com/album/ID      → ("spotify", "spotify:album:ID")
      open.spotify.com/playlist/ID   → ("spotify", "spotify:playlist:ID")

    Raises ValueError for unrecognised URLs.
    """
    import re
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    path = parsed.path

    # --- Netflix ---
    if "netflix.com" in host:
        m = re.match(r"/watch/(\d+)", path)
        if m:
            return "netflix", m.group(1)
        m = re.match(r"/title/(\d+)", path)
        if m:
            return "netflix", f"title:{m.group(1)}"
        raise ValueError(f"Unrecognised Netflix URL: {url}")

    # --- YouTube ---
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        if vid:
            return "youtube", vid
        raise ValueError(f"Unrecognised YouTube URL: {url}")

    if host == "youtu.be":
        vid = path.lstrip("/").split("/")[0]
        if vid:
            return "youtube", vid
        raise ValueError(f"Unrecognised youtu.be URL: {url}")

    # --- Spotify ---
    if "spotify.com" in host:
        m = re.match(r"/(track|album|playlist|artist)/([A-Za-z0-9]+)", path)
        if m:
            return "spotify", f"spotify:{m.group(1)}:{m.group(2)}"
        raise ValueError(f"Unrecognised Spotify URL: {url}")

    raise ValueError(
        f"Unsupported URL: {url}\n"
        "Supported: netflix.com, youtube.com, youtu.be, open.spotify.com"
    )


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
    try:
        platform, content_id = _parse_cast_url(url)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    # Netflix title URL → resolve to an actual video/episode ID
    if platform == "netflix" and content_id.startswith("title:"):
        title_id = int(content_id.split(":", 1)[1])
        from smartest_tv.resolve import resolve as do_resolve
        try:
            content_id = do_resolve("netflix", str(title_id), title_id=title_id)
        except ValueError as exc:
            click.echo(f"❌ {exc}", err=True)
            sys.exit(1)

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app(platform, d.platform)

    async def _do():
        await d.connect()
        if platform == "netflix":
            try:
                await d.close_app(app_id)
                import asyncio as _asyncio
                await _asyncio.sleep(2)
            except Exception:
                pass
        await d.launch_app_deep(app_id, content_id)

    _run(_do())

    from smartest_tv import cache as _cache
    _cache.record_play(platform, url, content_id, None, None)

    click.echo(f"▶ Casting {url} on {name} (content: {content_id})")


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
        click.echo("❌ No query provided.", err=True)
        sys.exit(1)

    try:
        content_id = do_resolve(platform, query_str, season, episode, title_id)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    _output(content_id, ctx.obj["fmt"])


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
        click.echo("❌ No query provided.", err=True)
        sys.exit(1)

    # Step 1: Resolve content ID (once — works for all TVs)
    try:
        content_id = do_resolve(platform, query_str, season, episode, title_id)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    desc = f"{query_str}"
    if season and episode:
        desc += f" S{season}E{episode}"

    # Step 2: Launch on TV(s)
    if _is_multi(ctx):
        targets = _get_targets(ctx)

        async def _play_on(d):
            app_id, name = resolve_app(platform, d.platform)
            if platform.lower() == "netflix":
                try:
                    await d.close_app(app_id)
                    await asyncio.sleep(2)
                except Exception:
                    pass
            await d.launch_app_deep(app_id, content_id)
            return f"▶ {desc} on {name} ({content_id})"

        results = _run(_broadcast_action(targets, _play_on))
        _print_results(results)
    else:
        d = _get_driver(ctx.obj["tv_name"])
        app_id, name = resolve_app(platform, d.platform)

        async def _do():
            await d.connect()
            if platform.lower() == "netflix":
                try:
                    await d.close_app(app_id)
                    await asyncio.sleep(2)
                except Exception:
                    pass
            await d.launch_app_deep(app_id, content_id)

        _run(_do())
        click.echo(f"▶ Playing {desc} on {name} (content: {content_id})")

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
    import time as _time

    entries = _cache.get_history(limit)
    if not entries:
        click.echo("No play history yet.")
        return

    if ctx.obj["fmt"] == "json":
        _output(entries, "json")
    else:
        for e in entries:
            ts = _time.strftime("%m/%d %H:%M", _time.localtime(e["time"]))
            desc = e["query"]
            if e.get("season") and e.get("episode"):
                desc += f" S{e['season']}E{e['episode']}"
            click.echo(f"  {ts}  {e['platform']:8s}  {desc}")


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

    if not results:
        click.echo("No recommendations available. Try: stv whats-on")
        return

    fmt = ctx.obj["fmt"]
    if fmt == "json":
        import json
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if recent:
        click.echo(f"Based on your recent watching ({', '.join(recent[:3])}):\n")
    else:
        click.echo("Trending now (no watch history yet):\n")

    for i, rec in enumerate(results, 1):
        title = rec["title"]
        platform = rec["platform"].capitalize()
        reason = rec["reason"]
        click.echo(f"  {i}. {title:<30s}  {platform:<8s}  — {reason}")


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

    if not query_str:
        # Find most recent Netflix play
        last = _cache.get_last_played(platform="netflix")
        if not last:
            click.echo("❌ No Netflix history. Play something first.", err=True)
            sys.exit(1)
        query_str = last["query"]

    result = _cache.get_next_episode(query_str)
    if not result:
        click.echo(f"❌ No next episode for '{query_str}'. Finished or not in history.", err=True)
        sys.exit(1)

    q, season, episode = result

    try:
        content_id = do_resolve("netflix", q, season, episode)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app("netflix", d.platform)

    async def _do():
        await d.connect()
        try:
            await d.close_app(app_id)
            import asyncio
            await asyncio.sleep(2)
        except Exception:
            pass
        await d.launch_app_deep(app_id, content_id)

    _run(_do())
    _cache.record_play("netflix", q, content_id, season, episode)
    click.echo(f"▶ Playing {q} S{season}E{episode} on Netflix (content: {content_id})")


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
    item = _cache.queue_add(platform, query, season, episode)
    desc = item["query"]
    if item.get("season") and item.get("episode"):
        desc += f" S{item['season']}E{item['episode']}"
    click.echo(f"Added to queue: [{platform}] {desc}")


@queue_group.command("show")
@click.pass_context
def queue_show_cmd(ctx):
    """Show the current play queue."""
    from smartest_tv import cache as _cache
    items = _cache.queue_show()
    if not items:
        click.echo("Queue is empty.")
        return
    if ctx.obj["fmt"] == "json":
        _output(items, "json")
    else:
        for i, item in enumerate(items, 1):
            desc = item["query"]
            if item.get("season") and item.get("episode"):
                desc += f" S{item['season']}E{item['episode']}"
            click.echo(f"  {i}. [{item['platform']}] {desc}")


@queue_group.command("play")
@click.pass_context
def queue_play_cmd(ctx):
    """Play the next item in the queue."""
    from smartest_tv import cache as _cache
    from smartest_tv.resolve import resolve as do_resolve

    item = _cache.queue_pop()
    if not item:
        click.echo("Queue is empty.")
        return

    platform = item["platform"]
    query = item["query"]
    season = item.get("season")
    episode = item.get("episode")

    try:
        content_id = do_resolve(platform, query, season, episode)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    d = _get_driver(ctx.obj["tv_name"])
    app_id, name = resolve_app(platform, d.platform)

    async def _do():
        await d.connect()
        if platform.lower() == "netflix":
            try:
                await d.close_app(app_id)
                import asyncio
                await asyncio.sleep(2)
            except Exception:
                pass
        await d.launch_app_deep(app_id, content_id)

    _run(_do())
    _cache.record_play(platform, query, content_id, season, episode)

    desc = query
    if season and episode:
        desc += f" S{season}E{episode}"
    click.echo(f"▶ Playing {desc} on {name} (content: {content_id})")


@queue_group.command("skip")
def queue_skip_cmd():
    """Skip the current queue item (remove without playing)."""
    from smartest_tv import cache as _cache
    items = _cache.queue_show()
    if not items:
        click.echo("Queue is empty.")
        return
    skipped = items[0]
    _cache.queue_skip()
    desc = skipped["query"]
    if skipped.get("season") and skipped.get("episode"):
        desc += f" S{skipped['season']}E{skipped['episode']}"
    click.echo(f"Skipped: [{skipped['platform']}] {desc}")

    remaining = _cache.queue_show()
    if remaining:
        next_item = remaining[0]
        next_desc = next_item["query"]
        if next_item.get("season") and next_item.get("episode"):
            next_desc += f" S{next_item['season']}E{next_item['episode']}"
        click.echo(f"Next: [{next_item['platform']}] {next_desc}")
    else:
        click.echo("Queue is now empty.")


@queue_group.command("clear")
def queue_clear_cmd():
    """Clear the entire play queue."""
    from smartest_tv import cache as _cache
    _cache.queue_clear()
    click.echo("Queue cleared.")


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

    if p == "netflix" and season and first_ep_id and count:
        cache.put_netflix_show(slug, title_id or 0, season, first_ep_id, count)
        last_ep_id = first_ep_id + count - 1
        click.echo(f"Cached: {query} S{season} episodes {first_ep_id}–{last_ep_id} ({count} eps)")
    elif content_id:
        cache.put(p, slug, content_id)
        click.echo(f"Cached: {query} → {content_id}")
    else:
        click.echo("❌ Need --content-id or (--season + --first-ep-id + --count)", err=True)
        sys.exit(1)


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
        _output(result, ctx.obj["fmt"])
    else:
        click.echo("(not cached)", err=True)
        sys.exit(1)


@cache_group.command("show")
@click.pass_context
def cache_show(ctx):
    """Show all cached content IDs."""
    from smartest_tv import cache

    data = cache._load()
    if not data:
        click.echo("Cache is empty.")
        return
    _output(data, ctx.obj["fmt"])


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
        click.echo("Nothing to contribute. Play some content first.", err=True)
        sys.exit(1)

    click.echo(json.dumps(clean, ensure_ascii=False, indent=2))
    click.echo("", err=True)
    click.echo("☝ Copy this and submit a PR to:", err=True)
    click.echo("  https://github.com/Hybirdss/smartest-tv", err=True)
    click.echo("  Add entries to community-cache.json", err=True)


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

    for name, scene in scenes.items():
        tag = "" if name in BUILTIN_SCENES else " [custom]"
        click.echo(f"  {name}{tag}")
        click.echo(f"    {scene.get('description', '')}")
        for step in scene.get("steps", []):
            action = step.get("action")
            if action == "volume":
                click.echo(f"      volume -> {step.get('value')}")
            elif action == "notify":
                click.echo(f"      notify -> {step.get('message')}")
            elif action == "screen_off":
                click.echo(f"      screen off")
            elif action == "screen_on":
                click.echo(f"      screen on")
            elif action == "play":
                click.echo(f"      play {step.get('platform')} \"{step.get('query')}\"")
            elif action == "webhook":
                click.echo(f"      webhook -> {step.get('url')}")
            else:
                click.echo(f"      {action}")


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
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    for msg in results:
        click.echo(f"  {msg}")
    click.echo(f"Scene '{name}' done.")


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
        click.echo(f"❌ '{name}' is a built-in scene. Choose a different name.", err=True)
        sys.exit(1)

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
        click.echo("No steps added. Scene not saved.")
        return

    save_custom_scene(name, description, steps)
    click.echo(f"Scene '{name}' saved with {len(steps)} step(s).")


@scene_group.command("delete")
@click.argument("name")
def scene_delete_cmd(name):
    """Delete a custom scene.

    Example:
        stv scene delete my-scene
    """
    from smartest_tv.scenes import delete_custom_scene

    try:
        delete_custom_scene(name)
        click.echo(f"Scene '{name}' deleted.")
    except KeyError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)


# -- Multi TV Management -----------------------------------------------------


@main.group("multi")
def multi_group():
    """Manage multiple TVs."""


@multi_group.command("list")
@click.pass_context
def multi_list(ctx):
    """List all configured TVs and their status."""
    tvs = list_tvs()
    if not tvs:
        click.echo("No TVs configured. Run: stv setup")
        return
    if ctx.obj["fmt"] == "json":
        _output(tvs, "json")
    else:
        for tv in tvs:
            default_marker = " (default)" if tv.get("default") else ""
            mac_str = f"  mac={tv['mac']}" if tv.get("mac") else ""
            click.echo(f"  {tv['name']}: {tv['platform'].upper()} @ {tv['ip']}{mac_str}{default_marker}")


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
    if platform == "remote" and not url:
        click.echo("❌ Remote TVs require --url. Example: --url http://friend-ip:8911", err=True)
        sys.exit(1)
    if platform != "remote" and not ip:
        click.echo("❌ Local TVs require --ip.", err=True)
        sys.exit(1)

    try:
        add_tv(name, platform, ip or url, mac=mac, default=is_default)
        if platform == "remote":
            click.echo(f"Added remote TV '{name}': {url}")
        else:
            default_str = " (set as default)" if is_default else ""
            click.echo(f"Added TV '{name}': {platform.upper()} @ {ip}{default_str}")
    except Exception as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


@multi_group.command("remove")
@click.argument("name")
def multi_remove(name):
    """Remove a TV from the config.

    Example:
        stv multi remove bedroom
    """
    try:
        remove_tv(name)
        click.echo(f"Removed TV '{name}'.")
    except KeyError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


@multi_group.command("default")
@click.argument("name")
def multi_default(name):
    """Set the default TV.

    Example:
        stv multi default living-room
    """
    try:
        set_default_tv(name)
        click.echo(f"Default TV set to '{name}'.")
    except KeyError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


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
    if not groups:
        click.echo("No groups configured.")
        click.echo("Create one: stv group create party living-room bedroom")
        return

    if ctx.obj["fmt"] == "json":
        _output(groups, "json")
    else:
        for name, members in groups.items():
            click.echo(f"  {name}: {', '.join(members)}")


@group_group.command("create")
@click.argument("name")
@click.argument("members", nargs=-1, required=True)
def group_create_cmd(name, members):
    """Create a TV group.

    Examples:
        stv group create party living-room bedroom
        stv group create everywhere living-room bedroom friend-tv
    """
    try:
        save_group(name, list(members))
        click.echo(f"Group '{name}' created: {', '.join(members)}")
    except (ValueError, KeyError) as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


@group_group.command("delete")
@click.argument("name")
def group_delete_cmd(name):
    """Delete a TV group.

    Example:
        stv group delete party
    """
    try:
        delete_group(name)
        click.echo(f"Group '{name}' deleted.")
    except KeyError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
