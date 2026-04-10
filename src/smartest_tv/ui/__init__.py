"""stv UI — Rich-powered rendering for every command.

Public API:
    from smartest_tv.ui import console, theme
    from smartest_tv.ui import render  # all render_* functions

Each render function returns a Rich renderable (Panel, Table, Group, ...).
The caller is responsible for printing via `console.print(renderable)`.

JSON output is never routed through this module — cli.py handles that directly.
"""
from smartest_tv.ui.theme import ICONS, THEMES, get_console, get_theme

console = get_console()
theme = get_theme()

__all__ = ["console", "theme", "get_console", "get_theme", "THEMES", "ICONS"]
