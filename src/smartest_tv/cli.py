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
from smartest_tv.config import get_tv_config
from smartest_tv.drivers.base import TVDriver


def _get_driver() -> TVDriver:
    """Create driver from config file (or env var overrides)."""
    tv = get_tv_config()
    platform = tv.get("platform", "")

    if not platform:
        click.echo("❌ No TV configured. Run: stv setup", err=True)
        sys.exit(1)

    if platform == "lg":
        from smartest_tv.drivers.lg import LGDriver
        return LGDriver(ip=tv["ip"], mac=tv.get("mac", ""))
    elif platform == "samsung":
        from smartest_tv.drivers.samsung import SamsungDriver
        return SamsungDriver(ip=tv["ip"], mac=tv.get("mac", ""))
    elif platform in ("android", "firetv"):
        from smartest_tv.drivers.android import AndroidDriver
        return AndroidDriver(ip=tv["ip"])
    elif platform == "roku":
        from smartest_tv.drivers.roku import RokuDriver
        return RokuDriver(ip=tv["ip"])
    else:
        click.echo(f"❌ Unknown platform: {platform}. Run: stv setup", err=True)
        sys.exit(1)


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
@click.pass_context
def main(ctx, fmt):
    """stv — Talk to your TV. It listens."""
    ctx.ensure_object(dict)
    ctx.obj["fmt"] = fmt


# -- Setup & Diagnostics ----------------------------------------------------


@main.command()
def setup():
    """Set up your TV. Discovers, pairs, and configures everything."""
    from smartest_tv.setup import run_setup
    run_setup()


@main.command()
@click.pass_context
def doctor(ctx):
    """Check if everything is working."""
    tv = get_tv_config()
    if not tv.get("platform"):
        click.echo("❌ No TV configured. Run: stv setup")
        return

    click.echo(f"📺 {tv.get('name', 'TV')} ({tv['platform'].upper()}, {tv['ip']})")
    click.echo()

    d = _get_driver()
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
def on():
    """Turn on the TV."""
    d = _get_driver()
    _run(d.connect())
    _run(d.power_on())
    click.echo("TV turning on.")


@main.command()
def off():
    """Turn off the TV."""
    d = _get_driver()

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
    """Get or set volume. No argument = show current."""
    d = _get_driver()

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
def mute():
    """Toggle mute."""
    d = _get_driver()

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
def launch(app, content_id):
    """Launch an app, optionally with deep link content ID."""
    d = _get_driver()

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
def close(app):
    """Close a running app."""
    d = _get_driver()

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
    d = _get_driver()

    async def _do():
        await d.connect()
        return [{"id": a.id, "name": a.name} for a in await d.list_apps()]

    _output(_run(_do()), ctx.obj["fmt"])


# -- Media -------------------------------------------------------------------


@main.command()
def play():
    """Resume playback."""
    d = _get_driver()
    _run(d.connect())
    _run(d.play())
    click.echo("Playing.")


@main.command()
def pause():
    """Pause playback."""
    d = _get_driver()
    _run(d.connect())
    _run(d.pause())
    click.echo("Paused.")


# -- Status ------------------------------------------------------------------


@main.command()
@click.pass_context
def status(ctx):
    """Show TV status."""
    d = _get_driver()

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
    d = _get_driver()

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
def notify(message):
    """Show a notification on the TV."""
    d = _get_driver()

    async def _do():
        await d.connect()
        await d.notify(message)

    _run(_do())
    click.echo(f"Sent: {message}")


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
def play(platform, query, season, episode, title_id):
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

    # Step 1: Resolve content ID
    try:
        content_id = do_resolve(platform, query_str, season, episode, title_id)
    except ValueError as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(1)

    # Step 2: Launch on TV
    d = _get_driver()
    app_id, name = resolve_app(platform, d.platform)

    async def _do():
        await d.connect()
        # Netflix requires close-then-relaunch for deep links
        if platform.lower() == "netflix":
            try:
                await d.close_app(app_id)
                import asyncio
                await asyncio.sleep(2)
            except Exception:
                pass
        await d.launch_app_deep(app_id, content_id)

    _run(_do())
    desc = f"{query_str}"
    if season and episode:
        desc += f" S{season}E{episode}"
    click.echo(f"▶ Playing {desc} on {name} (content: {content_id})")


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


if __name__ == "__main__":
    main()
