"""Tests for multi-TV config (config.py)."""

import os
import textwrap
from pathlib import Path

import pytest

import smartest_tv.config as config_mod
from smartest_tv.config import (
    add_tv,
    get_tv_config,
    list_tvs,
    remove_tv,
    set_default_tv,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect all config I/O to a temp directory."""
    monkeypatch.setenv("STV_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")
    yield tmp_path


def write_config(tmp_path: Path, text: str) -> None:
    (tmp_path / "config.toml").write_text(textwrap.dedent(text))


# ---------------------------------------------------------------------------
# Legacy single-TV format
# ---------------------------------------------------------------------------

def test_legacy_get_tv_config(tmp_path):
    write_config(tmp_path, """
        [tv]
        platform = "lg"
        ip = "192.168.1.100"
        mac = "aa:bb:cc:dd:ee:ff"
    """)
    tv = get_tv_config()
    assert tv["platform"] == "lg"
    assert tv["ip"] == "192.168.1.100"
    assert tv["mac"] == "aa:bb:cc:dd:ee:ff"


def test_legacy_tv_name_ignored(tmp_path):
    """In legacy mode, tv_name arg is ignored (only one TV)."""
    write_config(tmp_path, """
        [tv]
        platform = "samsung"
        ip = "10.0.0.50"
    """)
    tv = get_tv_config(tv_name="any-name")
    assert tv["platform"] == "samsung"


def test_legacy_list_tvs(tmp_path):
    write_config(tmp_path, """
        [tv]
        platform = "lg"
        ip = "192.168.1.100"
    """)
    tvs = list_tvs()
    assert len(tvs) == 1
    assert tvs[0]["platform"] == "lg"
    assert tvs[0]["default"] is True


def test_legacy_env_var_override(tmp_path, monkeypatch):
    write_config(tmp_path, """
        [tv]
        platform = "lg"
        ip = "192.168.1.100"
    """)
    monkeypatch.setenv("TV_IP", "10.0.0.99")
    tv = get_tv_config()
    assert tv["ip"] == "10.0.0.99"


# ---------------------------------------------------------------------------
# Multi-TV format
# ---------------------------------------------------------------------------

def test_multi_get_by_name(tmp_path):
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.10"

        [tv.bedroom]
        platform = "samsung"
        ip = "192.168.1.20"
    """)
    tv = get_tv_config("bedroom")
    assert tv["platform"] == "samsung"
    assert tv["ip"] == "192.168.1.20"
    assert tv["name"] == "bedroom"


def test_multi_get_unknown_name(tmp_path):
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.10"
    """)
    with pytest.raises(KeyError, match="not found"):
        get_tv_config("nonexistent")


def test_multi_default_tv_by_flag(tmp_path):
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.10"

        [tv.bedroom]
        platform = "samsung"
        ip = "192.168.1.20"
        default = true
    """)
    tv = get_tv_config()
    assert tv["platform"] == "samsung"


def test_multi_only_one_tv_is_default(tmp_path):
    write_config(tmp_path, """
        [tv.only]
        platform = "roku"
        ip = "192.168.1.30"
    """)
    tv = get_tv_config()
    assert tv["platform"] == "roku"


def test_multi_no_default_returns_first(tmp_path):
    write_config(tmp_path, """
        [tv.alpha]
        platform = "lg"
        ip = "192.168.1.1"

        [tv.beta]
        platform = "samsung"
        ip = "192.168.1.2"
    """)
    tv = get_tv_config()
    assert tv["platform"] == "lg"


def test_multi_list_tvs(tmp_path):
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.10"

        [tv.bedroom]
        platform = "samsung"
        ip = "192.168.1.20"
        default = true
    """)
    tvs = list_tvs()
    assert len(tvs) == 2
    defaults = [t for t in tvs if t["default"]]
    assert len(defaults) == 1
    assert defaults[0]["name"] == "bedroom"


# ---------------------------------------------------------------------------
# add_tv (includes legacy migration)
# ---------------------------------------------------------------------------

def test_add_tv_to_empty_config():
    add_tv("living-room", "lg", "192.168.1.10")
    tv = get_tv_config("living-room")
    assert tv["platform"] == "lg"


def test_add_tv_migrates_legacy(tmp_path):
    write_config(tmp_path, """
        [tv]
        platform = "lg"
        ip = "192.168.1.100"
    """)
    add_tv("bedroom", "samsung", "192.168.1.20")
    # Old TV still accessible
    tvs = list_tvs()
    names = {t["name"] for t in tvs}
    assert "bedroom" in names


def test_add_tv_default_flag():
    add_tv("living-room", "lg", "192.168.1.10")
    add_tv("bedroom", "samsung", "192.168.1.20", default=True)
    tv = get_tv_config()
    assert tv["platform"] == "samsung"


# ---------------------------------------------------------------------------
# remove_tv
# ---------------------------------------------------------------------------

def test_remove_tv():
    add_tv("living-room", "lg", "192.168.1.10")
    add_tv("bedroom", "samsung", "192.168.1.20")
    remove_tv("bedroom")
    tvs = list_tvs()
    assert all(t["name"] != "bedroom" for t in tvs)


def test_remove_tv_not_found():
    add_tv("living-room", "lg", "192.168.1.10")
    with pytest.raises(KeyError, match="not found"):
        remove_tv("ghost")


def test_remove_tv_legacy_raises():
    """remove_tv on legacy config raises KeyError."""
    # No config file → get_tv_config returns empty, but remove_tv
    # loads a legacy-style config; we need to set one up explicitly.
    # Writing a legacy config first:
    isolated = config_mod.CONFIG_FILE.parent
    (isolated / "config.toml").write_text("[tv]\nplatform = \"lg\"\nip = \"1.1.1.1\"\n")
    with pytest.raises(KeyError):
        remove_tv("living-room")


# ---------------------------------------------------------------------------
# set_default_tv
# ---------------------------------------------------------------------------

def test_set_default_tv():
    add_tv("living-room", "lg", "192.168.1.10")
    add_tv("bedroom", "samsung", "192.168.1.20")
    set_default_tv("living-room")
    tv = get_tv_config()
    assert tv["platform"] == "lg"


def test_set_default_tv_not_found():
    add_tv("living-room", "lg", "192.168.1.10")
    with pytest.raises(KeyError, match="not found"):
        set_default_tv("ghost")


# ---------------------------------------------------------------------------
# No config — empty returns
# ---------------------------------------------------------------------------

def test_no_config_returns_empty():
    tv = get_tv_config()
    assert tv["platform"] == ""
    assert tv["ip"] == ""
