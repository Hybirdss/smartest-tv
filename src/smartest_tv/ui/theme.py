"""stv theme system — 3 built-in themes + Console factory.

Env override: STV_THEME=mocha|nord|gruvbox (default: mocha)

Themes map semantic roles (primary, success, warning, error, muted, accent)
to concrete hex colors, so render functions stay theme-agnostic.
"""
from __future__ import annotations

import os

from rich.console import Console
from rich.theme import Theme

# -- Themes ------------------------------------------------------------------

# Catppuccin Mocha (default) — https://github.com/catppuccin/catppuccin
_MOCHA = {
    "primary": "#cba6f7",  # mauve
    "success": "#a6e3a1",  # green
    "warning": "#f9e2af",  # yellow
    "error":   "#f38ba8",  # red / maroon
    "muted":   "#6c7086",  # overlay0
    "accent":  "#f5c2e7",  # pink (smartest-tv mascot)
    "info":    "#89b4fa",  # blue
    "text":    "#cdd6f4",  # text
    "dim":     "#585b70",  # surface2
}

# Nord — https://www.nordtheme.com/
_NORD = {
    "primary": "#88c0d0",  # frost 3
    "success": "#a3be8c",  # aurora green
    "warning": "#ebcb8b",  # aurora yellow
    "error":   "#bf616a",  # aurora red
    "muted":   "#4c566a",  # polar night 3
    "accent":  "#b48ead",  # aurora purple
    "info":    "#81a1c1",  # frost 2
    "text":    "#eceff4",  # snow storm 3
    "dim":     "#3b4252",  # polar night 1
}

# Gruvbox Dark — https://github.com/morhetz/gruvbox
_GRUVBOX = {
    "primary": "#fabd2f",  # bright yellow
    "success": "#b8bb26",  # bright green
    "warning": "#fe8019",  # bright orange
    "error":   "#fb4934",  # bright red
    "muted":   "#928374",  # gray
    "accent":  "#d3869b",  # bright purple
    "info":    "#83a598",  # bright blue
    "text":    "#ebdbb2",  # light fg
    "dim":     "#504945",  # dark2
}

THEMES: dict[str, dict[str, str]] = {
    "mocha":   _MOCHA,
    "nord":    _NORD,
    "gruvbox": _GRUVBOX,
}


# -- Semantic Icons ----------------------------------------------------------

ICONS = {
    # Status
    "on":       "●",
    "off":      "○",
    "ok":       "✓",
    "fail":     "✗",
    "warn":     "⚠",
    "info":     "ℹ",
    # TV / Media
    "tv":       "📺",
    "play":     "▶",
    "pause":    "⏸",
    "next":     "⏭",
    "prev":     "⏮",
    "volume":   "🔊",
    "mute":     "🔇",
    # Apps
    "netflix":  "🎬",
    "youtube":  "▶",
    "spotify":  "🎵",
    "watcha":   "🎞",
    "disney":   "✨",
    "prime":    "📦",
    "apple":    "🍏",
    # Scenes
    "movie":    "🎬",
    "kids":     "👶",
    "sleep":    "😴",
    "music":    "🎵",
    # Misc
    "cast":     "📡",
    "queue":    "📋",
    "cache":    "💾",
    "scene":    "🎭",
    "group":    "👥",
    "trending": "🔥",
    "star":     "⭐",
    "clock":    "🕐",
    "chart":    "📊",
    "doctor":   "🩺",
    "plug":     "🔌",
    "search":   "🔍",
    "bolt":     "⚡",
}


# -- App / Platform Mapping --------------------------------------------------

