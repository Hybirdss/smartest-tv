"""Samsung launch ladder: verify, escalate, report (issues #8 and #20).

Issue #20's reporter saw play_media "briefly report completion" while the
TV stayed on HDMI — three launch paths fired, none was verified, nothing
was reported. The driver now walks a best-first ladder and returns what
actually happened:

    DIAL → WS DEEP_LINK (verified via REST) → REST app-run → NATIVE_LAUNCH

Every test here pins one rung of that ladder with a fake REST layer and
a fake WS remote — no network.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("samsungtvws")

from samsungtvws.command import SamsungTVCommand  # noqa: E402

import smartest_tv._engine.drivers.samsung as samsung_mod  # noqa: E402
from smartest_tv._engine.drivers.samsung import SamsungDriver  # noqa: E402
from smartest_tv.drivers.base import LaunchResult  # noqa: E402

NETFLIX_ID = "3201907018807"  # in _DIAL_NETFLIX_IDS
DISNEY_ID = "3202009021709"   # not DIAL-aware → straight to DEEP_LINK


class _FakeRest:
    """Configurable stand-in for SamsungTVAsyncRest (no network)."""

    # Class-level knobs the tests tweak; instances read them live so a
    # run of rest_app_run can flip the app to "running".
    status: dict | None = {"app": {"running": True}}
    raise_status = False
    raise_run = False
    instances: list["_FakeRest"] = []

    def __init__(self, *args, **kwargs):
        self.status_calls: list[str] = []
        self.run_calls: list[str] = []
        _FakeRest.instances.append(self)

    async def rest_app_status(self, app_id):
        self.status_calls.append(app_id)
        if _FakeRest.raise_status:
            raise OSError("TV unreachable or feature not supported")
        return _FakeRest.status

    async def rest_app_run(self, app_id):
        self.run_calls.append(app_id)
        if _FakeRest.raise_run:
            raise OSError("TV unreachable or feature not supported")
        return {}


@pytest.fixture(autouse=True)
def fake_rest(monkeypatch):
    _FakeRest.status = {"app": {"running": True}}
    _FakeRest.raise_status = False
    _FakeRest.raise_run = False
    _FakeRest.instances = []
    monkeypatch.setattr(samsung_mod, "SamsungTVAsyncRest", _FakeRest)


@pytest.fixture
def driver(monkeypatch) -> SamsungDriver:
    # _verify_app_running/_rest_run_app create a real aiohttp session before
    # the (faked) REST object is built; stub it so nothing leaks.
    monkeypatch.setattr(samsung_mod.aiohttp, "ClientSession", MagicMock)
    d = SamsungDriver(ip="192.0.2.10", mac="aa:bb:cc:dd:ee:ff")
    d._verify_delay = 0
    remote = MagicMock()
    remote.send_command = AsyncMock()
    d._remote = remote
    return d


def _sent_payloads(driver) -> list[dict]:
    out = []
    for call in driver._remote.send_command.await_args_list:
        cmd = call.args[0]
        assert isinstance(cmd, SamsungTVCommand)
        payload = json.loads(cmd.get_payload())
        out.append(payload["params"]["data"])
    return out


async def test_dial_success_short_circuits_the_ladder(driver):
    """A 2xx DIAL POST is the best outcome — no WS or REST traffic at all."""
    async def fake_dial(app_name, body):
        assert app_name == "Netflix"
        return True

    driver._try_dial = fake_dial
    result = await driver.launch_app_deep(NETFLIX_ID, "80114790")

    assert result is LaunchResult.DIAL
    driver._remote.send_command.assert_not_awaited()
    assert _FakeRest.instances == []


async def test_deep_link_verified_running(driver):
    """DEEP_LINK sent, REST status says running → DEEP_LINK."""
    driver._dial_app_url = ""  # DIAL known-absent: skip M-SEARCH
    result = await driver.launch_app_deep(DISNEY_ID, "81002370")

    assert result is LaunchResult.DEEP_LINK
    payloads = _sent_payloads(driver)
    assert len(payloads) == 1
    assert payloads[0]["action_type"] == "DEEP_LINK"
    assert _FakeRest.instances[0].run_calls == []


async def test_ignored_deep_link_escalates_to_rest_run(driver):
    """Issue #8/#20 behavior: DEEP_LINK silently ignored, REST run saves it."""
    driver._dial_app_url = ""
    _FakeRest.status = {"app": {"running": False}}

    # The REST run makes the app start: flip status once run was POSTed.
    original_run = _FakeRest.rest_app_run

    async def run_then_running(self, app_id):
        await original_run(self, app_id)
        _FakeRest.status = {"app": {"running": True}}
        return {}

    _FakeRest.rest_app_run = run_then_running

    result = await driver.launch_app_deep(DISNEY_ID, "81002370")

    assert result is LaunchResult.APP_ONLY
    payloads = _sent_payloads(driver)
    assert payloads[0]["action_type"] == "DEEP_LINK"
    assert any(i.run_calls == [DISNEY_ID] for i in _FakeRest.instances)


