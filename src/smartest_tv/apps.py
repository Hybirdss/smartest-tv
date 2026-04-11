"""Unified app name resolution across platforms.

Maps friendly names (netflix, youtube, spotify) to platform-specific app IDs.
"""

from __future__ import annotations


def resolve_app(name: str, platform: str) -> tuple[str, str]:
    """Resolve a friendly app name to (platform_app_id, display_name).

    Args:
        name: App name or alias (e.g. "netflix", "youtube")
        platform: TV platform (e.g. "lg", "samsung", "roku", "android")

    Returns:
        (app_id, display_name)
    """
    try:
        from smartest_tv._engine.apps import resolve_app as _resolve
        return _resolve(name, platform)
    except ImportError:
        # Minimal fallback for common apps
        return _fallback_resolve(name, platform)


def _fallback_resolve(name: str, platform: str) -> tuple[str, str]:
    """Minimal app resolution without the engine."""
    _BASIC = {
        "netflix": {"lg": "netflix", "samsung": "11101200001", "roku": "12", "android": "com.netflix.ninja", "browser": "netflix"},
        "youtube": {"lg": "youtube.leanback.v4", "samsung": "111299001912", "roku": "837", "android": "com.google.android.youtube.tv", "browser": "youtube"},
        "spotify": {"lg": "spotify-beehive", "samsung": "3201606009684", "roku": "22297", "android": "com.spotify.tv.android", "browser": "spotify"},
        "appletv": {"lg": "com.apple.appletv", "samsung": "3201807016598", "roku": "2", "android": "com.apple.atve.androidtv.appletv", "browser": "appletv"},
    }
    _NAMES = {"netflix": "Netflix", "youtube": "YouTube", "spotify": "Spotify", "appletv": "Apple TV+"}

    key = name.lower().strip()
    if key in _BASIC and platform in _BASIC[key]:
        return _BASIC[key][platform], _NAMES.get(key, name)

    # Pass through raw app ID
    return name, name