# Raw app IDs → human names (TVs report opaque reverse-DNS IDs)
APP_NAMES: dict[str, str] = {
    # Netflix
    "netflix":                      "Netflix",
    "com.webos.app.netflix":        "Netflix",
    "com.netflix.ninja":             "Netflix",
    "3201907018807":                "Netflix",
    # YouTube
    "youtube.leanback.v4":           "YouTube",
    "com.webos.app.youtube":        "YouTube",
    "com.google.android.youtube.tv": "YouTube",
    "111477":                        "YouTube",
    # Spotify
    "spotify":                      "Spotify",
    "spotify-beehive":              "Spotify",
    "com.webos.app.spotify":         "Spotify",
    # Watcha
    "com.frograms.watchaplay.webos": "Watcha",
    # Disney+
    "com.disney.disneyplus":         "Disney+",
    # Prime Video
    "amazon":                        "Prime Video",
    "com.amazon.prime-video":        "Prime Video",
    # Apple TV+
    "com.apple.appletvplus":         "Apple TV+",
    # Live TV / Home
    "com.webos.app.livetv":          "Live TV",
    "com.webos.app.home":            "Home",
    "com.webos.app.homeconnect":     "Home",
}


def app_display_name(app_id: str | None) -> str:
    """Convert a raw app ID to a human-readable name."""
    if not app_id:
        return "Idle"
    if app_id in APP_NAMES:
        return APP_NAMES[app_id]
    # Heuristic: last segment of a reverse-DNS ID, titlecased
    tail = app_id.split(".")[-1].replace("-", " ").replace("_", " ")
    return tail.title() if tail else app_id


def app_icon(app_id: str | None) -> str:
    """Pick an icon for an app ID (matches on substring)."""
    if not app_id:
        return ICONS["tv"]
    lower = app_id.lower()
    for key in ("netflix", "youtube", "spotify", "watcha", "disney", "prime", "apple"):
        if key in lower:
            return ICONS[key]
    return ICONS["tv"]


# -- Theme / Console Factory -------------------------------------------------

_THEME_NAME: str | None = None


def get_theme_name() -> str:
    """Resolve the active theme name (env override > default)."""
    global _THEME_NAME
    if _THEME_NAME is not None:
        return _THEME_NAME
    name = os.environ.get("STV_THEME", "mocha").lower()
    if name not in THEMES:
        name = "mocha"
    _THEME_NAME = name
    return name


def get_theme() -> dict[str, str]:
    """Return the active theme's color dict."""
    return THEMES[get_theme_name()]


def _build_rich_theme(colors: dict[str, str]) -> Theme:
    """Build a Rich Theme from a color dict (semantic role → hex)."""
    return Theme({
        # Semantic roles
        "primary":  f"bold {colors['primary']}",
        "success":  colors["success"],
        "warning":  colors["warning"],
        "error":    f"bold {colors['error']}",
        "muted":    colors["muted"],
        "accent":   colors["accent"],
        "info":     colors["info"],
        "dim":      colors["dim"],
        # Power states
        "on":       f"bold {colors['success']}",
        "off":      f"{colors['muted']}",
        # Common Rich roles
        "logging.level.info":     colors["info"],
        "logging.level.warning":  colors["warning"],
        "logging.level.error":    colors["error"],
        "logging.level.debug":    colors["muted"],
        "repr.number":            colors["accent"],
        "repr.string":            colors["success"],
        "table.header":           f"bold {colors['primary']}",
        "progress.bar":           colors["primary"],
        "progress.percentage":    colors["accent"],
        "prompt":                 colors["primary"],
    })


_CONSOLE: Console | None = None


def get_console(force_reload: bool = False) -> Console:
    """Return a themed Rich Console singleton.

    Set STV_NO_COLOR=1 to force monochrome (useful in CI/tests).
    """
    global _CONSOLE
    if _CONSOLE is not None and not force_reload:
        return _CONSOLE
    colors = get_theme()
    rich_theme = _build_rich_theme(colors)
    no_color = os.environ.get("STV_NO_COLOR", "").strip() in ("1", "true", "yes")
    _CONSOLE = Console(
        theme=rich_theme,
        color_system=None if no_color else "auto",
        highlight=False,  # we style explicitly; no auto-highlighting
        soft_wrap=False,
    )
    return _CONSOLE