async def test_rest_run_denied_falls_back_to_native_launch(driver):
    """REST unavailable + DEEP_LINK ignored → plain NATIVE_LAUNCH."""
    driver._dial_app_url = ""
    _FakeRest.status = {"app": {"running": False}}
    _FakeRest.raise_run = True

    result = await driver.launch_app_deep(DISNEY_ID, "81002370")

    assert result is LaunchResult.NATIVE
    payloads = _sent_payloads(driver)
    assert [p["action_type"] for p in payloads] == ["DEEP_LINK", "NATIVE_LAUNCH"]


async def test_everything_refused_reports_failed(driver):
    """No path works → FAILED, so HA raises instead of a silent no-op."""
    driver._dial_app_url = ""
    _FakeRest.status = {"app": {"running": False}}
    _FakeRest.raise_run = True
    driver._remote.send_command = AsyncMock(side_effect=OSError("ws down"))

    result = await driver.launch_app_deep(DISNEY_ID, "81002370")

    assert result is LaunchResult.FAILED


async def test_unverifiable_status_is_reported_not_guessed(driver):
    """REST status endpoint broken → DEEP_LINK_UNVERIFIED, no escalation.

    Escalating on "unknown" would re-launch apps that are actually
    playing; guessing "running" would hide #8. Say unknown.
    """
    driver._dial_app_url = ""
    _FakeRest.raise_status = True

    result = await driver.launch_app_deep(DISNEY_ID, "81002370")

    assert result is LaunchResult.DEEP_LINK_UNVERIFIED
    assert _FakeRest.instances[0].run_calls == []


async def test_no_content_id_opens_app_only(driver):
    """Resolve() failed upstream → open the app, never deep-link garbage."""
    driver._dial_app_url = ""

    result = await driver.launch_app_deep(NETFLIX_ID, "")

    assert result is LaunchResult.APP_ONLY
    payloads = _sent_payloads(driver)
    assert payloads[0]["action_type"] == "NATIVE_LAUNCH"
    assert payloads[0]["metaTag"] == ""


class TestStatusParsing:
    """The REST payload shape varies across firmware generations."""

    def test_top_level_bool(self):
        assert samsung_mod._status_says_running({"running": True}) is True

    def test_top_level_string(self):
        assert samsung_mod._status_says_running({"running": "false"}) is False

    def test_wrapped_under_app(self):
        assert samsung_mod._status_says_running({"app": {"visible": "true"}}) is True

    def test_no_verdict_is_unknown_not_stopped(self):
        assert samsung_mod._status_says_running({"name": "Netflix"}) is None

    def test_non_dict_is_unknown(self):
        assert samsung_mod._status_says_running(None) is None

    def test_garbage_string_is_unknown(self):
        assert samsung_mod._status_says_running({"running": "maybe"}) is None


async def test_connect_reads_token_off_event_loop(tmp_path, monkeypatch):
    """The token file IO moves to a worker thread (issue #20 HA warning)."""
    class _ThreadAwareRemote:
        def __init__(self, host, token=None, token_file=None, port=8002, **kw):
            assert token_file is None, "token_file must not reach the library"
            assert token == "stored-token"
            self.token = token

        async def open(self):
            pass

    monkeypatch.setattr(samsung_mod, "SamsungTVWSAsyncRemote", _ThreadAwareRemote)

    token_file = tmp_path / "samsung_192.0.2.10.token"
    token_file.write_text("stored-token\n")

    d = SamsungDriver(ip="192.0.2.10", token_file=str(token_file))
    await d.connect()

    assert d._remote.token == "stored-token"
    # granted == stored → no rewrite: file still exactly as written
    assert token_file.read_text() == "stored-token\n"


async def test_connect_persists_newly_granted_token(tmp_path, monkeypatch):
    """First pairing: token granted by the TV is persisted via the pool."""

    class _PairingRemote:
        def __init__(self, host, token=None, token_file=None, port=8002, **kw):
            self.token = token

        async def open(self):
            self.token = "brand-new-token"

    monkeypatch.setattr(samsung_mod, "SamsungTVWSAsyncRemote", _PairingRemote)

    token_file = tmp_path / "samsung_192.0.2.10.token"
    token_file.write_text("")  # exists but empty → None

    d = SamsungDriver(ip="192.0.2.10", token_file=str(token_file))
    await d.connect()

    assert token_file.read_text() == "brand-new-token"
