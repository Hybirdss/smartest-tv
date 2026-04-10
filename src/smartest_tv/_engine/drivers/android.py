"""Android TV / Fire TV driver via ADB TCP.

Deep link intents:
  Netflix  : am start -d 'netflix://title/{id}'
  YouTube  : am start -d 'vnd.youtube:{id}'
  Spotify  : am start -d 'spotify:{type}:{id}'
  Disney+  : am start -d 'disneyplus://content/{id}'

Requires ADB debugging enabled on the TV (Developer Options → ADB debugging).
"""

from __future__ import annotations

import asyncio
import os
import re

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

try:
    from adb_shell.adb_device_async import AdbDeviceTcpAsync
    from adb_shell.auth.keygen import keygen
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
except ImportError:
    raise ImportError("Install Android driver: pip install 'smartest-tv[android]'")


# Deep link intent templates per app package
_DEEP_LINK_INTENTS: dict[str, str] = {
    "com.netflix.ninja": "am start -a android.intent.action.VIEW -d 'netflix://title/{id}'",
    "com.google.android.youtube.tv": "am start -a android.intent.action.VIEW -d 'vnd.youtube:{id}'",
    "com.google.android.youtube": "am start -a android.intent.action.VIEW -d 'vnd.youtube:{id}'",
    "com.spotify.tv.android": "am start -a android.intent.action.VIEW -d '{id}'",
    "com.spotify.music": "am start -a android.intent.action.VIEW -d '{id}'",
    "com.disney.disneyplus": "am start -a android.intent.action.VIEW -d 'https://www.disneyplus.com/video/{id}'",
    "com.amazon.amazonvideo.livingroom": "am start -a android.intent.action.VIEW -n com.amazon.amazonvideo.livingroom/com.amazon.ignition.IgnitionActivity --es 'contentId' '{id}'",
    "com.apple.atve.androidtv.appletv": "am start -a android.intent.action.VIEW -d 'https://tv.apple.com/us/show/{id}'",
    "com.hulu.livingroomplus": "am start -n com.hulu.livingroomplus/.WKWelcomeActivity --es 'deepLink' 'https://www.hulu.com/watch/{id}'",
    "net.cj.cjhv.gs.tving": "am start -a android.intent.action.VIEW -d 'tving://detail/{id}'",
    "com.coupang.play": "am start -a android.intent.action.VIEW -d 'coupangplay://watch/{id}'",
}


