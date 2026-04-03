"""Unit tests for smartest_tv.api."""

from __future__ import annotations

from smartest_tv import api


def test_get_driver_uses_factory_and_caches(monkeypatch):
    calls: list[None] = []
    sentinel = object()

    monkeypatch.setattr(api, "_driver", None)

    def fake_create_driver():
        calls.append(None)
        return sentinel

    monkeypatch.setattr(api, "create_driver", fake_create_driver)

    first = api._get_driver()
    second = api._get_driver()

    assert first is sentinel
    assert second is sentinel
    assert calls == [None]

