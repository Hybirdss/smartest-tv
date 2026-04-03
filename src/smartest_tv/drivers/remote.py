"""Remote TV driver — control a friend's TV through their stv API.

Usage:
    # Friend runs:  stv serve --host 0.0.0.0
    # You add:      stv multi add friend --platform remote --url http://friend-ip:8911

Then the friend's TV appears in your config like any other TV.
Groups, --all, and party mode work seamlessly across local and remote TVs.
"""

from __future__ import annotations

import json
import subprocess

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus


class RemoteDriver(TVDriver):
    """Control a TV through a remote stv instance's REST API."""

    platform = "remote"

    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self._info: dict | None = None

    def _post(self, path: str, data: dict | None = None) -> dict:
        args = [
            "curl", "-s", "--max-time", "10",
            "-X", "POST",
            "-H", "Content-Type: application/json",
        ]
        if data:
            args.extend(["-d", json.dumps(data)])
        args.append(f"{self.url}{path}")
        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
        if result.stdout and result.stdout.strip():
            return json.loads(result.stdout)
        return {}

    def _get(self, path: str) -> dict:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", f"{self.url}{path}"],
            capture_output=True, text=True, timeout=15,
        )
        if result.stdout and result.stdout.strip():
            return json.loads(result.stdout)
        return {}

    # -- Connection -----------------------------------------------------------

    async def connect(self) -> None:
        result = self._get("/api/ping")
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
        self._post("/api/power", {"action": "on"})

    async def power_off(self) -> None:
        self._post("/api/power", {"action": "off"})

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        r = self._get("/api/volume")
        return r.get("volume", 0)

    async def set_volume(self, level: int) -> None:
        self._post("/api/volume", {"level": level})

    async def volume_up(self) -> None:
        self._post("/api/volume", {"action": "up"})

    async def volume_down(self) -> None:
        self._post("/api/volume", {"action": "down"})

    async def set_mute(self, mute: bool) -> None:
        self._post("/api/mute", {"mute": mute})

    async def get_muted(self) -> bool:
        r = self._get("/api/volume")
        return r.get("muted", False)

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        self._post("/api/launch", {"app": app_id})

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        self._post("/api/launch", {"app": app_id, "content_id": content_id})

    async def close_app(self, app_id: str) -> None:
        self._post("/api/close", {"app": app_id})

    async def list_apps(self) -> list[App]:
        r = self._get("/api/apps")
        return [App(id=a["id"], name=a["name"]) for a in r.get("apps", [])]

    # -- Media Playback -------------------------------------------------------

    async def play(self) -> None:
        self._post("/api/media", {"action": "play"})

    async def pause(self) -> None:
        self._post("/api/media", {"action": "pause"})

    async def stop(self) -> None:
        self._post("/api/media", {"action": "stop"})

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        r = self._get("/api/status")
        return TVStatus(
            current_app=r.get("current_app"),
            volume=r.get("volume"),
            muted=r.get("muted"),
            sound_output=r.get("sound_output"),
        )

    async def info(self) -> TVInfo:
        r = self._get("/api/info")
        return TVInfo(
            platform=r.get("platform", "remote"),
            model=r.get("model", ""),
            firmware=r.get("firmware", ""),
            ip=self.url,
            name=r.get("name", f"Remote ({self.url})"),
        )

    # -- Notifications --------------------------------------------------------

    async def notify(self, message: str) -> None:
        self._post("/api/notify", {"message": message})

    # -- Screen ---------------------------------------------------------------

    async def screen_off(self) -> None:
        self._post("/api/screen", {"action": "off"})

    async def screen_on(self) -> None:
        self._post("/api/screen", {"action": "on"})
