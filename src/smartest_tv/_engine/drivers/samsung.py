"""Samsung Tizen TV driver via samsungtvws (WebSocket + REST).

Samsung has NO read-volume or read-mute API. Those methods raise NotImplementedError.
Volume can only be adjusted via KEY_VOLUP/KEY_VOLDOWN one step at a time.

The async `SamsungTVWSAsyncRemote` exposes only `send_command`/`send_commands` —
not `send_key`/`run_app` (those live on the sync class). We dispatch via the
`SendRemoteKey` and `ChannelEmitCommand` payload builders from
`samsungtvws.remote`.

Deep link ladder (launch_app_deep returns a LaunchResult, see drivers/base):
  1. Netflix / YouTube: DIAL first (issue #8) — parameters are interpreted
     by the app, not the OS, so Tizen metaTag quirks don't apply.
  2. ed.apps.launch DEEP_LINK with meta_tag, then VERIFY via the REST
     app-status endpoint — Tizen 9 firmware has been observed silently
     ignoring the command, and the old code trusted it blindly (issue #20).
  3. If the app provably did not start: REST applications/{id} POST, then
     plain NATIVE_LAUNCH — the paths the TV honors when DEEP_LINK drops.
  Other apps: enter the ladder at rung 2 (most are not DIAL receivers).
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any, Final

from smartest_tv.drivers.base import App, LaunchResult, TVDriver, TVInfo, TVStatus

from .. import dial

try:
    import aiohttp
    from samsungtvws.async_remote import SamsungTVWSAsyncRemote
    from samsungtvws.async_rest import SamsungTVAsyncRest
    from samsungtvws.remote import ChannelEmitCommand, SendRemoteKey
except ImportError as e:
    raise ImportError(
        "Samsung driver requires samsungtvws.\n"
        "  pipx inject stv 'samsungtvws[encrypted]'   (recommended)\n"
        "  pip install 'stv[samsung]'                 (alternative)"
    ) from e

_LOG = logging.getLogger(__name__)


def _status_says_running(status: Any) -> bool | None:
    """Interpret a REST app-status payload.

    True/False when a recognizable running/visible key is present; None
    when the payload carries no verdict either way (older firmwares
    return metadata only) so callers treat it as unknown, not "stopped".
    """
    if not isinstance(status, dict):
        return None
    scopes = [status]
    inner = status.get("app")
    if isinstance(inner, dict):
        scopes.append(inner)
    for scope in scopes:
        for key in ("running", "visible"):
            value = scope.get(key)
            if isinstance(value, str) and value.strip().lower() in ("true", "false"):
                return value.strip().lower() == "true"
            if isinstance(value, bool):
                return value
    return None


# DIAL canonical app names + Samsung app IDs that should route through DIAL.
# IDs sourced from xchwarze/samsung-tv-ws-api APPLICATIONS.md — apps that ship
# multiple IDs across Tizen versions are listed exhaustively.
_DIAL_NETFLIX_IDS: Final[frozenset[str]] = frozenset(
    {"11101200001", "3201907018807"}
)
_DIAL_YOUTUBE_IDS: Final[frozenset[str]] = frozenset({"111299001912"})
_DIAL_DISCOVERY_TIMEOUT: Final[float] = 3.0


class SamsungDriver(TVDriver):
    """Samsung Tizen TV driver."""

    platform = "samsung"

    def __init__(self, ip: str, mac: str = "", port: int = 8002, token_file: str = ""):
        from smartest_tv.config import CONFIG_DIR

        self.ip = ip
        self.mac = mac
        self.port = port
        # Honor STV_CONFIG_DIR (see android.py — #15): pairing tokens must
        # live somewhere persistent in containerized setups.
        self.token_file = token_file or str(CONFIG_DIR / f"samsung_{ip}.token")
        self._remote: SamsungTVWSAsyncRemote | None = None
        self._session: aiohttp.ClientSession | None = None
        # DIAL Application-URL cache. None = not yet looked up; "" = looked up
        # and not present (so we don't M-SEARCH on every launch).
        self._dial_app_url: str | None = None
        # Seconds to wait before the first post-launch app-status poll and
        # between retries. Attribute (not constant) so tests can zero it.
        self._verify_delay: float = 1.5

    async def connect(self) -> None:
        # samsungtvws reads and writes the token file with blocking IO
        # inside its async open() (connection.py:91). Home Assistant's
        # strict mode flags exactly that (issue #20's log warning), so we
        # own the file here: read it in a worker thread, hand the token
        # to the remote directly, and persist any newly granted token
        # through the thread pool afterwards.
        def _load_token() -> str | None:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            try:
                with open(self.token_file) as f:
                    return f.readline().strip() or None
            except OSError:
                return None

        token = await asyncio.to_thread(_load_token)
        self._remote = SamsungTVWSAsyncRemote(
            host=self.ip,
            port=self.port,
            token=token,
            token_file=None,
            timeout=10.0,
            name="SmartestTV",
        )
        await self._remote.open()

        granted = (getattr(self._remote, "token", None) or "").strip() or None
        if granted and granted != token:
            await asyncio.to_thread(self._save_token, granted)

    def _save_token(self, token: str) -> None:
        with open(self.token_file, "w") as f:
            f.write(token)

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
        await r.send_command(SendRemoteKey.click("KEY_POWER"))

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        raise NotImplementedError("Samsung has no read-volume API")

    async def set_volume(self, level: int) -> None:
        # Naive: bottom-out then count up. Batched via send_commands so the
        # async connection only takes the per-key delay between sends, not
        # round-trips between awaits.
        r = await self._ensure()
        bottom = [SendRemoteKey.click("KEY_VOLDOWN")] * 50
        await r.send_commands(bottom, key_press_delay=0.05)
        ups = [SendRemoteKey.click("KEY_VOLUP")] * max(0, min(100, level))
        if ups:
            await r.send_commands(ups, key_press_delay=0.05)

    async def volume_up(self) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_VOLUP"))

    async def volume_down(self) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_VOLDOWN"))

    async def set_mute(self, mute: bool) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_MUTE"))  # Toggle only

    async def get_muted(self) -> bool:
        raise NotImplementedError("Samsung has no read-mute API")

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        r = await self._ensure()
        await r.send_command(ChannelEmitCommand.launch_app(app_id, "NATIVE_LAUNCH", ""))

    async def launch_app_deep(
        self, app_id: str, content_id: str
    ) -> LaunchResult | None:
        """Launch content and *report what the TV actually did* (issues #8, #20).

        Ladder, best-first:
        1. DIAL REST for Netflix/YouTube — interpreted by the app, immune
           to Tizen metaTag quirks.
        2. WS ``ed.apps.launch`` DEEP_LINK, then VERIFY via the REST app
           status endpoint instead of trusting the fire-and-forget send.
        3. If verification says the app never started (the Tizen 9
           behavior — silently ignored), escalate through the REST
           ``applications/{id}`` POST the TV honors, then plain
           NATIVE_LAUNCH.

        Returns a LaunchResult so callers can tell "playing the title"
        from "opened the app" from "nothing happened" — the difference
        issue #20's reporter could not see at all.
        """
        if content_id:
            if app_id in _DIAL_NETFLIX_IDS:
                if await self._try_dial("Netflix", dial.netflix_body(content_id)):
                    return LaunchResult.DIAL
            elif app_id in _DIAL_YOUTUBE_IDS:
                if await self._try_dial("YouTube", dial.youtube_body(content_id)):
                    return LaunchResult.DIAL
            # DIAL didn't apply or didn't reach the TV. Fall back to the
            # Tizen WebSocket DEEP_LINK path — the same payload PR #7 fixed.
            # A WS send failure must not end the ladder: the REST paths
            # below run on a different port and may still work.
            try:
                r = await self._ensure()
                await r.send_command(
                    ChannelEmitCommand.launch_app(app_id, "DEEP_LINK", content_id)
                )
            except Exception:  # noqa: BLE001 — verification decides next
                _LOG.debug("DEEP_LINK send failed for %s", app_id, exc_info=True)
        else:
            # Nothing to deep-link into — resolve() failed upstream. Open
            # the app itself so the user is one click away, never nothing.
            r = await self._ensure()
            await r.send_command(
                ChannelEmitCommand.launch_app(app_id, "NATIVE_LAUNCH", "")
            )

        verified = await self._verify_app_running(app_id)
        if verified is True:
            # Started. With a content_id we can't distinguish "playing the
            # title" from "app opened at its home screen" without app-side
            # feedback — deep-link optimism, callers phrase the rest.
            return LaunchResult.DEEP_LINK if content_id else LaunchResult.APP_ONLY
        if verified is None:
            # Model exposes no usable REST status endpoint — don't guess.
            return (
                LaunchResult.DEEP_LINK_UNVERIFIED
                if content_id
                else LaunchResult.NATIVE
            )

        # Explicitly not running: the TV ignored the deep link (issue #8
        # behavior). Escalate through the paths the TV does honor —
        # issue #20's TV ignores DEEP_LINK but honors REST app-run.
        if await self._rest_run_app(app_id):
            if await self._verify_app_running(app_id) is not False:
                _LOG.warning(
                    "DEEP_LINK for app %s was ignored by the TV; started the "
                    "app via REST instead (issue #8) — pick the title manually",
                    app_id,
                )
                return LaunchResult.APP_ONLY
            return LaunchResult.FAILED

        try:
            r = await self._ensure()
            await r.send_command(
                ChannelEmitCommand.launch_app(app_id, "NATIVE_LAUNCH", "")
            )
        except Exception:  # noqa: BLE001 — last rung failed; report, don't raise
            return LaunchResult.FAILED
        return LaunchResult.NATIVE

    async def _verify_app_running(
        self, app_id: str, attempts: int = 3
    ) -> bool | None:
        """Poll the REST app-status endpoint.

        Returns True (app running), False (app definitely not running) or
        None (this model's REST API is unusable — status unverifiable).
        Tolerant to the two response shapes seen in the wild (top-level
        ``running``/``visible`` keys, or wrapped under ``app``) and to
        string ("true") vs boolean values.
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()
            rest = SamsungTVAsyncRest(
                host=self.ip, session=self._session, port=self.port, timeout=5.0
            )
            await asyncio.sleep(self._verify_delay)
            for attempt in range(attempts):
                try:
                    status = await rest.rest_app_status(app_id)
                except Exception:  # noqa: BLE001 — REST unusable → unknown
                    return None
                verdict = _status_says_running(status)
                if verdict is not None:
                    return verdict
                if attempt < attempts - 1:
                    await asyncio.sleep(self._verify_delay)
            return False
        except Exception:  # noqa: BLE001
            return None

    async def _rest_run_app(self, app_id: str) -> bool:
        """POST applications/{id} — the launch path Tizen reliably honors."""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()
            rest = SamsungTVAsyncRest(
                host=self.ip, session=self._session, port=self.port, timeout=5.0
            )
            await rest.rest_app_run(app_id)
            return True
        except Exception:  # noqa: BLE001
            return False

    async def _try_dial(self, app_name: str, body: str) -> bool:
        """Attempt a DIAL launch for one of the DIAL-aware apps.

        Discovers the TV's Application-URL on first call (cached for the
        lifetime of the driver) and POSTs the launch body. Returns
        ``True`` if the TV accepted the launch with a 2xx status, so the
        caller knows to skip the WebSocket fallback.
        """
        if self._dial_app_url is None:
            url = await dial.discover_application_url(
                self.ip, timeout=_DIAL_DISCOVERY_TIMEOUT
            )
            # Empty string sentinels "we tried, the TV doesn't speak DIAL"
            # so subsequent launches skip the multicast round-trip.
            self._dial_app_url = url or ""
        if not self._dial_app_url:
            return False
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return await dial.launch(
            self._dial_app_url, app_name, body, session=self._session
        )

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
        await r.send_command(SendRemoteKey.click("KEY_PLAY"))

    async def pause(self) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_PAUSE"))

    async def stop(self) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_STOP"))

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
        await r.send_command(SendRemoteKey.click("KEY_CHUP"))

    async def channel_down(self) -> None:
        r = await self._ensure()
        await r.send_command(SendRemoteKey.click("KEY_CHDOWN"))
