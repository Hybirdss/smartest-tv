"""Android TV / Google TV / Fire TV driver via Android TV Remote Protocol v2.

Uses the same protocol as the Google TV mobile app — no ADB, no developer
mode, no 'Build number 7 taps'. Works out of the box on any Android TV
since the Android TV Remote Service is pre-installed.

Migrated from adb-shell which required Developer Options → ADB debugging.
"""

from __future__ import annotations

import os
from pathlib import Path

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

try:
    from androidtvremote2 import AndroidTVRemote, CannotConnect, InvalidAuth
except ImportError:
    raise ImportError("Install Android driver: pip install 'smartest-tv[android]'")


# Android TV key codes (KEYCODE_* from KeyEvent)
# Using numeric values for consistency with androidtvremote2
KEY_POWER = 26
KEY_WAKEUP = 224
KEY_SLEEP = 223
KEY_VOLUME_UP = 24
KEY_VOLUME_DOWN = 25
KEY_VOLUME_MUTE = 164
KEY_MEDIA_PLAY = 126
KEY_MEDIA_PAUSE = 127
KEY_MEDIA_PLAY_PAUSE = 85
KEY_MEDIA_STOP = 86
KEY_CHANNEL_UP = 166
KEY_CHANNEL_DOWN = 167
KEY_HOME = 3
KEY_BACK = 4


# Deep link templates — Android TV Remote uses URLs, not shell intents
_DEEP_LINKS: dict[str, str] = {
    "com.netflix.ninja": "https://www.netflix.com/title/{id}",
    "com.google.android.youtube.tv": "https://www.youtube.com/watch?v={id}",
    "com.google.android.youtube": "https://www.youtube.com/watch?v={id}",
    "com.spotify.tv.android": "spotify:{id}",
    "com.spotify.music": "spotify:{id}",
    "com.disney.disneyplus": "https://www.disneyplus.com/video/{id}",
    "com.amazon.amazonvideo.livingroom": "https://www.primevideo.com/detail/{id}",
    "com.apple.atve.androidtv.appletv": "https://tv.apple.com/us/show/{id}",
    "com.hulu.livingroomplus": "https://www.hulu.com/watch/{id}",
}


