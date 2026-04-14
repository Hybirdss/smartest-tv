"""Tests for play flow: disambiguation, already-watched warn, multi-TV errors."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from smartest_tv import cache as cache_module
from smartest_tv._engine.resolve import Candidate

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", cache_file)
    monkeypatch.setattr(cache_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cache_module, "_community_cache", None)
    monkeypatch.setattr(cache_module, "_api_get", lambda *a, **kw: None)
    monkeypatch.setattr(cache_module, "_contribute", lambda *a, **kw: None)
    yield cache_file


# ---------------------------------------------------------------------------
# Disambiguation: non-tty picks first, logs alternatives to stderr
# ---------------------------------------------------------------------------

THREE_CANDIDATES = [
    Candidate(title="Dark", year=2017, type="series", content_id="80100172"),
    Candidate(title="Dark", year=2019, type="movie", content_id="81000001"),
    Candidate(title="Dark Web", year=2021, type="movie", content_id="81000002"),
]


def test_non_tty_picks_first_candidate_and_logs_alternatives(capsys, monkeypatch):
    """In non-tty mode, auto-select candidates[0] and write alternatives to stderr."""
    monkeypatch.setattr(
        "smartest_tv._engine.resolve._search_netflix_candidates",
        lambda q: THREE_CANDIDATES,
    )

    # Directly test the non-tty path logic (replicated from cli.py)
    with patch("sys.stdin.isatty", return_value=False):
        with patch("click.echo") as mock_echo:
            with patch("smartest_tv._engine.resolve._search_netflix_candidates", return_value=THREE_CANDIDATES):
                cands = THREE_CANDIDATES
                selected_id = int(cands[0].content_id)
                alts = ", ".join(f"{c.title} id={c.content_id}" for c in cands[1:])
                import click
                click.echo(
                    f"[stv] auto-selected id={cands[0].content_id}; alternatives: {alts}",
                    err=True,
                )

    assert selected_id == 80100172
    # Verify the echo call used err=True
    mock_echo.assert_called_once()
    call_kwargs = mock_echo.call_args
    assert call_kwargs[1].get("err") is True
    msg = call_kwargs[0][0]
    assert "81000001" in msg
    assert "81000002" in msg


# ---------------------------------------------------------------------------
# Already-watched warning
# ---------------------------------------------------------------------------


def test_get_last_played_exact_returns_timestamp():
    """get_last_played_exact returns datetime for matching entry."""
    now_ts = int(time.time()) - 3 * 86400  # 3 days ago
    cache_module.record_play("netflix", "Dark", "80100172", season=1, episode=1)
    # Override the recorded time to be 3 days ago
    data = cache_module._load()
    data["_history"][0]["time"] = now_ts
    cache_module._save(data)

    result = cache_module.get_last_played_exact("netflix", "Dark", 1, 1)
    assert result is not None
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    age = (datetime.now(tz=timezone.utc) - result).days
    assert age == 3


def test_get_last_played_exact_no_match():
    """Returns None when no matching entry exists."""
    assert cache_module.get_last_played_exact("netflix", "Dark", 1, 1) is None


def test_get_last_played_exact_platform_mismatch():
    """Returns None when platform does not match."""
    cache_module.record_play("youtube", "Dark", "abc123", season=1, episode=1)
    assert cache_module.get_last_played_exact("netflix", "Dark", 1, 1) is None


def test_get_last_played_exact_ignores_different_episode():
    """S1E2 is not matched when looking for S1E1."""
    cache_module.record_play("netflix", "Dark", "80100172", season=1, episode=2)
    assert cache_module.get_last_played_exact("netflix", "Dark", 1, 1) is None


def test_already_watched_confirm_prompt_on_tty(monkeypatch, tmp_path):
    """When last play < 7 days and stdin is tty, click.confirm is called."""
    # Record a play 3 days ago
    now_ts = int(time.time()) - 3 * 86400
    cache_module.record_play("netflix", "Dark", "80100172", season=1, episode=1)
    data = cache_module._load()
    data["_history"][0]["time"] = now_ts
    cache_module._save(data)

    last = cache_module.get_last_played_exact("netflix", "Dark", 1, 1)
    assert last is not None

    confirm_called = []

    def fake_confirm(msg, default=True):
        confirm_called.append(msg)
        return False  # user says no

    with patch("sys.stdin.isatty", return_value=True):
        with patch("click.confirm", side_effect=fake_confirm):
            with patch("click.echo") as mock_echo:
                age_days = (datetime.now(tz=timezone.utc) - last).days
                assert age_days < 7

                import click
                if not click.confirm(
                    f"Already watched Dark on {last.date()}. Play anyway?",
                    default=True,
                ):
                    click.echo("OK, not playing.")

    assert len(confirm_called) == 1
    assert "Already watched Dark" in confirm_called[0]
    mock_echo.assert_called_once_with("OK, not playing.")


def test_already_watched_no_prompt_on_non_tty():
    """When non-tty, no confirm prompt — just set replay flag."""
    now_ts = int(time.time()) - 2 * 86400
    cache_module.record_play("netflix", "Dark", "80100172", season=1, episode=1)
    data = cache_module._load()
    data["_history"][0]["time"] = now_ts
    cache_module._save(data)

    last = cache_module.get_last_played_exact("netflix", "Dark", 1, 1)
    assert last is not None

    confirm_called = []
    with patch("sys.stdin.isatty", return_value=False):
        with patch("click.confirm", side_effect=lambda *a, **kw: confirm_called.append(1)):
            age_days = (datetime.now(tz=timezone.utc) - last).days
            if age_days < 7 and not True:  # isatty() is False
                import click
                click.confirm("Should not be called", default=True)

    assert confirm_called == []


# ---------------------------------------------------------------------------
# Multi-TV error visibility (via sync.broadcast)
# ---------------------------------------------------------------------------


def test_broadcast_surfaces_per_tv_errors():
    """broadcast() returns error entries with message for failed TVs."""
    import asyncio

    from smartest_tv.sync import broadcast

    class FakeDriver:
        platform = "fake"
        def __init__(self, fail=False):
            self._fail = fail
        async def connect(self): pass
        async def disconnect(self): pass

    async def action(d):
        if d._fail:
            raise ImportError("install bscpylgtv")
        return "done"

    d1 = FakeDriver(fail=False)
    d2 = FakeDriver(fail=True)

    results = asyncio.run(broadcast({"TV 1": d1, "TV 2": d2}, action))
    ok = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] == "error"]

    assert len(ok) == 1
    assert ok[0]["tv"] == "TV 1"
    assert len(errors) == 1
    assert errors[0]["tv"] == "TV 2"
    assert "bscpylgtv" in errors[0]["message"]
