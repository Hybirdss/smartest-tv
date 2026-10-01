"""cli._run translates connect failures into actionable errors.

The #1 user-facing failure — TV off/asleep or DHCP re-lease — used to
surface as a raw OSError traceback. _run now wraps it into a clean
one-line ClickException naming the two recovery commands. Logic errors
must keep propagating untouched.
"""

from __future__ import annotations

import asyncio

import click
import pytest

from smartest_tv import cli


def test_oserror_becomes_hinted_click_error():
    async def boom():
        raise OSError(113, "Connect call failed ('192.168.200.101', 3001)")

    with pytest.raises(click.ClickException) as ei:
        cli._run(boom())
    msg = str(ei.value)
    assert "Connection failed" in msg
    assert "stv doctor" in msg
    assert "stv setup" in msg


def test_timeout_becomes_hinted_click_error():
    async def slow():
        raise asyncio.TimeoutError()

    with pytest.raises(click.ClickException):
        cli._run(slow())


def test_success_value_passes_through():
    async def fine():
        return 42

    assert cli._run(fine()) == 42


def test_logic_errors_are_not_masked():
    async def bug():
        raise ValueError("bad episode number")

    with pytest.raises(ValueError):
        cli._run(bug())
