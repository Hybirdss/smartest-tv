"""Samsung Tizen TV driver via samsungtvws (WebSocket + REST).

Samsung has NO read-volume or read-mute API. Those methods raise NotImplementedError.
Volume can only be adjusted via KEY_VOLUP/KEY_VOLDOWN one step at a time.

Deep link format: run_app(app_id, "DEEP_LINK", meta_tag)
  Netflix  : meta_tag = "{numeric_id}"
  YouTube  : meta_tag = "{video_id}"
  Spotify  : meta_tag = "spotify:{type}:{id}"
"""

from __future__ import annotations

import os
import socket
from typing import Any

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

try:
    from samsungtvws.async_remote import SamsungTVWSAsyncRemote
    from samsungtvws.async_rest import SamsungTVAsyncRest
    import aiohttp
except ImportError:
    raise ImportError("Install Samsung driver: pip install 'smartest-tv[samsung]'")


class SamsungDriver(TVDriver):
    """Samsung Tizen TV driver."""

    platform = "samsung"

    def __init__(self, ip: str, mac: str = "", port: int = 8002, token_file: str = ""):
        self.ip = ip
        self.mac = mac
        self.port = port
        self.token_file = token_file or os.path.expanduser(
            f"~/.config/smartest-tv/samsung_{ip}.token"
        )
        self._remote: SamsungTVWSAsyncRemote | None = None
        self._session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        self._remote = SamsungTVWSAsyncRemote(
            host=self.ip,
            port=self.port,
            token_file=self.token_file,
            timeout=10.0,
            name="SmartestTV",
        )
        await self._remote.open()

    async def disconnect(self) -> None:
        if self._remote:
            await self._remote.close()
            self._remote = None
        if self._session:
            await self._session.close()
            self._session = None

    async def _ensure(self) -> SamsungTVWSAsyncRemote:
        if self._remote is None:
            await self.connect()
        return self._remote  # type: ignore

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
        r = await self._ensure()
        await r.send_key("KEY_POWER")

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        raise NotImplementedError("Samsung has no read-volume API")

    async def set_volume(self, level: int) -> None:
        # Naive: bottom-out then count up
        r = await self._ensure()
        for _ in range(50):
            await r.send_key("KEY_VOLDOWN", key_press_delay=0.05)
        for _ in range(max(0, min(100, level))):
            await r.send_key("KEY_VOLUP", key_press_delay=0.05)

    async def volume_up(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_VOLUP")

    async def volume_down(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_VOLDOWN")

    async def set_mute(self, mute: bool) -> None:
        r = await self._ensure()
        await r.send_key("KEY_MUTE")  # Toggle only

    async def get_muted(self) -> bool:
        raise NotImplementedError("Samsung has no read-mute API")

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        r = await self._ensure()
        await r.run_app(app_id, app_type="NATIVE_LAUNCH", meta_tag="")

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        r = await self._ensure()
        await r.run_app(app_id, app_type="DEEP_LINK", meta_tag=content_id)

    async def close_app(self, app_id: str) -> None:
        if not self._session:
            self._session = aiohttp.ClientSession()
        rest = SamsungTVAsyncRest(
            host=self.ip, session=self._session, port=self.port, timeout=10.0
        )
        await rest.rest_app_close(app_id)

    async def list_apps(self) -> list[App]:
        r = await self._ensure()
        raw = await r.app_list()
        if not raw:
            return []
        return [App(id=a.get("appId", ""), name=a.get("name", "")) for a in raw]

    # -- Media ----------------------------------------------------------------

    async def play(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_PLAY")

    async def pause(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_PAUSE")

    async def stop(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_STOP")

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        return TVStatus(powered=True, current_app=None, volume=None, muted=None)

    async def info(self) -> TVInfo:
        if not self._session:
            self._session = aiohttp.ClientSession()
        rest = SamsungTVAsyncRest(
            host=self.ip, session=self._session, port=self.port, timeout=10.0
        )
        data: dict[str, Any] = await rest.rest_device_info()
        device = data.get("device", {})
        return TVInfo(
            platform="samsung",
            model=device.get("modelName", ""),
            firmware=device.get("firmwareVersion", ""),
            ip=self.ip,
            mac=device.get("wifiMac", self.mac),
            name=device.get("name", "Samsung TV"),
        )

    # -- Channels -------------------------------------------------------------

    async def channel_up(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_CHUP")

    async def channel_down(self) -> None:
        r = await self._ensure()
        await r.send_key("KEY_CHDOWN")
