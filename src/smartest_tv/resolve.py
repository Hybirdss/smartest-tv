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

    # --- Episode with title_id → HTTP scrape (all seasons at once) ---
    if title_id and season and episode:
        try:
            seasons = _scrape_netflix_all_seasons(title_id)
            if season <= len(seasons):
                ep_ids = seasons[season - 1]

                # Cache all seasons
                for i, s_ids in enumerate(seasons, 1):
                    cache.put_netflix_show(slug, title_id, i, s_ids[0], len(s_ids))

                if episode <= len(ep_ids):
                    return str(ep_ids[episode - 1])
                raise ValueError(
                    f"{query} S{season} has {len(ep_ids)} episodes, "
                    f"episode {episode} requested."
                )
        except ValueError:
            raise
        except Exception:
            pass

    # --- Auto-discover title ID via web search ---
    if not title_id:
        title_id = _search_netflix_title_id(query)
        if title_id:
            return resolve_netflix(query, season, episode, title_id)
        raise ValueError(
            f"Could not find '{query}' on Netflix. Try:\n"
            f"  stv search netflix \"{query}\"   (check the title exists)\n"
            f"  stv play netflix \"{query}\" --title-id XXXXX   (manual ID)"
        )
    raise ValueError(
        f"Found Netflix title {title_id} but could not extract S{season}E{episode}. Try:\n"
        f"  stv search netflix \"{query}\"   (check season/episode count)\n"
        f"  stv cache set netflix \"{query}\" -s {season} --first-ep-id ID --count N"
    )


def _search_netflix_title_id(query: str) -> int | None:
    """Search for a Netflix title ID via Brave Search."""
    return _web_search_first_match(
        f"{query} site:netflix.com/title",
        r"netflix\.com/title/(\d+)",
        cast=int,
    )


def _web_search_first_match(query: str, pattern: str, cast=str):
    """Search Brave (fallback DuckDuckGo) and return first regex match."""
    from urllib.parse import quote

    for search_url in [
        f"https://search.brave.com/search?q={quote(query)}",
        f"https://html.duckduckgo.com/html/?q={quote(query)}",
    ]:
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-L", "--compressed", "--max-time", "10",
                    "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    search_url,
                ],
                capture_output=True, text=True, timeout=15,
            )
            matches = re.findall(pattern, result.stdout or "")
            if matches:
                return cast(matches[0]) if cast else matches[0]
        except (subprocess.TimeoutExpired, OSError):
            continue
    return None


def _scrape_netflix_all_seasons(title_id: int) -> list[list[int]]:
    """Scrape ALL season episode IDs from Netflix title page via curl.

    Netflix embeds videoIds for all seasons in the initial HTML (in <script>
    tags). No Playwright needed.

    Returns a list of lists: seasons[0] = [S1E1_id, S1E2_id, ...], etc.
    Sorted by first episode ID (earlier seasons have lower IDs).
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

    # Netflix embeds __typename with each videoId:
    #   "Episode" = actual episode, "Season" = season container, "Show" = the show
    # Filter to Episodes only — this perfectly excludes season IDs.
    episode_ids = set()
    season_ids = set()
    for m in re.finditer(
        r'"__typename":"(Episode|Season|Show)","videoId":(\d+)', html
    ):
        typename, vid = m.group(1), int(m.group(2))
        if typename == "Episode":
            episode_ids.add(vid)
        elif typename == "Season":
            season_ids.add(vid)

    # If __typename parsing found episodes, use those (precise).
    # Otherwise fall back to raw videoId extraction (less precise).
    if episode_ids:
        unique = sorted(episode_ids)
    else:
        raw_ids = [int(m) for m in re.findall(r'"videoId"\s*:\s*(\d+)', html)]
        unique = sorted(set(vid for vid in raw_ids if vid != title_id and vid not in season_ids))

    # Find ALL sequential clusters (each cluster = one season)
    clusters = _find_all_sequential_clusters(unique)

    # Sort by first ID (earlier seasons have lower IDs)
    clusters.sort(key=lambda c: c[0])
    return clusters


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
    """Resolve Spotify content to a URI.

    Accepts:
      - Direct URI: spotify:track:xxx
      - Direct URL: https://open.spotify.com/track/xxx
      - Search query: "Ye White Lines" → searches DuckDuckGo for Spotify URL
    """
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

    # Search web for Spotify URL
    uri = _search_spotify(query)
    if uri:
        cache.put("spotify", slug, uri)
        return uri

    raise ValueError(f"No Spotify results for: {query}")


def _search_spotify(query: str) -> str | None:
    """Search for a Spotify track/album via Brave Search."""
    from urllib.parse import quote

    for search_url in [
        f"https://search.brave.com/search?q={quote(query)}+site:open.spotify.com",
        f"https://html.duckduckgo.com/html/?q={quote(query)}+site:open.spotify.com",
    ]:
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-L", "--compressed", "--max-time", "10",
                    "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    search_url,
                ],
                capture_output=True, text=True, timeout=15,
            )
            matches = re.findall(
                r"open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)",
                result.stdout or "",
            )
            if matches:
                # Prefer track > album > playlist
                priority = {"track": 0, "album": 1, "playlist": 2}
                matches.sort(key=lambda m: priority.get(m[0], 99))
                return f"spotify:{matches[0][0]}:{matches[0][1]}"
        except (subprocess.TimeoutExpired, OSError):
            continue
    return None


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


def _find_all_sequential_clusters(ids: list[int], min_length: int = 3) -> list[list[int]]:
    """Find all consecutive runs of at least min_length in a sorted list.

    Netflix episode IDs are consecutive (e.g., 81726715-81726725 for S1,
    82656790-82656799 for S2). Non-episode IDs (recommendations, season IDs)
    are scattered and won't form long runs.

    Args:
        ids: Sorted, deduplicated list of integer IDs.
        min_length: Minimum cluster length to include (default 3 filters noise).

    Returns:
        List of clusters, each cluster is a list of consecutive IDs.
    """
    if not ids:
        return []

    sorted_ids = sorted(set(ids))
    clusters: list[list[int]] = []
    current = [sorted_ids[0]]

    for i in range(1, len(sorted_ids)):
        if sorted_ids[i] == sorted_ids[i - 1] + 1:
            current.append(sorted_ids[i])
        else:
            if len(current) >= min_length:
                clusters.append(current)
            current = [sorted_ids[i]]

    if len(current) >= min_length:
        clusters.append(current)

    return clusters
