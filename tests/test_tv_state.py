"""Tests for tv_state and tv_state_watch MCP tools."""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

# Stub fastmcp before importing server so the optional dep isn't required.
if "fastmcp" not in sys.modules:
    _fmcp = types.ModuleType("fastmcp")

    class _FastMCP:
        def __init__(self, *a, **kw): pass
        def tool(self):
            def decorator(fn): return fn
            return decorator

    class _Context:
        pass

    _fmcp.FastMCP = _FastMCP
    _fmcp.Context = _Context
    sys.modules["fastmcp"] = _fmcp

from smartest_tv import server  # noqa: E402
from smartest_tv.drivers.base import TVStatus  # noqa: E402


def _make_mock_driver(st: TVStatus) -> MagicMock:
    d = MagicMock()
    d.platform = "roku"
    d.status = AsyncMock(return_value=st)
    return d


@pytest.mark.asyncio
async def test_tv_state_returns_expected_keys(monkeypatch):
    st = TVStatus(
        current_app="Netflix",
        volume=30,
        muted=False,
        powered=True,
        title="Stranger Things",
        position_s=120,
        duration_s=3600,
        play_state="playing",
    )
    mock_driver = _make_mock_driver(st)
    monkeypatch.setattr(server, "_get_driver", AsyncMock(return_value=mock_driver))

    result = await server.tv_state("living room")

    assert result["app"] == "Netflix"
    assert result["title"] == "Stranger Things"
    assert result["position_seconds"] == 120
    assert result["duration_seconds"] == 3600
    assert result["play_state"] == "playing"
    assert result["volume"] == 30
    assert result["mute"] is False
    assert result["power_state"] == "on"
    assert result["driver"] == "roku"
    assert result["target_tv"] == "living room"
    assert result["fetched_at"].endswith("Z")
    assert result["app_id"] is None
    assert result["subtitle"] is None
    assert result["hdmi_input"] is None


@pytest.mark.asyncio
async def test_tv_state_powered_false_gives_unknown(monkeypatch):
    st = TVStatus(powered=False)
    mock_driver = _make_mock_driver(st)
    monkeypatch.setattr(server, "_get_driver", AsyncMock(return_value=mock_driver))

    result = await server.tv_state(None)
    assert result["power_state"] == "unknown"


@pytest.mark.asyncio
async def test_tv_state_watch_calls_snapshot_n_times(monkeypatch):
    call_count = 0

    async def fake_snapshot(tv_name):
        nonlocal call_count
        call_count += 1
        return {"snapshot": call_count, "target_tv": tv_name}

    monkeypatch.setattr(server, "_snapshot", fake_snapshot)

    async def noop_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", noop_sleep)

    result = await server.tv_state_watch(tv_name="bedroom", interval=0, count=3, ctx=None)

    assert call_count == 3
    assert result == {"snapshot": 3, "target_tv": "bedroom"}


@pytest.mark.asyncio
async def test_tv_state_watch_reports_progress(monkeypatch):
    async def fake_snapshot(tv_name):
        return {"snapshot": 1}

    monkeypatch.setattr(server, "_snapshot", fake_snapshot)

    async def noop_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", noop_sleep)

    progress_calls: list[tuple] = []

    ctx = MagicMock()
    ctx.report_progress = AsyncMock(side_effect=lambda cur, total, data: progress_calls.append((cur, total)))

    await server.tv_state_watch(tv_name=None, interval=0, count=3, ctx=ctx)

    assert len(progress_calls) == 3
    assert progress_calls[0] == (1, 3)
    assert progress_calls[2] == (3, 3)
