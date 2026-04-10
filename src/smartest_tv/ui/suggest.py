"""Context-aware next-action suggestions for the home dashboard.

Rules:
  - If user has a recent Netflix S/E play → suggest `stv next`
  - If user has recent plays in any platform → suggest `stv whats-on <platform>`
  - Always include 2-3 stable fallbacks (scene, whats-on, queue)

Pure functions — take cache snapshot in, return list of suggestion dicts out.
"""
from __future__ import annotations

from typing import Any

from smartest_tv.ui.theme import ICONS, app_icon


def suggest_for(history: list[dict[str, Any]] | None = None,
                app_id: str | None = None) -> list[dict[str, str]]:
    """Return 3-4 contextual suggestions for the home dashboard.

    Args:
        history: list of recent play entries from cache.get_history()
        app_id: currently active app on the TV (from status)

    Returns:
        List of { icon, command, description } dicts.
    """
    suggestions: list[dict[str, str]] = []
    history = history or []

    # --- 1. Continue the last Netflix show (if S/E recorded) ---
    for entry in history:
        if entry.get("platform") == "netflix" and entry.get("season") and entry.get("episode"):
            query = entry.get("query", "")
            suggestions.append({
                "icon": ICONS["next"],
                "command": "stv next",
                "description": f"continue {query} (S{entry['season']}E{entry['episode']+1})",
            })
            break

    # --- 2. Recently used platform → suggest trending ---
    if history:
        recent_platforms = []
        for entry in history[:5]:
            p = entry.get("platform")
            if p and p not in recent_platforms:
                recent_platforms.append(p)
        for p in recent_platforms:
            if p in ("netflix", "youtube"):
                suggestions.append({
                    "icon": app_icon(p),
                    "command": f"stv whats-on {p}",
                    "description": f"trending on {p.capitalize()}",
                })
                break

    # --- 3. Scene presets are always a good nudge ---
    if len(suggestions) < 3:
        suggestions.append({
            "icon": ICONS["scene"],
            "command": "stv scene movie-night",
            "description": "dim lights + cinema mode",
        })

    # --- 4. If still short, add insights (social proof of "there's more") ---
    if len(suggestions) < 3:
        suggestions.append({
            "icon": ICONS["chart"],
            "command": "stv insights",
            "description": "weekly watching stats",
        })

    # --- 5. If the TV is idle, a search is more useful than a generic play ---
    if not app_id or "home" in (app_id or "").lower() or "livetv" in (app_id or "").lower():
        if not any("whats-on" in s["command"] for s in suggestions):
            suggestions.insert(0, {
                "icon": ICONS["trending"],
                "command": "stv whats-on",
                "description": "what's trending right now",
            })

    # Cap at 3
    return suggestions[:3]
