"""Interactive setup wizard for smartest-tv.

`stv setup` — discovers TV, pairs, saves config, tests, detects AI client.
Zero questions. Zero env vars. Just works.
"""

from __future__ import annotations

import asyncio
import shutil
import sys

import click

from smartest_tv.config import save as save_config


def run_setup(ip: str | None = None) -> None:
    """Run the full interactive setup."""
    click.echo()

    if ip:
        click.echo(f"🔍 Connecting to {ip}...")
        click.echo()
        tvs = asyncio.run(_probe_ip(ip))
    else:
        click.echo("🔍 Scanning your network for smart TVs...")
        click.echo()
        tvs = asyncio.run(_discover_all())

    if not tvs:
        click.echo("❌ No TV found on your network.")
        click.echo()
        click.echo("   Checklist:")
        click.echo("   • Is the TV turned on?")
        click.echo("   • Are TV and computer on the same Wi-Fi?")
        if not ip:
            click.echo("   • Try: stv setup --ip 192.168.1.XXX")
        click.echo()
        sys.exit(1)

    if len(tvs) == 1:
        tv = tvs[0]
        click.echo(f"   Found: {tv['name']} [{tv['platform'].upper()}]")
        click.echo()
    else:
        click.echo(f"Found {len(tvs)} TVs:")
        for i, t in enumerate(tvs, 1):
            click.echo(f"  {i}. {t['name']} ({t['ip']}) [{t['platform'].upper()}]")
        click.echo()
        choice = click.prompt("Which one?", type=int, default=1)
        tv = tvs[choice - 1]

    click.echo(f"📺 {tv['name']}")
    click.echo(f"   {tv['platform'].upper()} • {tv['ip']}")
    click.echo()

    # Platform-specific pairing guidance
    platform = tv["platform"]

    if platform == "roku":
        click.echo("   No pairing needed — Roku is open by default. ✨")
    elif platform in ("android", "firetv"):
        click.echo("   📋 Quick one-time setup on your TV:")
        click.echo("      Settings → About → tap 'Build number' 7 times")
        click.echo("      → Developer Options → enable 'ADB debugging'")
        click.echo()
        click.prompt("   Ready? Press Enter", default="", show_default=False)
        click.echo()
        click.echo("   👀 Accept 'Allow USB debugging?' on your TV.")
    else:
        click.echo("   👀 A popup just appeared on your TV.")
        click.echo("   Press OK — this is the only time you need the remote.")
        if platform == "lg":
            click.echo("   💡 No remote? Use the LG ThinQ app on your phone.")
        elif platform == "samsung":
            click.echo("   💡 No remote? Use the SmartThings app on your phone.")

    click.echo()
    click.echo("   ⏳ Connecting...", nl=False)

    try:
        mac = asyncio.run(_pair_tv(tv))
        tv["mac"] = mac
    except Exception as e:
        click.echo(" ❌")
        click.echo()
        click.echo(f"   Connection failed: {e}")
        click.echo("   Make sure you approved the popup on your TV.")
        click.echo("   Run `stv setup` again to retry.")
        sys.exit(1)

    click.echo(" ✅")
    click.echo()

    # Save config
    path = save_config(
        platform=tv["platform"],
        ip=tv["ip"],
        mac=tv.get("mac", ""),
        name=tv.get("name", ""),
    )
    click.echo(f"   💾 Config saved to {path}")

    # Test notification
    click.echo("   🧪 Sending test notification...", nl=False)
    try:
        asyncio.run(_test_notify(tv))
        click.echo(" look at your TV! 👋")
    except Exception:
        click.echo(" (notification not supported, but connection works)")

    click.echo()

    # Detect AI clients
    _detect_ai_clients()

    # Done
    click.echo("🎉 You're all set! Your voice is now the remote.")
    click.echo()
    click.echo("   stv launch youtube dQw4w9WgXcQ    # Play a video")
    click.echo("   stv volume 30                      # Set volume")
    click.echo("   stv off                             # Good night")
    click.echo()


async def _probe_ip(ip: str) -> list[dict]:
    """Probe a specific IP for TV services and detect platform."""
    # Try each platform driver in order
    for platform, port in [("lg", 3000), ("samsung", 8001), ("roku", 8060)]:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=2.0,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            name = _make_name(platform, ip)
            return [{"ip": ip, "name": name, "platform": platform, "raw": ""}]
        except Exception:
            pass

    # Try ADB
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, 5555),
            timeout=2.0,
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return [{"ip": ip, "name": f"Android TV ({ip})", "platform": "android", "raw": ""}]
    except Exception:
        pass

    return []


async def _discover_all() -> list[dict]:
    """Discover TVs on the network with platform auto-detection."""
    try:
        from smartest_tv.discovery import discover
        return await discover(timeout=3.0)
    except Exception:
        return []


def _make_name(platform: str, ip: str) -> str:
    brand = {"lg": "LG", "samsung": "Samsung", "roku": "Roku"}.get(platform, "Smart")
    return f"{brand} TV ({ip})"


async def _pair_tv(tv: dict) -> str:
    """Connect and pair with the TV. Returns MAC if available."""
    platform = tv["platform"]
    ip = tv["ip"]

    if platform == "lg":
        from smartest_tv.drivers.lg import LGDriver
        driver = LGDriver(ip=ip)
        await driver.connect()
        info = await driver.info()
        await driver.disconnect()
        return info.mac or ""

    elif platform == "samsung":
        from smartest_tv.drivers.samsung import SamsungDriver
        driver = SamsungDriver(ip=ip)
        await driver.connect()
        info = await driver.info()
        await driver.disconnect()
        return info.mac or ""

    elif platform in ("android", "firetv"):
        from smartest_tv.drivers.android import AndroidDriver
        driver = AndroidDriver(ip=ip)
        await driver.connect()
        await driver.disconnect()
        return ""

    elif platform == "roku":
        from smartest_tv.drivers.roku import RokuDriver
        driver = RokuDriver(ip=ip)
        await driver.connect()
        info = await driver.info()
        await driver.disconnect()
        return info.mac or ""

    return ""


async def _test_notify(tv: dict) -> None:
    """Send a test notification to the TV."""
    platform = tv["platform"]
    ip = tv["ip"]

    if platform == "lg":
        from smartest_tv.drivers.lg import LGDriver
        driver = LGDriver(ip=ip)
        await driver.connect()
        await driver.notify("👋 Hello from smartest-tv!")
        await driver.disconnect()


def _detect_ai_clients() -> None:
    """Detect installed AI clients and offer to configure them."""
    import pathlib

    claude_code = shutil.which("claude")
    cursor_config = any(
        p.exists()
        for p in [
            pathlib.Path.home() / ".cursor" / "mcp.json",
            pathlib.Path.home() / ".cursor" / "settings.json",
        ]
    )

    if claude_code:
        click.echo("   🤖 Detected Claude Code")
        click.echo("      Run: claude mcp add stv -- uvx stv")
        click.echo()

    if cursor_config:
        click.echo("   🤖 Detected Cursor")
        click.echo('      Add to MCP settings: {"command": "uvx", "args": ["stv"]}')
        click.echo()

    if not claude_code and not cursor_config:
        click.echo("   💡 To use with an AI assistant:")
        click.echo("      Claude Code: claude mcp add stv -- uvx stv")
        click.echo("      Other: see README for MCP config")
        click.echo()
