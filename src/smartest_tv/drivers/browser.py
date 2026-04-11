"""Browser driver — opens content in the default web browser.

No TV required. Resolves content IDs to streaming URLs and opens them.
Works as a fallback when no TV is configured, or explicitly via --on browser.
"""

from __future__ import annotations

import webbrowser

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

# Platform → URL template. {content_id} is replaced at launch time.
_DEEP_LINKS: dict[str, str] = {
    "netflix": "https://www.netflix.com/watch/{content_id}",
    "youtube": "https://www.youtube.com/watch?v={content_id}",
    "spotify": "https://open.spotify.com/track/{content_id}",
    "disney": "https://www.disneyplus.com/play/{content_id}",
    "prime": "https://www.amazon.com/dp/{content_id}",
    "max": "https://play.max.com/show/{content_id}",
    "appletv": "https://tv.apple.com/show/{content_id}",
    "crunchyroll": "https://www.crunchyroll.com/watch/{content_id}",
    "paramount": "https://www.paramountplus.com/shows/video/{content_id}",
}


class BrowserDriver(TVDriver):
    """Opens streaming content in the default web browser."""

    platform = "browser"

    def __init__(self) -> None:
        self._last_url: str | None = None

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def power_on(self) -> None:
        pass

    async def power_off(self) -> None:
        pass

    async def get_volume(self) -> int:
        return 0

    async def set_volume(self, level: int) -> None:
        pass

    async def volume_up(self) -> None:
        pass

    async def volume_down(self) -> None:
        pass

    async def set_mute(self, mute: bool) -> None:
        pass

    async def get_muted(self) -> bool:
        return False

    async def launch_app(self, app_id: str) -> None:
        url = _DEEP_LINKS.get(app_id, f"https://{app_id}.com")
        webbrowser.open(url.split("/{content_id}")[0])

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        # app_id here is the platform name (netflix, youtube, etc.)
        # or a raw app ID — try to match against known platforms
        platform_key = app_id.lower()
        # Handle platform-specific app IDs (e.g. "netflix", "youtube.leanback.v4")
        for key in _DEEP_LINKS:
            if key in platform_key:
                platform_key = key
                break

        # Handle spotify: URIs before template matching
        if content_id.startswith("spotify:"):
            parts = content_id.split(":")
            if len(parts) == 3:
                url = f"https://open.spotify.com/{parts[1]}/{parts[2]}"
            else:
                url = f"https://open.spotify.com/search/{content_id}"
            self._last_url = url
            webbrowser.open(url)
            return

        template = _DEEP_LINKS.get(platform_key)
        if template:
            url = template.replace("{content_id}", content_id)
        elif content_id.startswith("http"):
            url = content_id
        else:
            url = f"https://www.google.com/search?q={content_id}"

        self._last_url = url
        webbrowser.open(url)

    async def close_app(self, app_id: str) -> None:
        pass

    async def list_apps(self) -> list[App]:
        return [App(id=k, name=k.title()) for k in _DEEP_LINKS]

    async def play(self) -> None:
        pass

    async def pause(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def status(self) -> TVStatus:
        return TVStatus(current_app="browser", powered=True)

    async def info(self) -> TVInfo:
        return TVInfo(platform="browser", name="Default Browser")
