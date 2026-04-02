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
# Trending
# ---------------------------------------------------------------------------

def fetch_netflix_trending(limit: int = 10) -> list[dict]:
    """Fetch Netflix Top 10 from top10.netflix.com.

    Falls back to Brave Search if the scrape yields nothing.
    Returns: [{"rank": 1, "title": "...", "category": "TV"}, ...]
    """
    import time as _time

    # --- Cache check (24h TTL) ---
    from smartest_tv import cache as _cache
    cached = _cache.get("_trending", "netflix")
    if cached and isinstance(cached, dict):
        ts = cached.get("ts", 0)
        if _time.time() - ts < 86400:
            return cached.get("items", [])[:limit]

    items: list[dict] = []

    # --- 1st attempt: top10.netflix.com ---
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L", "--compressed", "--max-time", "10",
                "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "-H", "Accept-Language: en-US,en;q=0.9",
                "https://top10.netflix.com/",
            ],
            capture_output=True, text=True, timeout=15,
        )
        html = result.stdout or ""

        # top10.netflix.com uses JSON-LD or inline JSON: {"rank":1,"title":"...","category":"..."}
        # Try to extract from script tag with JSON data
        json_match = re.search(r'"weekly_top10":\s*(\[.*?\])', html, re.DOTALL)
        if json_match:
            import json
            rows = json.loads(json_match.group(1))
            for row in rows:
                items.append({
                    "rank": row.get("rank", len(items) + 1),
                    "title": row.get("show_title", row.get("title", "")),
                    "category": row.get("category", ""),
                })

        # Fallback: look for structured title list in HTML
        if not items:
            # top10.netflix.com renders titles in <td> cells with rank numbers
            # Pattern: rank number followed by show title
            ranks = re.findall(r'<td[^>]*class="[^"]*rank[^"]*"[^>]*>(\d+)</td>', html)
            titles = re.findall(r'<td[^>]*class="[^"]*show-title[^"]*"[^>]*>\s*([^<]+)\s*</td>', html)
            categories = re.findall(r'<td[^>]*class="[^"]*category[^"]*"[^>]*>\s*([^<]+)\s*</td>', html)
            for i, title in enumerate(titles):
                rank = int(ranks[i]) if i < len(ranks) else i + 1
                cat = categories[i].strip() if i < len(categories) else ""
                items.append({"rank": rank, "title": title.strip(), "category": cat})
    except (subprocess.TimeoutExpired, OSError, ValueError, KeyError, IndexError):
        pass

    # --- 2nd attempt: Brave Search fallback ---
    if not items:
        try:
            from urllib.parse import quote
            query = "Netflix top 10 this week TV shows movies"
            result = subprocess.run(
                [
                    "curl", "-s", "-L", "--compressed", "--max-time", "10",
                    "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    f"https://search.brave.com/search?q={quote(query)}",
                ],
                capture_output=True, text=True, timeout=15,
            )
            html = result.stdout or ""
            # Extract numbered list items from search snippets
            found = re.findall(r'(\d+)\.\s+([A-Z][^\n<]{3,60}?)(?:\s*[-–—]\s*(TV|Film|Series|Movie))?', html)
            seen: set[str] = set()
            for rank_str, title, cat in found:
                title = title.strip()
                if title and title not in seen and len(title) > 2:
                    seen.add(title)
                    items.append({"rank": int(rank_str), "title": title, "category": cat or ""})
                    if len(items) >= limit:
                        break
        except (subprocess.TimeoutExpired, OSError, ValueError, KeyError, IndexError):
            pass

    # Cache results
    if items:
        from smartest_tv import cache as _cache
        _cache.put("_trending", "netflix", {"ts": _time.time(), "items": items})

    return items[:limit]


