"""Unit tests for smartest_tv.insights — no TV, no network required."""
from __future__ import annotations

import time

import pytest

import smartest_tv.insights as insights_module
from smartest_tv.insights import (
    format_report,
    get_insights,
    get_screen_time,
    get_subscription_value,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_history(count=10, platform="netflix", hours_ago_start=0):
    """Generate fake history entries."""
    entries = []
    now = int(time.time())
    for i in range(count):
        entries.append({
            "platform": platform,
            "query": f"Show {i % 3}",  # 3 unique shows
            "content_id": str(80000000 + i),
            "time": now - (hours_ago_start + i) * 3600,
            "season": 1,
            "episode": i + 1,
        })
    return entries


# ---------------------------------------------------------------------------
# get_insights
# ---------------------------------------------------------------------------


def test_insights_empty_history(monkeypatch):
    """Empty history returns zeros/empty collections."""
    monkeypatch.setattr(insights_module, "get_history", lambda n: [])
    result = get_insights("week")
    assert result["total_plays"] == 0
    assert result["total_hours_estimate"] == 0.0
    assert result["by_platform"] == {}
    assert result["top_shows"] == []
    assert result["binge_sessions"] == 0
    assert result["peak_hour"] is None


def test_insights_basic_counts(monkeypatch):
    """total_plays matches number of entries within the period."""
    history = _make_history(count=8, platform="netflix", hours_ago_start=0)
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    assert result["total_plays"] == 8


def test_insights_platform_breakdown(monkeypatch):
    """by_platform correctly counts each platform."""
    history = (
        _make_history(count=5, platform="netflix")
        + _make_history(count=3, platform="youtube")
    )
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    assert result["by_platform"]["netflix"] == 5
    assert result["by_platform"]["youtube"] == 3


def test_insights_top_shows(monkeypatch):
    """top_shows ranks shows by frequency (most-played first)."""
    history = _make_history(count=9, platform="netflix", hours_ago_start=0)
    # 9 entries, 3 unique shows — each show "Show 0", "Show 1", "Show 2"
    # Show 0: indices 0,3,6 → 3 plays
    # Show 1: indices 1,4,7 → 3 plays
    # Show 2: indices 2,5,8 → 3 plays
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    top_shows = result["top_shows"]
    assert len(top_shows) <= 5
    # All three shows should appear
    show_names = [s for s, _ in top_shows]
    assert "Show 0" in show_names
    assert "Show 1" in show_names
    assert "Show 2" in show_names


def test_insights_binge_detection(monkeypatch):
    """Binge detection: 3+ episodes of the same show in one day counts as a session."""
    now = int(time.time())
    # 5 entries for the same show on the same day (within the last hour)
    history = [
        {
            "platform": "netflix",
            "query": "Dark",
            "content_id": str(80000000 + i),
            "time": now - i * 600,  # 10 minutes apart — all within 1 hour
            "season": 1,
            "episode": i + 1,
        }
        for i in range(5)
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    assert result["binge_sessions"] >= 1


def test_insights_no_binge_two_episodes(monkeypatch):
    """2 episodes of the same show in a day does NOT count as a binge."""
    now = int(time.time())
    history = [
        {
            "platform": "netflix",
            "query": "Dark",
            "content_id": "80000001",
            "time": now - 600,
            "season": 1,
            "episode": 1,
        },
        {
            "platform": "netflix",
            "query": "Dark",
            "content_id": "80000002",
            "time": now - 1200,
            "season": 1,
            "episode": 2,
        },
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    assert result["binge_sessions"] == 0


def test_insights_peak_hour(monkeypatch):
    """peak_hour is the clock-hour with the most plays."""
    now = int(time.time())
    # Create entries clustered at a specific hour (UTC midnight +/- some hours).
    # We pin the timestamp to be exactly 22:00 UTC on a recent day.
    import datetime as dt
    today_utc = dt.datetime.now(dt.timezone.utc).replace(hour=22, minute=30, second=0, microsecond=0)
    base_ts = int(today_utc.timestamp())

    history = [
        {
            "platform": "youtube",
            "query": "video",
            "content_id": str(i),
            "time": base_ts - i * 60,  # all within the same hour
        }
        for i in range(5)
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_insights("week")
    # The insights module converts timestamps to UTC; verify the peak_hour
    # matches what _dt() would compute for the same timestamps.
    from datetime import datetime, timezone
    expected_hour = datetime.fromtimestamp(base_ts, tz=timezone.utc).hour
    assert result["peak_hour"] == expected_hour


def test_insights_period_filter_day(monkeypatch):
    """period='day' only counts entries from the last 24 hours."""
    now = int(time.time())
    recent = [
        {
            "platform": "netflix",
            "query": "Show 0",
            "content_id": "1",
            "time": now - 3600,  # 1 hour ago — inside 'day'
        }
    ]
    old = [
        {
            "platform": "netflix",
            "query": "Show 0",
            "content_id": "2",
            "time": now - 48 * 3600,  # 2 days ago — outside 'day'
        }
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: recent + old)
    result = get_insights("day")
    assert result["total_plays"] == 1


def test_insights_period_filter_week(monkeypatch):
    """period='week' only counts entries from the last 7 days."""
    now = int(time.time())
    inside = [
        {
            "platform": "netflix",
            "query": "Show 0",
            "content_id": "1",
            "time": now - 5 * 86400,  # 5 days ago — inside 'week'
        }
    ]
    outside = [
        {
            "platform": "netflix",
            "query": "Show 0",
            "content_id": "2",
            "time": now - 8 * 86400,  # 8 days ago — outside 'week'
        }
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: inside + outside)
    result = get_insights("week")
    assert result["total_plays"] == 1


# ---------------------------------------------------------------------------
# get_screen_time
# ---------------------------------------------------------------------------


def test_screen_time_basic(monkeypatch):
    """total_minutes is the sum of per-platform minute estimates."""
    history = _make_history(count=4, platform="netflix")
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_screen_time("week")
    # netflix = 45 min/play × 4 plays = 180 min
    assert result["total_minutes"] == 180
    assert result["period"] == "week"


def test_screen_time_by_hour(monkeypatch):
    """by_hour groups plays into clock-hour buckets."""
    import datetime as dt
    today = dt.datetime.now(dt.timezone.utc).replace(minute=30, second=0, microsecond=0)
    h20 = today.replace(hour=20)
    h21 = today.replace(hour=21)

    history = [
        {"platform": "youtube", "query": "a", "content_id": "1", "time": int(h20.timestamp())},
        {"platform": "youtube", "query": "b", "content_id": "2", "time": int(h20.timestamp()) + 300},
        {"platform": "youtube", "query": "c", "content_id": "3", "time": int(h21.timestamp())},
    ]
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_screen_time("week")
    assert result["by_hour"].get(20, 0) == 2
    assert result["by_hour"].get(21, 0) == 1


def test_screen_time_empty(monkeypatch):
    """Empty history returns zeros and None for first/last play."""
    monkeypatch.setattr(insights_module, "get_history", lambda n: [])
    result = get_screen_time("day")
    assert result["total_minutes"] == 0
    assert result["first_play"] is None
    assert result["last_play"] is None


# ---------------------------------------------------------------------------
# get_subscription_value
# ---------------------------------------------------------------------------


def test_subscription_value_good(monkeypatch):
    """Frequent watching → 'good_value' verdict."""
    # 10 netflix plays/month × 45 min = 7.5 hours → $17.99/7.5h ≈ $2.40/h < $3
    history = _make_history(count=10, platform="netflix", hours_ago_start=0)
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_subscription_value("netflix", monthly_cost=17.99)
    assert result["verdict"] == "good_value"
    assert result["plays_this_month"] == 10
    assert result["platform"] == "netflix"


def test_subscription_value_bad(monkeypatch):
    """Rare watching → 'consider_canceling' verdict."""
    # 1 play/month × 45 min = 0.75 hours → $17.99/0.75h ≈ $24/h > $8
    history = _make_history(count=1, platform="netflix", hours_ago_start=0)
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    result = get_subscription_value("netflix", monthly_cost=17.99)
    assert result["verdict"] == "consider_canceling"


def test_subscription_value_no_history(monkeypatch):
    """Zero plays → 'consider_canceling' (no cost_per_hour)."""
    monkeypatch.setattr(insights_module, "get_history", lambda n: [])
    result = get_subscription_value("netflix", monthly_cost=17.99)
    assert result["verdict"] == "consider_canceling"
    assert result["cost_per_hour"] is None
    assert result["plays_this_month"] == 0


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


def test_format_report_output(monkeypatch):
    """format_report returns a non-empty string containing key info."""
    history = _make_history(count=6, platform="netflix")
    monkeypatch.setattr(insights_module, "get_history", lambda n: history)
    insights = get_insights("week")
    report = format_report(insights)
    assert isinstance(report, str)
    assert len(report) > 0
    assert "6" in report  # total_plays
    assert "netflix" in report.lower()


def test_format_report_empty(monkeypatch):
    """format_report handles empty insights without raising."""
    monkeypatch.setattr(insights_module, "get_history", lambda n: [])
    insights = get_insights("week")
    report = format_report(insights)
    assert isinstance(report, str)
    assert "0 plays" in report
