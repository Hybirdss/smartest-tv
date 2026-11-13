"""Unit tests for the Apple TV+ resolver in smartest_tv.resolve — no network, no TV, no curl."""
from __future__ import annotations

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from smartest_tv import cache as cache_module
from smartest_tv import resolve as resolve_module
from smartest_tv.http import HttpResult
from smartest_tv.resolve import resolve_appletv

SHOW_ID = "umc.cmc.show00000000000000000000"
PARAMS = {
    "utscf": "OjAAAAEAAAAAAAMAEAAAACMAKwAtADgA",
    "utsk": "6e3013c6d6fae3c2::::::235656c069bb0efb",
    "caller": "web",
    "sf": "143441",
    "v": "101",
    "pfm": "web",
    "locale": "en-US",
}


def _ep(season: int, episode: int) -> dict:
    return {
        "id": f"umc.cmc.s{season}e{episode:02d}aaaaaaaaaaaaaaaaaaaaaaa",
        "seasonNumber": season,
        "episodeNumber": episode,
        "title": f"S{season}E{episode}",
    }


# Two seasons, 9 + 10 episodes, in the order the route returns them.
ALL_EPISODES = [_ep(1, n) for n in range(1, 10)] + [_ep(2, n) for n in range(1, 11)]


def _show_page(with_params: bool = True) -> str:
    """A show page like tv.apple.com renders it: params + a six-episode shelf."""
    shelf_items = [
        {"$kind": "EpisodeLockup", "id": e["id"], "title": e["title"]} for e in ALL_EPISODES[:6]
    ] + [{"$kind": "ShelfPaginationTrigger", "id": f"ShelfPaginationTrigger#{i}"} for i in range(6, 19)]
    first = {"data": {"uts": {"requiredParamsMap": {"Default": PARAMS}}}} if with_params else {"data": {}}
    data = {"data": [first, {"data": {"shelves": [{"id": "uts.marker.EpisodeList", "items": shelf_items}]}}]}
    return f'<html><script type="application/json" id="serialized-server-data">{json.dumps(data)}</script></html>'


