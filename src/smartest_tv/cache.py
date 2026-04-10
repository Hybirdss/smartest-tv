"""Local + community content ID cache for smartest-tv.

Three-tier cache:
  1. Local cache (~/.config/smartest-tv/cache.json) — instant
  2. Remi API (api.remi.dev) — ~0.1s, shared across all users
  3. GitHub fallback — ~0.3s, static seed data
  4. Web search + scraping — 2-3s last resort

New resolutions are contributed back to the API so all users benefit.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

from smartest_tv.config import CONFIG_DIR

log = logging.getLogger("smartest-tv")

CACHE_FILE = CONFIG_DIR / "cache.json"

# Cache entries older than this are re-validated in the background on next access.
# The stale value is returned immediately — re-resolve never blocks playback.
CACHE_TTL_SECONDS = 90 * 86400  # 90 days

# API server (primary) — set STV_CACHE_API to override
CACHE_API_URL = os.environ.get(
    "STV_CACHE_API",
    "https://remi-api.narukys.workers.dev/v1",
)
# GitHub raw (fallback, static seed data)
_GITHUB_FALLBACK_URL = "https://raw.githubusercontent.com/Hybirdss/smartest-tv/main/community-cache.json"

# API key for contributing resolutions
# Default: public contributor key (write-only, rate-limited)
# Override with STV_CACHE_API_KEY env var for admin access
CACHE_API_KEY = os.environ.get(
    "STV_CACHE_API_KEY",
    "stv_pub_eRZpBRM0PDzjx5j2PVN3QnHuxxjMURsQ",
)

_community_cache: dict | None = None  # in-memory cache for session


def _load() -> dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def get(platform: str, key: str) -> Any | None:
    """Get a cached value. Checks local → API (single entry) → community (full).

    Stale entries (older than CACHE_TTL_SECONDS) are returned immediately
    but trigger a background re-resolve so the next call gets fresh data.
    """
    data = _load()
    result = data.get(platform, {}).get(key)
    if result is not None:
        _maybe_revalidate(data, platform, key)
        return result

    # Try API single-entry lookup (faster than loading full cache)
    result = _api_get(platform, key)
    if result is not None:
        put(platform, key, result)
        return result

    # Try full community cache (fallback)
    cc = _load_community()
    result = cc.get(platform, {}).get(key)
    if result is not None:
        # Promote to local cache (put without re-contributing)
        data = _load()
        if platform not in data:
            data[platform] = {}
        data[platform][key] = result
        _save(data)
    return result


def _api_get(platform: str, slug: str) -> Any | None:
    """Look up a single entry from the API server. Returns None on miss/error."""
    from smartest_tv.http import curl
    r = curl(f"{CACHE_API_URL}/cache/{platform}/{slug}", timeout=2)
    if not r.ok or not r.body:
        return None
    try:
        resp = json.loads(r.body)
        data = resp.get("data")
        if data is None:
            return None
        # Unwrap structured format back to what stv expects
        if platform == "youtube":
            return data.get("video_id") or data
        if platform == "spotify":
            return data.get("uri") or data
        return data
    except (json.JSONDecodeError, AttributeError):
        return None


def _load_community() -> dict:
    """Fetch community cache. Tries API server first, then GitHub fallback.

    Cached in-memory per session — only one network call per stv invocation.
    """
    global _community_cache
    if _community_cache is not None:
        return _community_cache

    from smartest_tv.http import curl

    _MAX_COMMUNITY_CACHE_SIZE = 2 * 1024 * 1024  # 2 MB safety limit

    # 1) Try API server (fast, up-to-date)
    r = curl(f"{CACHE_API_URL}/cache", timeout=3)
    if r.ok and r.body and len(r.body) < _MAX_COMMUNITY_CACHE_SIZE:
        try:
            _community_cache = json.loads(r.body)
            return _community_cache
        except json.JSONDecodeError:
            pass

    # 2) Fallback to GitHub static file
    log.debug("API cache unavailable, falling back to GitHub")
    r = curl(_GITHUB_FALLBACK_URL, timeout=3)
    if r.body and len(r.body) < _MAX_COMMUNITY_CACHE_SIZE:
        try:
            _community_cache = json.loads(r.body)
            return _community_cache
        except json.JSONDecodeError:
            pass

    _community_cache = {}
    return _community_cache


def put(platform: str, key: str, value: Any) -> None:
    """Store a value in local cache + contribute to API."""
    data = _load()
    if platform not in data:
        data[platform] = {}
    data[platform][key] = value
    # Track when this entry was cached for TTL-based revalidation
    data.setdefault("_timestamps", {})[f"{platform}:{key}"] = int(time.time())
    _save(data)

    # Contribute YouTube/Spotify resolutions to API
    if platform == "youtube":
        _contribute(platform, key, {"video_id": value})
    elif platform == "spotify":
        _contribute(platform, key, {"uri": value})


def get_netflix_episode(title_slug: str, season: int, episode: int) -> str | None:
    """Look up a cached Netflix episode ID. Checks local → API → community."""
    # Try local first
    data = _load()
    result = _lookup_netflix_episode(data, title_slug, season, episode)
    if result:
        _maybe_revalidate(data, "netflix", title_slug)
        return result

    # Try API single-entry lookup
    show_data = _api_get("netflix", title_slug)
    if show_data and isinstance(show_data, dict):
        result = _lookup_netflix_episode({"netflix": {title_slug: show_data}}, title_slug, season, episode)
        if result:
            # Promote to local cache
            data = _load()
            if "netflix" not in data:
                data["netflix"] = {}
            data["netflix"][title_slug] = show_data
            _save(data)
            return result

    # Try full community cache (fallback)
    cc = _load_community()
    result = _lookup_netflix_episode(cc, title_slug, season, episode)
    if result:
        show = cc.get("netflix", {}).get(title_slug)
        if show:
            data = _load()
            if "netflix" not in data:
                data["netflix"] = {}
            data["netflix"][title_slug] = show
            _save(data)
    return result


def _lookup_netflix_episode(data: dict, slug: str, season: int, episode: int) -> str | None:
    """Look up episode from a cache dict."""
    show = data.get("netflix", {}).get(slug)
    if not show:
        return None
    season_data = show.get("seasons", {}).get(str(season))
    if not season_data:
        return None
    first_id = season_data.get("first_episode_id")
    count = season_data.get("episode_count", 0)
    if first_id and 1 <= episode <= count:
        return str(first_id + episode - 1)
    return None


def put_netflix_show(
    title_slug: str,
    title_id: int,
    season: int,
    first_episode_id: int,
    episode_count: int,
) -> None:
    """Cache a Netflix show's season data locally + contribute to API."""
    data = _load()
    if "netflix" not in data:
        data["netflix"] = {}
    if title_slug not in data["netflix"]:
        data["netflix"][title_slug] = {"title_id": title_id, "seasons": {}}
    data["netflix"][title_slug]["seasons"][str(season)] = {
        "first_episode_id": first_episode_id,
        "episode_count": episode_count,
    }
    data.setdefault("_timestamps", {})[f"netflix:{title_slug}"] = int(time.time())
    _save(data)

    # Contribute to API (fire-and-forget, never blocks)
    _contribute("netflix", title_slug, data["netflix"][title_slug])


