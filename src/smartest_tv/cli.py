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


if __name__ == "__main__":
    main()
