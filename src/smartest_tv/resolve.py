"""Content ID resolver for streaming platforms.

Resolution chain:
  1. Local cache → instant (0ms)
  2. Engine (local, PyPI install) → fast (2-3s)
  3. API fallback (GitHub clone) → fast (1-2s)

The cache is the real product. Once any ID is discovered, it's cached forever.
"""

from __future__ import annotations

import re

from smartest_tv import cache
from smartest_tv.http import curl_json


# ---------------------------------------------------------------------------
# Check if the engine is available (PyPI install vs GitHub clone)
# ---------------------------------------------------------------------------

def _has_engine() -> bool:
    try:
        from smartest_tv._engine import resolve as _r  # noqa: F401
        return True
    except ImportError:
        return False


_ENGINE = _has_engine()


# ---------------------------------------------------------------------------
# Netflix
# ---------------------------------------------------------------------------

def resolve_netflix(
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve a Netflix show/movie to an episode or movie ID."""
    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_netflix as _resolve
        return _resolve(query, season, episode, title_id)
    return _api_resolve("netflix", query, season, episode, title_id)


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def resolve_youtube(query: str) -> str:
    """Resolve YouTube search → video ID."""
    slug = _slugify(query)
    cached = cache.get("youtube", slug)
    if cached:
        return cached

    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_youtube as _resolve
        return _resolve(query)
    return _api_resolve("youtube", query)


# ---------------------------------------------------------------------------
# Spotify
# ---------------------------------------------------------------------------

def resolve_spotify(query: str) -> str:
    """Resolve Spotify content to a URI."""
    # Direct URI/URL passthrough (no engine needed)
    if query.startswith("spotify:"):
        return query
    if "open.spotify.com" in query:
        m = re.search(r"open\.spotify\.com/(track|album|artist|playlist)/([A-Za-z0-9]+)", query)
        if m:
            return f"spotify:{m.group(1)}:{m.group(2)}"

    slug = _slugify(query)
    cached = cache.get("spotify", slug)
    if cached:
        return cached

    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_spotify as _resolve
        return _resolve(query)
    return _api_resolve("spotify", query)


# ---------------------------------------------------------------------------
# Trending
# ---------------------------------------------------------------------------

def fetch_netflix_trending(limit: int = 10) -> list[dict]:
    """Fetch Netflix Top 10."""
    if _ENGINE:
        from smartest_tv._engine.resolve import fetch_netflix_trending as _fn
        return _fn(limit)
    return _api_trending("netflix", limit)


def fetch_youtube_trending(limit: int = 10) -> list[dict]:
    """Fetch YouTube trending."""
    if _ENGINE:
        from smartest_tv._engine.resolve import fetch_youtube_trending as _fn
        return _fn(limit)
    return _api_trending("youtube", limit)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def get_recommendations(mood: str | None = None, limit: int = 5) -> list[dict]:
    """Get content recommendations based on watch history + trending."""
    if _ENGINE:
        from smartest_tv._engine.resolve import get_recommendations as _fn
        return _fn(mood, limit)

    # Fallback: trending-only recommendations
    results: list[dict] = []
    try:
        for item in fetch_netflix_trending(limit):
            results.append({
                "title": item.get("title", ""),
                "platform": "netflix",
                "reason": f"Trending #{item.get('rank', '?')}",
            })
    except Exception:
        pass
    return results[:limit]


# ---------------------------------------------------------------------------
# Unified resolver
# ---------------------------------------------------------------------------

def resolve(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve content to a platform-specific ID."""
    p = platform.lower().strip()
    if p == "netflix":
        return resolve_netflix(query, season, episode, title_id)
    elif p == "youtube":
        return resolve_youtube(query)
    elif p == "spotify":
        return resolve_spotify(query)
    else:
        raise ValueError(f"Unsupported platform: {platform}. Use netflix, youtube, or spotify.")


# ---------------------------------------------------------------------------
# API fallback (for GitHub clones without _engine)
# ---------------------------------------------------------------------------

def _api_resolve(platform: str, query: str, season: int | None = None,
                 episode: int | None = None, title_id: int | None = None) -> str:
    """Resolve via the hosted API fallback."""
    import os
    from smartest_tv.cache import CACHE_API_URL
    from smartest_tv.http import curl
    import json

    body: dict = {"platform": platform, "query": query}
    if season is not None:
        body["season"] = season
    if episode is not None:
        body["episode"] = episode
    if title_id is not None:
        body["title_id"] = title_id

    headers: dict[str, str] = {"Content-Type": "application/json"}
    license_key = _get_license_key()
    if license_key:
        headers["X-License-Key"] = license_key

    r = curl(
        f"{CACHE_API_URL}/resolve",
        method="POST",
        data=json.dumps(body),
        headers=headers,
        timeout=10,
    )

    if r.body:
        try:
            data = json.loads(r.body)
        except (json.JSONDecodeError, ValueError):
            data = {}

        if data.get("content_id"):
            content_id = data["content_id"]
            slug = _slugify(query)
            cache.put(platform, slug, content_id)
            return content_id

        if data.get("error") == "rate_limited":
            raise ValueError(
                f"Daily resolve limit reached. "
                f"Install from PyPI for unlimited local resolution: pip install stv"
            )

    raise ValueError(
        f"Could not resolve {platform}: {query}. "
        f"Install from PyPI for local resolution: pip install stv"
    )


def _api_trending(platform: str, limit: int) -> list[dict]:
    """Fetch trending via the hosted API."""
    from smartest_tv.cache import CACHE_API_URL
    data = curl_json(f"{CACHE_API_URL}/trending/{platform}?limit={limit}", timeout=5)
    if data and isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_license_key_cache: str | None = None


def _get_license_key() -> str:
    """Get the Polar license key from env var or license.key file."""
    global _license_key_cache
    if _license_key_cache is not None:
        return _license_key_cache

    import os
    key = os.environ.get("STV_LICENSE_KEY", "")
    if not key:
        from smartest_tv.config import CONFIG_DIR
        license_file = CONFIG_DIR / "license.key"
        if license_file.exists():
            try:
                key = license_file.read_text().strip()
            except OSError:
                key = ""

    _license_key_cache = key
    return key


def _slugify(text: str) -> str:
    """Normalize text to cache key."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")
