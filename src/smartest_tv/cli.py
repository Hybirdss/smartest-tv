"""smartest-tv CLI — AI-first TV control from the terminal.

Usage:
    tv status
    tv launch netflix 82656797
    tv volume 30
    tv off
    tv apps --format json
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import click

from smartest_tv.apps import resolve_app
from smartest_tv.drivers.base import TVDriver


def _get_driver() -> TVDriver:
    """Create driver from env vars."""
    platform = os.environ.get("TV_PLATFORM", "lg")

    if platform == "lg":
        from smartest_tv.drivers.lg import LGDriver

        return LGDriver(
            ip=os.environ.get("TV_IP", ""),
            mac=os.environ.get("TV_MAC", ""),
            key_file=os.environ.get("TV_KEY_FILE", ""),
        )
    elif platform == "samsung":
        from smartest_tv.drivers.samsung import SamsungDriver

        return SamsungDriver(ip=os.environ.get("TV_IP", ""))
    elif platform in ("android", "firetv"):
        from smartest_tv.drivers.android import AndroidDriver

        return AndroidDriver(ip=os.environ.get("TV_IP", ""))
    elif platform == "roku":
        from smartest_tv.drivers.roku import RokuDriver

        return RokuDriver(ip=os.environ.get("TV_IP", ""))
    else:
        click.echo(f"Unknown platform: {platform}", err=True)
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
    """smartest-tv — Control any smart TV from the terminal."""
    ctx.ensure_object(dict)
    ctx.obj["fmt"] = fmt


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
