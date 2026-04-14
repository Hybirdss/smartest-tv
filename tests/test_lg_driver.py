"""Regression tests for the LG driver's aiowebostv subclass.

webOS 24/25 rejects several ``subscribe_*`` calls with
``401 insufficient permissions`` because aiowebostv's registration
manifest does not request the matching ``com.webos.*`` permissions.
The vanilla ``_get_states_and_subscribe_state_updates`` launches eight
subscriptions in parallel inside ``connect()`` and only suppresses
``WebOsTvServiceNotFoundError`` when collecting their results — a plain
``WebOsTvCommandError`` propagates and kills the connection.

These tests pin the broad fix:

1. The override completes cleanly when every subscription raises 401.
   This is the regression that closes issue #4.
2. The override propagates non-``WebOsTvCommandError`` failures so real
   bugs still surface.
3. The override mirrors upstream's ``_get_states_and_subscribe_state_updates``
   structure — if aiowebostv adds a new subscription, the test fails
   loudly so the override can be resynced.
4. The override completes the ``do_state_update_callbacks`` epilogue
   so callers depending on the post-connect callback fire still see it.
"""

from __future__ import annotations

import inspect
import re
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("aiowebostv")

from aiowebostv import WebOsClient  # noqa: E402
from aiowebostv.exceptions import (  # noqa: E402
    WebOsTvCommandError,
    WebOsTvCommandTimeoutError,
)

from smartest_tv._engine.drivers.lg import _SmarTestWebOsClient  # noqa: E402

# Subscriptions upstream fires from _get_states_and_subscribe_state_updates.
# Used by both the override-mirror test and the all-401 simulation.
_UPSTREAM_SUBSCRIPTIONS = (
    "subscribe_power_state",
    "subscribe_current_app",
    "subscribe_muted",
    "subscribe_volume",
    "subscribe_apps",
    "subscribe_inputs",
    "subscribe_sound_output",
    "subscribe_media_foreground_app",
)
_UPSTREAM_SETTERS = (
    "set_power_state",
    "set_current_app_state",
    "set_muted_state",
    "set_volume_state",
    "set_apps_state",
    "set_inputs_state",
    "set_sound_output_state",
    "set_media_state",
)


class _FakeTvInfo:
    system: dict | None = None
    software: dict | None = None


class _FakeTvState:
    pass


def _build_client() -> _SmarTestWebOsClient:
    """Return a client wired with the minimum state the upstream method touches.

    Bypasses ``WebOsClient.__init__`` (no sockets, no event loop). Stubs:
    - ``tv_info`` with empty system/software
    - ``state_update_callbacks = []`` so ``do_state_update_callbacks``
      short-circuits before touching ``tv_state``
    - ``do_state_update`` writable
    - ``get_system_info`` / ``get_software_info`` as AsyncMocks
    - all 8 ``set_*_state`` callbacks as AsyncMocks
    """
    client = _SmarTestWebOsClient.__new__(_SmarTestWebOsClient)
    client.tv_info = _FakeTvInfo()
    client.tv_state = _FakeTvState()
    client.state_update_callbacks = []
    client.do_state_update = True
    client.get_system_info = AsyncMock(return_value={"modelName": "fake"})
    client.get_software_info = AsyncMock(return_value={"version": "fake"})
    for setter in _UPSTREAM_SETTERS:
        setattr(client, setter, AsyncMock())
    return client


@pytest.mark.asyncio
async def test_connect_survives_401_on_every_subscription(monkeypatch):
    """The actual issue #4 reproducer.

    Make every parent ``subscribe_*`` raise 401. Our override must
    complete without raising and reach the ``do_state_update_callbacks``
    epilogue.
    """

    async def raise_401(self, callback):
        raise WebOsTvCommandError("{'type': 'error', 'id': 13, 'error': '401 insufficient permissions'}")

    for name in _UPSTREAM_SUBSCRIPTIONS:
        monkeypatch.setattr(f"aiowebostv.WebOsClient.{name}", raise_401)

    client = _build_client()
    client.do_state_update = False  # set true at end of override

    await client._get_states_and_subscribe_state_updates()

    assert client.do_state_update is True
    # All 8 set_*_state callbacks were never invoked because every
    # subscribe coroutine raised before calling its callback. That's
    # the correct degraded state — push state missing, getters fall back.
    for setter in _UPSTREAM_SETTERS:
        getattr(client, setter).assert_not_awaited()