# ---------------------------------------------------------------------------
# TTL-based background revalidation
# ---------------------------------------------------------------------------

def _maybe_revalidate(data: dict, platform: str, key: str) -> None:
    """If a cached entry is older than CACHE_TTL_SECONDS, re-resolve in background.

    The stale value is always returned immediately — this never blocks.
    On success the local cache (and community cache) are silently updated.
    """
    ts_key = f"{platform}:{key}"
    cached_at = data.get("_timestamps", {}).get(ts_key, 0)
    if cached_at and time.time() - cached_at < CACHE_TTL_SECONDS:
        return  # still fresh

    # Don't re-resolve internal keys
    if key.startswith("_"):
        return

    def _bg_revalidate() -> None:
        try:
            fresh = _api_get(platform, key)
            if fresh is not None:
                put(platform, key, fresh)
                log.debug("Revalidated %s:%s from API", platform, key)
        except Exception:
            pass  # best-effort, never crash

    threading.Thread(target=_bg_revalidate, daemon=True).start()


# ---------------------------------------------------------------------------
# API contribution — send new resolutions to the shared cache
# ---------------------------------------------------------------------------

def _contribute(platform: str, slug: str, entry_data: Any) -> None:
    """Submit a newly resolved content ID to the shared community cache.

    Privacy: only the platform name (netflix/youtube/spotify), the content
    slug (e.g. "frieren"), and the resolved content ID (Netflix title ID,
    YouTube video ID, Spotify URI) are sent. No user identifier, no IP
    address, no watch history, no PII. Fire-and-forget background HTTPS
    POST that never blocks playback.

    Disable entirely with ``STV_NO_CONTRIBUTE=1`` in env. See README#Privacy
    for the full policy.
    """
    if os.environ.get("STV_NO_CONTRIBUTE"):
        return

    def _post() -> None:
        from smartest_tv.http import curl
        headers = {}
        if CACHE_API_KEY:
            headers["Authorization"] = f"Bearer {CACHE_API_KEY}"
        r = curl(
            f"{CACHE_API_URL}/cache/{platform}/{slug}",
            method="POST",
            data=json.dumps(entry_data),
            headers=headers,
            timeout=5,
        )
        if r.ok:
            log.debug("Contributed %s:%s to API", platform, slug)
        else:
            log.debug("API contribution failed for %s:%s: %s", platform, slug, r.error)

    threading.Thread(target=_post, daemon=True).start()


