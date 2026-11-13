"""Android driver: status() right after connect(), and a failed connect().

androidtvremote2 fills power / app / volume on the remote during
``async_connect()`` and fires the ``*_updated`` callbacks on changes only.
A driver that copies state from the callbacks reports nothing until the TV
changes app or power; Home Assistant showed such a TV as off with no app
after every restart. status() reads the remote's own state instead.
"""

from __future__ import annotations

import pytest

pytest.importorskip("androidtvremote2")

from androidtvremote2 import ConnectionClosed  # noqa: E402

from smartest_tv._engine.drivers.android import AndroidDriver  # noqa: E402


class FakeRemote:
    """The slice of androidtvremote2.AndroidTVRemote the driver touches."""

    def __init__(self):
        self.is_on = True
        self.current_app = "com.netflix.ninja"
        self.volume_info = {"level": 17, "muted": False, "max": 100}
        self.connect_error: Exception | None = None

    async def async_connect(self):
        if self.connect_error:
            raise self.connect_error

    def disconnect(self):
        pass


@pytest.fixture()
def driver(monkeypatch, tmp_path):
    remote = FakeRemote()

    async def _build(self):
        return remote

    monkeypatch.setattr(AndroidDriver, "_build_remote", _build)
    d = AndroidDriver(ip="192.0.2.10", cert_dir=str(tmp_path))
    d.fake_remote = remote
    return d


@pytest.mark.asyncio
async def test_status_reflects_initial_state_right_after_connect(driver):
    await driver.connect()
    st = await driver.status()
    assert st.powered is True
    assert st.current_app == "com.netflix.ninja"
    assert st.volume == 17
    assert st.muted is False


@pytest.mark.asyncio
async def test_no_app_or_volume_reported_yet(driver):
    driver.fake_remote.current_app = ""  # the library's value before the first IME message
    driver.fake_remote.volume_info = None
    await driver.connect()
    st = await driver.status()
    assert st.powered is True
    assert st.current_app is None
    assert st.volume is None
    assert st.muted is None


@pytest.mark.asyncio
async def test_later_changes_on_the_remote_are_visible(driver):
    await driver.connect()
    driver.fake_remote.is_on = False
    driver.fake_remote.current_app = "com.google.android.apps.tv.launcherx"
    driver.fake_remote.volume_info = {"level": 3, "muted": True, "max": 100}
    st = await driver.status()
    assert st.powered is False
    assert st.current_app == "com.google.android.apps.tv.launcherx"
    assert st.volume == 3
    assert st.muted is True


@pytest.mark.asyncio
async def test_connection_lost_during_connect_leaves_no_remote_behind(driver):
    driver.fake_remote.connect_error = ConnectionClosed("lost while waiting for the remote to start")
    with pytest.raises(RuntimeError, match="Cannot connect"):
        await driver.connect()
    assert driver._remote is None  # the next connect() tries again instead of returning early
