"""Unit tests for smartest_tv.scenes — no TV, no network required."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

import smartest_tv.scenes as scenes_module
from smartest_tv.scenes import (
    BUILTIN_SCENES,
    delete_custom_scene,
    get_scene,
    list_scenes,
    save_custom_scene,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_scenes(tmp_path, monkeypatch):
    """Redirect scenes file to a temp dir so tests don't touch ~/.config."""
    scenes_file = tmp_path / "scenes.json"
    monkeypatch.setattr(scenes_module, "SCENES_FILE", scenes_file)
    monkeypatch.setattr(scenes_module, "CONFIG_DIR", tmp_path)
    yield scenes_file


# ---------------------------------------------------------------------------
# list_scenes / get_scene
# ---------------------------------------------------------------------------


def test_builtin_scenes_present():
    scenes = list_scenes()
    assert "movie-night" in scenes
    assert "kids" in scenes
    assert "sleep" in scenes
    assert "music" in scenes


def test_builtin_scene_count():
    assert len(BUILTIN_SCENES) == 4


def test_get_scene_builtin():
    s = get_scene("movie-night")
    assert s is not None
    assert "steps" in s
    assert any(step["action"] == "volume" for step in s["steps"])


def test_get_scene_missing_returns_none():
    assert get_scene("nonexistent") is None


# ---------------------------------------------------------------------------
# Custom scene CRUD
# ---------------------------------------------------------------------------


def test_save_and_retrieve_custom_scene():
    save_custom_scene("work", "Work mode", [{"action": "volume", "value": 5}])
    scenes = list_scenes()
    assert "work" in scenes
    assert scenes["work"]["description"] == "Work mode"


def test_custom_overrides_builtin(isolated_scenes):
    # Saving a scene with same name as builtin should override it in list_scenes()
    save_custom_scene("sleep", "Custom sleep", [{"action": "screen_off"}])
    s = get_scene("sleep")
    assert s["description"] == "Custom sleep"


def test_delete_custom_scene():
    save_custom_scene("tmp", "Temp", [{"action": "notify", "message": "hi"}])
    delete_custom_scene("tmp")
    assert get_scene("tmp") is None


def test_delete_builtin_raises():
    with pytest.raises(KeyError, match="built-in"):
        delete_custom_scene("movie-night")


def test_delete_missing_raises():
    with pytest.raises(KeyError, match="not found"):
        delete_custom_scene("ghost")


def test_custom_scene_persists_to_file(isolated_scenes):
    save_custom_scene("party", "Party mode", [{"action": "volume", "value": 30}])
    data = json.loads(isolated_scenes.read_text())
    assert "party" in data
    assert data["party"]["steps"][0]["value"] == 30


# ---------------------------------------------------------------------------
# run_scene
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_scene_unknown_raises():
    from smartest_tv.scenes import run_scene
    with pytest.raises(KeyError, match="not found"):
        await run_scene("nonexistent")


@pytest.mark.asyncio
async def test_run_scene_volume_step():
    """run_scene volume step calls set_volume and returns result message."""
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()
    mock_driver.set_volume = AsyncMock()

    with patch("smartest_tv.scenes.run_scene.__module__"), \
         patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        # Inject a simple scene with one volume step
        save_custom_scene("vol-test", "test", [{"action": "volume", "value": 25}])
        results = await run_scene("vol-test")

    assert any("25" in r for r in results)


@pytest.mark.asyncio
async def test_run_scene_notify_step():
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()
    mock_driver.notify = AsyncMock()

    with patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        save_custom_scene("notif-test", "test", [{"action": "notify", "message": "Hello TV"}])
        results = await run_scene("notif-test")

    assert any("Hello TV" in r for r in results)


@pytest.mark.asyncio
async def test_run_scene_screen_off_step():
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()
    mock_driver.screen_off = AsyncMock()

    with patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        save_custom_scene("screen-test", "test", [{"action": "screen_off"}])
        results = await run_scene("screen-test")

    assert any("Screen off" in r for r in results)


@pytest.mark.asyncio
async def test_run_scene_unknown_action_skipped():
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()

    with patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        save_custom_scene("unk-test", "test", [{"action": "teleport"}])
        results = await run_scene("unk-test")

    assert any("teleport" in r and "skipped" in r for r in results)


@pytest.mark.asyncio
async def test_run_scene_keyerror_surfaces_not_crashes():
    """Missing required key in a custom step is reported per-step, not raised."""
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()
    mock_driver.set_volume = AsyncMock()
    mock_driver.notify = AsyncMock()

    with patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        save_custom_scene(
            "partial",
            "broken custom scene",
            [
                {"action": "volume", "value": 15},
                {"action": "notify"},  # missing "message" — used to raise KeyError
                {"action": "screen_off"},
            ],
        )
        results = await run_scene("partial")

    # First step should still have run, second step should report missing field,
    # third step should still execute (not short-circuited).
    assert any("Volume set to 15" in r for r in results)
    assert any("notify" in r and "missing" in r for r in results)
    assert any("Screen off" in r for r in results)
    mock_driver.set_volume.assert_awaited_once_with(15)
    mock_driver.screen_off.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_scene_webhook_rejects_non_http_scheme():
    """Webhook with file:// or javascript: scheme is refused per-step."""
    from smartest_tv.scenes import run_scene

    mock_driver = AsyncMock()
    mock_driver.connect = AsyncMock()

    with patch("smartest_tv.drivers.factory.create_driver", return_value=mock_driver):
        save_custom_scene(
            "ssrf",
            "attempted ssrf",
            [{"action": "webhook", "url": "file:///etc/passwd"}],
        )
        results = await run_scene("ssrf")

    assert any("refused" in r.lower() and "non-http" in r.lower() for r in results)
