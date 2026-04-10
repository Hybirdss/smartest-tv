"""Audio mode for smartest-tv.

Play content on TVs with screens turned off — turns any TV into a
whole-home audio system without the light pollution.

Main API:
  audio_play(query, platform, rooms)   — play content + screen off
  audio_stop(rooms)                    — restore screens (screen on)
  audio_volume(room, level)            — set volume on a specific room
"""

from __future__ import annotations

from smartest_tv.apps import resolve_app
from smartest_tv.config import get_all_tv_names, get_group_members
from smartest_tv.drivers.factory import create_driver
from smartest_tv.resolve import resolve
from smartest_tv.sync import broadcast, connect_all


def _resolve_rooms(rooms: list[str] | None) -> list[str]:
    """Return TV names for the given rooms (or all TVs if rooms is None).

    Each element of *rooms* may be either a TV name or a group name; group
    names are transparently expanded.  Duplicates are deduplicated while
    preserving order.
    """
    if rooms is None:
        return get_all_tv_names()

    names: list[str] = []
    seen: set[str] = set()
    for r in rooms:
        try:
            members = get_group_members(r)
        except KeyError:
            members = [r]
        for m in members:
            if m not in seen:
                names.append(m)
                seen.add(m)
    return names


async def audio_play(
    query: str,
    platform: str = "youtube",
    rooms: list[str] | None = None,
) -> list[dict]:
    """Play content on target TVs with screens turned off (audio-only mode).

    Parameters
    ----------
    query:
        Search query or content title (e.g. ``"lo-fi hip hop radio"``).
    platform:
        Streaming platform: ``"youtube"``, ``"spotify"``, or ``"netflix"``.
        Defaults to ``"youtube"`` — best for music / ambient audio.
    rooms:
        TV names or group names to target.  ``None`` targets all configured TVs.

    Returns
    -------
    List of broadcast result dicts (one per TV) with keys
    ``"tv"``, ``"status"``, and ``"message"``.
    """
    tv_names = _resolve_rooms(rooms)
    content_id = resolve(platform, query)
    drivers, failures = await connect_all(tv_names, create_driver)

    async def _play(driver):
        tv_platform = driver.platform if hasattr(driver, "platform") else "lg"
        app_id, _ = resolve_app(platform, tv_platform)
        await driver.launch_app_deep(app_id, content_id)
        return f"Playing {query!r} on {platform}"

    play_results = await broadcast(drivers, _play)

    async def _screen_off(driver):
        await driver.screen_off()
        return "Screen off"

    screen_results = await broadcast(drivers, _screen_off)

    # Merge results: report error if either step failed
    merged: dict[str, dict] = {}
    for r in failures:
        merged[r["tv"]] = r
    for r in play_results:
        merged[r["tv"]] = r
    for r in screen_results:
        if r["tv"] in merged and r["status"] == "error":
            merged[r["tv"]]["status"] = "error"
            merged[r["tv"]]["message"] += f"; screen_off failed: {r['message']}"

    return list(merged.values())


async def audio_stop(rooms: list[str] | None = None) -> list[dict]:
    """Stop audio mode: turn screens back on.

    Parameters
    ----------
    rooms:
        TV names or group names to target.  ``None`` targets all configured TVs.

    Returns
    -------
    List of broadcast result dicts (one per TV).
    """
    tv_names = _resolve_rooms(rooms)
    drivers, failures = await connect_all(tv_names, create_driver)

    async def _screen_on(driver):
        await driver.screen_on()
        return "Screen on"

    return failures + await broadcast(drivers, _screen_on)


async def audio_volume(room: str, level: int) -> str:
    """Set volume for a specific room / TV.

    Parameters
    ----------
    room:
        TV name (as configured in config.toml).
    level:
        Volume level 0-100.

    Returns
    -------
    A confirmation string.
    """
    driver = create_driver(room)
    await driver.connect()
    await driver.set_volume(level)
    return f"Volume set to {level} on {room}"
