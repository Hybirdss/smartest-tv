"""Tests for remote TV driver and API server."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from smartest_tv.drivers.remote import RemoteDriver


@pytest.fixture
def driver():
    return RemoteDriver(url="http://192.168.1.50:8911")


def test_remote_driver_url_trailing_slash():
    d = RemoteDriver(url="http://192.168.1.50:8911/")
    assert d.url == "http://192.168.1.50:8911"


def test_remote_driver_platform():
    d = RemoteDriver(url="http://localhost:8911")
    assert d.platform == "remote"


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_connect_success(mock_run, driver):
    mock_run.return_value = MagicMock(
        stdout=json.dumps({"status": "ok", "name": "Friend TV", "platform": "lg"}),
    )
    import asyncio
    asyncio.run(driver.connect())
    mock_run.assert_called_once()
    assert "ping" in mock_run.call_args[0][0][-1]


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_connect_failure(mock_run, driver):
    mock_run.return_value = MagicMock(stdout="")
    import asyncio
    with pytest.raises(ConnectionError, match="not responding"):
        asyncio.run(driver.connect())


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_launch_app_deep(mock_run, driver):
    mock_run.return_value = MagicMock(
        stdout=json.dumps({"launched": "Netflix", "content_id": "82656797"}),
    )
    import asyncio
    asyncio.run(driver.launch_app_deep("netflix", "82656797"))

    call_args = mock_run.call_args[0][0]
    assert "/api/launch" in call_args[-1]
    # Check the JSON body contains the right data
    body_idx = call_args.index("-d") + 1
    body = json.loads(call_args[body_idx])
    assert body["app"] == "netflix"
    assert body["content_id"] == "82656797"


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_set_volume(mock_run, driver):
    mock_run.return_value = MagicMock(stdout=json.dumps({"volume": 25}))
    import asyncio
    asyncio.run(driver.set_volume(25))

    call_args = mock_run.call_args[0][0]
    assert "/api/volume" in call_args[-1]
    body_idx = call_args.index("-d") + 1
    body = json.loads(call_args[body_idx])
    assert body["level"] == 25


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_power_off(mock_run, driver):
    mock_run.return_value = MagicMock(stdout=json.dumps({"power": "off"}))
    import asyncio
    asyncio.run(driver.power_off())
    call_args = mock_run.call_args[0][0]
    assert "/api/power" in call_args[-1]


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_notify(mock_run, driver):
    mock_run.return_value = MagicMock(stdout=json.dumps({"notified": "hey!"}))
    import asyncio
    asyncio.run(driver.notify("hey!"))
    call_args = mock_run.call_args[0][0]
    assert "/api/notify" in call_args[-1]
    body_idx = call_args.index("-d") + 1
    body = json.loads(call_args[body_idx])
    assert body["message"] == "hey!"


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_get_volume(mock_run, driver):
    mock_run.return_value = MagicMock(stdout=json.dumps({"volume": 30, "muted": False}))
    import asyncio
    vol = asyncio.run(driver.get_volume())
    assert vol == 30


@patch("smartest_tv.drivers.remote.subprocess.run")
def test_status(mock_run, driver):
    mock_run.return_value = MagicMock(stdout=json.dumps({
        "current_app": "netflix",
        "volume": 20,
        "muted": False,
        "sound_output": "speaker",
    }))
    import asyncio
    s = asyncio.run(driver.status())
    assert s.current_app == "netflix"
    assert s.volume == 20


# ---------------------------------------------------------------------------
# Factory integration
# ---------------------------------------------------------------------------


def test_factory_creates_remote_driver(tmp_path, monkeypatch):
    """factory.create_driver returns RemoteDriver for platform=remote."""
    import smartest_tv.config as config_mod
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")

    (tmp_path / "config.toml").write_text("""
[tv.friend]
platform = "remote"
url = "http://10.0.0.5:8911"
    """)

    from smartest_tv.drivers.factory import create_driver
    d = create_driver("friend")
    assert isinstance(d, RemoteDriver)
    assert d.url == "http://10.0.0.5:8911"
