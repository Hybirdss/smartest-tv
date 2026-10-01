"""config.update_tv_ip — stale-IP persistence for the self-heal."""

from __future__ import annotations

import tomllib

import pytest

import smartest_tv.config as config_mod


@pytest.fixture()
def isolated_config(monkeypatch, tmp_path):
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")
    return tmp_path / "config.toml"


def test_legacy_single_tv_update(isolated_config):
    isolated_config.write_text(
        '''[tv]
platform = "lg"
ip = "192.168.200.101"
mac = "a4:36:c7:dc:f7:8c"
name = "Living Room"
'''
    )
    assert config_mod.update_tv_ip(None, "192.168.200.101", "192.168.200.107")

    cfg = config_mod.get_tv_config(None)
    assert cfg["ip"] == "192.168.200.107"
    assert cfg["mac"] == "a4:36:c7:dc:f7:8c"  # untouched
    assert cfg["name"] == "Living Room"
    assert cfg["platform"] == "lg"


def test_legacy_ip_mismatch_is_noop(isolated_config):
    isolated_config.write_text(
        '''[tv]
platform = "lg"
ip = "10.0.0.5"
'''
    )
    assert not config_mod.update_tv_ip(None, "192.168.200.101", "192.168.200.107")
    assert config_mod.get_tv_config(None)["ip"] == "10.0.0.5"


def test_multi_tv_named_target(isolated_config):
    isolated_config.write_text(
        '''[tv."living-room"]
platform = "lg"
ip = "192.168.200.101"
mac = "a4:36:c7:dc:f7:8c"
name = "Living Room"
default = true

[tv.bedroom]
platform = "samsung"
ip = "192.168.200.102"

[groups]
party = ["living-room", "bedroom"]
'''
    )
    assert config_mod.update_tv_ip("living-room", "192.168.200.101", "192.168.200.107")

    parsed = tomllib.loads(isolated_config.read_text())
    tvs = parsed["tv"]
    assert tvs["living-room"]["ip"] == "192.168.200.107"
    assert tvs["bedroom"]["ip"] == "192.168.200.102"  # untouched
    assert parsed["groups"]["party"] == ["living-room", "bedroom"]  # preserved


def test_multi_tv_match_by_ip_when_unnamed(isolated_config):
    isolated_config.write_text(
        '''[tv."living-room"]
platform = "lg"
ip = "192.168.200.101"
mac = "a4:36:c7:dc:f7:8c"

[tv.remote-friend]
platform = "remote"
url = "http://203.0.113.9:8911"
api_key = "secret"
'''
    )
    assert config_mod.update_tv_ip(None, "192.168.200.101", "192.168.200.107")

    parsed = tomllib.loads(isolated_config.read_text())
    assert parsed["tv"]["living-room"]["ip"] == "192.168.200.107"
    # Remote entry survives intact — including api_key, which the writer
    # used to drop (silent credential loss on rewrite).
    assert parsed["tv"]["remote-friend"]["api_key"] == "secret"
    assert parsed["tv"]["remote-friend"]["url"] == "http://203.0.113.9:8911"


def test_unknown_name_is_noop(isolated_config):
    isolated_config.write_text(
        '''[tv."living-room"]
platform = "lg"
ip = "192.168.200.101"
'''
    )
    assert not config_mod.update_tv_ip("attic", "192.168.200.101", "192.168.200.107")
