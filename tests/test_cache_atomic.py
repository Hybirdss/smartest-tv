"""Concurrent write safety for cache.json / queue.json.

A multi-TV broadcast spawns background threads (revalidate + contribute)
while the foreground records play history. With plain write_text(),
overlapping writes produced torn JSON or silently overwrote entries.
These tests exercise N parallel writers and assert no loss.
"""
from __future__ import annotations

import json
import threading

import pytest

import smartest_tv.cache as cache_module


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    queue_file = tmp_path / "queue.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", cache_file)
    monkeypatch.setattr(cache_module, "QUEUE_FILE", queue_file)
    monkeypatch.setattr(cache_module, "CONFIG_DIR", tmp_path)
    # Disable community + API lookups so threads never hit the network.
    monkeypatch.setattr(cache_module, "_api_get", lambda *_, **__: None)
    monkeypatch.setattr(cache_module, "_contribute", lambda *_, **__: None)
    yield


def test_put_many_concurrent_writers_preserve_all_entries(monkeypatch):
    """Each thread writes a distinct key; all must survive the race.

    Injects a sleep inside ``_save`` to stretch the critical section so
    the lock is genuinely contended. On a broken (unlocked) impl, two
    threads both ``_load`` pre-save, each adds its own key, and the
    second ``_save`` overwrites the first — keys go missing. This test
    was tautological in its first form (threads may serialise fast
    enough on a warm path that the race never fires), so the sleep
    forces an interleave every time.
    """
    import time as _time

    real_save = cache_module._save

    def slow_save(data):
        # 5 ms is well over the time another thread needs to enter the
        # critical section; without the RLock this guarantees overlap.
        _time.sleep(0.005)
        real_save(data)

    monkeypatch.setattr(cache_module, "_save", slow_save)

    N = 30

    def writer(i):
        cache_module.put("netflix", f"show-{i}", f"id-{i}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    data = json.loads(cache_module.CACHE_FILE.read_text())
    netflix = data.get("netflix", {})
    for i in range(N):
        assert netflix.get(f"show-{i}") == f"id-{i}", f"lost show-{i}"


def test_record_play_concurrent_writes_keep_entries():
    """50 parallel record_play calls — history should contain 50 entries,
    not lose any to overwrite races."""
    N = 50

    def writer(i):
        cache_module.record_play("youtube", f"query-{i}", f"vid-{i}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    history = cache_module.get_history(limit=N)
    queries = {entry["query"] for entry in history}
    # _history is capped at 50 entries; we wrote exactly 50, so all are present.
    assert len(queries) == N


def test_queue_add_concurrent_keeps_all_items():
    N = 30

    def writer(i):
        cache_module.queue_add("netflix", f"q-{i}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    items = cache_module.queue_show()
    assert len(items) == N
    queries = {it["query"] for it in items}
    for i in range(N):
        assert f"q-{i}" in queries
