"""The Android driver's deep-link templates, pinned per app.

Regression: the Apple TV+ template used the ``/show/`` path with the
*episode* id the resolver returns. The app accepted the URL and then did
nothing; only the episode path with ``?action=play`` starts playback.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("androidtvremote2")

from smartest_tv._engine.drivers.android import AndroidDriver  # noqa: E402


@pytest.fixture
def driver(tmp_path):
    d = AndroidDriver("192.0.2.10", cert_dir=str(tmp_path))
    d._remote = MagicMock()  # already "connected": _ensure() returns it as-is
    return d


@pytest.mark.asyncio
async def test_appletv_deep_link_plays_the_episode(driver):
    await driver.launch_app_deep("com.apple.atve.androidtv.appletv", "umc.cmc.52paqbqoy5648w4e81k0lrqqh")
    driver._remote.send_launch_app_command.assert_called_once_with(
        "https://tv.apple.com/us/episode/umc.cmc.52paqbqoy5648w4e81k0lrqqh?action=play"
    )


@pytest.mark.asyncio
async def test_netflix_deep_link_uses_the_title_path(driver):
    await driver.launch_app_deep("com.netflix.ninja", "80057281")
    driver._remote.send_launch_app_command.assert_called_once_with("https://www.netflix.com/title/80057281")


@pytest.mark.asyncio
async def test_appletv_url_is_stripped_to_its_id(driver):
    await driver.launch_app_deep(
        "com.apple.atve.androidtv.appletv",
        "https://tv.apple.com/us/episode/in-the-fires-of-dead-stars/umc.cmc.52paqbqoy5648w4e81k0lrqqh?showId=umc.cmc.4luj",
    )
    driver._remote.send_launch_app_command.assert_called_once_with(
        "https://tv.apple.com/us/episode/umc.cmc.52paqbqoy5648w4e81k0lrqqh?action=play"
    )
