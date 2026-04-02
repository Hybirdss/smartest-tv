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
