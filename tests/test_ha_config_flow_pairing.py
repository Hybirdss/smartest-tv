"""Config flow pairing step (issue #15 regression tests).

Home Assistant is not installable in CI, so we stub the handful of HA
symbols config_flow needs (ConfigFlow, vol, Platform, …) and drive the
real flow class. This pins the contract that an Android TV entry cannot
be created without completing PIN pairing.
"""

from __future__ import annotations

import enum
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class _VolModule(types.ModuleType):
    def Schema(self, schema):  # noqa: N802
        return schema

    def Required(self, key, **_):  # noqa: N802
        return key

    def Optional(self, key, default=None, **_):  # noqa: N802
        return key

    def In(self, options):  # noqa: N802
        return options


class _Platform(str, enum.Enum):
    MEDIA_PLAYER = "media_player"


def _install_ha_stubs(monkeypatch):
    ha = types.ModuleType("homeassistant")
    ce = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    const = types.ModuleType("homeassistant.const")

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            pass

        def __init__(self):
            self.hass = None

        async def async_set_unique_id(self, uid):
            self._unique_id = uid

        def _abort_if_unique_id_configured(self):
            pass

        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(self, *, step_id, data_schema=None, errors=None,
                            description_placeholders=None):
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
                "description_placeholders": description_placeholders or {},
            }

    class OptionsFlow:
        pass

    ce.ConfigFlow = ConfigFlow
    ce.OptionsFlow = OptionsFlow
    ce.ConfigFlowResult = dict
    ce.ConfigEntry = object
    core.HomeAssistant = object
    const.Platform = _Platform

    monkeypatch.setitem(sys.modules, "homeassistant", ha)
    monkeypatch.setitem(sys.modules, "homeassistant.config_entries", ce)
    monkeypatch.setitem(sys.modules, "homeassistant.core", core)
    monkeypatch.setitem(sys.modules, "homeassistant.const", const)
    monkeypatch.setitem(sys.modules, "voluptuous", _VolModule("voluptuous"))
    sys.modules["homeassistant"].config_entries = ce
    sys.modules["homeassistant"].core = core
    sys.modules["homeassistant"].const = const


class _FakeHass:
    """Only what the flow uses: executor delegation."""

    async def async_add_executor_job(self, fn, *args):
        return fn(*args)


class FakeAndroidDriver:
    calls: list[tuple] = []

    def __init__(self, ip, port=6466, cert_dir=""):
        self.ip = ip
        self.paired = False
        self.remote = object()

    async def connect(self):
        if not self.paired:
            raise RuntimeError("Not paired with this TV")

    async def start_pairing(self):
        FakeAndroidDriver.calls.append(("start_pairing", self.ip))
        return self.remote

    async def finish_pairing(self, remote, pin):
        FakeAndroidDriver.calls.append(("finish_pairing", pin))
        if pin != "123456":
            from androidtvremote2.exceptions import InvalidAuth
            raise InvalidAuth("bad pin")
        self.paired = True

    async def disconnect(self):
        pass


@pytest.fixture()
def cf(monkeypatch, tmp_path):
    _install_ha_stubs(monkeypatch)
    import smartest_tv._engine.drivers.android as android_mod
    import smartest_tv.config as config_mod

    FakeAndroidDriver.calls = []
    monkeypatch.setattr(android_mod, "AndroidDriver", FakeAndroidDriver)
    # Never touch the developer's real ~/.config/smartest-tv/config.toml
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")

    sys.path.insert(0, str(REPO_ROOT))
    try:
        import custom_components.smartest_tv.config_flow as cf_mod
    finally:
        pass
    return cf_mod


def _no_discover(monkeypatch, cf_mod):
    async def _nd(self):
        return []
    monkeypatch.setattr(cf_mod.SmarTestTVConfigFlow, "_async_discover", _nd)


def _make_flow(cf_mod):
    flow = cf_mod.SmarTestTVConfigFlow()
    flow.hass = _FakeHass()
    return flow


_ANDROID_INPUT = {
    "tv_name": "living-room",
    "platform": "android",
    "ip": "10.0.0.5",
    "mac": "",
}


@pytest.mark.asyncio
async def test_android_manual_entry_requires_pairing(cf, monkeypatch):
    _no_discover(monkeypatch, cf)
    flow = _make_flow(cf)

    result = await flow.async_step_user(None)
    assert result["type"] == "form" and result["step_id"] == "user"

    result = await flow.async_step_user(dict(_ANDROID_INPUT))
    # Must land on the pairing form, NOT create the entry yet
    assert result["type"] == "form"
    assert result["step_id"] == "pair"
    assert ("start_pairing", "10.0.0.5") in FakeAndroidDriver.calls


@pytest.mark.asyncio
async def test_android_pairing_wrong_pin_shows_error(cf, monkeypatch):
    _no_discover(monkeypatch, cf)
    flow = _make_flow(cf)
    await flow.async_step_user(None)
    await flow.async_step_user(dict(_ANDROID_INPUT))

    result = await flow.async_step_pair({"pin": "000000"})
    assert result["type"] == "form" and result["step_id"] == "pair"
    assert result["errors"].get("pin") == "invalid_pin"


@pytest.mark.asyncio
async def test_android_pairing_success_creates_entry(cf, monkeypatch):
    _no_discover(monkeypatch, cf)
    flow = _make_flow(cf)
    await flow.async_step_user(None)
    await flow.async_step_user(dict(_ANDROID_INPUT))

    result = await flow.async_step_pair({"pin": "123456"})
    assert result["type"] == "create_entry"
    assert result["data"] == {
        "tv_name": "living-room",
        "platform": "android",
        "ip": "10.0.0.5",
        "mac": "",
    }


@pytest.mark.asyncio
async def test_android_already_paired_skips_pin(cf, monkeypatch):
    _no_discover(monkeypatch, cf)

    class PairedDriver(FakeAndroidDriver):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.paired = True

    import smartest_tv._engine.drivers.android as android_mod
    monkeypatch.setattr(android_mod, "AndroidDriver", PairedDriver)

    flow = _make_flow(cf)
    await flow.async_step_user(None)
    result = await flow.async_step_user(dict(_ANDROID_INPUT))
    assert result["type"] == "create_entry"
    assert not any(c[0] == "start_pairing" for c in FakeAndroidDriver.calls)


@pytest.mark.asyncio
async def test_discovered_android_tv_also_pairs(cf, monkeypatch):
    flow = _make_flow(cf)
    flow._discovered = [
        {"ip": "10.0.0.7", "name": "Sony Bravia", "platform": "android", "mac": ""},
        {"ip": "10.0.0.8", "name": "Kitchen LG", "platform": "lg", "mac": ""},
    ]
    result = await flow.async_step_discover({"tv_index": "0"})
    assert result["type"] == "form" and result["step_id"] == "pair"
    assert ("start_pairing", "10.0.0.7") in FakeAndroidDriver.calls

    result = await flow.async_step_pair({"pin": "123456"})
    assert result["type"] == "create_entry"
    assert result["data"]["ip"] == "10.0.0.7"


@pytest.mark.asyncio
async def test_lg_entry_never_pairs(cf, monkeypatch):
    _no_discover(monkeypatch, cf)
    flow = _make_flow(cf)
    await flow.async_step_user(None)
    result = await flow.async_step_user({
        "tv_name": "lr", "platform": "lg", "ip": "10.0.0.6", "mac": "aa:bb:cc:dd:ee:ff",
    })
    assert result["type"] == "create_entry"
    assert result["data"]["platform"] == "lg"
    assert FakeAndroidDriver.calls == []
