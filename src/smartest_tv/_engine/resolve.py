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
from smartest_tv.http import curl, ytdlp, curl_json


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
        r = curl(search_url)
        if r.body:
            matches = re.findall(pattern, r.body)
            if matches:
                return cast(matches[0]) if cast else matches[0]
    return None


def _scrape_netflix_all_seasons(title_id: int) -> list[list[int]]:
    """Scrape ALL season episode IDs from Netflix title page via curl.

    Netflix embeds videoIds for all seasons in the initial HTML (in <script>
    tags). No Playwright needed.

    Returns a list of lists: seasons[0] = [S1E1_id, S1E2_id, ...], etc.
    Sorted by first episode ID (earlier seasons have lower IDs).
    """
    url = f"https://www.netflix.com/title/{title_id}"
    r = curl(url, headers={"Accept-Language": "en-US,en;q=0.9"})
    html = r.body
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

    r = ytdlp([f"ytsearch1:{query}", "--get-id", "--no-download"])
    if r.error and "not found" in r.error:
        raise ValueError(r.error)
    video_id = r.body.split("\n")[0].strip() if r.body else ""
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
        r = curl(search_url)
        if r.body:
            matches = re.findall(
                r"open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)",
                r.body,
            )
            if matches:
                # Prefer track > album > playlist
                priority = {"track": 0, "album": 1, "playlist": 2}
                matches.sort(key=lambda m: priority.get(m[0], 99))
                return f"spotify:{matches[0][0]}:{matches[0][1]}"
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
        r = curl("https://top10.netflix.com/", headers={"Accept-Language": "en-US,en;q=0.9"})
        html = r.body

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

        if not items:
            ranks = re.findall(r'<td[^>]*class="[^"]*rank[^"]*"[^>]*>(\d+)</td>', html)
            titles = re.findall(r'<td[^>]*class="[^"]*show-title[^"]*"[^>]*>\s*([^<]+)\s*</td>', html)
            categories = re.findall(r'<td[^>]*class="[^"]*category[^"]*"[^>]*>\s*([^<]+)\s*</td>', html)
            for i, title in enumerate(titles):
                rank = int(ranks[i]) if i < len(ranks) else i + 1
                cat = categories[i].strip() if i < len(categories) else ""
                items.append({"rank": rank, "title": title.strip(), "category": cat})
    except (ValueError, KeyError, IndexError):
        pass

    # --- 2nd attempt: Brave Search fallback ---
    if not items:
        try:
            from urllib.parse import quote
            query = "Netflix top 10 this week TV shows movies"
            r = curl(f"https://search.brave.com/search?q={quote(query)}")
            html = r.body
            found = re.findall(r'(\d+)\.\s+([A-Z][^\n<]{3,60}?)(?:\s*[-–—]\s*(TV|Film|Series|Movie))?', html)
            seen: set[str] = set()
            for rank_str, title, cat in found:
                title = title.strip()
                if title and title not in seen and len(title) > 2:
                    seen.add(title)
                    items.append({"rank": int(rank_str), "title": title, "category": cat or ""})
                    if len(items) >= limit:
                        break
        except (ValueError, KeyError, IndexError):
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
            r = ytdlp([
                "--flat-playlist", "--dump-single-json", "--no-warnings",
                "--playlist-items", f"1-{limit}",
                "https://www.youtube.com/feed/trending",
            ])
            if r.body:
                import json
                data = json.loads(r.body)
                entries = data.get("entries", [])
                for i, entry in enumerate(entries, 1):
                    items.append({
                        "rank": i,
                        "title": entry.get("title", ""),
                        "channel": entry.get("uploader") or entry.get("channel", ""),
                        "video_id": entry.get("id", ""),
                        "view_count": entry.get("view_count"),
                    })
        except (ValueError, KeyError, IndexError):
            pass

    # --- 2nd attempt: YouTube RSS trending feed ---
    if not items:
        try:
            r = curl("https://www.youtube.com/feeds/videos.xml?chart=trending")
            xml = r.body
            titles = re.findall(r"<title>([^<]+)</title>", xml)
            video_ids = re.findall(r"<yt:videoId>([^<]+)</yt:videoId>", xml)
            channels = re.findall(r"<name>([^<]+)</name>", xml)
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
        except (ValueError, KeyError, IndexError):
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
        data = curl_json(llm_url, data={"model": "qwen3.5:9b", "prompt": prompt, "stream": False})
        if data:
            response_text = data.get("response", "")
            m = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if m:
                reasons = _json.loads(m.group(0))
                if isinstance(reasons, list) and len(reasons) == len(results):
                    for i, reason in enumerate(reasons):
                        if isinstance(reason, str) and reason.strip():
                            results[i]["reason"] = reason.strip()
    except (ValueError, KeyError, IndexError):
        pass  # LLM enhancement is best-effort

    return results


