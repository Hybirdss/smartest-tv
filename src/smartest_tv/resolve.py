"""Content ID resolver for streaming platforms.

Three-tier strategy:
  1. Cache hit → instant (0ms)
  2. Built-in resolution → fast (yt-dlp for YouTube, ~2s)
  3. Fail with helpful message → AI or user fills the gap

The cache is the real product here. Once any ID is discovered (by AI,
by the user, by HTTP scraping), it's cached forever. Repeat plays are
always instant.
"""

from __future__ import annotations

import re
import shutil
import subprocess

from smartest_tv import cache


# ---------------------------------------------------------------------------
# Netflix
# ---------------------------------------------------------------------------

def resolve_netflix(
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve Netflix content to a videoId.

    Movies: title_id IS the videoId.
    Episodes: needs season + episode + cached data or title_id for scraping.
    """
    slug = _slugify(query)

    # --- Cache check ---
    if season and episode:
        cached = cache.get_netflix_episode(slug, season, episode)
        if cached:
            return cached

    # --- Movie (no season/episode) → title_id is the videoId ---
    if title_id and not season:
        return str(title_id)

    # --- Episode with title_id → try HTTP scrape (works for S1) ---
    if title_id and season and episode:
        try:
            episode_ids = _scrape_netflix_episodes(title_id)
            if episode_ids and episode <= len(episode_ids):
                video_id = episode_ids[episode - 1]
                cache.put_netflix_show(slug, title_id, season, episode_ids[0], len(episode_ids))
                return str(video_id)
        except Exception:
            pass  # Fall through to helpful error

    # --- Can't resolve automatically ---
    hint = f'stv resolve netflix "{query}"'
    if season:
        hint += f" -s {season}"
    if episode:
        hint += f" -e {episode}"

    parts = []
    if not title_id:
        parts.append("pass --title-id (from netflix.com/title/XXXXX URL)")
    if season and season > 1:
        parts.append(
            f"for S{season}+, pre-cache with: "
            f'stv cache netflix "{query}" -s {season} --first-ep-id <ID> --count <N>'
        )
    advice = " or ".join(parts) if parts else "check the title ID"

    raise ValueError(f"Can't auto-resolve: {advice}")


def _scrape_netflix_episodes(title_id: int) -> list[int]:
    """Scrape episode videoIds from Netflix title page via curl.

    Only returns Season 1 episodes (Netflix server-renders S1 only).
    Returns empty list if scraping fails.
    """
    url = f"https://www.netflix.com/title/{title_id}"
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L", "--compressed", "--max-time", "10",
                "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "-H", "Accept-Language: en-US,en;q=0.9",
                url,
            ],
            capture_output=True, text=True, timeout=15,
        )
        html = result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return []

    if not html:
        return []

    raw_ids = [int(m) for m in re.findall(r'"videoId"\s*:\s*(\d+)', html)]
    unique = list(dict.fromkeys(vid for vid in raw_ids if vid != title_id))
    return _find_sequential_cluster(unique)


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def resolve_youtube(query: str) -> str:
    """Resolve YouTube search → video ID via yt-dlp."""
    slug = _slugify(query)
    cached = cache.get("youtube", slug)
    if cached:
        return cached

    if not shutil.which("yt-dlp"):
        raise ValueError("yt-dlp not found. Install: pip install yt-dlp")

    result = subprocess.run(
        ["yt-dlp", f"ytsearch1:{query}", "--get-id", "--no-download"],
        capture_output=True, text=True, timeout=15,
    )
    video_id = result.stdout.strip().split("\n")[0].strip()
    if not video_id:
        raise ValueError(f"No YouTube results for: {query}")

    cache.put("youtube", slug, video_id)
    return video_id


# ---------------------------------------------------------------------------
# Spotify
# ---------------------------------------------------------------------------

def resolve_spotify(query: str) -> str:
    """Resolve Spotify content to a URI."""
    if query.startswith("spotify:"):
        return query
    if "open.spotify.com" in query:
        m = re.search(r"open\.spotify\.com/(track|album|artist|playlist)/([A-Za-z0-9]+)", query)
        if m:
            return f"spotify:{m.group(1)}:{m.group(2)}"

    slug = _slugify(query)
    cached = cache.get("spotify", slug)
    if cached:
        return cached

    raise ValueError(
        f"Pass a Spotify URL or URI directly. "
        f"Example: stv play spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS"
    )


# ---------------------------------------------------------------------------
# Unified
# ---------------------------------------------------------------------------

def resolve(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve content to a platform-specific ID."""
    p = platform.lower().strip()
    if p == "netflix":
        return resolve_netflix(query, season, episode, title_id)
    elif p == "youtube":
        return resolve_youtube(query)
    elif p == "spotify":
        return resolve_spotify(query)
    else:
        raise ValueError(f"Unsupported platform: {platform}. Use netflix, youtube, or spotify.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")


def _find_sequential_cluster(ids: list[int]) -> list[int]:
    """Find the longest consecutive run in a list of IDs."""
    if not ids:
        return []

    sorted_ids = sorted(set(ids))
    best_start = 0
    best_len = 1
    cur_start = 0
    cur_len = 1

    for i in range(1, len(sorted_ids)):
        if sorted_ids[i] == sorted_ids[i - 1] + 1:
            cur_len += 1
        else:
            if cur_len > best_len:
                best_start = cur_start
                best_len = cur_len
            cur_start = i
            cur_len = 1

    if cur_len > best_len:
        best_start = cur_start
        best_len = cur_len

    return sorted_ids[best_start : best_start + best_len] if best_len >= 2 else []