def _fake_curl(show_page: str, route_ok: bool = True, route_body: str | None = None):
    """A curl() stand-in serving the search page, the show page and the episode route."""
    calls: list[tuple[str, dict | None]] = []

    def curl(url: str, headers: dict | None = None, **_kwargs) -> HttpResult:
        calls.append((url, headers))
        if url.startswith("https://tv.apple.com/search?"):
            return HttpResult(ok=True, body=f'<a href="/us/show/x/{SHOW_ID}">x</a>')
        if url.startswith("https://tv.apple.com/show/") and "/api/" not in url:
            return HttpResult(ok=True, body=show_page)
        if url.startswith(f"https://tv.apple.com/api/uts/v3/shows/{SHOW_ID}/episodes?"):
            if not route_ok:
                return HttpResult(ok=False, body="", error="timeout (10s)")
            if route_body is not None:
                return HttpResult(ok=True, body=route_body)
            skip, take = (int(x) for x in parse_qs(urlparse(url).query)["nextToken"][0].split(":"))
            return HttpResult(ok=True, body=json.dumps({"data": {"episodes": ALL_EPISODES[skip : skip + take]}}))
        return HttpResult(ok=False, body="", error=f"unexpected url {url}")

    return curl, calls


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Local cache only: no API lookups, no community cache, no contributions."""
    monkeypatch.setattr(cache_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cache_module, "CACHE_FILE", tmp_path / "cache.json")
    stored: dict[str, str] = {}
    monkeypatch.setattr(resolve_module.cache, "get", lambda platform, key: stored.get(f"{platform}/{key}"))
    monkeypatch.setattr(resolve_module.cache, "put", lambda platform, key, value: stored.__setitem__(f"{platform}/{key}", value))
    return stored


@pytest.fixture
def no_api_fallback(monkeypatch):
    """Make the hosted-API fallback observable instead of hitting the network."""
    calls: list[tuple] = []

    def fake(platform, query, season=None, episode=None, title_id=None):
        calls.append((platform, query, season, episode))
        return "FALLBACK"

    monkeypatch.setattr(resolve_module, "_api_resolve", fake)
    return calls


# ---------------------------------------------------------------------------
# Episodes past the server-rendered six, and seasons past the first
# ---------------------------------------------------------------------------


def test_episode_past_the_rendered_shelf(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 7) == _ep(1, 7)["id"]
    route_calls = [c for c in calls if "/episodes?" in c[0]]
    assert len(route_calls) == 1
    assert no_api_fallback == []


def test_second_season_needs_the_second_page(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 2, 3) == _ep(2, 3)["id"]
    tokens = [parse_qs(urlparse(c[0]).query)["nextToken"][0] for c in calls if "/episodes?" in c[0]]
    assert tokens == ["0:10", "10:10"]


def test_first_episode_without_season_or_episode(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter") == _ep(1, 1)["id"]


def test_route_request_carries_page_params_and_referer(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        resolve_appletv("Dark Matter", 1, 7)
    url, headers = next(c for c in calls if "/episodes?" in c[0])
    q = parse_qs(urlparse(url).query)
    assert q["utsk"] == [PARAMS["utsk"]]
    assert q["utscf"] == [PARAMS["utscf"]]
    assert q["sf"] == [PARAMS["sf"]]
    assert q["caller"] == ["web"]
    assert q["locale"] == [PARAMS["locale"]]  # the page's own, not a hardcoded one
    assert q["selectedSeasonEpisodesOnly"] == ["false"]
    assert headers["Referer"] == "https://tv.apple.com/"


def test_walk_stops_once_past_the_wanted_season(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 12) == "FALLBACK"  # S1 has 9 episodes
    tokens = [parse_qs(urlparse(c[0]).query)["nextToken"][0] for c in calls if "/episodes?" in c[0]]
    assert tokens == ["0:10"]  # page 1 already contained S2E1, no need to read on


def test_route_with_an_unexpected_shape_is_not_fatal(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page(), route_body=json.dumps({"data": {"episodes": {"items": ["x"]}}}))
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 2) == _ep(1, 2)["id"]  # shelf still answers
        assert resolve_appletv("Dark Matter", 1, 7) == "FALLBACK"


def test_result_is_cached_under_season_episode_key(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        resolve_appletv("Dark Matter", 1, 7)
        assert isolated_cache == {"appletv/dark-matter:s1e7": _ep(1, 7)["id"]}
        before = len(calls)
        assert resolve_appletv("Dark Matter", 1, 7) == _ep(1, 7)["id"]
    assert len(calls) == before  # served from cache, no requests


def test_unknown_episode_falls_back_to_the_api(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page())
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 3, 1) == "FALLBACK"
    assert no_api_fallback == [("appletv", "Dark Matter", 3, 1)]
    assert isolated_cache == {}


# ---------------------------------------------------------------------------
# Route unavailable: the rendered shelf still covers the first six episodes
# ---------------------------------------------------------------------------


def test_route_down_uses_the_shelf_for_rendered_episodes(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page(), route_ok=False)
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 2) == _ep(1, 2)["id"]
    assert no_api_fallback == []


def test_route_down_past_the_shelf_falls_back_to_the_api(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page(), route_ok=False)
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 7) == "FALLBACK"
    assert no_api_fallback == [("appletv", "Dark Matter", 1, 7)]


def test_route_down_episode_without_season_uses_the_shelf_position(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page(), route_ok=False)
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", None, 3) == _ep(1, 3)["id"]
    assert isolated_cache == {"appletv/dark-matter:s1e3": _ep(1, 3)["id"]}


def test_route_down_never_uses_the_shelf_for_a_later_season(isolated_cache, no_api_fallback):
    curl, _calls = _fake_curl(_show_page(), route_ok=False)
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 2, 1) == "FALLBACK"
    assert no_api_fallback == [("appletv", "Dark Matter", 2, 1)]
    assert isolated_cache == {}


def test_page_without_params_uses_the_shelf(isolated_cache, no_api_fallback):
    curl, calls = _fake_curl(_show_page(with_params=False))
    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Dark Matter", 1, 3) == _ep(1, 3)["id"]
    assert not any("/episodes?" in c[0] for c in calls)


def test_search_miss_falls_back_to_the_api(isolated_cache, no_api_fallback):
    def curl(url, headers=None, **_kwargs):
        return HttpResult(ok=True, body="<html>no shows here</html>")

    with patch("smartest_tv.http.curl", curl):
        assert resolve_appletv("Nonexistent Show", 1, 1) == "FALLBACK"
