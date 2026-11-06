"""Content ID resolver for streaming platforms.

Resolution chain:
  1. Local cache → instant (0ms)
  2. Engine (local, PyPI install) → fast (2-3s)
  3. API fallback (GitHub clone) → fast (1-2s)

The cache is the real product. Once any ID is discovered, it's cached forever.
"""

from __future__ import annotations

import logging
import re

from smartest_tv import cache
from smartest_tv.http import curl_json

log = logging.getLogger("smartest-tv")

# ---------------------------------------------------------------------------
# Check if the engine is available (PyPI install vs GitHub clone)
# ---------------------------------------------------------------------------

def _has_engine() -> bool:
    try:
        from smartest_tv._engine import resolve as _r  # noqa: F401
        return True
    except ImportError:
        return False


_ENGINE = _has_engine()


# ---------------------------------------------------------------------------
# Netflix
# ---------------------------------------------------------------------------

def resolve_netflix(
    query: str,
    season: int | None = None,
    episode: int | None = None,
    title_id: int | None = None,
) -> str:
    """Resolve a Netflix show/movie to an episode or movie ID."""
    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_netflix as _resolve
        return _resolve(query, season, episode, title_id)
    return _api_resolve("netflix", query, season, episode, title_id)


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def resolve_youtube(query: str) -> str:
    """Resolve YouTube search → video ID."""
    slug = _slugify(query)
    cached = cache.get("youtube", slug)
    if cached:
        return cached

    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_youtube as _resolve
        return _resolve(query)
    return _api_resolve("youtube", query)


# ---------------------------------------------------------------------------
# Spotify
# ---------------------------------------------------------------------------

def resolve_spotify(query: str) -> str:
    """Resolve Spotify content to a URI."""
    # Direct URI/URL passthrough (no engine needed)
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

    if _ENGINE:
        from smartest_tv._engine.resolve import resolve_spotify as _resolve
        return _resolve(query)
    return _api_resolve("spotify", query)


# ---------------------------------------------------------------------------
# Apple TV+
# ---------------------------------------------------------------------------

# Apple TV+ server-renders the Episodes shelf of a show page with the first
# six episodes only (the rest of the shelf is pagination placeholders), and
# the shelf carries no season/episode numbers. The web page fills the rest
# in from this route with the parameters it embeds in the page
# (``requiredParamsMap.Default``: utsk, utscf, sf, v; the utsk token is
# short-lived, so it is read at resolve time). Episodes come back ten per
# page, all seasons in order, each with ``seasonNumber`` / ``episodeNumber``.
_APPLETV_EPISODES_URL = "https://tv.apple.com/api/uts/v3/shows/{show_id}/episodes"
_APPLETV_PAGE_SIZE = 10
_APPLETV_MAX_PAGES = 100  # 1000 episodes; the walk stops early once past the wanted season
# What the web client adds on top of the page's own parameter block.
_APPLETV_ROUTE_PARAMS = {
    "includeSeasonSummary": "false",
    "selectedSeasonEpisodesOnly": "false",
}
_APPLETV_HEADERS = {"Referer": "https://tv.apple.com/", "Accept": "application/json"}


def _appletv_page_params(server_data: dict) -> dict | None:
    """The ``requiredParamsMap.Default`` block of a tv.apple.com page, or None."""
    try:
        for entry in server_data["data"]:
            params = entry.get("data", {}).get("uts", {}).get("requiredParamsMap", {}).get("Default")
            if isinstance(params, dict) and params:
                return dict(params)
    except (KeyError, AttributeError, TypeError):
        pass
    return None


def _appletv_shelves(server_data: dict) -> list:
    """The ``shelves`` list of a tv.apple.com show page, wherever it sits in ``data``."""
    try:
        for entry in server_data["data"]:
            shelves = entry.get("data", {}).get("shelves")
            if isinstance(shelves, list):
                return shelves
    except (KeyError, AttributeError, TypeError):
        pass
    return []


