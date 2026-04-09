"""Unified app name resolution across platforms.

Maps friendly names (netflix, youtube, spotify) to platform-specific app IDs.
Content IDs (Netflix episode numbers, YouTube video IDs, Spotify URIs) are
the same across all platforms — only the app ID and launch mechanism differ.
"""

from __future__ import annotations

# {alias: {platform: app_id}}
APP_REGISTRY: dict[str, dict[str, str]] = {
    "netflix": {
        "lg": "netflix",
        "samsung": "3201907018807",
        "android": "com.netflix.ninja",
        "roku": "12",
    },
    "youtube": {
        "lg": "youtube.leanback.v4",
        "samsung": "111299001912",
        "android": "com.google.android.youtube.tv",
        "roku": "837",
    },
    "spotify": {
        "lg": "spotify-beehive",
        "samsung": "3201606009684",
        "android": "com.spotify.tv.android",
        "roku": "19977",
    },
    "disney": {
        "lg": "com.disney.disneyplus-prod",
        "samsung": "3202009021709",
        "android": "com.disney.disneyplus",
        "roku": "291097",
    },
    "prime": {
        "lg": "amazon",
        "samsung": "3201910019365",
        "android": "com.amazon.amazonvideo.livingroom",
        "roku": "13",
    },
    "appletv": {
        "lg": "com.apple.appletv",
        "samsung": "3201807016597",
        "android": "com.apple.atve.androidtv.appletv",
        "roku": "551012",
    },
    "hulu": {
        "lg": "hulu",
        "samsung": "3201601007625",
        "android": "com.hulu.livingroomplus",
        "roku": "2285",
    },
    # Korean services
    "tving": {"lg": "cj.eandm", "samsung": "LBUSEANDM0100", "android": "net.cj.cjhv.gs.tving"},
    "wavve": {"lg": "pooq", "android": "com.kt.smarttv.pooq"},
    "coupang": {"lg": "coupangplay", "android": "com.coupang.play"},
    # System
    "browser": {"lg": "com.webos.app.browser", "samsung": "org.tizen.browser"},
    "hdmi1": {"lg": "com.webos.app.hdmi1"},
    "hdmi2": {"lg": "com.webos.app.hdmi2"},
}

# Aliases
_ALIASES = {
    "disney+": "disney",
    "disneyplus": "disney",
    "primevideo": "prime",
    "amazon": "prime",
    "apple": "appletv",
    "apple tv": "appletv",
    "coupangplay": "coupang",
}


def resolve_app(name: str, platform: str) -> tuple[str, str]:
    """Resolve a friendly app name to a platform-specific app ID.

    Returns (app_id, canonical_name). Falls back to using name as raw app ID.
    """
    key = name.lower().strip().replace(" ", "").replace("-", "").replace("_", "")
    key = _ALIASES.get(key, key)

    if key in APP_REGISTRY:
        registry = APP_REGISTRY[key]
        if platform in registry:
            return registry[platform], key
        # Platform not in registry — use key as-is
        return name, key

    return name, name
