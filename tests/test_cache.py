"""Unit tests for smartest_tv.cache — uses tmp_path, no real network."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import smartest_tv.cache as cache_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect cache file to a temp dir, reset community cache, block network."""
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", cache_file)
    monkeypatch.setattr(cache_module, "CONFIG_DIR", tmp_path)
    # Reset the in-memory community cache between tests
    monkeypatch.setattr(cache_module, "_community_cache", None)
    # Block API calls — unit tests must not hit the network
    monkeypatch.setattr(cache_module, "_api_get", lambda *a, **kw: None)
    monkeypatch.setattr(cache_module, "_contribute", lambda *a, **kw: None)
    yield cache_file


@pytest.fixture()
def no_community(monkeypatch):
    """Make community cache always return empty (no network calls)."""
    monkeypatch.setattr(cache_module, "_community_cache", {})


# ---------------------------------------------------------------------------
# Basic put / get
# ---------------------------------------------------------------------------


def test_put_and_get(no_community):
    cache_module.put("youtube", "baby-shark", "XqZsoesa55w")
    assert cache_module.get("youtube", "baby-shark") == "XqZsoesa55w"


def test_get_missing_returns_none(no_community):
    assert cache_module.get("youtube", "missing-key") is None


def test_put_overwrites(no_community):
    cache_module.put("youtube", "key", "v1")
    cache_module.put("youtube", "key", "v2")
    assert cache_module.get("youtube", "key") == "v2"


def test_cache_persists_to_disk(isolated_cache, no_community):
    cache_module.put("spotify", "test", "spotify:track:123")
    raw = json.loads(isolated_cache.read_text())
    assert raw["spotify"]["test"] == "spotify:track:123"


# ---------------------------------------------------------------------------
# Netflix episode lookup (local cache only)
# ---------------------------------------------------------------------------


def test_put_and_get_netflix_episode(no_community):
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    # S1E1 → first_episode_id
    assert cache_module.get_netflix_episode("frieren", 1, 1) == "81726716"
    # S1E5 → first_episode_id + 4
    assert cache_module.get_netflix_episode("frieren", 1, 5) == "81726720"
    # S1E10 → last episode
    assert cache_module.get_netflix_episode("frieren", 1, 10) == "81726725"


def test_get_netflix_episode_out_of_range(no_community):
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    # Episode 11 doesn't exist in a 10-ep season
    assert cache_module.get_netflix_episode("frieren", 1, 11) is None


def test_get_netflix_episode_wrong_season(no_community):
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    assert cache_module.get_netflix_episode("frieren", 2, 1) is None


def test_get_netflix_episode_unknown_show(no_community):
    assert cache_module.get_netflix_episode("unknown-show", 1, 1) is None


# ---------------------------------------------------------------------------
# Community cache fallback + promotion
# ---------------------------------------------------------------------------


def test_community_cache_fallback(monkeypatch):
    """When local cache misses, falls back to community cache."""
    community_data = {
        "netflix": {
            "frieren": {
                "title_id": 81726714,
                "seasons": {"1": {"first_episode_id": 81726716, "episode_count": 10}},
            }
        }
    }
    monkeypatch.setattr(cache_module, "_community_cache", community_data)

    result = cache_module.get_netflix_episode("frieren", 1, 1)
    assert result == "81726716"


def test_community_cache_promotes_to_local(monkeypatch, isolated_cache):
    """A community cache hit should write the show to local cache."""
    community_data = {
        "netflix": {
            "frieren": {
                "title_id": 81726714,
                "seasons": {"1": {"first_episode_id": 81726716, "episode_count": 10}},
            }
        }
    }
    monkeypatch.setattr(cache_module, "_community_cache", community_data)

    # First lookup → hits community cache
    cache_module.get_netflix_episode("frieren", 1, 1)

    # Now local cache should contain the show
    local = json.loads(isolated_cache.read_text())
    assert "frieren" in local.get("netflix", {})


def test_community_cache_simple_key_promotes(monkeypatch, isolated_cache):
    """get() should promote a community value to local cache."""
    community_data = {"youtube": {"baby-shark": "XqZsoesa55w"}}
    monkeypatch.setattr(cache_module, "_community_cache", community_data)

    result = cache_module.get("youtube", "baby-shark")
    assert result == "XqZsoesa55w"

    # Check local disk
    local = json.loads(isolated_cache.read_text())
    assert local["youtube"]["baby-shark"] == "XqZsoesa55w"


# ---------------------------------------------------------------------------
# Play history
# ---------------------------------------------------------------------------


def test_record_play_basic(no_community):
    cache_module.record_play("netflix", "Frieren", "82656797", season=2, episode=8)
    history = cache_module.get_history(10)
    assert len(history) == 1
    entry = history[0]
    assert entry["platform"] == "netflix"
    assert entry["query"] == "Frieren"
    assert entry["content_id"] == "82656797"
    assert entry["season"] == 2
    assert entry["episode"] == 8


def test_history_most_recent_first(no_community):
    cache_module.record_play("youtube", "video1", "id1")
    cache_module.record_play("youtube", "video2", "id2")
    history = cache_module.get_history(10)
    assert history[0]["query"] == "video2"
    assert history[1]["query"] == "video1"


def test_history_max_50_entries(no_community):
    for i in range(60):
        cache_module.record_play("youtube", f"video{i}", f"id{i}")
    history = cache_module.get_history(100)
    assert len(history) == 50


def test_history_limit_parameter(no_community):
    for i in range(20):
        cache_module.record_play("youtube", f"video{i}", f"id{i}")
    assert len(cache_module.get_history(5)) == 5


def test_history_no_season_episode_omitted(no_community):
    cache_module.record_play("youtube", "baby shark", "XqZ")
    entry = cache_module.get_history(1)[0]
    assert "season" not in entry
    assert "episode" not in entry


# ---------------------------------------------------------------------------
# get_next_episode
# ---------------------------------------------------------------------------


def test_next_episode_same_season(no_community):
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    cache_module.record_play("netflix", "Frieren", "81726720", season=1, episode=5)

    result = cache_module.get_next_episode("Frieren")
    assert result == ("Frieren", 1, 6)


def test_next_episode_crosses_season_boundary(no_community):
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    cache_module.put_netflix_show("frieren", 81726714, 2, 82656790, 10)
    # Last episode of S1
    cache_module.record_play("netflix", "Frieren", "81726725", season=1, episode=10)

    result = cache_module.get_next_episode("Frieren")
    assert result == ("Frieren", 2, 1)


def test_next_episode_last_episode_returns_none(no_community):
    """No next episode after the final episode of the final season."""
    cache_module.put_netflix_show("frieren", 81726714, 1, 81726716, 10)
    cache_module.record_play("netflix", "Frieren", "81726725", season=1, episode=10)

    result = cache_module.get_next_episode("Frieren")
    # No S2 in cache → should return None
    assert result is None


def test_next_episode_no_history_returns_none(no_community):
    result = cache_module.get_next_episode("NonExistentShow")
    assert result is None


def test_next_episode_without_cached_show_still_increments(no_community):
    """If no show data in cache, just increment episode number."""
    cache_module.record_play("netflix", "Frieren", "82656797", season=2, episode=8)

    result = cache_module.get_next_episode("Frieren")
    assert result == ("Frieren", 2, 9)