def _appletv_episode_from_api(show_id: str, params: dict, season: int, episode: int) -> tuple[str | None, bool]:
    """Walk the show's episode list until (season, episode) turns up.

    Returns ``(episode_id, answered)``: ``answered`` is False when the route
    could not be read at all (transport error, unexpected body), True when
    it listed the show's episodes, whether or not the wanted one was there.
    """
    import json as _json
    from urllib.parse import urlencode

    from smartest_tv.http import curl as _curl

    # The page's block as-is (storefront, locale, token …) plus the route's own
    # switches; the web client sends exactly this combination.
    query = {str(k): str(v) for k, v in params.items()}
    query.update(_APPLETV_ROUTE_PARAMS)

    # Episodes come back season by season; once the route is past the wanted
    # season there is nothing left to find.
    skip = 0
    for _ in range(_APPLETV_MAX_PAGES):
        query["nextToken"] = f"{skip}:{_APPLETV_PAGE_SIZE}"
        page = _curl(_APPLETV_EPISODES_URL.format(show_id=show_id) + "?" + urlencode(query), headers=_APPLETV_HEADERS)
        if not page.ok or not page.body:
            log.debug("appletv episodes page %d for %s failed: %s", skip, show_id, page.error)
            return None, False
        try:
            episodes = _json.loads(page.body)["data"]["episodes"]
        except (_json.JSONDecodeError, KeyError, TypeError):
            episodes = None
        if not isinstance(episodes, list):
            log.debug("appletv episodes page %d for %s unreadable", skip, show_id)
            return None, False
        if not episodes:
            return None, True
        for ep in episodes:
            if not isinstance(ep, dict):
                continue
            ep_id = str(ep.get("id", ""))
            ep_season = ep.get("seasonNumber")
            if ep_season == season and ep.get("episodeNumber") == episode and ep_id.startswith("umc.cmc."):
                return ep_id, True
            if isinstance(ep_season, int) and ep_season > season:
                return None, True
        skip += len(episodes)
    return None, True


def resolve_appletv(
    query: str,
    season: int | None = None,
    episode: int | None = None,
) -> str:
    """Resolve an Apple TV+ show to an episode ID.

    Apple TV+ server-renders show metadata in a ``serialized-server-data``
    script tag: the show's season list and the first six episodes of the
    Episodes shelf.  The rest of the episodes come from the same paging
    route the web page uses, with the parameters embedded in that tag.
    No authentication required.

    Resolution chain:
      1. Local cache (instant)
      2. curl show page → parse serialized-server-data → episode route → episode ID
      3. The six server-rendered episodes, by position (route unavailable)
      4. API fallback
    """
    slug = _slugify(query)
    cache_key = f"{slug}:s{season or 1}e{episode or 1}"
    cached = cache.get("appletv", cache_key)
    if cached:
        return cached

    import json as _json

    from smartest_tv.http import curl as _curl

    # Step 1: search for the show to get its showId
    search_result = _curl(f"https://tv.apple.com/search?term={_url_encode(query)}")
    if not search_result.ok:
        return _api_resolve("appletv", query, season, episode)

    show_ids = re.findall(r'umc\.cmc\.[a-z0-9]+', search_result.body)
    if not show_ids:
        return _api_resolve("appletv", query, season, episode)

    # The first umc.cmc ID on the search page is usually the best match
    show_id = show_ids[0]

    # Step 2: fetch the show page to get episode IDs
    show_result = _curl(f"https://tv.apple.com/show/{slug}/{show_id}")
    if not show_result.ok:
        return _api_resolve("appletv", query, season, episode)

    # Parse serialized-server-data
    m = re.search(
        r'<script[^>]*id="serialized-server-data"[^>]*>(.*?)</script>',
        show_result.body,
        re.DOTALL,
    )
    if not m:
        return _api_resolve("appletv", query, season, episode)

    try:
        server_data = _json.loads(m.group(1))

        # Step 3: the episode route, matched on season/episode number
        want_season = int(season) if season is not None else 1
        want_episode = int(episode) if episode is not None else 1
        params = _appletv_page_params(server_data)
        answered = False
        if params:
            ep_id, answered = _appletv_episode_from_api(show_id, params, want_season, want_episode)
            if ep_id:
                cache.put("appletv", cache_key, ep_id)
                return ep_id

        # Step 4: the server-rendered shelf, by position. Only the first six
        # episodes of the first season are rendered and the shelf carries no
        # season numbers, so this is a last resort for when the route could
        # not be read; when the route listed the show and the episode was
        # not there, the shelf has nothing better to say.
        if answered or want_season != 1:
            return _api_resolve("appletv", query, season, episode)

        episodes: list[dict] = []
        for shelf in _appletv_shelves(server_data):
            for item in shelf.get("items", []):
                item_id = item.get("id", "")
                if item_id.startswith("umc.cmc.") and item.get("title"):
                    episodes.append(item)

        if not episodes:
            return _api_resolve("appletv", query, season, episode)

        target_idx = max(0, want_episode - 1)
        if target_idx < len(episodes):
            ep_id = episodes[target_idx]["id"]
            cache.put("appletv", cache_key, ep_id)
            return ep_id

    except (KeyError, IndexError, AttributeError, TypeError, ValueError):
        pass

    return _api_resolve("appletv", query, season, episode)


