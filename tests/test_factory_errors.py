"""Factory driver-import error handling (issues #14 regression tests).

Two failure modes must not be confused:
  1. Driver package genuinely missing → install advice.
  2. A transitive dependency broken (e.g. mixed-version aiofiles inside
     Home Assistant) → name the real culprit, never "install adb-shell".
"""

from __future__ import annotations

import sys

import pytest

from smartest_tv.drivers.factory import _driver_import_error


def test_missing_driver_package_gives_install_advice():
    exc = ImportError("No module named 'androidtvremote2'", name="androidtvremote2")
    with pytest.raises(ImportError) as ei:
        _driver_import_error("Android", "androidtvremote2", "android", exc)
    msg = str(ei.value)
    assert "androidtvremote2" in msg
    assert "stv[android]" in msg
    # adb-shell was the LEGACY driver — must never appear again (issue #14)
    assert "adb-shell" not in msg
    # bscpylgtv was the LEGACY LG lib — same rule
    exc2 = ImportError("No module named 'aiowebostv'", name="aiowebostv")
    with pytest.raises(ImportError) as ei2:
        _driver_import_error("LG", "aiowebostv", "lg", exc2)
    assert "aiowebostv" in str(ei2.value)
    assert "bscpylgtv" not in str(ei2.value)


def test_broken_transitive_dependency_names_root_cause():
    # Exact shape of the issue #14 traceback: androidtvremote2 is installed,
    # but its aiofiles dependency is a mixed-version install.
    exc = ImportError(
        "cannot import name 'wrap' from 'aiofiles.base'",
        name="aiofiles.base",
    )
    with pytest.raises(ImportError) as ei:
        _driver_import_error("Android", "androidtvremote2", "android", exc)
    msg = str(ei.value)
    assert "aiofiles" in msg
    assert "force-reinstall" in msg
    # Root cause must stay visible and chained
    assert ei.value.__cause__ is exc


def test_transitive_detection_walks_cause_chain():
    """Production shape: factory catches the engine driver's re-raise
    (name=None), whose __cause__ is another re-raise, whose __cause__ is
    the real aiofiles failure. The name lives two levels down."""
    real = ImportError("cannot import name 'wrap' from 'aiofiles.base'", name="aiofiles.base")
    engine = ImportError("Android driver requires androidtvremote2...")
    engine.__cause__ = real
    caught = ImportError("Android driver requires androidtvremote2...")
    caught.__cause__ = engine

    with pytest.raises(ImportError) as ei:
        _driver_import_error("Android", "androidtvremote2", "android", caught)
    msg = str(ei.value)
    assert "aiofiles" in msg and "force-reinstall" in msg
    # The inline message shows the REAL error, not the re-raise text
    assert "cannot import name 'wrap'" in msg
    assert ei.value.__cause__ is caught


def test_original_exception_always_chained():
    exc = ImportError("No module named 'samsungtvws'", name="samsungtvws")
    with pytest.raises(ImportError) as ei:
        _driver_import_error("Samsung", "samsungtvws", "samsung", exc)
    assert ei.value.__cause__ is exc


def test_create_driver_android_missing_surfaces_helpful_error(monkeypatch, tmp_path):
    """End-to-end: factory must chain the real cause when the driver module
    itself fails to import (None-injection forces ImportError)."""
    import smartest_tv.drivers.factory as factory_mod

    monkeypatch.setattr(factory_mod, "get_tv_config", lambda name=None: {
        "platform": "android", "ip": "1.2.3.4", "mac": "",
    })
    monkeypatch.setitem(sys.modules, "smartest_tv._engine.drivers.android", None)
    with pytest.raises(ImportError) as ei:
        factory_mod.create_driver("lr")
    assert "android" in str(ei.value).lower()
