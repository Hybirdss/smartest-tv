"""LG webOS TV driver via aiowebostv (WebSocket SSAP protocol).

Migrated from bscpylgtv to aiowebostv (Home Assistant's official library)
to support webOS 24/25 which added new permission requirements that
bscpylgtv hasn't caught up with.
"""

from __future__ import annotations

import json
import os
import re
import socket
from pathlib import Path

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

try:
    from aiowebostv import WebOsClient
    from aiowebostv import endpoints as ep
except ImportError:
    raise ImportError("Install LG driver: pip install 'smartest-tv[lg]'")


# App aliases → (webOS app ID, display name)
LG_APPS: dict[str, tuple[str, str]] = {
    "netflix": ("netflix", "Netflix"),
    "youtube": ("youtube.leanback.v4", "YouTube"),
    "disney": ("com.disney.disneyplus-prod", "Disney+"),
    "spotify": ("spotify-beehive", "Spotify"),
    "prime": ("amazon", "Prime Video"),
    "appletv": ("com.apple.appletv", "Apple TV+"),
    "hulu": ("hulu", "Hulu"),
    "tving": ("cj.eandm", "TVING"),
    "wavve": ("pooq", "wavve"),
    "coupang": ("coupangplay", "Coupang Play"),
    "browser": ("com.webos.app.browser", "Browser"),
    "hdmi1": ("com.webos.app.hdmi1", "HDMI 1"),
    "hdmi2": ("com.webos.app.hdmi2", "HDMI 2"),
}


