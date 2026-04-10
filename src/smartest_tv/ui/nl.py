"""Natural-language fallback parser.

When a user types `stv <something>` and `<something>` isn't a known command,
try to parse it as natural language and dispatch to the right command.

Rules (deterministic, no LLM):
  1. "play <X>"              → ("play", ["auto", "<X>"])  — auto-detect platform
  2. "play <X> on <platform>" → ("play", ["<platform>", "<X>"])
  3. "<X> on <platform>"      → ("play", ["<platform>", "<X>"])
  4. "what's on" / "whats on" → ("whats-on", [])
  5. "what's on <platform>"   → ("whats-on", ["<platform>"])
  6. "search <X>"             → ("search", ["auto", "<X>"])
  7. "next" / "continue"      → ("next", [])
  8. "recommend" / "suggest"  → ("recommend", [])
  9. "stats" / "insights"     → ("insights", [])
 10. Bare string (fallback)   → ("search", ["<bare>"])  — handled as hint

If nothing matches, returns None and the caller shows `render_nl_hint`.

Platform auto-detection:
  - "youtube" / "yt" / "video"  → youtube
  - "netflix" / "nf"             → netflix
  - "spotify"                    → spotify
  - otherwise                    → "auto" (let resolve pick)
"""
from __future__ import annotations

import re

_PLATFORM_SYNONYMS = {
    "yt":      "youtube",
    "youtube": "youtube",
    "nf":      "netflix",
    "netflix": "netflix",
    "spotify": "spotify",
    "sp":      "spotify",
    "music":   "spotify",  # "play music X" → spotify
}

_PLAY_VERBS = {"play", "watch", "cast", "start", "open", "launch"}
_SEARCH_VERBS = {"search", "find", "look", "lookup"}
_CONTINUE_VERBS = {"next", "continue", "resume"}
_TRENDING_PHRASES = {"whats on", "what's on", "trending", "popular"}
_INSIGHTS_PHRASES = {"stats", "statistics", "insights", "history", "report"}
_RECOMMEND_PHRASES = {"recommend", "suggest", "suggestion", "recommendation"}


def parse(user_input: str) -> tuple[str, list[str]] | None:
    """Parse `user_input` into (command, args) or return None.

    Examples:
        >>> parse("play dark on netflix")
        ('play', ['netflix', 'dark'])
        >>> parse("youtube lofi beats")
        ('play', ['youtube', 'lofi beats'])
        >>> parse("what's on netflix")
        ('whats-on', ['netflix'])
        >>> parse("stats")
        ('insights', [])
    """
    if not user_input or not user_input.strip():
        return None

    # Normalize: lowercase, collapse whitespace
    raw = user_input.strip()
    lower = re.sub(r"\s+", " ", raw.lower())
    tokens = lower.split(" ")

    # Preserve original case for content strings — lowercase is only for matching
    raw_tokens = raw.split()

    # --- Rule: "what's on [platform]" / "trending [platform]" ---
    for phrase in _TRENDING_PHRASES:
        if lower.startswith(phrase):
            rest = lower[len(phrase):].strip()
            if not rest:
                return ("whats-on", [])
            platform = _resolve_platform(rest.split()[0])
            return ("whats-on", [platform] if platform != "auto" else [])

    # --- Rule: "next" / "continue" ---
    if tokens[0] in _CONTINUE_VERBS:
        # Optional show query after the verb
        if len(tokens) > 1:
            query = " ".join(raw_tokens[1:])
            return ("next", [query])
        return ("next", [])

    # --- Rule: "recommend [mood]" ---
    if tokens[0] in _RECOMMEND_PHRASES:
        if len(tokens) > 1:
            return ("recommend", ["--mood", tokens[1]])
        return ("recommend", [])

    # --- Rule: "stats" / "insights" ---
    if tokens[0] in _INSIGHTS_PHRASES:
        return ("insights", [])

    # --- Rule: "play X [on <platform>]" / "watch X [on <platform>]" ---
    if tokens[0] in _PLAY_VERBS:
        rest_tokens = raw_tokens[1:]
        if not rest_tokens:
            return None
        query, platform = _split_on_platform(rest_tokens)
        # If no platform detected, default to netflix (most common play target)
        if platform == "auto":
            platform = "netflix"
        return ("play", [platform, query])

    # --- Rule: "search X" / "find X" ---
    if tokens[0] in _SEARCH_VERBS:
        rest_tokens = raw_tokens[1:]
        if not rest_tokens:
            return None
        query, platform = _split_on_platform(rest_tokens)
        if platform == "auto":
            platform = "netflix"
        return ("search", [platform, query])

    # --- Rule: "<platform> X" — first token is a platform keyword ---
    first_as_platform = _PLATFORM_SYNONYMS.get(tokens[0])
    if first_as_platform and len(raw_tokens) > 1:
        query = " ".join(raw_tokens[1:])
        return ("play", [first_as_platform, query])

    # --- Rule: "X on <platform>" (no verb) ---
    if " on " in lower:
        query, platform = _split_on_platform(raw_tokens)
        if platform != "auto":
            return ("play", [platform, query])

    # --- Last resort: multi-word query with no verb looks like a title ---
    # Send it to `search` (safer than `play` — won't try to launch random IDs).
    # Single words are too ambiguous → fall through to hint.
    if len(raw_tokens) >= 2 and not any(t.startswith("-") for t in tokens):
        return ("search", ["netflix", raw])

    return None


def _split_on_platform(tokens: list[str]) -> tuple[str, str]:
    """Split ['dark', 'on', 'netflix'] → ('dark', 'netflix')."""
    lower = [t.lower() for t in tokens]
    if "on" in lower:
        on_idx = lower.index("on")
        before = tokens[:on_idx]
        after = tokens[on_idx + 1:]
        if after:
            platform = _resolve_platform(after[0])
            return (" ".join(before), platform)
    # Look for a trailing platform keyword: "dark netflix" → ("dark", "netflix")
    if len(tokens) >= 2 and _PLATFORM_SYNONYMS.get(lower[-1]):
        return (" ".join(tokens[:-1]), _PLATFORM_SYNONYMS[lower[-1]])
    return (" ".join(tokens), "auto")


def _resolve_platform(token: str) -> str:
    """Normalize a platform name synonym."""
    return _PLATFORM_SYNONYMS.get(token.lower(), "auto")


def suggestions_for(user_input: str) -> list[str]:
    """When parse() returns None, suggest a few closest commands."""
    return [
        f'stv play "{user_input}"        # play by name',
        f'stv search netflix "{user_input}"   # find the ID first',
        "stv whats-on                  # see what's trending",
        "stv --help                    # show all commands",
    ]