def fetch_youtube_trending(limit: int = 10) -> list[dict]:
    """Fetch YouTube trending videos via yt-dlp or RSS feed.

    Returns: [{"rank": 1, "title": "...", "channel": "...", "video_id": "..."}, ...]
    """
    import time as _time

    # --- Cache check (1h TTL) ---
    from smartest_tv import cache as _cache
    cached = _cache.get("_trending", "youtube")
    if cached and isinstance(cached, dict):
        ts = cached.get("ts", 0)
        if _time.time() - ts < 3600:
            return cached.get("items", [])[:limit]

    items: list[dict] = []

    # --- 1st attempt: yt-dlp flat-playlist ---
    if shutil.which("yt-dlp"):
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--flat-playlist",
                    "--dump-single-json",
                    "--no-warnings",
                    "--playlist-items", f"1-{limit}",
                    "https://www.youtube.com/feed/trending",
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout.strip():
                import json
                data = json.loads(result.stdout.strip())
                entries = data.get("entries", [])
                for i, entry in enumerate(entries, 1):
                    items.append({
                        "rank": i,
                        "title": entry.get("title", ""),
                        "channel": entry.get("uploader") or entry.get("channel", ""),
                        "video_id": entry.get("id", ""),
                        "view_count": entry.get("view_count"),
                    })
        except (subprocess.TimeoutExpired, OSError, ValueError, KeyError, IndexError):
            pass

    # --- 2nd attempt: YouTube RSS trending feed ---
    if not items:
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-L", "--compressed", "--max-time", "10",
                    "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "https://www.youtube.com/feeds/videos.xml?chart=trending",
                ],
                capture_output=True, text=True, timeout=15,
            )
            xml = result.stdout or ""
            titles = re.findall(r"<title>([^<]+)</title>", xml)
            video_ids = re.findall(r"<yt:videoId>([^<]+)</yt:videoId>", xml)
            channels = re.findall(r"<name>([^<]+)</name>", xml)
            # Skip first title (feed title) and first channel (feed author)
            titles = titles[1:]
            channels = channels[1:]
            for i, (title, vid) in enumerate(zip(titles, video_ids), 1):
                channel = channels[i - 1] if i - 1 < len(channels) else ""
                items.append({
                    "rank": i,
                    "title": title.strip(),
                    "channel": channel.strip(),
                    "video_id": vid.strip(),
                    "view_count": None,
                })
                if len(items) >= limit:
                    break
        except (subprocess.TimeoutExpired, OSError, ValueError, KeyError, IndexError):
            pass

    # Cache results
    if items:
        from smartest_tv import cache as _cache
        _cache.put("_trending", "youtube", {"ts": _time.time(), "items": items})

    return items[:limit]


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

_MOOD_CATEGORIES = {
    "chill": {"netflix": ["documentary", "reality", "comedy"], "youtube": ["music", "relaxing", "lo-fi"]},
    "action": {"netflix": ["thriller", "action", "crime"], "youtube": ["action", "sports", "highlights"]},
    "kids": {"netflix": ["animation", "family", "kids"], "youtube": ["animation", "kids", "cartoons"]},
    "random": {"netflix": [], "youtube": []},
}


