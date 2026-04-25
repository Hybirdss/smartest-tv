"""Tests for the DIAL helper module (issue #8 Tier 1).

Covers the pure parsing/body-building helpers and the HTTP launch path
(via mocked ``aiohttp.ClientSession``). SSDP socket I/O in
``discover_application_url`` is left out of unit coverage — it's a thin
wrapper around ``socket.sendto``/``loop.sock_recvfrom`` and the
testable bit (header parsing) is exercised via ``parse_application_url``
directly.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from smartest_tv._engine import dial

# -- parse_application_url -------------------------------------------------


class TestParseApplicationUrl:
    def test_extracts_url_case_insensitively(self):
        response = (
            "HTTP/1.1 200 OK\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            "Application-URL: http://192.168.1.50:8080/ws/app/\r\n"
            "ST: urn:dial-multiscreen-org:service:dial:1\r\n"
            "\r\n"
        )
        assert dial.parse_application_url(response) == "http://192.168.1.50:8080/ws/app"

    def test_lowercase_header_name_works(self):
        response = "HTTP/1.1 200 OK\r\napplication-url: http://10.0.0.5:8080/apps\r\n\r\n"
        assert dial.parse_application_url(response) == "http://10.0.0.5:8080/apps"

    def test_strips_trailing_slash(self):
        response = "Application-URL: http://tv.local/dial/\r\n"
        assert dial.parse_application_url(response) == "http://tv.local/dial"

    def test_returns_none_when_missing(self):
        response = "HTTP/1.1 200 OK\r\nST: ssdp:all\r\n\r\n"
        assert dial.parse_application_url(response) is None

    def test_returns_none_for_empty_value(self):
        response = "Application-URL:   \r\n"
        assert dial.parse_application_url(response) is None

    def test_does_not_swallow_subsequent_headers(self):
        # Regression guard: the regex must stop at end of line, not consume
        # following headers into the URL.
        response = (
            "Application-URL: http://192.168.1.50:8080/ws/app\r\n"
            "Server: SHP, UPnP/1.0, Samsung UPnP SDK/1.0\r\n"
        )
        assert dial.parse_application_url(response) == "http://192.168.1.50:8080/ws/app"


# -- netflix_body ----------------------------------------------------------


class TestNetflixBody:
    def test_numeric_id_wraps_into_m_param(self):
        assert (
            dial.netflix_body("80100172")
            == "m=https://www.netflix.com/watch/80100172&source_type=4"
        )

    def test_passes_through_prebuilt_m_string(self):
        prebuilt = "m=https://www.netflix.com/watch/80100172&source_type=4"
        assert dial.netflix_body(prebuilt) == prebuilt

    def test_extracts_id_from_watch_url(self):
        assert "80100172" in dial.netflix_body("https://www.netflix.com/watch/80100172")

    def test_extracts_id_from_title_url(self):
        assert "70234439" in dial.netflix_body(
            "https://www.netflix.com/title/70234439?something=else"
        )


# -- youtube_body ----------------------------------------------------------


class TestYouTubeBody:
    def test_raw_video_id(self):
        assert dial.youtube_body("dQw4w9WgXcQ") == "v=dQw4w9WgXcQ"

    def test_extracts_from_watch_url(self):
        assert dial.youtube_body("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == (
            "v=dQw4w9WgXcQ"
        )

    def test_extracts_from_short_url(self):
        assert dial.youtube_body("https://youtu.be/dQw4w9WgXcQ") == "v=dQw4w9WgXcQ"


# -- launch ----------------------------------------------------------------


class _MockResponse:
    def __init__(self, status: int):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def _session_with_status(status: int) -> MagicMock:
    session = MagicMock()
    session.post = MagicMock(return_value=_MockResponse(status))
    return session


@pytest.mark.asyncio
async def test_launch_posts_to_app_endpoint_and_returns_true_on_201():
    session = _session_with_status(201)
    ok = await dial.launch(
        "http://192.168.1.50:8080/ws/app",
        "Netflix",
        "m=https://www.netflix.com/watch/80100172&source_type=4",
        session=session,
    )
    assert ok is True
    args, kwargs = session.post.call_args
    assert args[0] == "http://192.168.1.50:8080/ws/app/Netflix"
    assert kwargs["data"] == b"m=https://www.netflix.com/watch/80100172&source_type=4"
    assert kwargs["headers"]["Content-Type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_launch_returns_false_on_4xx():
    session = _session_with_status(404)
    ok = await dial.launch(
        "http://tv.local/dial", "Netflix", "v=x", session=session
    )
    assert ok is False


@pytest.mark.asyncio
async def test_launch_returns_false_on_network_error():
    import aiohttp

    session = MagicMock()
    session.post = MagicMock(side_effect=aiohttp.ClientConnectorError(MagicMock(), OSError()))
    ok = await dial.launch(
        "http://tv.local/dial", "YouTube", "v=abc", session=session
    )
    assert ok is False


@pytest.mark.asyncio
async def test_launch_normalizes_trailing_slash():
    session = _session_with_status(200)
    await dial.launch(
        "http://tv.local/dial/", "YouTube", "v=abc", session=session
    )
    assert session.post.call_args.args[0] == "http://tv.local/dial/YouTube"
