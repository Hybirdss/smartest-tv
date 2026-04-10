"""Render functions — one per command/page.

Each render_* function takes raw data (dict / list) and returns a Rich
renderable (Panel, Table, Group, Text). They do NOT print — the caller
in cli.py does `console.print(render_status(data))`.

This module has ZERO click/driver dependencies. Pure rendering.
"""
from __future__ import annotations

import time
from typing import Any

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from smartest_tv.ui.common import (
    boxed,
    error_panel,
    kv_table,
    simple_table,
    status_dot,
    success_line,
    volume_bar,
)
from smartest_tv.ui.theme import (
    ICONS,
    app_display_name,
    app_icon,
    get_theme,
)

# ============================================================================
# Core / Status
# ============================================================================


def render_status(data: dict[str, Any], tv_name: str = "TV") -> Panel:
    """`stv status` — Now Playing card.

    data keys: platform, current_app, volume, muted, sound_output
    """
    theme = get_theme()
    platform = (data.get("platform") or "?").upper()
    app_id = data.get("current_app") or ""
    app_name = app_display_name(app_id)
    icon = app_icon(app_id)
    volume = data.get("volume", 0) or 0
    muted = bool(data.get("muted", False))
    sound = data.get("sound_output", "")

    # Header: TV name + platform badge
    header = Text()
    header.append(f"{tv_name}  ", style="primary")
    header.append(f"[{platform}]", style="muted")

    # Power + App row
    power = status_dot(True)  # if status responded, TV is on
    app_text = Text()
    app_text.append(f"{icon}  ", style="accent")
    if app_name == "Idle":
        app_text.append("Idle", style="muted")
    else:
        app_text.append(app_name, style=f"bold {theme['text']}")

    power_app_row = Text()
    power_app_row.append_text(power)
    power_app_row.append("   ")
    power_app_row.append_text(app_text)

    # Volume row
    vol_row = volume_bar(int(volume), muted=muted)

    # Sound output (optional, muted)
    body_items: list = [header, Text(""), power_app_row, Text(""), vol_row]
    if sound:
        body_items.append(Text(""))
        body_items.append(Text(f"Output: {sound}", style="muted"))

    return boxed(
        Group(*body_items),
        title=f"{ICONS['tv']} Now Playing",
    )


def render_info(data: dict[str, Any]) -> Panel:
    """`stv info` — TV system info."""
    pairs = {
        "Name":     data.get("name") or "-",
        "Platform": (data.get("platform") or "?").upper(),
        "Model":    data.get("model") or "-",
        "Firmware": data.get("firmware") or "-",
        "IP":       data.get("ip") or "-",
    }
    return boxed(kv_table(pairs), title=f"{ICONS['tv']} System Info")


def render_volume(volume: int, muted: bool = False) -> Panel:
    """`stv volume` (no arg) — current volume as a bar panel."""
    return boxed(volume_bar(volume, muted=muted), title=f"{ICONS['volume']} Volume")


# ============================================================================
# Doctor
# ============================================================================


def render_doctor(checks: list[dict[str, Any]], tv_label: str = "") -> Panel:
    """`stv doctor` — hierarchical health tree.

    checks: list of {name, status: "ok"|"warn"|"fail", detail: str}
    """
    tree = Tree(
        Text(f"{ICONS['doctor']}  stv doctor", style="primary"),
        guide_style="muted",
    )
    for c in checks:
        status = c.get("status", "ok")
        name = c.get("name", "?")
        detail = c.get("detail", "")
        if status == "ok":
            label = Text(f"{ICONS['ok']} {name}", style="success")
        elif status == "warn":
            label = Text(f"{ICONS['warn']} {name}", style="warning")
        else:
            label = Text(f"{ICONS['fail']} {name}", style="error")
        if detail:
            label.append(f"  — {detail}", style="muted")
        tree.add(label)

    subtitle = tv_label or None
    return Panel(
        tree,
        title=f"{ICONS['doctor']} Health Check",
        subtitle=subtitle,
        title_align="left",
        subtitle_align="right",
        border_style="primary",
        box=box.ROUNDED,
        padding=(1, 2),
    )


# ============================================================================
# Multi TV / Groups
# ============================================================================


