"""URL parsing helpers for direct cast commands."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


def parse_cast_url(url: str) -> tuple[str, str]:
    """Parse a streaming URL into (platform, content_id).

    Supported:
      netflix.com/watch/12345        -> ("netflix", "12345")
      netflix.com/title/12345        -> ("netflix", "title:12345")
      youtube.com/watch?v=ID         -> ("youtube", "ID")
      youtu.be/ID                    -> ("youtube", "ID")
      open.spotify.com/track/ID      -> ("spotify", "spotify:track:ID")
      open.spotify.com/album/ID      -> ("spotify", "spotify:album:ID")
      open.spotify.com/playlist/ID   -> ("spotify", "spotify:playlist:ID")

    Raises ValueError for unrecognised URLs.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    path = parsed.path

    if "netflix.com" in host:
        m = re.match(r"/watch/(\d+)", path)
        if m:
            return "netflix", m.group(1)
        m = re.match(r"/title/(\d+)", path)
        if m:
            return "netflix", f"title:{m.group(1)}"
        raise ValueError(f"Unrecognised Netflix URL: {url}")

    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        if vid:
            return "youtube", vid
        raise ValueError(f"Unrecognised YouTube URL: {url}")

    if host == "youtu.be":
        vid = path.lstrip("/").split("/")[0]
        if vid:
            return "youtube", vid
        raise ValueError(f"Unrecognised youtu.be URL: {url}")

    if "spotify.com" in host:
        m = re.match(r"/(track|album|playlist|artist)/([A-Za-z0-9]+)", path)
        if m:
            return "spotify", f"spotify:{m.group(1)}:{m.group(2)}"
        raise ValueError(f"Unrecognised Spotify URL: {url}")

    raise ValueError(
        f"Unsupported URL: {url}\n"
        "Supported: netflix.com, youtube.com, youtu.be, open.spotify.com"
    )
