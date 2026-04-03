"""Unit tests for smartest_tv.resolve — no network, no TV, no curl."""
from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from smartest_tv.resolve import _slugify
from smartest_tv._engine.resolve import (
    _find_all_sequential_clusters,
    _scrape_netflix_all_seasons,
)


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


def test_slugify_basic():
    assert _slugify("Frieren") == "frieren"


def test_slugify_spaces():
    assert _slugify("Jujutsu Kaisen") == "jujutsu-kaisen"


def test_slugify_special_chars():
    assert _slugify("The Glory!") == "the-glory"


def test_slugify_leading_trailing_spaces():
    assert _slugify("  baby shark  ") == "baby-shark"


# ---------------------------------------------------------------------------
# _find_all_sequential_clusters
# ---------------------------------------------------------------------------


def test_clusters_empty():
    assert _find_all_sequential_clusters([]) == []


def test_clusters_single_run():
    ids = list(range(100, 110))  # 10 consecutive IDs
    result = _find_all_sequential_clusters(ids)
    assert result == [list(range(100, 110))]


def test_clusters_two_seasons():
    s1 = list(range(1000, 1010))   # S1: 10 eps
    s2 = list(range(2000, 2010))   # S2: 10 eps
    ids = s1 + s2
    result = _find_all_sequential_clusters(ids)
    assert len(result) == 2
    assert result[0] == s1
    assert result[1] == s2


def test_clusters_min_length_filters_noise():
    # 2-item run should be excluded (default min_length=3)
    noise = [500, 501]
    real = list(range(1000, 1010))
    ids = noise + real
    result = _find_all_sequential_clusters(ids)
    assert result == [real]


def test_clusters_exactly_min_length_included():
    ids = [10, 11, 12]  # exactly 3
    result = _find_all_sequential_clusters(ids)
    assert result == [[10, 11, 12]]


def test_clusters_below_min_length_excluded():
    ids = [10, 11]  # only 2
    result = _find_all_sequential_clusters(ids)
    assert result == []


def test_clusters_deduplicates_input():
    ids = [10, 10, 11, 11, 12, 12]
    result = _find_all_sequential_clusters(ids)
    assert result == [[10, 11, 12]]


def test_clusters_custom_min_length():
    ids = [10, 11]  # 2 items
    result = _find_all_sequential_clusters(ids, min_length=2)
    assert result == [[10, 11]]


# ---------------------------------------------------------------------------
# _scrape_netflix_all_seasons — HTML parsing (no real network)
# ---------------------------------------------------------------------------


def _make_html(episode_ids: list[int], season_ids: list[int] = ()) -> str:
    """Build a minimal Netflix-like HTML with __typename entries."""
    parts = []
    for vid in episode_ids:
        parts.append(f'"__typename":"Episode","videoId":{vid}')
    for vid in season_ids:
        parts.append(f'"__typename":"Season","videoId":{vid}')
    return "<html><script>" + ",".join(parts) + "</script></html>"


def _mock_curl(html: str):
    """Return a mock HttpResult with the given html."""
    from smartest_tv.http import HttpResult
    return HttpResult(ok=bool(html), body=html)


def _mock_curl_error():
    from smartest_tv.http import HttpResult
    return HttpResult(ok=False, body="", error="mock error")


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_episodes_only_no_season_ids(mock_curl):
    """Episode IDs form one cluster = one season."""
    ep_ids = list(range(81726715, 81726725))  # 10 episodes
    season_ids = [81726714]  # title/season container — should be excluded
    mock_curl.return_value = _mock_curl(_make_html(ep_ids, season_ids))

    seasons = _scrape_netflix_all_seasons(81726714)
    assert len(seasons) == 1
    assert seasons[0] == ep_ids


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_two_seasons(mock_curl):
    """Two sequential clusters → two seasons, sorted by first ID."""
    s1 = list(range(81726715, 81726725))
    s2 = list(range(82656790, 82656800))
    mock_curl.return_value = _mock_curl(_make_html(s1 + s2))

    seasons = _scrape_netflix_all_seasons(81726714)
    assert len(seasons) == 2
    assert seasons[0] == s1  # lower IDs first
    assert seasons[1] == s2


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_filters_season_and_show_typenames(mock_curl):
    """Season and Show __typename entries must NOT appear in episode results."""
    ep_ids = list(range(1000, 1010))
    html = _make_html(ep_ids)
    html = html.replace("</script>", '"__typename":"Show","videoId":999</script>')
    mock_curl.return_value = _mock_curl(html)

    seasons = _scrape_netflix_all_seasons(999)
    all_ids = [vid for cluster in seasons for vid in cluster]
    assert 999 not in all_ids


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_empty_html_returns_empty(mock_curl):
    mock_curl.return_value = _mock_curl("")
    seasons = _scrape_netflix_all_seasons(12345)
    assert seasons == []


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_no_episodes_in_html_returns_empty(mock_curl):
    html = "<html><script>no video ids here</script></html>"
    mock_curl.return_value = _mock_curl(html)
    seasons = _scrape_netflix_all_seasons(12345)
    assert seasons == []


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_timeout_returns_empty(mock_curl):
    mock_curl.return_value = _mock_curl_error()
    seasons = _scrape_netflix_all_seasons(12345)
    assert seasons == []


@patch("smartest_tv._engine.resolve.curl")
def test_scrape_oserror_returns_empty(mock_curl):
    mock_curl.return_value = _mock_curl_error()
    seasons = _scrape_netflix_all_seasons(12345)
    assert seasons == []


# ---------------------------------------------------------------------------
# title_id regex (the pattern used in resolve.py's web search)
# ---------------------------------------------------------------------------


def test_title_id_regex_matches_netflix_url():
    pattern = r"netflix\.com/title/(\d+)"
    text = 'href="https://www.netflix.com/title/81726714"'
    m = re.search(pattern, text)
    assert m is not None
    assert m.group(1) == "81726714"


def test_title_id_regex_no_match_on_other_url():
    pattern = r"netflix\.com/title/(\d+)"
    text = "https://www.imdb.com/title/tt1234567"
    assert re.search(pattern, text) is None