def render_tv_list(tvs: list[dict[str, Any]]) -> Panel:
    """`stv multi list` — TV inventory table."""
    if not tvs:
        return boxed(
            Text("No TVs configured.\nRun: stv setup", style="muted"),
            title=f"{ICONS['tv']} TVs",
        )

    table = simple_table(["", "Name", "Platform", "Address", "MAC"])
    table.columns[0].justify = "center"
    table.columns[0].width = 3

    for tv in tvs:
        is_default = tv.get("default", False)
        marker = Text(ICONS["star"], style="accent") if is_default else Text("")
        name_text = Text(tv.get("name", "?"))
        if is_default:
            name_text.stylize("primary")
        platform = Text((tv.get("platform", "?")).upper(), style="info")
        addr = tv.get("ip", "") or tv.get("url", "") or "-"
        mac = tv.get("mac") or "-"
        table.add_row(marker, name_text, platform, Text(addr, style="muted"), Text(mac, style="dim"))

    footer = Text(f"{len(tvs)} TV{'s' if len(tvs) != 1 else ''} configured", style="muted")
    return boxed(
        Group(table, Text(""), footer),
        title=f"{ICONS['tv']} TVs",
    )


def render_group_list(groups: dict[str, list[str]]) -> Panel:
    """`stv group list` — named TV groups."""
    if not groups:
        return boxed(
            Group(
                Text("No groups configured.", style="muted"),
                Text(""),
                Text("Create one: stv group create party living-room bedroom", style="dim"),
            ),
            title=f"{ICONS['group']} Groups",
        )

    table = simple_table(["Group", "Members", "Count"])
    for name, members in groups.items():
        table.add_row(
            Text(name, style="primary"),
            Text(", ".join(members), style="accent"),
            Text(str(len(members)), style="muted"),
        )
    return boxed(table, title=f"{ICONS['group']} Groups")


# ============================================================================
# Scenes
# ============================================================================

_SCENE_ICONS = {
    "movie-night": ICONS["movie"],
    "kids":        ICONS["kids"],
    "sleep":       ICONS["sleep"],
    "music":       ICONS["music"],
}


def _scene_action_line(step: dict[str, Any]) -> Text:
    """Render a single scene step as a pretty line."""
    action = step.get("action", "?")
    arrow = Text(" → ", style="muted")
    t = Text()
    if action == "volume":
        t.append(f"{ICONS['volume']} volume", style="accent")
        t.append_text(arrow)
        t.append(str(step.get("value", "?")), style="primary")
    elif action == "notify":
        t.append(f"{ICONS['info']}  notify", style="accent")
        t.append_text(arrow)
        t.append(f'"{step.get("message", "")}"', style="success")
    elif action == "screen_off":
        t.append(f"{ICONS['off']}  screen", style="accent")
        t.append_text(arrow)
        t.append("off", style="muted")
    elif action == "screen_on":
        t.append(f"{ICONS['on']}  screen", style="accent")
        t.append_text(arrow)
        t.append("on", style="success")
    elif action == "play":
        t.append(f"{ICONS['play']} play", style="accent")
        t.append_text(arrow)
        plat = step.get("platform", "?")
        t.append(f"{plat}: ", style="info")
        t.append(f'"{step.get("query", "")}"', style="primary")
    elif action == "webhook":
        t.append(f"{ICONS['bolt']} webhook", style="accent")
        t.append_text(arrow)
        t.append(step.get("url", ""), style="muted")
    else:
        t.append(f"  {action}", style="muted")
    return t


def render_scenes(scenes: dict[str, dict[str, Any]], builtin: set[str]) -> Panel:
    """`stv scene list` — scene presets grid."""
    if not scenes:
        return boxed(Text("No scenes.", style="muted"), title=f"{ICONS['scene']} Scenes")

    cards: list = []
    for name, scene in scenes.items():
        icon = _SCENE_ICONS.get(name, ICONS["scene"])
        tag = "" if name in builtin else " [custom]"
        header = Text()
        header.append(f"{icon}  ", style="accent")
        header.append(name, style="primary")
        if tag:
            header.append(tag, style="muted")

        desc = scene.get("description", "")
        lines: list = [header]
        if desc:
            lines.append(Text(f"  {desc}", style="muted"))
        for step in scene.get("steps", []):
            step_line = Text("    ")
            step_line.append_text(_scene_action_line(step))
            lines.append(step_line)
        cards.append(Group(*lines))
        cards.append(Text(""))  # spacer

    # Drop trailing spacer
    if cards and isinstance(cards[-1], Text) and cards[-1].plain == "":
        cards.pop()

    return boxed(Group(*cards), title=f"{ICONS['scene']} Scenes")


