"""Watch Intelligence module for smartest-tv.

Analyzes TV viewing history stored in ~/.config/smartest-tv/cache.json
(under the ``_history`` key) and produces human-readable reports, screen-time
summaries, and subscription-value scores.

Main API:
  get_insights(period)            — comprehensive viewing report
  get_screen_time(period)         — screen-time breakdown by hour
  get_subscription_value(...)     — cost-per-hour for a platform
  format_report(insights)         — plain-text rendering of get_insights()
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

from smartest_tv.cache import get_history

# Minutes-per-play estimates, keyed by platform
_MINUTES_PER_PLAY: dict[str, float] = {
    "netflix": 45.0,
    "youtube": 15.0,
    "spotify": 3.0,
}

# Hours-per-play (derived from minutes, used for hour estimates)
_HOURS_PER_PLAY: dict[str, float] = {
    k: v / 60.0 for k, v in _MINUTES_PER_PLAY.items()
}

_PERIOD_SECONDS: dict[str, int] = {
    "day": 86_400,
    "week": 7 * 86_400,
    "month": 30 * 86_400,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_ts() -> int:
    """Current Unix timestamp (UTC)."""
    return int(datetime.now(timezone.utc).timestamp())


def _cutoff(period: str) -> int:
    """Unix timestamp marking the start of *period* relative to now."""
    seconds = _PERIOD_SECONDS.get(period, _PERIOD_SECONDS["week"])
    return _now_ts() - seconds


def _filter_period(entries: list[dict], period: str) -> list[dict]:
    """Return entries whose ``time`` field falls within *period*."""
    cut = _cutoff(period)
    return [e for e in entries if isinstance(e.get("time"), (int, float)) and e["time"] >= cut]


def _dt(entry: dict) -> datetime:
    """Parse an entry's ``time`` field into a UTC datetime."""
    return datetime.fromtimestamp(entry["time"], tz=timezone.utc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_insights(period: str = "week") -> dict[str, Any]:
    """Return a comprehensive viewing report for the given period.

    Parameters
    ----------
    period:
        One of ``"day"``, ``"week"``, or ``"month"``.

    Returns
    -------
    dict with keys:
        period, total_plays, total_hours_estimate, by_platform, by_day,
        top_shows, binge_sessions, peak_hour, streak_days
    """
    all_entries = get_history(50)
    entries = _filter_period(all_entries, period)

    total_plays = len(entries)

    # Hours estimate
    total_hours: float = sum(
        _HOURS_PER_PLAY.get(e.get("platform", ""), 0.25)
        for e in entries
    )
    total_hours = round(total_hours, 1)

    # By platform
    by_platform: dict[str, int] = {}
    for e in entries:
        p = e.get("platform", "")
        if p:
            by_platform[p] = by_platform.get(p, 0) + 1

    # By day-of-week
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    by_day: dict[str, int] = {d: 0 for d in day_names}
    for e in entries:
        try:
            dow = day_names[_dt(e).weekday()]
            by_day[dow] += 1
        except (OSError, OverflowError, ValueError):
            pass

    # Top 5 shows by play count
    show_counter: Counter = Counter()
    for e in entries:
        q = e.get("query", "").strip()
        if q:
            show_counter[q] += 1
    top_shows = show_counter.most_common(5)

    # Binge sessions: 3+ episodes of the same show in a single calendar day
    # Group entries by (show, date)
    show_day_counts: dict[tuple[str, str], int] = defaultdict(int)
    for e in entries:
        q = e.get("query", "").strip()
        if not q:
            continue
        try:
            date_str = _dt(e).strftime("%Y-%m-%d")
            show_day_counts[(q, date_str)] += 1
        except (OSError, OverflowError, ValueError):
            pass
    binge_sessions = sum(1 for v in show_day_counts.values() if v >= 3)

    # Peak hour (0-23)
    hour_counter: Counter = Counter()
    for e in entries:
        try:
            hour_counter[_dt(e).hour] += 1
        except (OSError, OverflowError, ValueError):
            pass
    peak_hour: int | None = hour_counter.most_common(1)[0][0] if hour_counter else None

    # Streak: consecutive days (ending today) with at least one play
    streak_days = _compute_streak(entries)

    return {
        "period": period,
        "total_plays": total_plays,
        "total_hours_estimate": total_hours,
        "by_platform": by_platform,
        "by_day": by_day,
        "top_shows": top_shows,
        "binge_sessions": binge_sessions,
        "peak_hour": peak_hour,
        "streak_days": streak_days,
    }


def _compute_streak(entries: list[dict]) -> int:
    """Count consecutive days ending today that contain at least one entry."""
    today = datetime.now(timezone.utc).date()
    active_days: set = set()
    for e in entries:
        try:
            active_days.add(_dt(e).date())
        except (OSError, OverflowError, ValueError):
            pass

    streak = 0
    day = today
    while day in active_days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_screen_time(period: str = "day") -> dict[str, Any]:
    """Return a screen-time breakdown useful for family/kids monitoring.

    Parameters
    ----------
    period:
        One of ``"day"``, ``"week"``, or ``"month"``.

    Returns
    -------
    dict with keys:
        period, total_minutes, by_platform, by_hour, first_play, last_play
    """
    all_entries = get_history(50)
    entries = _filter_period(all_entries, period)

    # Total minutes
    total_minutes: float = sum(
        _MINUTES_PER_PLAY.get(e.get("platform", ""), 15.0)
        for e in entries
    )

    # By platform (minutes)
    by_platform: dict[str, float] = {}
    for e in entries:
        p = e.get("platform", "")
        mins = _MINUTES_PER_PLAY.get(p, 15.0)
        by_platform[p] = by_platform.get(p, 0.0) + mins

    # Round to ints for readability
    by_platform_int: dict[str, int] = {k: round(v) for k, v in by_platform.items()}

    # By hour: plays per clock-hour
    by_hour: dict[int, int] = {}
    for e in entries:
        try:
            h = _dt(e).hour
            by_hour[h] = by_hour.get(h, 0) + 1
        except (OSError, OverflowError, ValueError):
            pass

    # First and last play times (HH:MM local)
    first_play: str | None = None
    last_play: str | None = None
    if entries:
        valid_times = sorted(
            e["time"] for e in entries
            if isinstance(e.get("time"), (int, float))
        )
        if valid_times:
            def _fmt(ts: float) -> str:
                return datetime.fromtimestamp(ts).strftime("%H:%M")

            first_play = _fmt(valid_times[0])
            last_play = _fmt(valid_times[-1])

    return {
        "period": period,
        "total_minutes": round(total_minutes),
        "by_platform": by_platform_int,
        "by_hour": by_hour,
        "first_play": first_play,
        "last_play": last_play,
    }


def get_subscription_value(
    platform: str = "netflix",
    monthly_cost: float = 17.99,
) -> dict[str, Any]:
    """Analyze whether a streaming subscription is worth its monthly cost.

    Parameters
    ----------
    platform:
        Platform to analyze (e.g. ``"netflix"``, ``"youtube"``, ``"spotify"``).
    monthly_cost:
        Monthly subscription price in USD.

    Returns
    -------
    dict with keys:
        platform, monthly_cost, plays_this_month, estimated_hours,
        cost_per_hour, verdict
    """
    all_entries = get_history(50)
    month_entries = _filter_period(all_entries, "month")
    platform_entries = [e for e in month_entries if e.get("platform") == platform]

    plays = len(platform_entries)
    hours_per_play = _HOURS_PER_PLAY.get(platform, 0.25)
    estimated_hours = round(plays * hours_per_play, 2)

    if estimated_hours > 0:
        cost_per_hour = round(monthly_cost / estimated_hours, 2)
    else:
        cost_per_hour = None

    # Verdict thresholds
    if cost_per_hour is None:
        verdict = "consider_canceling"
    elif cost_per_hour < 3.0:
        verdict = "good_value"
    elif cost_per_hour <= 8.0:
        verdict = "ok"
    else:
        verdict = "consider_canceling"

    return {
        "platform": platform,
        "monthly_cost": monthly_cost,
        "plays_this_month": plays,
        "estimated_hours": estimated_hours,
        "cost_per_hour": cost_per_hour,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(insights: dict[str, Any]) -> str:
    """Format the output of get_insights() as a compact plain-text report.

    Uses simple ASCII bar charts (█) and avoids Markdown syntax so the
    output looks clean in terminals and notification popups alike.

    Parameters
    ----------
    insights:
        The dict returned by :func:`get_insights`.

    Returns
    -------
    A multi-line string ready to print or log.
    """
    period = insights.get("period", "week")
    total_plays = insights.get("total_plays", 0)
    total_hours = insights.get("total_hours_estimate", 0.0)
    by_platform: dict[str, int] = insights.get("by_platform", {})
    top_shows: list[tuple[str, int]] = insights.get("top_shows", [])
    binge_sessions = insights.get("binge_sessions", 0)
    peak_hour = insights.get("peak_hour")
    streak_days = insights.get("streak_days", 0)

    lines: list[str] = []

    # Header with date range
    now = datetime.now(timezone.utc)
    period_seconds = _PERIOD_SECONDS.get(period, _PERIOD_SECONDS["week"])
    start = now - timedelta(seconds=period_seconds)
    period_label = period.capitalize()
    date_range = f"{start.strftime('%b %-d')} - {now.strftime('%b %-d')}"
    lines.append(f"{period_label} in Review ({date_range})")
    lines.append("\u2500" * 33)

    lines.append(f"{total_plays} plays · ~{total_hours} hours")
    lines.append("")

    # Platform breakdown
    if by_platform:
        lines.append("Platform breakdown:")
        max_count = max(by_platform.values()) if by_platform else 1
        bar_width = 12
        platform_order = sorted(by_platform, key=lambda k: by_platform[k], reverse=True)
        label_width = max(len(p.capitalize()) for p in platform_order)
        for plat in platform_order:
            count = by_platform[plat]
            filled = round(bar_width * count / max_count) if max_count else 0
            bar = "\u2588" * filled
            label = plat.capitalize().ljust(label_width)
            lines.append(f"  {label}  {bar:<{bar_width}} {count}")
        lines.append("")

    # Top shows
    if top_shows:
        lines.append("Top shows:")
        for i, (show, count) in enumerate(top_shows, 1):
            plural = "play" if count == 1 else "plays"
            lines.append(f"  {i}. {show} ({count} {plural})")
        lines.append("")

    # Footer stats
    if peak_hour is not None:
        # Convert 24h to 12h with am/pm
        if peak_hour == 0:
            hour_str = "12am"
        elif peak_hour < 12:
            hour_str = f"{peak_hour}am"
        elif peak_hour == 12:
            hour_str = "12pm"
        else:
            hour_str = f"{peak_hour - 12}pm"
        lines.append(f"Peak viewing: {hour_str}")

    lines.append(f"Binge sessions: {binge_sessions}")
    lines.append(f"Watch streak: {streak_days} day{'s' if streak_days != 1 else ''}")

    return "\n".join(lines)
