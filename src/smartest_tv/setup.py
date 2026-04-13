"""Zero-friction setup wizard for smartest-tv.

`stv setup` — discovers TV, pairs, saves config, tests. Rich UI throughout.
Zero questions when there's exactly one TV. One prompt when there are many.
"""

from __future__ import annotations

import asyncio
import shutil
import sys

import click
from rich.text import Text

from smartest_tv.config import save as save_config
from smartest_tv.ui import console as _ui_console
from smartest_tv.ui.common import boxed
from smartest_tv.ui.home import render_found_tv
from smartest_tv.ui.render import render_error
from smartest_tv.ui.theme import ICONS


def _print(r):
    _ui_console.print(r)


def run_setup(ip: str | None = None) -> None:
    """Run the full interactive setup."""
    _ui_console.print()

    # --- Discover ---
    if ip:
        with _ui_console.status(
            f"[primary]{ICONS['search']} Probing {ip}...[/primary]",
            spinner="dots",
        ):
            tvs = asyncio.run(_probe_ip(ip))
    else:
        with _ui_console.status(
            f"[primary]{ICONS['search']} Scanning your network for smart TVs...[/primary]",
            spinner="dots",
        ):
            tvs = asyncio.run(_discover_all())

    if not tvs:
        _print(render_error(
            "No TV found on your network.",
            hint=(
                "Checklist:\n"
                "  • Is the TV turned on?\n"
                "  • Are TV and computer on the same Wi-Fi?\n"
                + ("  • Try: stv setup --ip 192.168.1.XXX" if not ip else "  • Double-check the IP address")
            ),
        ))
        sys.exit(1)

    # --- Select ---
    if len(tvs) == 1:
        tv = tvs[0]
    else:
        _ui_console.print(f"\n[accent]Found {len(tvs)} TVs:[/accent]")
        for i, t in enumerate(tvs, 1):
            _ui_console.print(
                f"  [primary]{i}[/primary]. {t['name']}  "
                f"[muted]{t['platform'].upper()} · {t['ip']}[/muted]"
            )
        _ui_console.print()
        choice = click.prompt(click.style("Which one?", fg="magenta"), type=int, default=1)
        tv = tvs[choice - 1]

    _print(render_found_tv(tv['name'], tv['platform'], tv['ip']))

    # --- Pair ---
    platform = tv["platform"]
    pair_hint_msg = _pairing_hint(platform)
    if pair_hint_msg:
        _ui_console.print(f"[muted]   {pair_hint_msg}[/muted]\n")

    if platform in ("android", "firetv"):
        click.prompt(
            click.style("   Ready? Press Enter", fg="cyan"),
            default="", show_default=False,
        )

    try:
        with _ui_console.status(
            f"[primary]{ICONS['bolt']} Connecting to {tv['name']}...[/primary]",
            spinner="dots",
        ):
            mac = asyncio.run(_pair_tv(tv))
        tv["mac"] = mac
    except Exception as e:
        _print(render_error(
            f"Connection failed: {e}",
            hint=(
                "Make sure you approved the popup on your TV.\n"
                "Run `stv setup` again to retry."
            ),
        ))
        sys.exit(1)

    # --- Save config ---
    path = save_config(
        platform=tv["platform"],
        ip=tv["ip"],
        mac=tv.get("mac", ""),
        name=tv.get("name", ""),
    )

    # --- Test notification (non-blocking if unsupported) ---
    notify_ok = False
    try:
        with _ui_console.status(
            f"[primary]{ICONS['info']} Sending test notification...[/primary]",
            spinner="dots",
        ):
            asyncio.run(_test_notify(tv))
        notify_ok = True
    except Exception:
        pass

    # --- Success panel ---
    from rich.console import Group
    success_lines: list = [
        Text(),
        Text.from_markup(
            f"[success]{ICONS['ok']}[/success]  Paired with [primary]{tv['name']}[/primary]"
        ),
        Text.from_markup(f"[muted]   Config saved to[/muted]  [dim]{path}[/dim]"),
    ]
    if notify_ok:
        success_lines.append(
            Text.from_markup(
                f"[success]{ICONS['ok']}[/success]  "
                "[muted]Test notification sent — check your TV! [/muted][accent]👋[/accent]"
            )
        )
    success_lines.append(Text())
    success_lines.append(Text.from_markup("[accent]Try these next:[/accent]"))
    success_lines.append(Text.from_markup(
        "  [primary]stv[/primary]                          [muted]— see what's on[/muted]"
    ))
    success_lines.append(Text.from_markup(
        "  [primary]stv play netflix \"Wednesday\"[/primary]   [muted]— play by name[/muted]"
    ))
    success_lines.append(Text.from_markup(
        "  [primary]stv scene movie-night[/primary]         [muted]— cinema mode[/muted]"
    ))

    # --- Cache contribution notice ---
    success_lines.append(Text())
    success_lines.append(Text.from_markup(
        "[muted]Community cache:[/muted] [success]ON[/success] "
        "[muted]— anonymous content IDs only, no personal data.[/muted]"
    ))
    success_lines.append(Text.from_markup(
        "[muted]Disable:[/muted] [dim]export STV_NO_CONTRIBUTE=1[/dim]"
    ))

    _print(boxed(Group(*success_lines), title=f"{ICONS['tv']} You're all set"))

    # --- Detect AI clients ---
    _detect_ai_clients()


def _pairing_hint(platform: str) -> str:
    """Return a one-line pairing hint for the given platform."""
    if platform == "roku":
        return "No pairing needed — Roku is open by default."
    if platform in ("android", "firetv"):
        return (
            "Your TV will show a 6-digit PIN — enter it below when prompted.\n"
            "   No developer mode needed. Uses the same protocol as the\n"
            "   Google TV mobile app."
        )
    if platform == "lg":
        return "A popup just appeared on your TV. Press OK.\n   (No remote? Use the LG ThinQ app on your phone.)"
    if platform == "samsung":
        return "A popup just appeared on your TV. Press OK.\n   (No remote? Use the SmartThings app.)"
    return "A popup just appeared on your TV. Press OK."


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
        try:
            # Try existing pairing first
            await driver.connect()
            await driver.disconnect()
            return ""
        except RuntimeError:
            pass  # Not paired — run pairing flow

        # Start pairing: TV will show a 6-digit PIN
        remote = await driver.start_pairing()
        import click
        pin = click.prompt(
            "\n  A 6-digit PIN is shown on your TV. Enter it here",
            type=str,
            show_default=False,
        ).strip()
        await driver.finish_pairing(remote, pin)
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

    if claude_code or cursor_config:
        _ui_console.print(f"\n[accent]{ICONS['info']}  AI assistant detected[/accent]")
        if claude_code:
            _ui_console.print(
                "   [primary]claude mcp add stv -- uvx stv[/primary]     "
                "[muted]— wire stv into Claude Code[/muted]"
            )
        if cursor_config:
            _ui_console.print(
                '   [primary]Cursor MCP settings:[/primary] [muted]{"command": "uvx", "args": ["stv"]}[/muted]'
            )