# ---------------------------------------------------------------------------
# JustWatch GraphQL — universal resolver for Disney+, Max, Prime, Paramount+, etc.
# ---------------------------------------------------------------------------

_JUSTWATCH_URL = "https://apis.justwatch.com/graphql"

# Map stv platform names → JustWatch package names
_JW_PLATFORM_MAP = {
    "disney": "Disney Plus",
    "disneyplus": "Disney Plus",
    "disney+": "Disney Plus",
    "max": "Max",
    "hbo": "Max",
    "hbomax": "Max",
    "prime": "Amazon Prime Video",
    "primevideo": "Amazon Prime Video",
    "amazon": "Amazon Prime Video",
    "paramount": "Paramount Plus",
    "paramount+": "Paramount Plus",
    "paramountplus": "Paramount Plus",
    "peacock": "Peacock",
    "hulu": "Hulu",
    "appletv": "Apple TV Plus",
    "appletv+": "Apple TV Plus",
}


def _justwatch_search(query: str) -> str | None:
    """Search JustWatch for a show/movie and return its URL path.

    Tries Brave first, then DuckDuckGo, then direct JustWatch search API.
    """
    from urllib.parse import quote
    slug = _slugify(query)

    # 1) Try Brave
    for search_url in [
        f"https://search.brave.com/search?q={quote(query)}+site:justwatch.com/us",
        f"https://html.duckduckgo.com/html/?q={quote(query)}+justwatch.com+us",
    ]:
        r = curl(search_url, timeout=5)
        if r.body:
            m = re.search(r'justwatch\.com/us/(tv-show|movie)/([a-z0-9-]+)', r.body)
            if m:
                return f"/us/{m.group(1)}/{m.group(2)}"

    # 2) Try JustWatch's own search API
    import json as _json
    gql = _json.dumps({
        "query": 'query { popularTitles(country: US, first: 5, filter: { searchQuery: "%s" }) { edges { node { content(country: US, language: en) { fullPath title } } } } }' % query.replace('"', '\\"'),
    })
    r = curl(
        _JUSTWATCH_URL,
        method="POST",
        data=gql,
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    if r.body:
        try:
            data = _json.loads(r.body)
            edges = data.get("data", {}).get("popularTitles", {}).get("edges", [])
            if edges:
                path = edges[0].get("node", {}).get("content", {}).get("fullPath")
                if path:
                    return path
        except (ValueError, KeyError, IndexError):
            pass

    return None


def _justwatch_resolve_show(
    jw_path: str,
    target_package: str,
    season: int | None = None,
    episode: int | None = None,
) -> str | None:
    """Query JustWatch GraphQL for episode-level deep links.

    Returns the streaming URL for the target platform, or None.
    """
    import json as _json

    if season and episode:
        # Get season data with episodes
        season_path = f"{jw_path}/season-{season}"
        query = """query {
            urlV2(fullPath: "%s") {
                id node {
                    ... on Season {
                        episodes {
                            content(country: US, language: en) {
                                ... on EpisodeContent { title episodeNumber }
                            }
                            offers(country: US, platform: WEB) {
                                standardWebURL
                                package { clearName }
                            }
                        }
                    }
                }
            }
        }""" % season_path
    else:
        # Show/movie level
        query = """query {
            urlV2(fullPath: "%s") {
                id node {
                    ... on Show {
                        offers(country: US, platform: WEB) {
                            standardWebURL
                            package { clearName }
                        }
                    }
                    ... on Movie {
                        offers(country: US, platform: WEB) {
                            standardWebURL
                            package { clearName }
                        }
                    }
                }
            }
        }""" % jw_path

    r = curl(
        _JUSTWATCH_URL,
        method="POST",
        data=_json.dumps({"query": query}),
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    if not r.body:
        return None

    try:
        data = _json.loads(r.body)
    except (ValueError, KeyError):
        return None

    node = data.get("data", {}).get("urlV2", {}).get("node", {})

    if season and episode:
        # Find the specific episode
        episodes = node.get("episodes", [])
        for ep in episodes:
            ep_num = ep.get("content", {}).get("episodeNumber")
            if ep_num == episode:
                for offer in ep.get("offers", []):
                    if offer.get("package", {}).get("clearName", "") == target_package:
                        return offer.get("standardWebURL")
                # If target not found, return first available
                if ep.get("offers"):
                    return ep["offers"][0].get("standardWebURL")
        return None
    else:
        # Show/movie level
        for offer in node.get("offers", []):
            if offer.get("package", {}).get("clearName", "") == target_package:
                return offer.get("standardWebURL")
        if node.get("offers"):
            return node["offers"][0].get("standardWebURL")
        return None


def resolve_justwatch(
    platform: str,
    query: str,
    season: int | None = None,
    episode: int | None = None,
) -> str:
    """Resolve content via JustWatch GraphQL API.

    Works for Disney+, Max (HBO), Prime Video, Paramount+, Peacock, Hulu.
    Returns a streaming deep link URL.
    """
    slug = _slugify(query)
    cache_key = f"{slug}:s{season}e{episode}" if season and episode else slug
    cached = cache.get(platform, cache_key)
    if cached:
        return cached

    target_package = _JW_PLATFORM_MAP.get(platform.lower().strip(), "")
    if not target_package:
        raise ValueError(f"Unknown platform for JustWatch: {platform}")

    # Step 1: Find the show on JustWatch
    jw_path = _justwatch_search(query)
    if not jw_path:
        raise ValueError(
            f"Could not find '{query}' on JustWatch. Try:\n"
            f"  stv search {platform} \"{query}\""
        )

    # Step 2: Get the deep link
    url = _justwatch_resolve_show(jw_path, target_package, season, episode)
    if not url:
        raise ValueError(
            f"Found '{query}' on JustWatch but no {target_package} link"
            + (f" for S{season}E{episode}" if season else "")
            + ". It may not be available on this platform."
        )

    # Clean affiliate tracking from URL
    if "?" in url:
        # Extract the actual streaming URL from JustWatch affiliate redirect
        m = re.search(r'[?&]u=(https?%3A%2F%2F[^&]+)', url)
        if m:
            from urllib.parse import unquote
            url = unquote(m.group(1))

    cache.put(platform, cache_key, url)
    return url


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
    """Resolve content to a platform-specific ID or deep link URL.

    Platform-specific resolvers (Netflix, YouTube, Spotify) are tried first.
    For all other platforms, JustWatch GraphQL is used as a universal fallback.
    """
    p = platform.lower().strip()

    # Platform-specific resolvers (fastest, most precise)
    if p == "netflix":
        return resolve_netflix(query, season, episode, title_id)
    elif p == "youtube":
        return resolve_youtube(query)
    elif p == "spotify":
        return resolve_spotify(query)

    # JustWatch universal resolver (Disney+, Max, Prime, Paramount+, etc.)
    if p in _JW_PLATFORM_MAP:
        return resolve_justwatch(p, query, season, episode)

    raise ValueError(
        f"Unsupported platform: {platform}. Supported: "
        "netflix, youtube, spotify, disney, max, prime, paramount, peacock, hulu, appletv"
    )


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
