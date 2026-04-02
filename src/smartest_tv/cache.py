"""Local + community content ID cache for smartest-tv.

Three-tier cache:
  1. Local cache (~/.config/smartest-tv/cache.json) — instant
  2. Community cache (GitHub raw) — ~0.3s, shared across all users
  3. Web search + scraping — 2-3s fallback

Cache lives at ~/.config/smartest-tv/cache.json
Community cache: https://raw.githubusercontent.com/Hybirdss/smartest-tv/main/community-cache.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smartest_tv.config import CONFIG_DIR

CACHE_FILE = CONFIG_DIR / "cache.json"
COMMUNITY_CACHE_URL = "https://raw.githubusercontent.com/Hybirdss/smartest-tv/main/community-cache.json"
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
    """Get a cached value. Checks local, then community cache."""
    data = _load()
    result = data.get(platform, {}).get(key)
    if result is not None:
        return result

    # Try community cache
    cc = _load_community()
    result = cc.get(platform, {}).get(key)
    if result is not None:
        # Promote to local cache
        put(platform, key, result)
    return result


def _load_community() -> dict:
    """Fetch community cache from GitHub. Cached in-memory per session."""
    global _community_cache
    if _community_cache is not None:
        return _community_cache

    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", COMMUNITY_CACHE_URL],
            capture_output=True, text=True, timeout=5,
        )
        if result.stdout:
            _community_cache = json.loads(result.stdout)
            return _community_cache
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass

    _community_cache = {}
    return _community_cache


def put(platform: str, key: str, value: Any) -> None:
    """Store a value in cache."""
    data = _load()
    if platform not in data:
        data[platform] = {}
    data[platform][key] = value
    _save(data)


def get_netflix_episode(title_slug: str, season: int, episode: int) -> str | None:
    """Look up a cached Netflix episode ID. Checks local, then community."""
    # Try local first
    result = _lookup_netflix_episode(_load(), title_slug, season, episode)
    if result:
        return result

    # Try community cache
    cc = _load_community()
    result = _lookup_netflix_episode(cc, title_slug, season, episode)
    if result:
        # Promote show to local cache
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
    """Cache a Netflix show's season data."""
    data = _load()
    if "netflix" not in data:
        data["netflix"] = {}
    if title_slug not in data["netflix"]:
        data["netflix"][title_slug] = {"title_id": title_id, "seasons": {}}
    data["netflix"][title_slug]["seasons"][str(season)] = {
        "first_episode_id": first_episode_id,
        "episode_count": episode_count,
    }
    _save(data)


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