# ---------------------------------------------------------------------------
# Play history
# ---------------------------------------------------------------------------

def record_play(platform: str, query: str, content_id: str,
                season: int | None = None, episode: int | None = None) -> None:
    """Record a play event to history."""
    import time
    data = _load()
    if "_history" not in data:
        data["_history"] = []

    entry = {
        "platform": platform,
        "query": query,
        "content_id": content_id,
        "time": int(time.time()),
    }
    if season is not None:
        entry["season"] = season
    if episode is not None:
        entry["episode"] = episode

    # Keep last 50 entries
    data["_history"] = [entry] + data["_history"][:49]
    _save(data)


def get_history(limit: int = 10) -> list[dict]:
    """Get recent play history."""
    data = _load()
    return data.get("_history", [])[:limit]


def analyze_history() -> dict:
    """Analyze watch history for recommendation patterns.

    Returns a dict with:
      - top_platform: most-watched platform (or None)
      - recent_shows: list of recent unique show queries (last 10)
      - watch_count: {platform: count} across last 50 entries
    """
    entries = get_history(50)
    if not entries:
        return {"top_platform": None, "recent_shows": [], "watch_count": {}}

    watch_count: dict[str, int] = {}
    recent_shows: list[str] = []
    seen_shows: set[str] = set()

    for entry in entries:
        platform = entry.get("platform", "")
        if platform:
            watch_count[platform] = watch_count.get(platform, 0) + 1

        query = entry.get("query", "")
        if query and query not in seen_shows and len(recent_shows) < 10:
            recent_shows.append(query)
            seen_shows.add(query)

    top_platform = max(watch_count, key=watch_count.get) if watch_count else None
    return {
        "top_platform": top_platform,
        "recent_shows": recent_shows,
        "watch_count": watch_count,
    }


def get_last_played(query: str | None = None, platform: str | None = None) -> dict | None:
    """Get the most recent play for a query or platform."""
    for entry in get_history(50):
        if query and query.lower() in entry.get("query", "").lower():
            return entry
        if platform and not query and entry.get("platform") == platform:
            return entry
        if not query and not platform:
            return entry
    return None


def get_next_episode(query: str) -> tuple[str, int, int] | None:
    """Get the next episode to watch for a Netflix show.

    Returns (query, season, episode) or None if no history.
    """
    last = get_last_played(query=query)
    if not last or last.get("platform") != "netflix":
        return None

    season = last.get("season")
    episode = last.get("episode")
    if not season or not episode:
        return None

    slug = _slugify(query)
    data = _load()
    show = data.get("netflix", {}).get(slug)
    if not show:
        return (query, season, episode + 1)

    season_data = show.get("seasons", {}).get(str(season))
    if not season_data:
        return (query, season, episode + 1)

    ep_count = season_data.get("episode_count", 0)
    if episode < ep_count:
        return (query, season, episode + 1)

    # Next season?
    next_season = str(season + 1)
    if next_season in show.get("seasons", {}):
        return (query, season + 1, 1)

    return None  # Finished all seasons


def _slugify(text: str) -> str:
    """Normalize text to cache key."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")


# ---------------------------------------------------------------------------
# Play queue
# ---------------------------------------------------------------------------

QUEUE_FILE = CONFIG_DIR / "queue.json"


def _load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_queue(data: list[dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def queue_add(platform: str, query: str, season: int | None = None, episode: int | None = None) -> dict:
    """Add an item to the play queue. Returns the new item."""
    from datetime import datetime, timezone
    item = {
        "platform": platform,
        "query": query,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    if season is not None:
        item["season"] = season
    if episode is not None:
        item["episode"] = episode
    data = _load_queue()
    data.append(item)
    _save_queue(data)
    return item


def queue_show() -> list[dict]:
    """Return the current queue."""
    return _load_queue()


def queue_pop() -> dict | None:
    """Remove and return the first item in the queue."""
    data = _load_queue()
    if not data:
        return None
    item = data.pop(0)
    _save_queue(data)
    return item


def queue_skip() -> None:
    """Remove the first item in the queue without returning it."""
    data = _load_queue()
    if data:
        data.pop(0)
        _save_queue(data)


def queue_clear() -> None:
    """Clear the entire queue."""
    _save_queue([])
