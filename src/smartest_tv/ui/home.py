"""Home dashboard — what you see when you type `stv` with no args.

Four states:
  1. first_run        — no config, show welcome + auto-setup CTA
  2. connected        — config valid + TV reachable, show Now Playing + suggestions
  3. offline          — config valid but TV unreachable, show troubleshooting
  4. error            — config corrupt or broken, show error panel + recovery

This module is pure rendering; cli.py decides which state applies.
"""
from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smartest_tv.ui.common import boxed, volume_bar
from smartest_tv.ui.theme import ICONS, app_display_name, app_icon

# ============================================================================
# State 1: First run — no config exists
# ============================================================================


def render_home_first_run() -> Panel:
    """Shown when no config.toml exists. Invites auto-setup."""
    title = Text("smartest-tv", style="primary")
    title.append("  ", style="")
    title.append("v0.10.0", style="muted")

    pitch = Text("Talk to your TV. It listens.", style="accent")

    welcome = Text()
    welcome.append(f"{ICONS['tv']}  ", style="accent")
    welcome.append("Welcome! ", style="primary")
    welcome.append("No TV connected yet.", style="muted")

    next_line = Text()
    next_line.append(f"{ICONS['bolt']}  ", style="accent")
    next_line.append("Run ", style="muted")
    next_line.append("stv setup", style="bold primary")
    next_line.append(" and I'll find your TV automatically.", style="muted")

    hint = Text()
    hint.append("    ", style="")
    hint.append("Takes 30 seconds. No IP addresses, no pairing codes.", style="dim")

    footer = Text()
    footer.append(f"{ICONS['info']}  ", style="accent")
    footer.append("Need help? ", style="muted")
    footer.append("stv --help", style="primary")

    body = Group(
        title,
        pitch,
        Text(""),
        welcome,
        Text(""),
        next_line,
        hint,
        Text(""),
        footer,
    )
    return Panel(
        Padding(body, (1, 2)),
        title=f"{ICONS['tv']} smartest-tv",
        title_align="left",
        border_style="primary",
        box=box.DOUBLE,
        padding=(0, 0),
    )


# ============================================================================
# State 2: Connected — TV alive, status known
# ============================================================================


def render_home_connected(
    tv_label: str,
    status: dict[str, Any],
    suggestions: list[dict[str, str]],
) -> Group:
    """Now Playing card + contextual suggestions.

    Args:
        tv_label: Display name like "거실 TV"
        status: { platform, current_app, volume, muted, sound_output }
        suggestions: [{ icon, command, description }, ...]
    """
    # --- Now Playing card (reuses logic from render_status but tighter) ---
    platform = (status.get("platform") or "?").upper()
    app_id = status.get("current_app") or ""
    app_name = app_display_name(app_id)
    icon = app_icon(app_id)
    volume = int(status.get("volume", 0) or 0)
    muted = bool(status.get("muted", False))

    header = Text()
    header.append(f"{tv_label}  ", style="primary")
    header.append(f"[{platform}]", style="muted")

    power_line = Text()
    power_line.append(f"{ICONS['on']} ON", style="on")
    power_line.append("   ")
    power_line.append(f"{icon}  ", style="accent")
    if app_name == "Idle":
        power_line.append("Idle", style="muted")
    else:
        power_line.append(app_name, style="bold")

    vol_line = volume_bar(volume, muted=muted)

    now_playing = boxed(
        Group(header, Text(""), power_line, Text(""), vol_line),
        title=f"{ICONS['tv']} Now Playing",
    )

    # --- Suggestions card ---
    if suggestions:
        suggestion_lines: list = []
        for s in suggestions:
            line = Text()
            line.append(f"  {s.get('icon', '▸')}  ", style="accent")
            line.append(s.get("command", ""), style="bold primary")
            desc = s.get("description", "")
            if desc:
                line.append(f"  — {desc}", style="muted")
            suggestion_lines.append(line)

        footer = Text()
        footer.append(f"  {ICONS['info']}  ", style="muted")
        footer.append("stv --help", style="dim")
        footer.append("  for all commands", style="dim")

        suggestions_panel = boxed(
            Group(*suggestion_lines, Text(""), footer),
            title=f"{ICONS['star']} What's next?",
        )
        return Group(now_playing, suggestions_panel)

    return Group(now_playing)


