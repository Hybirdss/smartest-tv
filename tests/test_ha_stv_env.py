"""Home Assistant integration keeps stv's state under /config (issue #15).

Same stub approach as test_ha_config_flow_pairing: HA is not installable in
CI, so the one HA symbol stv_env imports is stubbed and the real module is
driven with a fake ``hass``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class _FakeConfig:
    def __init__(self, root: Path, country: str | None):
        self._root = root
        self.country = country

    def path(self, *parts: str) -> str:
        return str(self._root.joinpath(*parts))


class _FakeHass:
    def __init__(self, root: Path, country: str | None = "RS"):
        self.config = _FakeConfig(root, country)


@pytest.fixture()
def stv_env(monkeypatch, tmp_path):
    # Importing the package runs custom_components/smartest_tv/__init__.py,
    # which needs the same HA stubs as the config-flow tests.
    from tests.test_ha_config_flow_pairing import _install_ha_stubs

    _install_ha_stubs(monkeypatch)
    # ensure_stv_env() writes os.environ itself; setenv first so monkeypatch
    # records the original (absent) state and restores it afterwards.
    for var in ("STV_CONFIG_DIR", "STV_REGION"):
        monkeypatch.setenv(var, "")
        monkeypatch.delenv(var)

    import smartest_tv.cache as cache_mod
    import smartest_tv.config as config_mod
    import smartest_tv.scenes as scenes_mod

    # Whatever the test does, never touch the developer's real config.
    untouched = tmp_path / "untouched"
    monkeypatch.setattr(config_mod, "CONFIG_DIR", untouched)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", untouched / "config.toml")
    monkeypatch.setattr(cache_mod, "CACHE_FILE", untouched / "cache.json")
    monkeypatch.setattr(cache_mod, "QUEUE_FILE", untouched / "queue.json")
    monkeypatch.setattr(scenes_mod, "SCENES_FILE", untouched / "scenes.json")
    monkeypatch.setattr(config_mod, "_cached_region", None)

    monkeypatch.syspath_prepend(str(REPO_ROOT))
    import custom_components.smartest_tv.stv_env as mod

    monkeypatch.setattr(mod, "LEGACY_CONFIG_DIR", tmp_path / "legacy")
    return mod


def test_env_points_stv_at_ha_config_dir(stv_env, tmp_path):
    import smartest_tv.cache as cache_mod
    import smartest_tv.config as config_mod
    import smartest_tv.scenes as scenes_mod

    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))

    new_dir = tmp_path / "hacfg" / "smartest-tv"
    assert os.environ["STV_CONFIG_DIR"] == str(new_dir)
    assert os.environ["STV_REGION"] == "RS"
    # Modules imported before the call are fixed up too, derived paths included.
    assert config_mod.CONFIG_DIR == new_dir
    assert config_mod.CONFIG_FILE == new_dir / "config.toml"
    assert cache_mod.CACHE_FILE == new_dir / "cache.json"
    assert cache_mod.QUEUE_FILE == new_dir / "queue.json"
    assert scenes_mod.SCENES_FILE == new_dir / "scenes.json"
    assert config_mod.get_region() == "RS"


def test_explicit_env_wins(stv_env, tmp_path, monkeypatch):
    import smartest_tv.config as config_mod

    monkeypatch.setenv("STV_CONFIG_DIR", str(tmp_path / "custom"))
    monkeypatch.setenv("STV_REGION", "DE")
    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    assert config_mod.CONFIG_DIR == tmp_path / "custom"
    assert config_mod.get_region() == "DE"


def test_invalid_region_goes_through_stv_validation(stv_env, tmp_path, monkeypatch):
    import smartest_tv.config as config_mod

    monkeypatch.setenv("STV_REGION", "usa")
    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    assert config_mod.get_region() != "usa"  # stv ignores a non-2-letter value


def test_no_country_leaves_region_alone(stv_env, tmp_path):
    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg", country=None))
    assert "STV_REGION" not in os.environ


def test_missing_tv_is_registered_from_entry_data(stv_env, tmp_path):
    import smartest_tv.config as config_mod

    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    assert not config_mod.CONFIG_FILE.exists()

    key = stv_env.ensure_tv_registered("TCL", "android", "10.0.0.5", "14:ea:63:83:ef:b4")
    assert key == "TCL"
    tv = config_mod.get_tv_config("TCL")
    assert tv["platform"] == "android"
    assert tv["ip"] == "10.0.0.5"
    assert tv["mac"] == "14:ea:63:83:ef:b4"

    # Second call finds it and leaves the file alone.
    mtime = config_mod.CONFIG_FILE.stat().st_mtime_ns
    assert stv_env.ensure_tv_registered("TCL", "android", "10.0.0.5", "") == "TCL"
    assert config_mod.CONFIG_FILE.stat().st_mtime_ns == mtime


def test_entry_name_is_looked_up_the_way_add_tv_stored_it(stv_env, tmp_path):
    """Discovery names TVs "android_10.0.0.5"; add_tv stores that as "android_10-0-0-5"."""
    import smartest_tv.config as config_mod

    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    config_mod.add_tv(name="android_10.0.0.5", platform="android", ip="10.0.0.5")

    key = stv_env.ensure_tv_registered("android_10.0.0.5", "android", "10.0.0.5", "")
    assert key == "android_10-0-0-5"
    assert config_mod.get_tv_config(key)["ip"] == "10.0.0.5"
    assert list(config_mod.load()["tv"]) == ["android_10-0-0-5"]  # not re-added under another key


def test_legacy_state_is_copied_once(stv_env, tmp_path):
    import smartest_tv.config as config_mod

    legacy = stv_env.LEGACY_CONFIG_DIR
    legacy.mkdir(parents=True)
    (legacy / "config.toml").write_text('[tv.lr]\nplatform = "lg"\nip = "10.0.0.6"\n')
    (legacy / "android-cert").mkdir()
    (legacy / "android-cert" / "cert.pem").write_text("pem")

    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    assert stv_env.migrate_legacy_state() is True
    new_dir = tmp_path / "hacfg" / "smartest-tv"
    assert (new_dir / "android-cert" / "cert.pem").read_text() == "pem"
    assert config_mod.get_tv_config("lr")["ip"] == "10.0.0.6"

    # Already migrated: the new location is left alone.
    (legacy / "config.toml").write_text('[tv.other]\nplatform = "roku"\nip = "10.0.0.9"\n')
    assert stv_env.migrate_legacy_state() is False
    assert config_mod.get_tv_config("lr")["ip"] == "10.0.0.6"


def test_nothing_to_migrate(stv_env, tmp_path):
    stv_env.ensure_stv_env(_FakeHass(tmp_path / "hacfg"))
    assert stv_env.migrate_legacy_state() is False
    assert not (tmp_path / "hacfg" / "smartest-tv").exists()