def get_recommendations(mood: str | None = None, limit: int = 5) -> list[dict]:
    """Get content recommendations based on history + trending.

    Rules:
    - Uses history to determine top platform (falls back to Netflix)
    - Filters trending by mood keywords when mood is given
    - Prefers content not already in recent history
    - Falls back to trending-only if history is empty

    LLM enhancement:
    - If STV_LLM_URL env var is set, calls an Ollama/OpenAI-compatible API
      for natural language recommendation reasons.
    """
    import os
    import time as _time
    from smartest_tv import cache as _cache

    history_data = _cache.analyze_history()
    top_platform = history_data["top_platform"] or "netflix"
    recent_shows = set(history_data["recent_shows"])

    trending_nf = fetch_netflix_trending(20)
    trending_yt = fetch_youtube_trending(20)

    # Build candidate pool
    candidates: list[dict] = []

    def _score_netflix(item: dict) -> int:
        title = item.get("title", "").lower()
        cat = item.get("category", "").lower()
        already_watched = any(s.lower() in title or title in s.lower() for s in recent_shows)
        score = 0
        if not already_watched:
            score += 2
        if mood and mood != "random":
            keywords = _MOOD_CATEGORIES.get(mood, {}).get("netflix", [])
            if any(kw in title or kw in cat for kw in keywords):
                score += 3
        if top_platform == "netflix":
            score += 1
        return score

    def _score_youtube(item: dict) -> int:
        title = item.get("title", "").lower()
        channel = item.get("channel", "").lower()
        already_watched = any(s.lower() in title or title in s.lower() for s in recent_shows)
        score = 0
        if not already_watched:
            score += 2
        if mood and mood != "random":
            keywords = _MOOD_CATEGORIES.get(mood, {}).get("youtube", [])
            if any(kw in title or kw in channel for kw in keywords):
                score += 3
        if top_platform == "youtube":
            score += 1
        return score

    scored_nf = sorted(
        [{"item": it, "score": _score_netflix(it), "platform": "netflix"} for it in trending_nf],
        key=lambda x: x["score"], reverse=True,
    )
    scored_yt = sorted(
        [{"item": it, "score": _score_youtube(it), "platform": "youtube"} for it in trending_yt],
        key=lambda x: x["score"], reverse=True,
    )

    # Interleave, top-platform first
    if top_platform == "youtube":
        merged = _interleave(scored_yt, scored_nf, limit)
    else:
        merged = _interleave(scored_nf, scored_yt, limit)

    # Build result dicts with rule-based reasons
    results: list[dict] = []
    for entry in merged[:limit]:
        item = entry["item"]
        platform = entry["platform"]
        title = item.get("title", "")

        already_watched = any(s.lower() in title.lower() or title.lower() in s.lower() for s in recent_shows)
        if already_watched:
            reason = "In your history"
        elif mood and mood != "random":
            reason = f"Matches {mood} mood"
        elif platform == top_platform:
            reason = f"Your most-watched platform"
        else:
            reason = "Trending now"

        if platform == "netflix":
            cat = item.get("category", "")
            if cat:
                reason = f"{cat} — {reason}"

        results.append({"title": title, "platform": platform, "reason": reason})

    # Optional LLM enhancement
    llm_url = os.environ.get("STV_LLM_URL")
    if llm_url and results:
        results = _enhance_with_llm(llm_url, results, history_data["recent_shows"], mood)

    return results


def _interleave(primary: list[dict], secondary: list[dict], limit: int) -> list[dict]:
    """Interleave two scored lists, primary first, alternating."""
    out: list[dict] = []
    pi, si = 0, 0
    primary_turn = True
    while len(out) < limit and (pi < len(primary) or si < len(secondary)):
        if primary_turn and pi < len(primary):
            out.append(primary[pi])
            pi += 1
        elif not primary_turn and si < len(secondary):
            out.append(secondary[si])
            si += 1
        elif pi < len(primary):
            out.append(primary[pi])
            pi += 1
        elif si < len(secondary):
            out.append(secondary[si])
            si += 1
        primary_turn = not primary_turn
    return out


def _enhance_with_llm(llm_url: str, results: list[dict], recent_shows: list[str], mood: str | None) -> list[dict]:
    """Optionally enhance recommendation reasons via LLM (Ollama-compatible API).

    If the LLM call fails for any reason, returns results unchanged.
    """
    import json as _json

    titles_str = ", ".join(r["title"] for r in results)
    history_str = ", ".join(recent_shows[:5]) if recent_shows else "nothing yet"
    mood_str = mood or "no specific mood"

    prompt = (
        f"User recently watched: {history_str}. "
        f"Mood: {mood_str}. "
        f"Give a short (5-10 word) personalized reason for each of these titles: {titles_str}. "
        f"Respond as a JSON array of strings in the same order, e.g. [\"reason1\", \"reason2\"]."
    )

    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10",
             "-H", "Content-Type: application/json",
             "-d", _json.dumps({"model": "qwen3.5:9b", "prompt": prompt, "stream": False}),
             llm_url],
            capture_output=True, text=True, timeout=15,
        )
        if result.stdout:
            data = _json.loads(result.stdout)
            response_text = data.get("response", "")
            # Extract JSON array from response
            m = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if m:
                reasons = _json.loads(m.group(0))
                if isinstance(reasons, list) and len(reasons) == len(results):
                    for i, reason in enumerate(reasons):
                        if isinstance(reason, str) and reason.strip():
                            results[i]["reason"] = reason.strip()
    except Exception:
        pass  # LLM enhancement is best-effort

    return results


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
