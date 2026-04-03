"""Tests for TV group management and sync features."""

import textwrap
from pathlib import Path

import pytest

import smartest_tv.config as config_mod
from smartest_tv.config import (
    add_tv,
    delete_group,
    get_all_tv_names,
    get_group_members,
    get_groups,
    get_tv_config,
    list_tvs,
    save_group,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect all config I/O to a temp directory."""
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.toml")
    yield tmp_path


def write_config(path: Path, text: str) -> None:
    (path / "config.toml").write_text(textwrap.dedent(text))


def _setup_multi_tv(tmp_path):
    """Create a multi-TV config with 3 TVs."""
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.100"
        default = true

        [tv.bedroom]
        platform = "samsung"
        ip = "192.168.1.101"

        [tv.friend]
        platform = "remote"
        url = "http://203.0.113.50:8911"
    """)


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------


def test_save_and_get_group(tmp_path):
    _setup_multi_tv(tmp_path)
    save_group("party", ["living-room", "bedroom"])
    members = get_group_members("party")
    assert members == ["living-room", "bedroom"]


def test_get_groups_multiple(tmp_path):
    _setup_multi_tv(tmp_path)
    save_group("home", ["living-room", "bedroom"])
    save_group("all", ["living-room", "bedroom", "friend"])
    groups = get_groups()
    assert "home" in groups
    assert "all" in groups
    assert len(groups["all"]) == 3


def test_delete_group(tmp_path):
    _setup_multi_tv(tmp_path)
    save_group("party", ["living-room", "bedroom"])
    delete_group("party")
    assert "party" not in get_groups()


def test_delete_nonexistent_group(tmp_path):
    _setup_multi_tv(tmp_path)
    with pytest.raises(KeyError, match="not found"):
        delete_group("nonexistent")


def test_save_group_unknown_tv(tmp_path):
    _setup_multi_tv(tmp_path)
    with pytest.raises(ValueError, match="Unknown TV"):
        save_group("bad", ["living-room", "ghost-tv"])


def test_get_group_members_unknown_group(tmp_path):
    _setup_multi_tv(tmp_path)
    with pytest.raises(KeyError, match="not found"):
        get_group_members("nonexistent")


def test_get_group_members_validates_tvs(tmp_path):
    """If a TV was removed but group still references it, error on access."""
    _setup_multi_tv(tmp_path)
    save_group("party", ["living-room", "bedroom"])
    # Remove bedroom from TV config by rewriting without it
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.100"

        [groups]
        party = ["living-room", "bedroom"]
    """)
    with pytest.raises(KeyError, match="Unknown TV"):
        get_group_members("party")


def test_group_with_remote_tv(tmp_path):
    _setup_multi_tv(tmp_path)
    save_group("watch-party", ["living-room", "friend"])
    members = get_group_members("watch-party")
    assert "friend" in members


# ---------------------------------------------------------------------------
# get_all_tv_names
# ---------------------------------------------------------------------------


def test_get_all_tv_names(tmp_path):
    _setup_multi_tv(tmp_path)
    names = get_all_tv_names()
    assert set(names) == {"living-room", "bedroom", "friend"}


def test_get_all_tv_names_empty(tmp_path):
    assert get_all_tv_names() == []


# ---------------------------------------------------------------------------
# Groups persist alongside TV config
# ---------------------------------------------------------------------------


def test_groups_survive_tv_add(tmp_path):
    _setup_multi_tv(tmp_path)
    save_group("home", ["living-room", "bedroom"])
    add_tv("kitchen", "roku", "192.168.1.102")
    # Groups should still be there
    groups = get_groups()
    assert "home" in groups
    assert groups["home"] == ["living-room", "bedroom"]


def test_groups_from_toml(tmp_path):
    """Groups defined directly in TOML are readable."""
    write_config(tmp_path, """
        [tv.living-room]
        platform = "lg"
        ip = "192.168.1.100"

        [tv.bedroom]
        platform = "samsung"
        ip = "192.168.1.101"

        [groups]
        party = ["living-room", "bedroom"]
    """)
    groups = get_groups()
    assert groups["party"] == ["living-room", "bedroom"]


# ---------------------------------------------------------------------------
# Remote TV config
# ---------------------------------------------------------------------------


def test_remote_tv_in_config(tmp_path):
    _setup_multi_tv(tmp_path)
    tv = get_tv_config("friend")
    assert tv["platform"] == "remote"
    assert tv["url"] == "http://203.0.113.50:8911"


def test_add_remote_tv(tmp_path):
    _setup_multi_tv(tmp_path)
    add_tv("jake", "remote", "http://10.0.0.5:8911")
    tv = get_tv_config("jake")
    assert tv["platform"] == "remote"
