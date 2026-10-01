"""Shared playback helpers."""

from __future__ import annotations

import asyncio

from smartest_tv.drivers.base import LaunchResult


async def launch_content(
    driver, platform: str, app_id: str, content_id: str
) -> LaunchResult | None:
    """Launch content on a TV driver, handling Netflix close->relaunch.

    Returns the driver's :class:`LaunchResult` when the driver reports one
    (Samsung), ``None`` otherwise — callers use :func:`describe_launch` to
    turn it into a human-facing line instead of guessing.
    """
    if platform.lower() == "netflix":
        try:
            await driver.close_app(app_id)
            await asyncio.sleep(2)
        except Exception:
            pass
    return await driver.launch_app_deep(app_id, content_id)


def describe_launch(
    result: LaunchResult | None,
    *,
    platform: str,
    query: str,
    tv_name: str = "",
) -> tuple[str, str]:
    """Map a LaunchResult to ``(level, message)`` for logs and the CLI.

    ``level`` is one of ``info`` / ``warning`` / ``error``. Issue #20's
    core complaint was silence: play_media looked successful while the TV
    did nothing. Every outcome now speaks, at the right severity.
    """
    label = f"'{query}' on {tv_name or 'the TV'}"
    app = platform.capitalize()

    if result is None:
        return "info", f"Playing {label}"
    if result is LaunchResult.DIAL:
        return "info", f"Playing {label} via DIAL"
    if result is LaunchResult.DEEP_LINK:
        return "info", f"Playing {label} via deep link"
    if result is LaunchResult.DEEP_LINK_UNVERIFIED:
        return (
            "warning",
            f"Sent deep link for {label}, but this TV exposes no way to "
            "verify the app started. If nothing plays, open the app manually.",
        )
    if result is LaunchResult.APP_ONLY:
        return (
            "warning",
            f"Opened {app} for {label}, but the TV ignored the deep link "
            "(Samsung firmware quirk, issue #8) — pick the title manually.",
        )
    if result is LaunchResult.NATIVE:
        return (
            "warning",
            f"Fell back to a plain {app} launch for {label} — the deep "
            "link was ignored; pick the title manually.",
        )
    return (
        "error",
        f"Failed to start {label} — the TV did not respond to any launch path.",
    )
