"""Remote TV driver — control a friend's TV through their stv API.

Usage:
    # Friend runs:  stv serve --host 0.0.0.0
    # You add:      stv multi add friend --platform remote --url http://friend-ip:8911

Then the friend's TV appears in your config like any other TV.
Groups, --all, and party mode work seamlessly across local and remote TVs.
"""

from __future__ import annotations

import asyncio
import json
import threading

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus
from smartest_tv.http import curl, curl_json


class RemoteDriver(TVDriver):
    """Control a TV through a remote stv instance's REST API."""

    platform = "remote"

    def __init__(self, url: str, api_key: str | None = None):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self._info: dict | None = None

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _post(self, path: str, data: dict | None = None) -> dict:
        h = self._headers()
        h["Content-Type"] = "application/json"
        r = curl(
            f"{self.url}{path}",
            method="POST",
            data=json.dumps(data) if data else None,
            headers=h,
        )
        if r.body:
            try:
                return json.loads(r.body)
            except json.JSONDecodeError:
                return {}
        return {}

    def _get(self, path: str) -> dict:
        r = curl(f"{self.url}{path}", headers=self._headers())
        if r.body:
            try:
                return json.loads(r.body)
            except json.JSONDecodeError:
                return {}
        return {}

    async def _run_sync(self, fn, *args):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _target():
            try:
                result = fn(*args)
            except Exception as exc:
                loop.call_soon_threadsafe(future.set_exception, exc)
            else:
                loop.call_soon_threadsafe(future.set_result, result)

        threading.Thread(target=_target, daemon=True).start()
        return await future

    async def _apost(self, path: str, data: dict | None = None) -> dict:
        return await self._run_sync(self._post, path, data)

    async def _aget(self, path: str) -> dict:
        return await self._run_sync(self._get, path)

    # -- Connection -----------------------------------------------------------

    async def connect(self) -> None:
        result = await self._aget("/api/ping")
        if result.get("status") != "ok":
            raise ConnectionError(
                f"Remote stv at {self.url} not responding. "
                f"Is your friend running 'stv serve'?"
            )
        self._info = result

    async def disconnect(self) -> None:
        pass

    # -- Power ----------------------------------------------------------------

    async def power_on(self) -> None:
        await self._apost("/api/power", {"action": "on"})

    async def power_off(self) -> None:
        await self._apost("/api/power", {"action": "off"})

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        r = await self._aget("/api/volume")
        return r.get("volume", 0)

    async def set_volume(self, level: int) -> None:
        await self._apost("/api/volume", {"level": level})

    async def volume_up(self) -> None:
        await self._apost("/api/volume", {"action": "up"})

    async def volume_down(self) -> None:
        await self._apost("/api/volume", {"action": "down"})

    async def set_mute(self, mute: bool) -> None:
        await self._apost("/api/mute", {"mute": mute})

    async def get_muted(self) -> bool:
        r = await self._aget("/api/volume")
        return r.get("muted", False)

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        await self._apost("/api/launch", {"app": app_id})

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        await self._apost("/api/launch", {"app": app_id, "content_id": content_id})

    async def close_app(self, app_id: str) -> None:
        await self._apost("/api/close", {"app": app_id})

    async def list_apps(self) -> list[App]:
        r = await self._aget("/api/apps")
        return [App(id=a["id"], name=a["name"]) for a in r.get("apps", [])]

    # -- Media Playback -------------------------------------------------------

    async def play(self) -> None:
        await self._apost("/api/media", {"action": "play"})

    async def pause(self) -> None:
        await self._apost("/api/media", {"action": "pause"})

    async def stop(self) -> None:
        await self._apost("/api/media", {"action": "stop"})

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        r = await self._aget("/api/status")
        return TVStatus(
            current_app=r.get("current_app"),
            volume=r.get("volume"),
            muted=r.get("muted"),
            sound_output=r.get("sound_output"),
        )

    async def info(self) -> TVInfo:
        r = await self._aget("/api/info")
        return TVInfo(
            platform=r.get("platform", "remote"),
            model=r.get("model", ""),
            firmware=r.get("firmware", ""),
            ip=self.url,
            name=r.get("name", f"Remote ({self.url})"),
        )

    # -- Notifications --------------------------------------------------------

    async def notify(self, message: str) -> None:
        await self._apost("/api/notify", {"message": message})

    # -- Screen ---------------------------------------------------------------

    async def screen_off(self) -> None:
        await self._apost("/api/screen", {"action": "off"})

    async def screen_on(self) -> None:
        await self._apost("/api/screen", {"action": "on"})
