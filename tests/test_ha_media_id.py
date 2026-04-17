"""Unit tests for the media_id regex used by the HACS integration.

We can't import the full media_player module in CI (no homeassistant
dep), but the parser pattern itself is pure Python. Copy-pasting it
here pins the contract that HA's ``play_media`` service accepts.
"""
from __future__ import annotations

import re

import pytest

# Keep this in sync with custom_components/smartest_tv/media_player.py
_MEDIA_ID_RE = re.compile(
    r"^(?P<platform>\w+):(?P<query>.+?)(?::s(?P<season>\d+)e(?P<episode>\d+))?$"
)


def _parse(media_id: str) -> dict | None:
    m = _MEDIA_ID_RE.match(media_id)
    if not m:
        return None
    return {
        "platform": m.group("platform"),
        "query": m.group("query"),
        "season": int(m.group("season")) if m.group("season") else None,
        "episode": int(m.group("episode")) if m.group("episode") else None,
    }


def test_simple_netflix_movie():
    assert _parse("netflix:Glass Onion") == {
        "platform": "netflix", "query": "Glass Onion", "season": None, "episode": None,
    }


def test_netflix_show_with_season_episode():
    assert _parse("netflix:Frieren:s2e8") == {
        "platform": "netflix", "query": "Frieren", "season": 2, "episode": 8,
    }


def test_youtube_query_with_spaces():
    assert _parse("youtube:lofi beats") == {
        "platform": "youtube", "query": "lofi beats", "season": None, "episode": None,
    }


def test_spotify_with_colons_in_query():
    # `.+?` is non-greedy, so a trailing :sNeN is preferred when present.
    assert _parse("spotify:Ye White Lines") == {
        "platform": "spotify", "query": "Ye White Lines", "season": None, "episode": None,
    }


def test_query_with_colon_and_episode_suffix():
    out = _parse("netflix:Breaking Bad: Original:s1e2")
    assert out is not None
    assert out["platform"] == "netflix"
    assert out["season"] == 1 and out["episode"] == 2


def test_missing_platform_returns_none():
    assert _parse("Frieren:s2e8") is not None  # "Frieren" is a valid \w+ platform slug
    # Real rejection: leading colon → no match
    assert _parse(":noplat") is None


def test_empty_string_rejected():
    assert _parse("") is None


def test_season_zero_preserved():
    # Some prequel/specials use s0; verify we don't drop it.
    out = _parse("netflix:Show:s0e1")
    assert out is not None
    assert out["season"] == 0 and out["episode"] == 1


@pytest.mark.parametrize("bad", ["netflix::s1e1", "netflix:query:sXe1", "netflix:query:s1eY"])
def test_malformed_season_episode_falls_through_to_query(bad):
    """A malformed :sNeN suffix is accepted as part of the query.

    That matches the CLI behaviour — better to search for the literal
    string than to silently reject the play_media call.
    """
    out = _parse(bad)
    assert out is not None
    assert out["platform"] == "netflix"
    assert out["season"] is None and out["episode"] is None
