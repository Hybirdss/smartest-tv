"""Tests for the browser driver."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from smartest_tv.drivers.browser import BrowserDriver


@pytest.fixture
def driver():
    return BrowserDriver()


@pytest.mark.asyncio
async def test_launch_netflix(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("netflix", "80114792")
        mock_open.assert_called_once_with("https://www.netflix.com/watch/80114792")


@pytest.mark.asyncio
async def test_launch_youtube(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("youtube", "dQw4w9WgXcQ")
        mock_open.assert_called_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_launch_spotify_uri(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("spotify", "spotify:track:abc123")
        mock_open.assert_called_once_with("https://open.spotify.com/track/abc123")


@pytest.mark.asyncio
async def test_launch_spotify_direct(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("spotify", "4iV5W9uYEdYUVa79Axb7Rh")
        mock_open.assert_called_once_with("https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh")


@pytest.mark.asyncio
async def test_launch_unknown_content(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("unknown_app", "some-id")
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        assert "some-id" in url


@pytest.mark.asyncio
async def test_launch_http_url(driver):
    with patch("smartest_tv.drivers.browser.webbrowser.open") as mock_open:
        await driver.launch_app_deep("custom", "https://example.com/video")
        mock_open.assert_called_once_with("https://example.com/video")


@pytest.mark.asyncio
async def test_status(driver):
    s = await driver.status()
    assert s.current_app == "browser"
    assert s.powered is True


@pytest.mark.asyncio
async def test_info(driver):
    i = await driver.info()
    assert i.platform == "browser"


@pytest.mark.asyncio
async def test_connect_disconnect_noop(driver):
    await driver.connect()
    await driver.disconnect()


@pytest.mark.asyncio
async def test_list_apps(driver):
    apps = await driver.list_apps()
    names = [a.id for a in apps]
    assert "netflix" in names
    assert "youtube" in names
    assert "spotify" in names


def test_factory_no_config():
    """When no TV is configured, factory returns BrowserDriver."""
    from unittest.mock import patch as _patch
    with _patch("smartest_tv.drivers.factory.get_tv_config", return_value={}):
        from smartest_tv.drivers.factory import create_driver
        d = create_driver()
        assert isinstance(d, BrowserDriver)


def test_factory_browser_platform():
    """Explicit browser platform in config."""
    from unittest.mock import patch as _patch
    with _patch("smartest_tv.drivers.factory.get_tv_config", return_value={"platform": "browser"}):
        from smartest_tv.drivers.factory import create_driver
        d = create_driver()
        assert isinstance(d, BrowserDriver)


def test_factory_tv_name_browser():
    """--tv browser bypasses config lookup entirely."""
    from smartest_tv.drivers.factory import create_driver
    d = create_driver(tv_name="browser")
    assert isinstance(d, BrowserDriver)
