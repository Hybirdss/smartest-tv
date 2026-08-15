"""Config TOML safety (issue #15 regression tests).

A display name containing spaces ("Living Room") or non-ASCII ("거실 TV")
must never be written as a bare TOML section key — `[tv.Living Room]` is
invalid TOML and made every later config read crash with
TOMLDecodeError, which surfaced to users as "did not bind to tv".
"""

from __future__ import annotations

import tomllib

import pytest

import smartest_tv.config as config_mod


@pytest.fixture()
def isolated_config(monkeypatch, tmp_path):
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")
    return tmp_path / "config.toml"


def test_legacy_migration_with_space_name_writes_valid_toml(isolated_config):
    isolated_config.write_text(
        '''[tv]
platform = "lg"
ip = "192.168.200.101"
mac = "a4:36:c7:dc:f7:8c"
name = "Living Room"
'''
    )
    config_mod.add_tv("bedroom", "samsung", "10.0.0.9", "", default=False)

    # The rewritten file must parse — the old code wrote `[tv.Living Room]`.
    parsed = tomllib.loads(isolated_config.read_text())
    tvs = {k: v for k, v in parsed["tv"].items() if isinstance(v, dict)}
    assert "Living-Room" in tvs  # key sanitized
    assert tvs["Living-Room"]["name"] == "Living Room"  # display name kept
    assert "bedroom" in tvs

    # And get_tv_config resolves both by display semantics
    cfg = config_mod.get_tv_config("Living-Room")
    assert cfg["ip"] == "192.168.200.101"


def test_legacy_migration_with_korean_name(isolated_config):
    isolated_config.write_text(
        '''[tv]
platform = "lg"
ip = "1.2.3.4"
name = "거실 TV"
'''
    )
    config_mod.add_tv("office", "lg", "5.6.7.8", "", default=False)
    parsed = tomllib.loads(isolated_config.read_text())
    tvs = {k: v for k, v in parsed["tv"].items() if isinstance(v, dict)}
    assert set(tvs) == {"거실-TV", "office"}  # unicode kept, space dashed
    assert tvs["거실-TV"]["name"] == "거실 TV"


def test_spacey_existing_key_round_trips(isolated_config):
    # Simulate a config that already carries a spacey key (e.g. synced
    # from another machine): rewriting must quote it, not corrupt it.
    isolated_config.write_text('''[tv."My TV"]
platform = "roku"
ip = "1.1.1.1"
''')
    config_mod.add_tv("kitchen", "roku", "2.2.2.2", "", default=False)
    parsed = tomllib.loads(isolated_config.read_text())
    tvs = {k: v for k, v in parsed["tv"].items() if isinstance(v, dict)}
    assert "My TV" in tvs and "kitchen" in tvs


def test_corrupt_config_does_not_crash_load(isolated_config):
    isolated_config.write_text("[tv.Living Room]\nplatform = 'lg'\n")  # invalid TOML
    config = config_mod.load()
    assert config == {}
    # Broken file preserved for manual recovery
    assert (isolated_config.parent / "config.toml.corrupt").exists()
    # And add_tv on top of the corrupt file heals it
    config_mod.add_tv("fresh", "lg", "3.3.3.3", "", default=False)
    parsed = tomllib.loads(isolated_config.read_text())
    assert "fresh" in parsed["tv"]


def test_group_names_with_spaces_round_trip(isolated_config):
    config_mod.add_tv("a", "lg", "1.1.1.1", "", default=True)
    config_mod.add_tv("b", "lg", "2.2.2.2", "", default=False)
    config_mod.save_group("Upstairs TVs", ["a", "b"])
    parsed = tomllib.loads(isolated_config.read_text())
    # group keys are sanitized ("Upstairs TVs" → "Upstairs-TVs") and quoted
    assert parsed["groups"]["Upstairs-TVs"] == ["a", "b"]
