"""Tests for fetch_netflix_trending and fetch_youtube_trending (mocked network)."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

import smartest_tv.cache as cache_mod
from smartest_tv.resolve import fetch_netflix_trending, fetch_youtube_trending


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect cache I/O to a temp directory and reset in-memory community cache."""
    monkeypatch.setenv("STV_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(cache_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(cache_mod, "_community_cache", {})
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


def _mock_curl(stdout: str):
    """Return a mock subprocess.run result with given stdout."""
    result = MagicMock()
    result.stdout = stdout
    result.returncode = 0
    return result


def test_netflix_trending_json_ld_parsing():
    with patch("subprocess.run", return_value=_mock_curl(NETFLIX_JSON_HTML)):
        items = fetch_netflix_trending(limit=10)
    assert len(items) == 3
    assert items[0]["rank"] == 1
    assert items[0]["title"] == "Frieren"
    assert items[0]["category"] == "TV"
    assert items[2]["title"] == "Parasite"


def test_netflix_trending_limit():
    with patch("subprocess.run", return_value=_mock_curl(NETFLIX_JSON_HTML)):
        items = fetch_netflix_trending(limit=2)
    assert len(items) == 2


def test_netflix_trending_html_table_fallback():
    """When JSON-LD not present, falls back to HTML table parsing."""
    with patch("subprocess.run", return_value=_mock_curl(NETFLIX_HTML_TABLE)):
        items = fetch_netflix_trending(limit=10)
    assert len(items) == 2
    titles = [i["title"] for i in items]
    assert "Bridgerton" in titles
    assert "Squid Game" in titles


def test_netflix_trending_cached(tmp_path):
    """Results are cached for 24h; second call should not call subprocess."""
    with patch("subprocess.run", return_value=_mock_curl(NETFLIX_JSON_HTML)) as mock_run:
        fetch_netflix_trending()
        fetch_netflix_trending()
    # subprocess.run only called once (second hit is from cache)
    assert mock_run.call_count == 1


def test_netflix_trending_network_error():
    """Network failure returns empty list gracefully."""
    with patch("subprocess.run", side_effect=OSError("no network")):
        items = fetch_netflix_trending()
    assert isinstance(items, list)


def test_netflix_trending_empty_html():
    with patch("subprocess.run", return_value=_mock_curl("")):
        items = fetch_netflix_trending()
    assert isinstance(items, list)


# ---------------------------------------------------------------------------
# YouTube trending
# ---------------------------------------------------------------------------

YTDLP_OUTPUT = '{"entries": [{"id": "abc123", "title": "Trending Video 1", "uploader": "Channel A"}, {"id": "def456", "title": "Trending Video 2", "uploader": "Channel B"}, {"id": "ghi789", "title": "Trending Video 3", "uploader": "Channel C"}]}'


def _yt_run_side_effect(cmd, **kwargs):
    """Return valid yt-dlp JSON for yt-dlp calls, empty for everything else."""
    if cmd and "yt-dlp" in cmd[0]:
        r = MagicMock()
        r.stdout = YTDLP_OUTPUT
        r.returncode = 0
        return r
    r = MagicMock()
    r.stdout = ""
    r.returncode = 0
    return r


def test_youtube_trending_ytdlp_parsing():
    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        with patch("subprocess.run", side_effect=_yt_run_side_effect):
            items = fetch_youtube_trending(limit=10)

    assert len(items) == 3
    assert items[0]["video_id"] == "abc123"
    assert items[0]["title"] == "Trending Video 1"
    assert items[0]["rank"] == 1


def test_youtube_trending_limit():
    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        with patch("subprocess.run", side_effect=_yt_run_side_effect):
            items = fetch_youtube_trending(limit=2)
    assert len(items) == 2


def test_youtube_trending_ytdlp_not_found():
    """Falls back gracefully when yt-dlp is missing."""
    with patch("shutil.which", return_value=None):
        with patch("subprocess.run", return_value=_mock_curl("")):
            items = fetch_youtube_trending()
    assert isinstance(items, list)


def test_youtube_trending_cached():
    """Results are cached for 1h; second call should not call yt-dlp again."""
    yt_calls = []

    def counting_side_effect(cmd, **kwargs):
        if cmd and "yt-dlp" in cmd[0]:
            yt_calls.append(1)
            r = MagicMock()
            r.stdout = YTDLP_OUTPUT
            return r
        r = MagicMock()
        r.stdout = ""
        return r

    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        with patch("subprocess.run", side_effect=counting_side_effect):
            fetch_youtube_trending()
            fetch_youtube_trending()
    assert len(yt_calls) == 1


def test_youtube_trending_network_error():
    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        with patch("subprocess.run", side_effect=OSError("no network")):
            items = fetch_youtube_trending()
    assert isinstance(items, list)
