"""Scene preset system for smartest-tv.

A scene is a named sequence of TV actions (steps) run in order.
Built-in presets are hardcoded here; user presets live in
~/.config/smartest-tv/scenes.json.
"""

from __future__ import annotations

import json
from typing import Any

from smartest_tv.config import CONFIG_DIR
from smartest_tv.playback import launch_content

SCENES_FILE = CONFIG_DIR / "scenes.json"

BUILTIN_SCENES: dict[str, dict[str, Any]] = {
    "movie-night": {
        "description": "Dim the lights, set volume, cinema mode",
        "steps": [
            {"action": "volume", "value": 20},
            {"action": "notify", "message": "Movie night! Enjoy the show."},
        ],
    },
    "kids": {
        "description": "Safe content, volume limit",
        "steps": [
            {"action": "volume", "value": 15},
            {"action": "play", "platform": "youtube", "query": "Cocomelon"},
        ],
    },
    "sleep": {
        "description": "Screen off, ambient sounds, auto-off timer",
        "steps": [
            {"action": "volume", "value": 10},
            {"action": "notify", "message": "Sleep timer set. Good night."},
        ],
    },
    "music": {
        "description": "Screen off, play music",
        "steps": [
            {"action": "screen_off"},
            {"action": "notify", "message": "Music mode on."},
        ],
    },
}


# ---------------------------------------------------------------------------
# Custom scene persistence
# ---------------------------------------------------------------------------


def _load_custom() -> dict[str, Any]:
    if SCENES_FILE.exists():
        try:
            return json.loads(SCENES_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_custom(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SCENES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def list_scenes() -> dict[str, dict[str, Any]]:
    """Return all scenes (builtin + custom). Custom overrides builtin."""
    scenes = dict(BUILTIN_SCENES)
    scenes.update(_load_custom())
    return scenes


def get_scene(name: str) -> dict[str, Any] | None:
    """Look up a scene by name. Returns None if not found."""
    return list_scenes().get(name)


def save_custom_scene(name: str, description: str, steps: list[dict]) -> None:
    """Persist a custom scene."""
    data = _load_custom()
    data[name] = {"description": description, "steps": steps}
    _save_custom(data)


def delete_custom_scene(name: str) -> None:
    """Delete a custom scene. Raises KeyError if not found or is builtin."""
    if name in BUILTIN_SCENES:
        raise KeyError(f"'{name}' is a built-in scene and cannot be deleted.")
    data = _load_custom()
    if name not in data:
        raise KeyError(f"Scene '{name}' not found.")
    del data[name]
    _save_custom(data)


# ---------------------------------------------------------------------------
# Scene execution engine
# ---------------------------------------------------------------------------


async def run_scene(name: str, tv_name: str | None = None) -> list[str]:
    """Execute a scene by name. Returns a list of result messages.

    Each step's ``action`` maps to a TV operation:
      - volume      → set_volume(value)
      - notify      → notify(message)
      - screen_off  → screen_off()
      - screen_on   → screen_on()
      - play        → resolve + launch (platform + query required)
      - webhook     → HTTP POST to url
    """
    scene = get_scene(name)
    if not scene:
        raise KeyError(f"Scene '{name}' not found. Run: stv scene list")

    from smartest_tv.drivers.base import TVDriver

    # Lazy-import driver only if TV actions are present
    _driver: TVDriver | None = None

    async def _get_driver() -> TVDriver:
        nonlocal _driver
        if _driver is None:
            from smartest_tv.drivers.factory import create_driver
            _driver = create_driver(tv_name)
            await _driver.connect()
        return _driver

    results: list[str] = []

    for idx, step in enumerate(scene.get("steps", []), 1):
        action = step.get("action")
        # Per-step try/except so a malformed custom step (missing key,
        # unreachable platform, bad URL) doesn't abort the whole scene
        # halfway through — the user would otherwise see volume changed
        # but no app launched, with a raw KeyError and no indication of
        # which step broke.
        try:
            if action == "volume":
                d = await _get_driver()
                value = int(step["value"])
                await d.set_volume(value)
                results.append(f"[{idx}] Volume set to {value}.")

            elif action == "notify":
                d = await _get_driver()
                msg = step["message"]
                await d.notify(msg)
                results.append(f"[{idx}] Notification: {msg}")

            elif action == "screen_off":
                d = await _get_driver()
                await d.screen_off()
                results.append(f"[{idx}] Screen off.")

            elif action == "screen_on":
                d = await _get_driver()
                await d.screen_on()
                results.append(f"[{idx}] Screen on.")

            elif action == "play":
                from smartest_tv.apps import resolve_app
                from smartest_tv.resolve import resolve as do_resolve

                platform = step["platform"]
                query = step["query"]
                season = step.get("season")
                episode = step.get("episode")

                content_id = do_resolve(platform, query, season, episode)
                d = await _get_driver()
                app_id, app_name = resolve_app(platform, d.platform)
                await launch_content(d, platform, app_id, content_id)

                from smartest_tv import cache as _cache
                _cache.record_play(platform, query, content_id, season, episode)
                results.append(f"[{idx}] Playing {query} on {app_name}.")

            elif action == "webhook":
                from smartest_tv.http import curl as _curl
                url = step["url"]
                # Reject non-http(s) schemes — a custom scene file with a
                # file:// or javascript: URL is either a mistake or an
                # exfiltration attempt via curl.
                from urllib.parse import urlparse as _urlparse
                scheme = _urlparse(url).scheme.lower()
                if scheme not in ("http", "https"):
                    results.append(f"[{idx}] Webhook: refused non-http(s) URL.")
                    continue
                r = _curl(url, method="POST", timeout=10)
                if r.ok:
                    results.append(f"[{idx}] Webhook {url}: OK")
                else:
                    results.append(f"[{idx}] Webhook {url}: failed ({r.error or 'unknown'})")

            else:
                results.append(f"[{idx}] Unknown action '{action}' — skipped.")

        except KeyError as exc:
            results.append(
                f"[{idx}] {action!r} failed: missing required field {exc} — skipped."
            )
        except (ValueError, TypeError) as exc:
            results.append(f"[{idx}] {action!r} failed: {exc} — skipped.")
        except Exception as exc:  # noqa: BLE001 — surface driver errors to user
            results.append(f"[{idx}] {action!r} failed: {type(exc).__name__}: {exc}")

    return results