@pytest.mark.asyncio
async def test_connect_propagates_unrelated_subscription_exceptions(monkeypatch):
    """Real bugs still kill connect — we are not a blanket try/except.

    A non-``WebOsTvCommandError`` raised inside a subscribe task surfaces
    via ``task.result()`` because our ``suppress`` is scoped to
    ``WebOsTvCommandError`` only.
    """

    async def boom(self, callback):
        raise RuntimeError("bus is on fire")

    # Make exactly one subscription raise the unrelated error; the other
    # seven succeed so we know the failure came from the right place.
    async def ok(self, callback):
        return {"subscribed": True}

    monkeypatch.setattr("aiowebostv.WebOsClient.subscribe_power_state", boom)
    for name in _UPSTREAM_SUBSCRIPTIONS:
        if name != "subscribe_power_state":
            monkeypatch.setattr(f"aiowebostv.WebOsClient.{name}", ok)

    client = _build_client()

    with pytest.raises(RuntimeError, match="bus is on fire"):
        await client._get_states_and_subscribe_state_updates()


@pytest.mark.asyncio
async def test_connect_swallows_subscription_timeout(monkeypatch):
    """Subscription timeouts degrade gracefully — same path as 401.

    ``WebOsTvCommandTimeoutError`` is a subclass of
    ``WebOsTvCommandError`` raised by aiowebostv when the WS doesn't
    respond to a request within the timeout. The main connection has
    already succeeded by the time this method runs, so a per-subscription
    timeout is a missing push channel, not a broken connection. Letting
    connect succeed (with that subscription's state missing) matches the
    behavior we get on a 401 — the next ``status()`` poll fetches it.
    """

    async def time_out(self, callback):
        raise WebOsTvCommandTimeoutError("timeout waiting for response")

    monkeypatch.setattr("aiowebostv.WebOsClient.subscribe_volume", time_out)

    async def ok(self, callback):
        return {"subscribed": True}

    for name in _UPSTREAM_SUBSCRIPTIONS:
        if name != "subscribe_volume":
            monkeypatch.setattr(f"aiowebostv.WebOsClient.{name}", ok)

    client = _build_client()
    await client._get_states_and_subscribe_state_updates()
    assert client.do_state_update is True


@pytest.mark.asyncio
async def test_do_state_update_callbacks_fires_after_subscription_failures(
    monkeypatch,
):
    """The connect epilogue runs even when every subscription failed."""

    async def raise_401(self, callback):
        raise WebOsTvCommandError("401 insufficient permissions")

    for name in _UPSTREAM_SUBSCRIPTIONS:
        monkeypatch.setattr(f"aiowebostv.WebOsClient.{name}", raise_401)

    client = _build_client()
    callback_seen = []

    async def state_callback(state):
        callback_seen.append(state)

    client.state_update_callbacks = [state_callback]

    await client._get_states_and_subscribe_state_updates()

    # do_state_update_callbacks fires once with the (still mostly empty)
    # tv_state. The driver's downstream code can react to "connected but
    # state unknown" rather than seeing connect raise.
    assert len(callback_seen) == 1


def test_override_mirrors_upstream_subscribe_flow():
    """Guard against aiowebostv changing the method body under us.

    The override is a verbatim copy of
    ``WebOsClient._get_states_and_subscribe_state_updates`` with the
    ``suppress`` widened. If upstream restructures the method (renames
    a subscription, adds a new one, changes the gather strategy), our
    copy diverges silently. This test pins the structural assumption
    by extracting the set of ``subscribe_*`` names referenced in the
    upstream method body and asserting our override references the same
    set.
    """
    upstream_src = inspect.getsource(WebOsClient._get_states_and_subscribe_state_updates)
    override_src = inspect.getsource(_SmarTestWebOsClient._get_states_and_subscribe_state_updates)
    upstream_subs = set(re.findall(r"self\.(subscribe_\w+)\(", upstream_src))
    override_subs = set(re.findall(r"self\.(subscribe_\w+)\(", override_src))
    assert upstream_subs == set(_UPSTREAM_SUBSCRIPTIONS), (
        f"upstream changed: {upstream_subs} vs known {_UPSTREAM_SUBSCRIPTIONS}"
    )
    assert override_subs == upstream_subs, f"override drifted: {override_subs} missing {upstream_subs - override_subs}"
