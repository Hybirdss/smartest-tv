"""Tests for fetch_netflix_trending and fetch_youtube_trending (mocked network)."""

from unittest.mock import patch

import pytest

import smartest_tv.cache as cache_mod
import smartest_tv.http as http_mod
from smartest_tv.resolve import fetch_netflix_trending, fetch_youtube_trending


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect cache I/O to a temp directory and reset in-memory community cache."""
    monkeypatch.setenv("STV_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(cache_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(cache_mod, "_community_cache", {})
    monkeypatch.setattr(cache_mod, "_api_get", lambda *a, **kw: None)
    monkeypatch.setattr(cache_mod, "_contribute", lambda *a, **kw: None)
    yield


# ---------------------------------------------------------------------------
# Netflix trending
# ---------------------------------------------------------------------------

NETFLIX_JSON_HTML = """
<html><body>
<script>
window.__data = {"weekly_top10": [
  {"rank": 1, "show_title": "Frieren", "category": "TV"},
  {"rank": 2, "show_title": "The Glory", "category": "TV"},
  {"rank": 3, "show_title": "Parasite", "category": "Film"}
]}
</script>
</body></html>
"""

NETFLIX_HTML_TABLE = """
<html><body>
<table>
  <tr>
    <td class="rank">1</td>
    <td class="show-title">Bridgerton</td>
    <td class="category">TV</td>
  </tr>
  <tr>
    <td class="rank">2</td>
    <td class="show-title">Squid Game</td>
    <td class="category">TV</td>
  </tr>
</table>
</body></html>
"""


def _mock_http_result(body: str):
    """Return a mock HttpResult."""
    return http_mod.HttpResult(ok=True, body=body)


def _mock_http_error():
    return http_mod.HttpResult(ok=False, body="", error="mock error")


def test_netflix_trending_json_ld_parsing():
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result(NETFLIX_JSON_HTML)):
        items = fetch_netflix_trending(limit=10)
    assert len(items) == 3
    assert items[0]["rank"] == 1
    assert items[0]["title"] == "Frieren"
    assert items[0]["category"] == "TV"
    assert items[2]["title"] == "Parasite"


def test_netflix_trending_limit():
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result(NETFLIX_JSON_HTML)):
        items = fetch_netflix_trending(limit=2)
    assert len(items) == 2


def test_netflix_trending_html_table_fallback():
    """When JSON-LD not present, falls back to HTML table parsing."""
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result(NETFLIX_HTML_TABLE)):
        items = fetch_netflix_trending(limit=10)
    assert len(items) == 2
    titles = [i["title"] for i in items]
    assert "Bridgerton" in titles
    assert "Squid Game" in titles


def test_netflix_trending_cached(tmp_path):
    """Results are cached for 24h; second call should not call curl."""
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result(NETFLIX_JSON_HTML)) as mock_curl:
        fetch_netflix_trending()
        fetch_netflix_trending()
    # curl only called once (second hit is from cache)
    assert mock_curl.call_count == 1


def test_netflix_trending_network_error():
    """Network failure returns empty list gracefully."""
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_error()):
        items = fetch_netflix_trending()
    assert isinstance(items, list)


def test_netflix_trending_empty_html():
    with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result("")):
        items = fetch_netflix_trending()
    assert isinstance(items, list)


# ---------------------------------------------------------------------------
# YouTube trending
# ---------------------------------------------------------------------------

YTDLP_OUTPUT = '{"entries": [{"id": "abc123", "title": "Trending Video 1", "uploader": "Channel A"}, {"id": "def456", "title": "Trending Video 2", "uploader": "Channel B"}, {"id": "ghi789", "title": "Trending Video 3", "uploader": "Channel C"}]}'


def _mock_ytdlp_result():
    return http_mod.HttpResult(ok=True, body=YTDLP_OUTPUT)


def test_youtube_trending_ytdlp_parsing():
    with patch("smartest_tv._engine.resolve.ytdlp", return_value=_mock_ytdlp_result()):
        with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
            items = fetch_youtube_trending(limit=10)

    assert len(items) == 3
    assert items[0]["video_id"] == "abc123"
    assert items[0]["title"] == "Trending Video 1"
    assert items[0]["rank"] == 1


def test_youtube_trending_limit():
    with patch("smartest_tv._engine.resolve.ytdlp", return_value=_mock_ytdlp_result()):
        with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
            items = fetch_youtube_trending(limit=2)
    assert len(items) == 2


def test_youtube_trending_ytdlp_not_found():
    """Falls back gracefully when yt-dlp is missing."""
    with patch("shutil.which", return_value=None):
        with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_result("")):
            items = fetch_youtube_trending()
    assert isinstance(items, list)


def test_youtube_trending_cached():
    """Results are cached for 1h; second call should not call yt-dlp again."""
    with patch("smartest_tv._engine.resolve.ytdlp", return_value=_mock_ytdlp_result()) as mock_yt:
        with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
            fetch_youtube_trending()
            fetch_youtube_trending()
    assert mock_yt.call_count == 1


def test_youtube_trending_network_error():
    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        with patch("smartest_tv._engine.resolve.ytdlp", return_value=_mock_http_error()):
            with patch("smartest_tv._engine.resolve.curl", return_value=_mock_http_error()):
                items = fetch_youtube_trending()
    assert isinstance(items, list)