class AndroidDriver(TVDriver):
    """Android TV / Google TV / Fire TV driver via Remote Protocol v2."""

    platform = "android"

    def __init__(self, ip: str, port: int = 6466, cert_dir: str = ""):
        self.ip = ip
        self.port = port
        self.cert_dir = cert_dir or os.path.expanduser(
            "~/.config/smartest-tv/android-cert"
        )
        self.certfile = str(Path(self.cert_dir) / "cert.pem")
        self.keyfile = str(Path(self.cert_dir) / "key.pem")
        self._remote: AndroidTVRemote | None = None

    async def _build_remote(self) -> AndroidTVRemote:
        Path(self.cert_dir).mkdir(parents=True, exist_ok=True)
        remote = AndroidTVRemote(
            client_name="smartest-tv",
            certfile=self.certfile,
            keyfile=self.keyfile,
            host=self.ip,
            api_port=self.port,
        )
        await remote.async_generate_cert_if_missing()
        return remote

    async def connect(self) -> None:
        if self._remote is not None:
            return
        self._remote = await self._build_remote()
        try:
            await self._remote.async_connect()
        except InvalidAuth:
            self._remote = None
            raise RuntimeError(
                "Not paired with this TV. Run: stv setup"
            )
        except CannotConnect as e:
            self._remote = None
            raise RuntimeError(f"Cannot connect to TV at {self.ip}: {e}")

    async def disconnect(self) -> None:
        if self._remote:
            self._remote.disconnect()
            self._remote = None

    async def _ensure(self) -> AndroidTVRemote:
        if self._remote is None:
            await self.connect()
        return self._remote  # type: ignore

    async def _key(self, code: int) -> None:
        r = await self._ensure()
        r.send_key_command(code)

    # -- Pairing (called from stv setup) --------------------------------------

    async def start_pairing(self) -> AndroidTVRemote:
        """Start pairing: TV displays a 6-digit PIN. Caller must call
        finish_pairing(pin) with the code shown on the TV."""
        remote = await self._build_remote()
        try:
            await remote.async_connect()
            # Already paired
            return remote
        except InvalidAuth:
            pass  # expected on first pair
        await remote.async_start_pairing()
        return remote

    async def finish_pairing(self, remote: AndroidTVRemote, pin: str) -> None:
        """Complete pairing with PIN shown on TV."""
        await remote.async_finish_pairing(pin)
        # Reconnect with new cert
        remote.disconnect()
        await remote.async_connect()
        self._remote = remote

    # -- Power ----------------------------------------------------------------

    async def power_on(self) -> None:
        await self._key(KEY_WAKEUP)

    async def power_off(self) -> None:
        await self._key(KEY_SLEEP)

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        r = await self._ensure()
        info = r.volume_info or {}
        return int(info.get("level", 0))

    async def set_volume(self, level: int) -> None:
        # Android TV Remote can't set absolute volume — step toward target
        r = await self._ensure()
        current = await self.get_volume()
        target = max(0, min(100, level))
        diff = target - current
        if diff == 0:
            return
        code = KEY_VOLUME_UP if diff > 0 else KEY_VOLUME_DOWN
        for _ in range(abs(diff)):
            r.send_key_command(code)

    async def volume_up(self) -> None:
        await self._key(KEY_VOLUME_UP)

    async def volume_down(self) -> None:
        await self._key(KEY_VOLUME_DOWN)

    async def set_mute(self, mute: bool) -> None:
        await self._key(KEY_VOLUME_MUTE)

    async def get_muted(self) -> bool:
        r = await self._ensure()
        info = r.volume_info or {}
        return bool(info.get("muted", False))

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        r = await self._ensure()
        r.send_launch_app_command(app_id)

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        r = await self._ensure()
        content_id = self._normalize_content_id(app_id, content_id)

        if app_id in _DEEP_LINKS:
            url = _DEEP_LINKS[app_id].replace("{id}", content_id)
            r.send_launch_app_command(url)
        else:
            # Fallback: treat content_id as a URL
            if content_id.startswith(("http://", "https://", "spotify:")):
                r.send_launch_app_command(content_id)
            else:
                r.send_launch_app_command(app_id)

    @staticmethod
    def _normalize_content_id(app_id: str, content_id: str) -> str:
        """Strip URLs to bare IDs for known apps."""
        import re

        if "netflix" in app_id and "netflix.com" in content_id:
            m = re.search(r"/(?:watch|title)/(\d+)", content_id)
            if m:
                return m.group(1)
        if "youtube" in app_id and (
            "youtube.com" in content_id or "youtu.be" in content_id
        ):
            m = re.search(
                r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", content_id
            )
            if m:
                return m.group(1)
        if "spotify" in app_id and "open.spotify.com" in content_id:
            m = re.search(
                r"open\.spotify\.com/(track|album|artist|playlist)/([A-Za-z0-9]+)",
                content_id,
            )
            if m:
                return f"spotify:{m.group(1)}:{m.group(2)}"
        return content_id

    async def close_app(self, app_id: str) -> None:
        # Android TV Remote Protocol doesn't support force-stop.
        # Use HOME as a close-equivalent.
        await self._key(KEY_HOME)

    async def list_apps(self) -> list[App]:
        # Android TV Remote Protocol doesn't expose installed app list.
        # Return an empty list — callers should use known app IDs.
        return []

    # -- Media ----------------------------------------------------------------

    async def play(self) -> None:
        await self._key(KEY_MEDIA_PLAY)

    async def pause(self) -> None:
        await self._key(KEY_MEDIA_PAUSE)

    async def stop(self) -> None:
        await self._key(KEY_MEDIA_STOP)

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        r = await self._ensure()
        vol_info = r.volume_info or {}
        return TVStatus(
            current_app=r.current_app,
            volume=int(vol_info.get("level", 0)),
            muted=bool(vol_info.get("muted", False)),
            powered=r.is_on,
        )

    async def info(self) -> TVInfo:
        r = await self._ensure()
        dev = r.device_info or {}
        return TVInfo(
            platform="android",
            model=dev.get("model", ""),
            firmware=dev.get("build_type", ""),
            ip=self.ip,
            name=dev.get("manufacturer", "Android TV"),
        )

    # -- Channels -------------------------------------------------------------

    async def channel_up(self) -> None:
        await self._key(KEY_CHANNEL_UP)

    async def channel_down(self) -> None:
        await self._key(KEY_CHANNEL_DOWN)
