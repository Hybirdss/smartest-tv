"""Tests for shared playback helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from smartest_tv.drivers.base import LaunchResult
from smartest_tv.playback import describe_launch, launch_content


def test_launch_content_restarts_netflix_before_deep_link():
    driver = AsyncMock()
    driver.launch_app_deep.return_value = LaunchResult.DEEP_LINK

    result = asyncio.run(launch_content(driver, "netflix", "netflix-app", "82656797"))

    driver.close_app.assert_awaited_once_with("netflix-app")
    driver.launch_app_deep.assert_awaited_once_with("netflix-app", "82656797")
    assert result is LaunchResult.DEEP_LINK


def test_launch_content_skips_close_for_youtube():
    driver = AsyncMock()

    asyncio.run(launch_content(driver, "youtube", "youtube-app", "abc123"))

    driver.close_app.assert_not_called()
    driver.launch_app_deep.assert_awaited_once_with("youtube-app", "abc123")


def test_launch_content_returns_none_for_legacy_drivers():
    """Drivers that don't report a LaunchResult must not break callers."""
    driver = AsyncMock()
    driver.launch_app_deep.return_value = None

    assert asyncio.run(launch_content(driver, "disney", "d+", "123")) is None


def test_describe_launch_levels():
    """Every outcome speaks, at the right severity (issue #20: no silence)."""
    cases = [
        (None, "info"),
        (LaunchResult.DIAL, "info"),
        (LaunchResult.DEEP_LINK, "info"),
        (LaunchResult.DEEP_LINK_UNVERIFIED, "warning"),
        (LaunchResult.APP_ONLY, "warning"),
        (LaunchResult.NATIVE, "warning"),
        (LaunchResult.FAILED, "error"),
    ]
    for result, level in cases:
        got_level, message = describe_launch(
            result, platform="netflix", query="Dark", tv_name="Living Room"
        )
        assert got_level == level, (result, got_level)
        assert message  # never an empty string — silence was the bug


def test_describe_launch_mentions_issue8_on_app_only():
    _, message = describe_launch(
        LaunchResult.APP_ONLY, platform="netflix", query="Dark", tv_name="X"
    )
    assert "issue #8" in message
    assert "pick the title manually" in message
