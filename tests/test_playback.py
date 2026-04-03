"""Tests for shared playback helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from smartest_tv.playback import launch_content


def test_launch_content_restarts_netflix_before_deep_link():
    driver = AsyncMock()

    asyncio.run(launch_content(driver, "netflix", "netflix-app", "82656797"))

    driver.close_app.assert_awaited_once_with("netflix-app")
    driver.launch_app_deep.assert_awaited_once_with("netflix-app", "82656797")


def test_launch_content_skips_close_for_youtube():
    driver = AsyncMock()

    asyncio.run(launch_content(driver, "youtube", "youtube-app", "abc123"))

    driver.close_app.assert_not_called()
    driver.launch_app_deep.assert_awaited_once_with("youtube-app", "abc123")