def render_scene_run(scene_name: str, messages: list[str]) -> Panel:
    """`stv scene run` — sequential execution trace."""
    lines: list = []
    for msg in messages:
        lines.append(success_line(msg))
    lines.append(Text(""))
    lines.append(Text(f"Scene '{scene_name}' done.", style="primary"))
    return boxed(Group(*lines), title=f"{ICONS['scene']} Running: {scene_name}")


# ============================================================================
# Trending / What's On
# ============================================================================


def _format_views(n) -> str:
    if n is None:
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def render_trending(
    netflix: list[dict] | None = None,
    youtube: list[dict] | None = None,
) -> Group:
    """`stv whats-on` — Netflix + YouTube trending tables."""
    sections: list = []

    if netflix is not None:
        if netflix:
            table = simple_table(["#", "Title", "Category"])
            table.columns[0].width = 3
            table.columns[0].justify = "right"
            for item in netflix:
                rank = str(item.get("rank", ""))
                title = item.get("title", "")
                category = item.get("category", "")
                table.add_row(
                    Text(rank, style="accent"),
                    Text(title, style="primary"),
                    Text(category, style="muted"),
                )
            sections.append(boxed(
                table,
                title=f"{ICONS['netflix']} Netflix  Top 10",
            ))
        else:
            sections.append(boxed(
                Text("Could not fetch trending data.", style="muted"),
                title=f"{ICONS['netflix']} Netflix",
            ))

    if youtube is not None:
        if youtube:
            table = simple_table(["#", "Channel", "Title", "Views"])
            table.columns[0].width = 3
            table.columns[0].justify = "right"
            table.columns[3].justify = "right"
            for item in youtube:
                rank = str(item.get("rank", ""))
                channel = item.get("channel", "")
                title = item.get("title", "")
                views = _format_views(item.get("view_count"))
                table.add_row(
                    Text(rank, style="accent"),
                    Text(channel, style="info"),
                    Text(title, style="primary"),
                    Text(views, style="muted"),
                )
            sections.append(boxed(
                table,
                title=f"{ICONS['youtube']} YouTube  Trending",
            ))
        else:
            sections.append(boxed(
                Text("Could not fetch trending data.", style="muted"),
                title=f"{ICONS['youtube']} YouTube",
            ))

    return Group(*sections)


# ============================================================================
# Search
# ============================================================================


def render_netflix_search(query: str, result: dict[str, Any]) -> Panel:
    title_id = result.get("title_id", "")
    url = result.get("url", "")
    seasons = result.get("seasons")

    lines: list = [
        Text(query, style="primary"),
        Text(""),
    ]
    lines.append(kv_table({
        "Netflix ID": str(title_id),
        "URL":        url,
    }))

    if seasons:
        lines.append(Text(""))
        lines.append(Text(f"{seasons} season{'s' if seasons != 1 else ''}:", style="accent"))
        for sn, info in result.get("episodes", {}).items():
            line = Text(f"  {sn}: ", style="info")
            line.append(info, style="muted")
            lines.append(line)

    return boxed(Group(*lines), title=f"{ICONS['netflix']} Netflix  Search")


def render_spotify_search(query: str, uri: str) -> Panel:
    lines = [
        Text(query, style="primary"),
        Text(""),
        kv_table({"URI": uri}),
    ]
    return boxed(Group(*lines), title=f"{ICONS['spotify']} Spotify  Search")


def render_youtube_search(query: str, results: list[dict]) -> Panel:
    table = simple_table(["ID", "Title"])
    table.columns[0].width = 12
    for r in results:
        table.add_row(
            Text(r.get("id", ""), style="accent"),
            Text(r.get("title", ""), style="primary"),
        )
    return boxed(
        Group(Text(query, style="primary"), Text(""), table),
        title=f"{ICONS['youtube']} YouTube  Search",
    )


