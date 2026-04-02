"""Unit tests for CLI helpers in smartest_tv.cli."""
from __future__ import annotations

import pytest

from smartest_tv.cli import _parse_season_episode


# ---------------------------------------------------------------------------
# _parse_season_episode
# ---------------------------------------------------------------------------


def test_lowercase_s_e():
    assert _parse_season_episode("s2e8") == (2, 8)


def test_uppercase_S_E():
    assert _parse_season_episode("S02E08") == (2, 8)


def test_mixed_case_Se():
    assert _parse_season_episode("S2e8") == (2, 8)


def test_x_separator():
    assert _parse_season_episode("2x8") == (2, 8)


def test_X_separator_uppercase():
    assert _parse_season_episode("2X8") == (2, 8)


def test_padded_numbers():
    assert _parse_season_episode("S01E01") == (1, 1)


def test_large_season_episode():
    assert _parse_season_episode("S10E24") == (10, 24)


def test_invalid_format_plain_text():
    assert _parse_season_episode("Frieren") == (None, None)


def test_invalid_format_empty_string():
    assert _parse_season_episode("") == (None, None)


def test_invalid_format_partial_match_no_episode():
    # "s2" with no episode part should not match
    assert _parse_season_episode("s2") == (None, None)


def test_invalid_format_only_numbers():
    assert _parse_season_episode("28") == (None, None)


def test_s_prefix_with_x_separator():
    # "sXeY" — the s-prefix pattern requires [eExX] after season digits
    assert _parse_season_episode("s2x8") == (2, 8)


def test_season_1_episode_1():
    assert _parse_season_episode("s1e1") == (1, 1)
