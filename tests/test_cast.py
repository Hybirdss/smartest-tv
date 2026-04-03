"""Tests for _parse_cast_url URL parsing logic."""

import pytest

from smartest_tv.cli import _parse_cast_url


# ---------------------------------------------------------------------------
# Netflix
# ---------------------------------------------------------------------------

def test_netflix_watch_url():
    assert _parse_cast_url("https://www.netflix.com/watch/82656797") == ("netflix", "82656797")


def test_netflix_watch_url_no_www():
    assert _parse_cast_url("https://netflix.com/watch/12345") == ("netflix", "12345")


def test_netflix_title_url():
    assert _parse_cast_url("https://www.netflix.com/title/81726714") == ("netflix", "title:81726714")


def test_netflix_title_url_no_www():
    assert _parse_cast_url("https://netflix.com/title/99999") == ("netflix", "title:99999")


def test_netflix_bad_path():
    with pytest.raises(ValueError, match="netflix"):
        _parse_cast_url("https://www.netflix.com/browse")


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def test_youtube_watch_url():
    assert _parse_cast_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == ("youtube", "dQw4w9WgXcQ")


def test_youtube_watch_url_no_www():
    assert _parse_cast_url("https://youtube.com/watch?v=dQw4w9WgXcQ") == ("youtube", "dQw4w9WgXcQ")


def test_youtube_short_url():
    assert _parse_cast_url("https://youtu.be/dQw4w9WgXcQ") == ("youtube", "dQw4w9WgXcQ")


def test_youtube_short_url_with_params():
    # Extra query params after the path should not break parsing
    assert _parse_cast_url("https://youtu.be/dQw4w9WgXcQ?t=42") == ("youtube", "dQw4w9WgXcQ")


def test_youtube_missing_v_param():
    with pytest.raises(ValueError, match="YouTube"):
        _parse_cast_url("https://www.youtube.com/channel/UCxyz")


# ---------------------------------------------------------------------------
# Spotify
# ---------------------------------------------------------------------------

def test_spotify_track_url():
    assert _parse_cast_url("https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz") == (
        "spotify", "spotify:track:3bbjDFVu9BtFtGD2fZpVfz"
    )


def test_spotify_album_url():
    assert _parse_cast_url("https://open.spotify.com/album/5poA9SAx0Xiz1cd17fWBLS") == (
        "spotify", "spotify:album:5poA9SAx0Xiz1cd17fWBLS"
    )


def test_spotify_playlist_url():
    assert _parse_cast_url("https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO") == (
        "spotify", "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO"
    )


def test_spotify_artist_url():
    assert _parse_cast_url("https://open.spotify.com/artist/0TnOYISbd1XYRBk9myaseg") == (
        "spotify", "spotify:artist:0TnOYISbd1XYRBk9myaseg"
    )


def test_spotify_bad_path():
    with pytest.raises(ValueError, match="Spotify"):
        _parse_cast_url("https://open.spotify.com/user/someuser")


# ---------------------------------------------------------------------------
# Unsupported / bad URLs
# ---------------------------------------------------------------------------

def test_unsupported_domain():
    with pytest.raises(ValueError, match="Unsupported"):
        _parse_cast_url("https://example.com/watch/12345")


def test_unsupported_disney():
    with pytest.raises(ValueError, match="Unsupported"):
        _parse_cast_url("https://www.disneyplus.com/movies/raya/foo")


def test_plain_string_no_scheme():
    with pytest.raises(ValueError):
        _parse_cast_url("netflix.com/watch/12345")