# ============================================================================
# History / Recommendations / Next
# ============================================================================


def render_history(entries: list[dict[str, Any]]) -> Panel:
    if not entries:
        return boxed(Text("No play history yet.", style="muted"), title=f"{ICONS['clock']} History")

    table = simple_table(["When", "Platform", "Title"])
    table.columns[2].overflow = "ellipsis"
    for e in entries:
        ts = time.strftime("%m/%d %H:%M", time.localtime(e.get("time", 0)))
        desc = e.get("query", "")
        if e.get("season") and e.get("episode"):
            desc += f" S{e['season']}E{e['episode']}"
        platform = e.get("platform", "")
        icon = app_icon(platform)
        plat_cell = Text(f"{icon} {platform}", style="info")
        table.add_row(
            Text(ts, style="muted"),
            plat_cell,
            Text(desc, style="primary"),
        )
    return boxed(table, title=f"{ICONS['clock']} Recent Plays")


def render_recommendations(results: list[dict[str, Any]], recent_shows: list[str] | None = None) -> Panel:
    if not results:
        return boxed(
            Group(
                Text("No recommendations available.", style="muted"),
                Text("Try: stv whats-on", style="dim"),
            ),
            title=f"{ICONS['star']} Recommendations",
        )

    header: list = []
    if recent_shows:
        t = Text("Based on your recent watching: ", style="muted")
        t.append(", ".join(recent_shows[:3]), style="accent")
        header.append(t)
    else:
        header.append(Text("Trending now (no watch history yet)", style="muted"))
    header.append(Text(""))

    table = simple_table(["#", "Title", "Platform", "Why"])
    table.columns[0].width = 3
    table.columns[0].justify = "right"
    for i, rec in enumerate(results, 1):
        icon = app_icon(rec.get("platform", ""))
        plat_cell = Text(f"{icon} {rec.get('platform', '').capitalize()}", style="info")
        table.add_row(
            Text(str(i), style="accent"),
            Text(rec.get("title", ""), style="primary"),
            plat_cell,
            Text(rec.get("reason", ""), style="muted"),
        )
    return boxed(Group(*header, table), title=f"{ICONS['star']} Recommendations")


# ============================================================================
# Queue
# ============================================================================


def render_queue(items: list[dict[str, Any]]) -> Panel:
    if not items:
        return boxed(
            Text("Queue is empty.", style="muted"),
            title=f"{ICONS['queue']} Play Queue",
        )

    table = simple_table(["#", "Platform", "Title"])
    table.columns[0].width = 3
    table.columns[0].justify = "right"
    for i, item in enumerate(items, 1):
        desc = item.get("query", "")
        if item.get("season") and item.get("episode"):
            desc += f" S{item['season']}E{item['episode']}"
        platform = item.get("platform", "")
        icon = app_icon(platform)
        plat_cell = Text(f"{icon} {platform}", style="info")
        table.add_row(
            Text(str(i), style="accent"),
            plat_cell,
            Text(desc, style="primary"),
        )
    footer = Text(f"{len(items)} item{'s' if len(items) != 1 else ''} queued", style="muted")
    return boxed(Group(table, Text(""), footer), title=f"{ICONS['queue']} Play Queue")


# ============================================================================
# Apps
# ============================================================================


def render_apps(apps: list[dict[str, Any]]) -> Panel:
    if not apps:
        return boxed(Text("No apps reported.", style="muted"), title=f"{ICONS['tv']} Apps")

    table = simple_table(["", "Name", "ID"])
    table.columns[0].width = 3
    table.columns[2].overflow = "ellipsis"
    for a in apps:
        app_id = a.get("id", "")
        icon = app_icon(app_id)
        table.add_row(
            Text(icon),
            Text(a.get("name", ""), style="primary"),
            Text(app_id, style="muted"),
        )
    return boxed(table, title=f"{ICONS['tv']} Installed Apps  ({len(apps)})")


# ============================================================================
# Insights / Screen Time / Sub Value
# ============================================================================


