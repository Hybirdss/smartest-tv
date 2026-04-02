"""Local content ID cache for smartest-tv.

Once a Netflix episode ID, YouTube video, or Spotify URI is resolved,
it's cached locally so the next lookup is instant (0ms vs 2-10 seconds).

Cache lives at ~/.config/smartest-tv/cache.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smartest_tv.config import CONFIG_DIR

CACHE_FILE = CONFIG_DIR / "cache.json"


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
    """Get a cached value. Returns None on miss."""
    data = _load()
    return data.get(platform, {}).get(key)


def put(platform: str, key: str, value: Any) -> None:
    """Store a value in cache."""
    data = _load()
    if platform not in data:
        data[platform] = {}
    data[platform][key] = value
    _save(data)


def get_netflix_episode(title_slug: str, season: int, episode: int) -> str | None:
    """Look up a cached Netflix episode ID."""
    data = _load()
    show = data.get("netflix", {}).get(title_slug)
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
    if season:
        entry["season"] = season
    if episode:
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
