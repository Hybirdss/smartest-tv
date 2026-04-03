"""Concurrent TV execution for multi-TV sync and party features.

Resolves content once, then launches on all target TVs simultaneously.
Handles partial failures gracefully — one TV failing doesn't stop the rest.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

from smartest_tv.drivers.base import TVDriver


async def broadcast(
    drivers: dict[str, TVDriver],
    action: Callable[[TVDriver], Coroutine[Any, Any, str | None]],
) -> list[dict[str, str]]:
    """Execute an async action on multiple TV drivers concurrently.

    Args:
        drivers: {tv_name: driver} — already connected or will connect.
        action: async fn(driver) -> result_message

    Returns:
        [{"tv": name, "status": "ok"|"error", "message": "..."}]
    """
    async def _one(name: str, driver: TVDriver) -> dict[str, str]:
        try:
            result = await action(driver)
            return {"tv": name, "status": "ok", "message": str(result or "done")}
        except Exception as e:
            return {"tv": name, "status": "error", "message": str(e)}

    results = await asyncio.gather(
        *[_one(name, driver) for name, driver in drivers.items()]
    )
    return list(results)


async def connect_all(
    tv_names: list[str],
    create_driver: Callable[[str | None], TVDriver],
) -> dict[str, TVDriver]:
    """Create and connect drivers for multiple TVs concurrently.

    Returns only successfully connected drivers.
    Failed connections are printed but don't stop the others.
    """
    async def _connect_one(name: str) -> tuple[str, TVDriver | None]:
        try:
            driver = create_driver(name)
            await driver.connect()
            return (name, driver)
        except Exception:
            return (name, None)

    results = await asyncio.gather(*[_connect_one(n) for n in tv_names])
    return {name: d for name, d in results if d is not None}