class AndroidDriver(TVDriver):
    """Android TV / Fire TV driver via ADB over TCP."""

    platform = "android"

    def __init__(self, ip: str, port: int = 5555, adb_key_path: str = ""):
        self.ip = ip
        self.port = port
        self.adb_key_path = adb_key_path or os.path.expanduser(
            "~/.config/smartest-tv/adbkey"
        )
        self._device: AdbDeviceTcpAsync | None = None

    async def connect(self) -> None:
        os.makedirs(os.path.dirname(self.adb_key_path), exist_ok=True)
        if not os.path.exists(self.adb_key_path):
            keygen(self.adb_key_path)

        signer = PythonRSASigner.FromRSAKeyPath(self.adb_key_path)
        self._device = AdbDeviceTcpAsync(self.ip, self.port, default_transport_timeout_s=9.0)
        await self._device.connect(rsa_keys=[signer], auth_timeout_s=10.0)

    async def disconnect(self) -> None:
        if self._device:
            await self._device.close()
            self._device = None

    async def _shell(self, cmd: str) -> str:
        if self._device is None:
            await self.connect()
        result = await self._device.shell(cmd)  # type: ignore
        return result or ""

    async def _keyevent(self, code: int) -> None:
        await self._shell(f"input keyevent {code}")

    # -- Power ----------------------------------------------------------------

    async def power_on(self) -> None:
        await self._keyevent(224)  # KEYCODE_WAKEUP

    async def power_off(self) -> None:
        await self._keyevent(223)  # KEYCODE_SLEEP

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        output = await self._shell("dumpsys audio | grep -m1 'STREAM_MUSIC'")
        match = re.search(r"index[=:](\d+)", output)
        return int(match.group(1)) if match else 0

    async def set_volume(self, level: int) -> None:
        await self._shell(f"media volume --stream 3 --set {max(0, min(100, level))}")

    async def volume_up(self) -> None:
        await self._keyevent(24)

    async def volume_down(self) -> None:
        await self._keyevent(25)

    async def set_mute(self, mute: bool) -> None:
        await self._keyevent(164)  # KEYCODE_VOLUME_MUTE (toggle)

    async def get_muted(self) -> bool:
        output = await self._shell("dumpsys audio | grep -m1 muted")
        return "true" in output.lower()

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        await self._shell(
            f"monkey -p {app_id} -c android.intent.category.LAUNCHER 1"
        )

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        # Normalize content IDs (strip URLs to bare IDs)
        content_id = self._normalize_content_id(app_id, content_id)

        if app_id in _DEEP_LINK_INTENTS:
            cmd = _DEEP_LINK_INTENTS[app_id].replace("{id}", content_id)
            await self._shell(cmd)
        else:
            await self._shell(
                f"am start -a android.intent.action.VIEW -d '{content_id}'"
            )

    @staticmethod
    def _normalize_content_id(app_id: str, content_id: str) -> str:
        """Strip URLs to bare IDs for known apps."""
        if "netflix" in app_id and "netflix.com" in content_id:
            m = re.search(r"/(?:watch|title)/(\d+)", content_id)
            if m:
                return m.group(1)
        if "youtube" in app_id and ("youtube.com" in content_id or "youtu.be" in content_id):
            m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", content_id)
            if m:
                return m.group(1)
        if "spotify" in app_id and "open.spotify.com" in content_id:
            m = re.search(r"open\.spotify\.com/(track|album|artist|playlist)/([A-Za-z0-9]+)", content_id)
            if m:
                return f"spotify:{m.group(1)}:{m.group(2)}"
        return content_id

    async def close_app(self, app_id: str) -> None:
        await self._shell(f"am force-stop {app_id}")

    async def list_apps(self) -> list[App]:
        output = await self._shell("pm list packages -3")
        apps = []
        for line in output.strip().split("\n"):
            if line.startswith("package:"):
                pkg = line[8:].strip()
                apps.append(App(id=pkg, name=pkg))
        return apps

    # -- Media ----------------------------------------------------------------

    async def play(self) -> None:
        await self._keyevent(126)  # KEYCODE_MEDIA_PLAY

    async def pause(self) -> None:
        await self._keyevent(127)  # KEYCODE_MEDIA_PAUSE

    async def stop(self) -> None:
        await self._keyevent(86)  # KEYCODE_MEDIA_STOP

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        # Run queries in parallel
        app_raw, vol_raw, muted_raw = await asyncio.gather(
            self._shell("dumpsys window windows | grep -m1 mCurrentFocus"),
            self.get_volume(),
            self.get_muted(),
        )
        current_app = None
        match = re.search(r"([a-zA-Z][a-zA-Z0-9_.]+\.[a-zA-Z0-9_.]+)", app_raw)
        if match:
            current_app = match.group(1)

        return TVStatus(
            current_app=current_app,
            volume=vol_raw,
            muted=muted_raw,
            powered=True,
        )

    async def info(self) -> TVInfo:
        model = (await self._shell("getprop ro.product.model")).strip()
        firmware = (await self._shell("getprop ro.build.version.release")).strip()
        name = (await self._shell("getprop ro.product.name")).strip()

        return TVInfo(
            platform="android",
            model=model,
            firmware=firmware,
            ip=self.ip,
            name=name or "Android TV",
        )

    # -- Channels -------------------------------------------------------------

    async def channel_up(self) -> None:
        await self._keyevent(166)  # KEYCODE_CHANNEL_UP

    async def channel_down(self) -> None:
        await self._keyevent(167)  # KEYCODE_CHANNEL_DOWN
