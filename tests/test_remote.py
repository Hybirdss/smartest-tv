"""Tests for remote TV driver and API server."""

import asyncio
import json
from unittest.mock import patch

import pytest

from smartest_tv.drivers.remote import RemoteDriver
from smartest_tv.http import HttpResult


@pytest.fixture
def driver():
    return RemoteDriver(url="http://192.168.1.50:8911")


def _ok(data: dict) -> HttpResult:
    return HttpResult(ok=True, body=json.dumps(data))


def _empty() -> HttpResult:
    return HttpResult(ok=False, body="", error="timeout")


def test_remote_driver_url_trailing_slash():
    d = RemoteDriver(url="http://192.168.1.50:8911/")
    assert d.url == "http://192.168.1.50:8911"


def test_remote_driver_platform():
    d = RemoteDriver(url="http://localhost:8911")
    assert d.platform == "remote"


def test_remote_driver_api_key():
    d = RemoteDriver(url="http://localhost:8911", api_key="stv_secret")
    assert d.api_key == "stv_secret"
    headers = d._headers()
    assert headers["Authorization"] == "Bearer stv_secret"


@patch("smartest_tv.drivers.remote.curl")
def test_connect_success(mock_curl, driver):
    mock_curl.return_value = _ok({"status": "ok", "name": "Friend TV", "platform": "lg"})
    asyncio.run(driver.connect())
    mock_curl.assert_called_once()
    assert "ping" in mock_curl.call_args[0][0]


@patch("smartest_tv.drivers.remote.curl")
def test_connect_failure(mock_curl, driver):
    mock_curl.return_value = _empty()
    with pytest.raises(ConnectionError, match="not responding"):
        asyncio.run(driver.connect())


@patch("smartest_tv.drivers.remote.curl")
def test_launch_app_deep(mock_curl, driver):
    mock_curl.return_value = _ok({"launched": "Netflix", "content_id": "82656797"})
    asyncio.run(driver.launch_app_deep("netflix", "82656797"))

    call_args = mock_curl.call_args
    assert "/api/launch" in call_args[0][0]


@patch("smartest_tv.drivers.remote.curl")
def test_set_volume(mock_curl, driver):
    mock_curl.return_value = _ok({"volume": 25})
    asyncio.run(driver.set_volume(25))
    assert "/api/volume" in mock_curl.call_args[0][0]


@patch("smartest_tv.drivers.remote.curl")
def test_power_off(mock_curl, driver):
    mock_curl.return_value = _ok({"power": "off"})
    asyncio.run(driver.power_off())
    assert "/api/power" in mock_curl.call_args[0][0]


@patch("smartest_tv.drivers.remote.curl")
def test_notify(mock_curl, driver):
    mock_curl.return_value = _ok({"notified": "hey!"})
    asyncio.run(driver.notify("hey!"))
    assert "/api/notify" in mock_curl.call_args[0][0]


@patch("smartest_tv.drivers.remote.curl")
def test_get_volume(mock_curl, driver):
    mock_curl.return_value = _ok({"volume": 30, "muted": False})
    vol = asyncio.run(driver.get_volume())
    assert vol == 30


@patch("smartest_tv.drivers.remote.curl")
def test_status(mock_curl, driver):
    mock_curl.return_value = _ok({
        "current_app": "netflix",
        "volume": 20,
        "muted": False,
        "sound_output": "speaker",
    })
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


def test_factory_passes_api_key(tmp_path, monkeypatch):
    """factory.create_driver passes api_key from config to RemoteDriver."""
    import smartest_tv.config as config_mod
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")

    (tmp_path / "config.toml").write_text("""
[tv.friend]
platform = "remote"
url = "http://10.0.0.5:8911"
api_key = "stv_test_key_123"
    """)

    from smartest_tv.drivers.factory import create_driver
    d = create_driver("friend")
    assert isinstance(d, RemoteDriver)
    assert d.api_key == "stv_test_key_123"
