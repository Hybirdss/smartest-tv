"""api._run_async works from sync and async contexts (py3.14 compat)."""

from __future__ import annotations

import asyncio

from smartest_tv.api import _run_async


async def _value(v):
    await asyncio.sleep(0)
    return v


def test_run_async_from_sync_context():
    assert _run_async(_value(7)) == 7


def test_run_async_from_running_loop():
    async def main():
        # Called from inside a running loop — must not deadlock or raise.
        return await asyncio.to_thread(_run_async, _value(9))

    assert asyncio.run(main()) == 9
