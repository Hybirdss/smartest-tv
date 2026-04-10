"""Tests for the natural-language fallback parser (ui/nl.py)."""
from __future__ import annotations

from smartest_tv.ui.nl import parse, suggestions_for


class TestPlayVerb:
    def test_play_x_on_netflix(self):
        assert parse("play dark on netflix") == ("play", ["netflix", "dark"])

    def test_play_multi_word_on_platform(self):
        assert parse("play the bear on netflix") == ("play", ["netflix", "the bear"])

    def test_play_without_platform_defaults_to_netflix(self):
        assert parse("play wednesday") == ("play", ["netflix", "wednesday"])

    def test_watch_verb_synonym(self):
        assert parse("watch dark on netflix") == ("play", ["netflix", "dark"])

    def test_start_verb(self):
        assert parse("start dark on netflix") == ("play", ["netflix", "dark"])

    def test_play_preserves_title_case(self):
        assert parse("play Stranger Things on netflix") == ("play", ["netflix", "Stranger Things"])


class TestPlatformFirstShorthand:
    def test_youtube_shorthand(self):
        assert parse("youtube lofi beats") == ("play", ["youtube", "lofi beats"])

    def test_yt_abbrev(self):
        assert parse("yt baby shark") == ("play", ["youtube", "baby shark"])

    def test_spotify_shorthand(self):
        assert parse("spotify ye white lines") == ("play", ["spotify", "ye white lines"])

    def test_netflix_shorthand(self):
        assert parse("netflix wednesday") == ("play", ["netflix", "wednesday"])


class TestTrending:
    def test_whats_on_bare(self):
        assert parse("what's on") == ("whats-on", [])

    def test_whats_on_no_apostrophe(self):
        assert parse("whats on") == ("whats-on", [])

    def test_whats_on_netflix(self):
        assert parse("what's on netflix") == ("whats-on", ["netflix"])

    def test_trending_platform(self):
        assert parse("trending youtube") == ("whats-on", ["youtube"])


class TestContinue:
    def test_next(self):
        assert parse("next") == ("next", [])

    def test_continue_synonym(self):
        assert parse("continue") == ("next", [])

    def test_resume_synonym(self):
        assert parse("resume") == ("next", [])

    def test_next_with_show(self):
        assert parse("next wednesday") == ("next", ["wednesday"])


class TestRecommend:
    def test_recommend(self):
        assert parse("recommend") == ("recommend", [])

    def test_suggest_synonym(self):
        assert parse("suggest") == ("recommend", [])

    def test_recommend_with_mood(self):
        assert parse("recommend chill") == ("recommend", ["--mood", "chill"])


class TestInsights:
    def test_stats(self):
        assert parse("stats") == ("insights", [])

    def test_insights(self):
        assert parse("insights") == ("insights", [])

    def test_history(self):
        assert parse("history") == ("insights", [])


class TestSearch:
    def test_search_verb(self):
        assert parse("search dark on netflix") == ("search", ["netflix", "dark"])

    def test_find_synonym(self):
        assert parse("find wednesday") == ("search", ["netflix", "wednesday"])


class TestFallback:
    def test_multi_word_bare_query_becomes_search(self):
        assert parse("the bear") == ("search", ["netflix", "the bear"])

    def test_title_with_episode_becomes_search(self):
        assert parse("wednesday s1e1") == ("search", ["netflix", "wednesday s1e1"])

    def test_single_word_returns_none(self):
        """Bare single word is too ambiguous → show hint."""
        assert parse("xyz") is None
        assert parse("dark") is None

    def test_empty_returns_none(self):
        assert parse("") is None

    def test_whitespace_returns_none(self):
        assert parse("   ") is None

    def test_flag_like_input_returns_none(self):
        assert parse("--help") is None


class TestSuggestionsHelper:
    def test_returns_useful_commands(self):
        suggestions = suggestions_for("xyz")
        assert len(suggestions) >= 3
        assert any("xyz" in s for s in suggestions)
        assert any("stv --help" in s for s in suggestions)
