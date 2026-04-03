"""Concurrent TV execution for multi-TV sync and party features.

Resolves content once, then launches on all target TVs simultaneously.
Handles partial failures gracefully — one TV failing doesn't stop the rest.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Awaitable, Callable, Coroutine

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
    create_driver: Callable[[str | None], TVDriver | Awaitable[TVDriver]],
) -> tuple[dict[str, TVDriver], list[dict[str, str]]]:
    """Create and connect drivers for multiple TVs concurrently.

    Returns connected drivers plus per-TV connection failures.
    """
    async def _connect_one(
        name: str,
    ) -> tuple[str, TVDriver | None, dict[str, str] | None]:
        try:
            maybe_driver = create_driver(name)
            if inspect.isawaitable(maybe_driver):
                driver = await maybe_driver
            else:
                driver = maybe_driver
                await driver.connect()
            return (name, driver, None)
        except Exception as e:
            return (
                name,
                None,
                {"tv": name, "status": "error", "message": str(e)},
            )

    results = await asyncio.gather(*[_connect_one(n) for n in tv_names])
    drivers = {name: d for name, d, _ in results if d is not None}
    failures = [failure for _, _, failure in results if failure is not None]
    return drivers, failures
