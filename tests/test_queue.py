"""Tests for play queue (cache.py queue_* functions)."""

import json
import os
import tempfile
from pathlib import Path

import pytest

import smartest_tv.cache as cache_mod


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect all cache/queue I/O to a temp directory."""
    monkeypatch.setenv("STV_CONFIG_DIR", str(tmp_path))
    # Reload the module-level constants to pick up the new env var
    monkeypatch.setattr(cache_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(cache_mod, "QUEUE_FILE", tmp_path / "queue.json")
    yield


# ---------------------------------------------------------------------------
# queue_add
# ---------------------------------------------------------------------------

def test_queue_add_basic():
    item = cache_mod.queue_add("netflix", "Frieren")
    assert item["platform"] == "netflix"
    assert item["query"] == "Frieren"
    assert "added_at" in item
    assert "season" not in item
    assert "episode" not in item


def test_queue_add_with_season_episode():
    item = cache_mod.queue_add("netflix", "Frieren", season=2, episode=8)
    assert item["season"] == 2
    assert item["episode"] == 8


def test_queue_add_youtube():
    item = cache_mod.queue_add("youtube", "baby shark")
    assert item["platform"] == "youtube"
    assert item["query"] == "baby shark"


def test_queue_add_multiple_items():
    cache_mod.queue_add("netflix", "Show A")
    cache_mod.queue_add("youtube", "Video B")
    cache_mod.queue_add("spotify", "Track C")
    q = cache_mod.queue_show()
    assert len(q) == 3
    assert q[0]["query"] == "Show A"
    assert q[1]["query"] == "Video B"
    assert q[2]["query"] == "Track C"


# ---------------------------------------------------------------------------
# queue_show
# ---------------------------------------------------------------------------

def test_queue_show_empty():
    assert cache_mod.queue_show() == []


def test_queue_show_preserves_order():
    for i in range(5):
        cache_mod.queue_add("youtube", f"Video {i}")
    q = cache_mod.queue_show()
    assert [item["query"] for item in q] == [f"Video {i}" for i in range(5)]


# ---------------------------------------------------------------------------
# queue_pop
# ---------------------------------------------------------------------------

def test_queue_pop_empty():
    assert cache_mod.queue_pop() is None


def test_queue_pop_returns_first():
    cache_mod.queue_add("netflix", "First")
    cache_mod.queue_add("netflix", "Second")
    popped = cache_mod.queue_pop()
    assert popped["query"] == "First"
    remaining = cache_mod.queue_show()
    assert len(remaining) == 1
    assert remaining[0]["query"] == "Second"


def test_queue_pop_removes_item():
    cache_mod.queue_add("youtube", "Only Item")
    cache_mod.queue_pop()
    assert cache_mod.queue_show() == []


# ---------------------------------------------------------------------------
# queue_skip
# ---------------------------------------------------------------------------

def test_queue_skip_removes_first():
    cache_mod.queue_add("netflix", "Skip Me")
    cache_mod.queue_add("netflix", "Keep Me")
    cache_mod.queue_skip()
    q = cache_mod.queue_show()
    assert len(q) == 1
    assert q[0]["query"] == "Keep Me"


def test_queue_skip_empty_is_noop():
    cache_mod.queue_skip()  # Should not raise
    assert cache_mod.queue_show() == []


# ---------------------------------------------------------------------------
# queue_clear
# ---------------------------------------------------------------------------

def test_queue_clear():
    for i in range(3):
        cache_mod.queue_add("youtube", f"Item {i}")
    cache_mod.queue_clear()
    assert cache_mod.queue_show() == []


def test_queue_clear_empty_is_noop():
    cache_mod.queue_clear()
    assert cache_mod.queue_show() == []


# ---------------------------------------------------------------------------
# Persistence: queue survives across calls
# ---------------------------------------------------------------------------

def test_queue_persists_to_disk(tmp_path):
    """Verify the queue is actually written to the JSON file."""
    cache_mod.queue_add("spotify", "My Track")
    queue_file = cache_mod.QUEUE_FILE
    assert queue_file.exists()
    data = json.loads(queue_file.read_text())
    assert len(data) == 1
    assert data[0]["query"] == "My Track"
