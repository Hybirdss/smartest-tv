"""Shared rendering primitives used across every command."""
from __future__ import annotations

from typing import Iterable

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smartest_tv.ui.theme import ICONS, get_theme


def volume_bar(level: int, width: int = 20, muted: bool = False) -> Text:
    """Render a volume bar (0-100 → `level` cells).

    Example (level=45): █████████░░░░░░░░░░░  45
    """
    level = max(0, min(100, level))
    filled = round(width * level / 100)
    theme = get_theme()

    bar = Text()
    if muted:
        bar.append(f"{ICONS['mute']} MUTED  ", style="error")
        bar.append("░" * width, style="muted")
        bar.append(f"  {level}", style="muted")
        return bar

    bar.append(f"{ICONS['volume']} ", style=theme["accent"])
    bar.append("█" * filled, style="primary")
    bar.append("░" * (width - filled), style="muted")
    bar.append(f"  {level}", style=f"bold {theme['text']}")
    return bar


def status_dot(ok: bool) -> Text:
    """Colored dot for on/off, reachable/unreachable."""
    if ok:
        return Text(f"{ICONS['on']} ON ", style="on")
    return Text(f"{ICONS['off']} OFF", style="off")


def title_bar(title: str, icon: str = "") -> Text:
    """Section header: icon + title in primary color."""
    t = Text()
    if icon:
        t.append(f"{icon}  ")
    t.append(title, style="primary")
    return t


def boxed(content, title: str = "", subtitle: str = "", border: str = "primary") -> Panel:
    """Standard rounded panel with consistent padding."""
    return Panel(
        content,
        title=title or None,
        title_align="left",
        subtitle=subtitle or None,
        subtitle_align="right",
        border_style=border,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def simple_table(headers: Iterable[str], **kwargs) -> Table:
    """A minimal table: no outer box, bold header row, tight padding."""
    t = Table(
        box=box.SIMPLE_HEAD,
        header_style="table.header",
        pad_edge=False,
        show_edge=False,
        **kwargs,
    )
    for h in headers:
        t.add_column(h)
    return t


def kv_table(pairs: dict) -> Table:
    """Two-column key/value table with no header."""
    t = Table(box=None, show_header=False, pad_edge=False, show_edge=False)
    t.add_column(style="muted", no_wrap=True)
    t.add_column(style="primary")
    for k, v in pairs.items():
        t.add_row(str(k), str(v))
    return t


def error_panel(message: str, hint: str = "") -> Panel:
    """Red-bordered panel for error output."""
    content: list = [Text(f"{ICONS['fail']} {message}", style="error")]
    if hint:
        content.append(Text(""))
        content.append(Text(hint, style="muted"))
    return Panel(
        Group(*content),
        title="Error",
        title_align="left",
        border_style="error",
        box=box.ROUNDED,
        padding=(0, 2),
    )


def info_line(message: str, icon: str = "") -> Text:
    """Single-line info text with optional leading icon."""
    t = Text()
    if icon:
        t.append(f"{icon}  ", style="accent")
    t.append(message, style="info")
    return t


def success_line(message: str, icon: str = "") -> Text:
    t = Text()
    t.append(f"{icon or ICONS['ok']}  ", style="success")
    t.append(message)
    return t
