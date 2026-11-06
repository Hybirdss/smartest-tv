"""launch_content with an unresolved title opens the app instead of crashing."""

from __future__ import annotations

import pytest

from smartest_tv.drivers.base import LaunchResult
from smartest_tv.playback import describe_launch, launch_content


class RecordingDriver:
    platform = "android"

    def __init__(self):
        self.calls: list[tuple] = []

    async def close_app(self, app_id):
        self.calls.append(("close_app", app_id))

    async def launch_app(self, app_id):
        self.calls.append(("launch_app", app_id))

    async def launch_app_deep(self, app_id, content_id):
        # Mirrors the LG / Android / Roku drivers: the id goes straight into a URL.
        content_id.startswith("x")
        self.calls.append(("launch_app_deep", app_id, content_id))


class RecordingSamsungDriver(RecordingDriver):
    """Samsung's launch_app_deep handles an empty id itself and verifies the launch."""

    platform = "samsung"

    async def launch_app_deep(self, app_id, content_id):
        self.calls.append(("launch_app_deep", app_id, content_id))
        return LaunchResult.APP_ONLY if content_id == "" else LaunchResult.DEEP_LINK


@pytest.mark.asyncio
@pytest.mark.parametrize("content_id", [None, ""])
async def test_unresolved_opens_app_and_reports_unresolved(content_id):
    d = RecordingDriver()
    result = await launch_content(d, "netflix", "com.netflix.ninja", content_id)
    assert result is LaunchResult.UNRESOLVED
    assert d.calls == [("launch_app", "com.netflix.ninja")]  # no Netflix restart, no deep link


@pytest.mark.asyncio
async def test_samsung_keeps_its_verified_empty_id_ladder():
    d = RecordingSamsungDriver()
    result = await launch_content(d, "netflix", "11101200001", None)
    assert result is LaunchResult.APP_ONLY
    assert d.calls == [("launch_app_deep", "11101200001", "")]


@pytest.mark.asyncio
async def test_resolved_content_id_still_deep_links():
    d = RecordingDriver()
    result = await launch_content(d, "youtube", "com.google.android.youtube.tv", "dQw4w9WgXcQ")
    assert result is None
    assert ("launch_app_deep", "com.google.android.youtube.tv", "dQw4w9WgXcQ") in d.calls


@pytest.mark.asyncio
async def test_resolved_netflix_still_restarts_the_app():
    d = RecordingDriver()
    await launch_content(d, "netflix", "com.netflix.ninja", "80057281")
    assert d.calls[0] == ("close_app", "com.netflix.ninja")


def test_describe_unresolved_is_a_self_contained_warning():
    level, message = describe_launch(
        LaunchResult.UNRESOLVED, platform="netflix", query="Dark Matter", tv_name="TCL"
    )
    assert level == "warning"
    assert "Netflix" in message and "Dark Matter" in message and "could not be resolved" in message