def render_insights(data: dict[str, Any]) -> Panel:
    period = (data.get("period") or "week").capitalize()
    total_plays = data.get("total_plays", 0)
    total_hours = data.get("total_hours_estimate", 0.0)
    by_platform: dict[str, int] = data.get("by_platform", {}) or {}
    top_shows: list = data.get("top_shows", []) or []
    binge_sessions = data.get("binge_sessions", 0)
    peak_hour = data.get("peak_hour")
    streak_days = data.get("streak_days", 0)

    header = Text()
    header.append(f"{total_plays}", style="primary")
    header.append(" plays  ·  ", style="muted")
    header.append(f"~{total_hours}", style="accent")
    header.append(" hours", style="muted")

    sections: list = [header, Text("")]

    if by_platform:
        sections.append(Text("Platform breakdown", style="accent"))
        max_count = max(by_platform.values()) or 1
        bar_width = 20
        order = sorted(by_platform, key=lambda k: by_platform[k], reverse=True)
        label_width = max(len(p) for p in order)
        for plat in order:
            count = by_platform[plat]
            filled = round(bar_width * count / max_count)
            line = Text(f"  {plat.ljust(label_width)}  ", style="info")
            line.append("█" * filled, style="primary")
            line.append("░" * (bar_width - filled), style="muted")
            line.append(f"  {count}", style="accent")
            sections.append(line)
        sections.append(Text(""))

    if top_shows:
        sections.append(Text("Top shows", style="accent"))
        for i, entry in enumerate(top_shows, 1):
            # entry may be (show, count) tuple OR dict
            if isinstance(entry, (tuple, list)):
                show, count = entry[0], entry[1]
            else:
                show = entry.get("title", "?")
                count = entry.get("count", 0)
            line = Text(f"  {i}. ", style="accent")
            line.append(str(show), style="primary")
            line.append(f"  ({count} play{'s' if count != 1 else ''})", style="muted")
            sections.append(line)
        sections.append(Text(""))

    # Footer stats
    footer = Table(box=None, show_header=False, pad_edge=False, show_edge=False)
    footer.add_column(style="muted")
    footer.add_column(style="primary")
    if peak_hour is not None:
        if peak_hour == 0:
            hour_str = "12am"
        elif peak_hour < 12:
            hour_str = f"{peak_hour}am"
        elif peak_hour == 12:
            hour_str = "12pm"
        else:
            hour_str = f"{peak_hour - 12}pm"
        footer.add_row(f"{ICONS['clock']} Peak viewing", hour_str)
    footer.add_row(f"{ICONS['trending']} Binge sessions", str(binge_sessions))
    footer.add_row(
        f"{ICONS['bolt']} Watch streak",
        f"{streak_days} day{'s' if streak_days != 1 else ''}",
    )
    sections.append(footer)

    return boxed(
        Group(*sections),
        title=f"{ICONS['chart']} {period} in Review",
    )


def render_screen_time(period: str, data: dict[str, Any]) -> Panel:
    total = data.get("total_minutes", 0) or 0
    hours = total // 60
    mins = total % 60

    header = Text()
    header.append(f"{hours}h {mins}m", style="primary")
    header.append(f"  ({period})", style="muted")

    sections: list = [header, Text("")]

    by_platform = data.get("by_platform", {}) or {}
    if by_platform:
        table = simple_table(["Platform", "Time"])
        for plat, minutes in by_platform.items():
            h, m = divmod(minutes, 60)
            icon = app_icon(plat)
            table.add_row(
                Text(f"{icon} {plat}", style="info"),
                Text(f"{h}h {m}m", style="primary"),
            )
        sections.append(table)
        sections.append(Text(""))

    if data.get("first_play"):
        sections.append(Text(f"First play: {data['first_play']}", style="muted"))
        sections.append(Text(f"Last play:  {data['last_play']}", style="muted"))

    return boxed(Group(*sections), title=f"{ICONS['clock']} Screen Time")


