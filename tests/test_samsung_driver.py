"""Regression tests for the Samsung driver's async dispatch.

Issue #6: ``SamsungTVWSAsyncRemote`` (samsungtvws >= 3.0) does NOT expose
``run_app`` or ``send_key`` — only ``send_command``/``send_commands``. The
driver must dispatch the right ``ChannelEmitCommand`` / ``SendRemoteKey``
payloads.

These tests mock the async remote to record dispatched payloads and
assert the wire format. They cover the production AttributeError that
hit Disney+ and Netflix launch on Tizen 9.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("samsungtvws")

from samsungtvws.command import SamsungTVCommand  # noqa: E402

from smartest_tv._engine.drivers.samsung import SamsungDriver  # noqa: E402


def _payload(call) -> dict:
    """Extract the JSON payload from a recorded send_command call."""
    cmd = call.args[0]
    assert isinstance(cmd, SamsungTVCommand), f"expected SamsungTVCommand, got {type(cmd)}"
    return json.loads(cmd.get_payload())


@pytest.fixture
def driver() -> SamsungDriver:
    d = SamsungDriver(ip="192.0.2.10", mac="aa:bb:cc:dd:ee:ff")
    remote = MagicMock()
    remote.send_command = AsyncMock()
    remote.send_commands = AsyncMock()
    remote.app_list = AsyncMock(return_value=[])
    d._remote = remote
    return d


@pytest.mark.asyncio
async def test_launch_app_deep_emits_deep_link_payload(driver):
    """Disney+ / Netflix deep link goes out as ed.apps.launch DEEP_LINK."""
    await driver.launch_app_deep("3201901017640", "81002370")  # Netflix Disney+ -> Stranger Things
    driver._remote.send_command.assert_awaited_once()
    payload = _payload(driver._remote.send_command.await_args)
    assert payload["method"] == "ms.channel.emit"
    assert payload["params"]["event"] == "ed.apps.launch"
    assert payload["params"]["data"]["action_type"] == "DEEP_LINK"
    assert payload["params"]["data"]["appId"] == "3201901017640"
    assert payload["params"]["data"]["metaTag"] == "81002370"


@pytest.mark.asyncio
async def test_launch_app_emits_native_launch_payload(driver):
    """Plain app launch goes out as NATIVE_LAUNCH with empty meta."""
    await driver.launch_app("11101200001")
    payload = _payload(driver._remote.send_command.await_args)
    assert payload["params"]["data"]["action_type"] == "NATIVE_LAUNCH"
    assert payload["params"]["data"]["appId"] == "11101200001"
    assert payload["params"]["data"]["metaTag"] == ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,key",
    [
        ("power_off", "KEY_POWER"),
        ("volume_up", "KEY_VOLUP"),
        ("volume_down", "KEY_VOLDOWN"),
        ("play", "KEY_PLAY"),
        ("pause", "KEY_PAUSE"),
        ("stop", "KEY_STOP"),
        ("channel_up", "KEY_CHUP"),
        ("channel_down", "KEY_CHDOWN"),
    ],
)
async def test_remote_keys_dispatch_via_send_command(driver, method, key):
    """Every key-driven control sends one SendRemoteKey click via send_command."""
    await getattr(driver, method)()
    payload = _payload(driver._remote.send_command.await_args)
    assert payload["params"]["Cmd"] == "Click"
    assert payload["params"]["DataOfCmd"] == key
    assert payload["params"]["TypeOfRemote"] == "SendRemoteKey"


@pytest.mark.asyncio
async def test_set_mute_toggles_via_key_mute(driver):
    """Samsung has no read-mute API; set_mute is a toggle send."""
    await driver.set_mute(True)
    payload = _payload(driver._remote.send_command.await_args)
    assert payload["params"]["DataOfCmd"] == "KEY_MUTE"


@pytest.mark.asyncio
async def test_set_volume_batches_with_send_commands(driver):
    """set_volume(level) emits 50 VOLDOWN then `level` VOLUP via send_commands.

    Batching avoids the deprecated ``send_command(list, ...)`` path noted in
    samsungtvws/async_connection.py:145 and reduces 100 sequential awaits.
    """
    await driver.set_volume(25)
    assert driver._remote.send_commands.await_count == 2

    bottom_call, ups_call = driver._remote.send_commands.await_args_list
    bottom_cmds = bottom_call.args[0]
    assert len(bottom_cmds) == 50
    assert all(
        json.loads(c.get_payload())["params"]["DataOfCmd"] == "KEY_VOLDOWN"
        for c in bottom_cmds
    )
    assert bottom_call.kwargs.get("key_press_delay") == 0.05

    ups_cmds = ups_call.args[0]
    assert len(ups_cmds) == 25
    assert all(
        json.loads(c.get_payload())["params"]["DataOfCmd"] == "KEY_VOLUP"
        for c in ups_cmds
    )


@pytest.mark.asyncio
async def test_set_volume_zero_skips_ups_batch(driver):
    """level=0 still bottoms out but skips the empty ups batch."""
    await driver.set_volume(0)
    assert driver._remote.send_commands.await_count == 1


@pytest.mark.asyncio
async def test_set_volume_clamps_high(driver):
    """level > 100 is clamped to 100 ups."""
    await driver.set_volume(250)
    _, ups_call = driver._remote.send_commands.await_args_list
    assert len(ups_call.args[0]) == 100


@pytest.mark.asyncio
async def test_set_volume_clamps_negative(driver):
    """Negative level is clamped to 0 — no ups batch is sent."""
    await driver.set_volume(-5)
    assert driver._remote.send_commands.await_count == 1
