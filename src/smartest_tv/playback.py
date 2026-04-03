"""Shared playback helpers."""

from __future__ import annotations

import asyncio


async def launch_content(driver, platform: str, app_id: str, content_id: str) -> None:
    """Launch content on a TV driver, handling Netflix close->relaunch."""
    if platform.lower() == "netflix":
        try:
            await driver.close_app(app_id)
            await asyncio.sleep(2)
        except Exception:
            pass
    await driver.launch_app_deep(app_id, content_id)