class LGDriver(TVDriver):
    """LG webOS TV driver."""

    platform = "lg"

    def __init__(self, ip: str, mac: str = "", key_file: str = ""):
        self.ip = ip
        self.mac = mac
        # aiowebostv stores raw client_key string — use .json
        self.key_file = key_file or os.path.expanduser(
            "~/.config/smartest-tv/lg_key.json"
        )
        self._client: WebOsClient | None = None

    def _load_client_key(self) -> str | None:
        """Load persisted client_key from JSON file.

        Handles migration from bscpylgtv (.db binary format) — if only
        the legacy file exists, remove it so aiowebostv can re-pair.
        The user will see a one-time TV prompt after upgrading.
        """
        p = Path(self.key_file)
        if p.exists():
            try:
                return json.loads(p.read_text()).get("client_key")
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                return None

        # Migrate: legacy bscpylgtv .db file exists but our .json doesn't
        # → wipe the legacy binary (can't read it) and force fresh pairing
        legacy = p.parent / "lg_key.db"
        if legacy.exists():
            try:
                backup = p.parent / "lg_key.db.bscpylgtv.bak"
                legacy.rename(backup)
            except OSError:
                try:
                    legacy.unlink()
                except OSError:
                    pass
        return None

    def _save_client_key(self, client_key: str) -> None:
        p = Path(self.key_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"client_key": client_key}))

    async def connect(self) -> None:
        if self._client is not None and self._client.is_connected():
            return

        client_key = self._load_client_key()
        self._client = WebOsClient(self.ip, client_key=client_key)
        await self._client.connect()

        # Persist the key if it was freshly obtained via pairing
        if self._client.client_key and self._client.client_key != client_key:
            self._save_client_key(self._client.client_key)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def _ensure(self) -> WebOsClient:
        if self._client is None or not self._client.is_connected():
            await self.connect()
        return self._client  # type: ignore

    # -- Power ----------------------------------------------------------------

    async def power_on(self) -> None:
        if not self.mac:
            raise ValueError("MAC address required for Wake-on-LAN")
        mac_bytes = bytes.fromhex(self.mac.replace(":", "").replace("-", ""))
        magic = b"\xff" * 6 + mac_bytes * 16
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic, ("255.255.255.255", 9))
        sock.close()

    async def power_off(self) -> None:
        c = await self._ensure()
        await c.power_off()

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        c = await self._ensure()
        status = await c.get_audio_status()
        return status.get("volume", 0)

    async def set_volume(self, level: int) -> None:
        c = await self._ensure()
        await c.set_volume(max(0, min(100, level)))

    async def volume_up(self) -> None:
        c = await self._ensure()
        await c.volume_up()

    async def volume_down(self) -> None:
        c = await self._ensure()
        await c.volume_down()

    async def set_mute(self, mute: bool) -> None:
        c = await self._ensure()
        await c.set_mute(mute)

    async def get_muted(self) -> bool:
        c = await self._ensure()
        status = await c.get_audio_status()
        return status.get("mute", False)

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        c = await self._ensure()
        await c.launch_app(app_id)

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        c = await self._ensure()

        # YouTube uses params+contentTarget
        if app_id == "youtube.leanback.v4":
            video_id = content_id
            if "youtube.com" in content_id or "youtu.be" in content_id:
                match = re.search(
                    r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", content_id
                )
                if match:
                    video_id = match.group(1)
            await c.launch_app_with_params(
                app_id,
                {"contentTarget": f"https://www.youtube.com/tv?v={video_id}"},
            )
            return

        # Netflix needs DIAL format
        if app_id == "netflix":
            if not content_id.startswith("m="):
                numeric_id = content_id
                if "netflix.com" in content_id:
                    match = re.search(r"/(?:watch|title)/(\d+)", content_id)
                    if match:
                        numeric_id = match.group(1)
                content_id = (
                    f"m=https://www.netflix.com/watch/{numeric_id}&source_type=4"
                )
            await c.launch_app_with_content_id(app_id, content_id)
            return

        # Everything else: contentId as-is
        await c.launch_app_with_content_id(app_id, content_id)

    async def close_app(self, app_id: str) -> None:
        c = await self._ensure()
        try:
            await c.close_app(app_id)
        except Exception:
            # webOS firmware may return 403 for LAUNCHER_CLOSE on some models.
            # Fall back to launching the home screen to "close" the app.
            await c.request(ep.LAUNCH, {"id": "com.webos.app.home"})

    async def list_apps(self) -> list[App]:
        c = await self._ensure()
        apps = await c.get_apps_all()
        return [App(id=a["id"], name=a.get("title", a["id"])) for a in apps]

    # -- Media ----------------------------------------------------------------

    async def play(self) -> None:
        c = await self._ensure()
        await c.play()

    async def pause(self) -> None:
        c = await self._ensure()
        await c.pause()

    async def stop(self) -> None:
        c = await self._ensure()
        await c.stop()

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        c = await self._ensure()
        audio = await c.get_audio_status()
        title: str | None = None
        play_state: str | None = None
        try:
            media_info = await c.get_media_foreground_app()
            if media_info:
                title = media_info.get("mediaId") or None
                play_state = media_info.get("playState") or None
        except Exception:
            pass
        return TVStatus(
            current_app=await c.get_current_app(),
            volume=audio.get("volume", 0),
            muted=audio.get("mute", False),
            sound_output=await c.get_sound_output(),
            title=title,
            play_state=play_state,
        )

    async def info(self) -> TVInfo:
        c = await self._ensure()
        si = await c.get_system_info()
        return TVInfo(
            platform="lg",
            model=si.get("modelName", ""),
            firmware=si.get("firmwareVersion", ""),
            ip=self.ip,
            mac=self.mac,
            name=si.get("receiverType", "LG TV"),
        )

    # -- Input ----------------------------------------------------------------

    async def set_input(self, source: str) -> None:
        c = await self._ensure()
        await c.set_input(source)

    async def list_inputs(self) -> list[dict]:
        c = await self._ensure()
        inputs = await c.get_inputs()
        return [
            {"id": i.get("id"), "label": i.get("label"), "connected": i.get("connected")}
            for i in inputs
        ]

    # -- Channels -------------------------------------------------------------

    async def channel_up(self) -> None:
        c = await self._ensure()
        await c.channel_up()

    async def channel_down(self) -> None:
        c = await self._ensure()
        await c.channel_down()

    # -- Notifications --------------------------------------------------------

    async def notify(self, message: str) -> None:
        c = await self._ensure()
        await c.request(ep.SHOW_MESSAGE, {"message": message})

    # -- Screen ---------------------------------------------------------------

    async def screen_off(self) -> None:
        c = await self._ensure()
        await c.request(ep.TURN_OFF_SCREEN)

    async def screen_on(self) -> None:
        c = await self._ensure()
        await c.request(ep.TURN_ON_SCREEN)
