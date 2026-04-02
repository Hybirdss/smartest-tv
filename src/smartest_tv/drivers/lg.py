"""LG webOS TV driver via bscpylgtv (WebSocket SSAP protocol)."""

from __future__ import annotations

import os
import re
import socket

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

try:
    from bscpylgtv import WebOsClient
    from bscpylgtv import endpoints as ep
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
        self.key_file = key_file or os.path.expanduser(
            "~/.config/smartest-tv/lg_key.db"
        )
        self._client: WebOsClient | None = None

    async def connect(self) -> None:
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        self._client = await WebOsClient.create(
            self.ip,
            key_file_path=self.key_file,
            ping_interval=None,
            states=[],
        )
        await self._client.connect()

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def _ensure(self) -> WebOsClient:
        if self._client is None:
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
        return await c.get_volume()

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
        return await c.get_muted()

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
        await c.close_app(app_id)

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
        return TVStatus(
            current_app=await c.get_current_app(),
            volume=await c.get_volume(),
            muted=await c.get_muted(),
            sound_output=await c.get_sound_output(),
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
        await c.turn_screen_off()

    async def screen_on(self) -> None:
        c = await self._ensure()
        await c.turn_screen_on()