def _url_encode(s: str) -> str:
    """Simple URL encoding for query parameters."""
    import urllib.parse
    return urllib.parse.quote_plus(s)


# ---------------------------------------------------------------------------
# Trending
# ---------------------------------------------------------------------------

def fetch_netflix_trending(limit: int = 10) -> list[dict]:
    """Fetch Netflix Top 10."""
    if _ENGINE:
        from smartest_tv._engine.resolve import fetch_netflix_trending as _fn
        return _fn(limit)
    return _api_trending("netflix", limit)


def fetch_youtube_trending(limit: int = 10) -> list[dict]:
    """Fetch YouTube trending."""
    if _ENGINE:
        from smartest_tv._engine.resolve import fetch_youtube_trending as _fn
        return _fn(limit)
    return _api_trending("youtube", limit)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def get_recommendations(mood: str | None = None, limit: int = 5) -> list[dict]:
    """Get content recommendations based on watch history + trending."""
    if _ENGINE:
        from smartest_tv._engine.resolve import get_recommendations as _fn
        return _fn(mood, limit)

    # Fallback: trending-only recommendations
    results: list[dict] = []
    try:
        for item in fetch_netflix_trending(limit):
            results.append({
                "title": item.get("title", ""),
                "platform": "netflix",
                "reason": f"Trending #{item.get('rank', '?')}",
            })
    except Exception:
        pass
    return results[:limit]


# ---------------------------------------------------------------------------
# Unified resolver
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
    elif p in ("appletv", "apple", "apple_tv", "apple-tv", "atv"):
        return resolve_appletv(query, season, episode)
    elif p == "auto":
        # Auto-detect platform via JustWatch
        if _ENGINE:
            from smartest_tv._engine.resolve import resolve_auto
            return resolve_auto(query, season, episode)
        raise ValueError("Auto-detect requires the resolution engine.")
    elif _ENGINE:
        # Try JustWatch-based platforms (disney, max, prime, etc.)
        from smartest_tv._engine.resolve import resolve as _engine_resolve
        return _engine_resolve(p, query, season, episode)
    else:
        raise ValueError(f"Unsupported platform: {platform}.")


# ---------------------------------------------------------------------------
# API fallback (for GitHub clones without _engine)
# ---------------------------------------------------------------------------

def _api_resolve(platform: str, query: str, season: int | None = None,
                 episode: int | None = None, title_id: int | None = None) -> str:
    """Resolve via the hosted API fallback."""
    import json

    from smartest_tv.cache import CACHE_API_URL
    from smartest_tv.http import curl

    body: dict = {"platform": platform, "query": query}
    if season is not None:
        body["season"] = season
    if episode is not None:
        body["episode"] = episode
    if title_id is not None:
        body["title_id"] = title_id

    headers: dict[str, str] = {"Content-Type": "application/json"}
    license_key = _get_license_key()
    if license_key:
        headers["X-License-Key"] = license_key

    r = curl(
        f"{CACHE_API_URL}/resolve",
        method="POST",
        data=json.dumps(body),
        headers=headers,
        timeout=10,
    )

    if r.body:
        try:
            data = json.loads(r.body)
        except (json.JSONDecodeError, ValueError):
            data = {}

        if data.get("content_id"):
            content_id = data["content_id"]
            slug = _slugify(query)
            cache.put(platform, slug, content_id)
            return content_id

        if data.get("error") == "rate_limited":
            raise ValueError(
                f"Daily resolve limit reached ({platform}: {query}). "
                f"Run: stv cache update"
            )

    raise ValueError(
        f"Could not resolve {platform}: {query}. "
        f"Try: stv cache update"
    )


def _api_trending(platform: str, limit: int) -> list[dict]:
    """Fetch trending via the hosted API."""
    from smartest_tv.cache import CACHE_API_URL
    data = curl_json(f"{CACHE_API_URL}/trending/{platform}?limit={limit}", timeout=5)
    if data and isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_license_key_cache: str | None = None


def _get_license_key() -> str:
    """Get the Polar license key from env var or license.key file."""
    global _license_key_cache
    if _license_key_cache is not None:
        return _license_key_cache

    import os
    key = os.environ.get("STV_LICENSE_KEY", "")
    if not key:
        from smartest_tv.config import CONFIG_DIR
        license_file = CONFIG_DIR / "license.key"
        if license_file.exists():
            try:
                key = license_file.read_text().strip()
            except OSError:
                key = ""

    _license_key_cache = key
    return key


def _slugify(text: str) -> str:
    """Normalize text to cache key."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")