# ============================================================================
# State 3: Offline — TV unreachable
# ============================================================================


def render_home_offline(tv_label: str, platform: str, ip: str, error: str = "") -> Panel:
    """Config is valid but the TV didn't respond."""
    header = Text()
    header.append(f"{tv_label}  ", style="primary")
    header.append(f"[{platform.upper()} · {ip}]", style="muted")

    status = Text()
    status.append(f"{ICONS['off']} OFF or unreachable", style="off")

    if error:
        status.append(f"  ({error[:50]})", style="dim")

    Text("")

    suggestions = Table(box=None, show_header=False, pad_edge=False, show_edge=False)
    suggestions.add_column(style="accent", no_wrap=True)
    suggestions.add_column(style="primary", no_wrap=True)
    suggestions.add_column(style="muted")
    suggestions.add_row(f"{ICONS['bolt']}", "stv on", "Wake the TV (Wake-on-LAN)")
    suggestions.add_row(f"{ICONS['doctor']}", "stv doctor", "Diagnose the connection")
    suggestions.add_row(f"{ICONS['tv']}", "stv setup", "Reconfigure or change TV")

    return boxed(
        Group(header, Text(""), status, Text(""), suggestions),
        title=f"{ICONS['tv']} smartest-tv",
    )


# ============================================================================
# State 4: NL fallback hint — user typed something we couldn't parse
# ============================================================================


def render_nl_hint(user_input: str, suggestions: list[str]) -> Panel:
    """Shown when `stv <garbage>` doesn't match a command or NL pattern."""
    query = Text()
    query.append(f"{ICONS['search']}  ", style="accent")
    query.append('Not sure what you meant by ', style="muted")
    query.append(f'"{user_input}"', style="primary")

    sep = Text("")

    hint_header = Text("Try one of these:", style="accent")

    lines: list = [query, sep, hint_header]
    for s in suggestions:
        line = Text(f"  → {s}", style="primary")
        lines.append(line)

    lines.append(Text(""))
    lines.append(Text("Or see all commands:  stv --help", style="dim"))

    return boxed(Group(*lines), title=f"{ICONS['info']} Didn't understand", border="warning")


# ============================================================================
# Live setup progress panels (used during auto-pair)
# ============================================================================


def render_discovering() -> Panel:
    """Live panel: scanning network for TVs."""
    body = Text()
    body.append(f"{ICONS['search']}  ", style="accent")
    body.append("Scanning your network for smart TVs...", style="primary")
    sub = Text("    SSDP / mDNS / port probe", style="dim")
    return boxed(Group(body, sub), title=f"{ICONS['tv']} smartest-tv setup")


def render_found_tv(tv_name: str, platform: str, ip: str) -> Panel:
    """Live panel: TV found, about to pair."""
    found = Text()
    found.append(f"{ICONS['ok']}  ", style="success")
    found.append("Found ", style="muted")
    found.append(tv_name, style="primary")
    found.append(f"  [{platform.upper()} · {ip}]", style="muted")

    pair_hint = Text()
    pair_hint.append(f"\n{ICONS['bolt']}  ", style="accent")
    pair_hint.append("Please press ", style="muted")
    pair_hint.append("OK", style="bold primary")
    pair_hint.append(" on your TV remote to pair.", style="muted")

    wait = Text("    (This is a one-time step.)", style="dim")

    return boxed(
        Group(found, pair_hint, wait),
        title=f"{ICONS['tv']} smartest-tv setup",
    )


def render_paired(tv_name: str) -> Panel:
    """Live panel: pairing succeeded."""
    ok = Text()
    ok.append(f"{ICONS['ok']}  ", style="success")
    ok.append("Paired with ", style="muted")
    ok.append(tv_name, style="primary")
    ok.append("!", style="muted")

    next_hint = Text("\n    Type ", style="dim")
    next_hint.append("stv", style="primary")
    next_hint.append(" to see what's playing.", style="dim")

    return boxed(
        Group(ok, next_hint),
        title=f"{ICONS['tv']} You're all set",
    )