def render_sub_value(platform: str, cost: float, data: dict[str, Any]) -> Panel:
    verdict = data.get("verdict", "unknown")
    cost_per_hour = data.get("cost_per_hour", 0) or 0
    plays = data.get("plays_this_month", 0) or 0
    hours = data.get("estimated_hours", 0) or 0

    verdict_map = {
        "good_value":        (f"{ICONS['ok']} Good value",        "success"),
        "ok":                (f"{ICONS['info']} OK",              "warning"),
        "consider_canceling": (f"{ICONS['warn']} Consider canceling", "error"),
    }
    label, style = verdict_map.get(verdict, (f"{ICONS['info']} Unknown", "muted"))

    verdict_text = Text(label, style=style)

    big = Text()
    big.append(f"${cost_per_hour:.2f}", style="primary")
    big.append(" / hour", style="muted")

    sections: list = [
        verdict_text,
        Text(""),
        big,
        Text(""),
        kv_table({
            "Plays this month": str(plays),
            "Est. hours":       f"{hours:.1f}",
            "Monthly cost":     f"${cost}",
        }),
    ]

    icon = app_icon(platform)
    return boxed(
        Group(*sections),
        title=f"{icon} {platform.capitalize()}  Subscription Value",
    )


# ============================================================================
# Multi-TV Broadcast Results
# ============================================================================


def render_broadcast_results(results: list[dict[str, Any]]) -> Panel:
    """Used for `stv --all <cmd>` — shows per-TV status."""
    table = simple_table(["", "TV", "Result"])
    table.columns[0].width = 3
    table.columns[0].justify = "center"
    for r in results:
        ok = r.get("status") == "ok"
        icon = Text(ICONS["ok"], style="success") if ok else Text(ICONS["fail"], style="error")
        tv_name = Text(r.get("tv", ""), style="primary")
        msg = Text(r.get("message", ""), style="muted" if ok else "error")
        table.add_row(icon, tv_name, msg)
    ok_count = sum(1 for r in results if r.get("status") == "ok")
    footer = Text(f"{ok_count}/{len(results)} succeeded", style="muted")
    return boxed(
        Group(table, Text(""), footer),
        title=f"{ICONS['cast']} Broadcast",
    )


# ============================================================================
# Cache / License
# ============================================================================


def render_cache_show(data: dict[str, Any]) -> Panel:
    if not data:
        return boxed(Text("Cache is empty.", style="muted"), title=f"{ICONS['cache']} Content Cache")

    table = simple_table(["Platform", "Key", "Value"])
    table.columns[2].overflow = "ellipsis"
    count = 0
    for platform, entries in data.items():
        if not isinstance(entries, dict):
            continue
        for k, v in entries.items():
            table.add_row(
                Text(platform, style="info"),
                Text(str(k), style="primary"),
                Text(str(v)[:60], style="muted"),
            )
            count += 1

    footer = Text(f"{count} entries", style="muted")
    return boxed(Group(table, Text(""), footer), title=f"{ICONS['cache']} Content Cache")


def render_license_status(
    key: str | None,
    source: str,
    tier: str = "Pro (unlimited resolves)",
    free_quota: str = "100 API resolves/day",
) -> Panel:
    if not key:
        return boxed(
            Group(
                Text("No license key found.", style="muted"),
                Text(""),
                Text(f"Using free tier ({free_quota})", style="dim"),
            ),
            title=f"{ICONS['bolt']} License",
        )

    masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key
    return boxed(
        kv_table({
            "Key":    masked,
            "Source": source,
            "Tier":   tier,
        }),
        title=f"{ICONS['bolt']} License",
    )


# ============================================================================
# Setup Wizard / Generic Messages
# ============================================================================


def render_success(message: str, title: str = "Success") -> Panel:
    return Panel(
        Text(f"{ICONS['ok']}  {message}", style="success"),
        title=title,
        title_align="left",
        border_style="success",
        box=box.ROUNDED,
        padding=(0, 2),
    )


def render_error(message: str, hint: str = "") -> Panel:
    return error_panel(message, hint)


def render_banner(title: str, subtitle: str = "") -> Panel:
    """Used by `stv serve` etc — welcome banner."""
    lines: list = [Text(title, style="primary")]
    if subtitle:
        lines.append(Text(subtitle, style="muted"))
    return Panel(
        Group(*lines),
        border_style="primary",
        box=box.DOUBLE,
        padding=(1, 3),
    )
