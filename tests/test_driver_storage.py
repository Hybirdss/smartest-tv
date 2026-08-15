"""Driver credential storage honors STV_CONFIG_DIR (issue #15).

Home Assistant runs in a container where $HOME (/root) does not survive
rebuilds. All three drivers must keep pairing credentials under
config.CONFIG_DIR (which honors STV_CONFIG_DIR) so pairing persists.
"""

from __future__ import annotations

import pytest

import smartest_tv.config as config_mod


@pytest.fixture()
def cfg(monkeypatch, tmp_path):
    """Point config.CONFIG_DIR at tmp_path."""
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    return config_mod


def test_android_cert_dir_uses_config_dir(cfg):
    pytest.importorskip("androidtvremote2")
    from smartest_tv._engine.drivers.android import AndroidDriver

    d = AndroidDriver(ip="1.2.3.4")
    assert d.cert_dir == str(cfg.CONFIG_DIR / "android-cert")
    assert "~" not in d.cert_dir


def test_samsung_token_file_uses_config_dir(cfg):
    pytest.importorskip("samsungtvws")
    from smartest_tv._engine.drivers.samsung import SamsungDriver

    d = SamsungDriver(ip="1.2.3.4")
    assert d.token_file == str(cfg.CONFIG_DIR / "samsung_1.2.3.4.token")


def test_lg_key_file_uses_config_dir(cfg):
    pytest.importorskip("aiowebostv")
    from smartest_tv._engine.drivers.lg import LGDriver

    d = LGDriver(ip="1.2.3.4")
    assert d.key_file == str(cfg.CONFIG_DIR / "lg_key.json")


def test_android_paired_property():
    pytest.importorskip("androidtvremote2")
    from smartest_tv._engine.drivers.android import AndroidDriver

    d = AndroidDriver(ip="1.2.3.4")
    assert d.paired is False
