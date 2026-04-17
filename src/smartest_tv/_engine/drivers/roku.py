"""Roku TV driver via ECP (External Control Protocol) — raw aiohttp, no SDK.

ECP is a simple HTTP REST API served on port 8060 of every Roku device.
Roku has NO get_volume or get_muted API; those two methods raise NotImplementedError
with a clear message. Volume/mute can only be adjusted one step at a time via keypress.

SSDP discovery: multicast M-SEARCH to 239.255.255.250:1900 with ST: roku:ecp.
The Location header in the response gives http://<IP>:8060/.
"""

from __future__ import annotations

import asyncio
import re
import socket
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode

try:
    import aiohttp
except ImportError:
    raise ImportError("Install Roku driver: pip install 'smartest-tv[roku]'")

from smartest_tv.drivers.base import App, TVDriver, TVInfo, TVStatus

# ---------------------------------------------------------------------------
# Well-known Roku app IDs (ECP numeric IDs)
# ---------------------------------------------------------------------------

ROKU_APP_IDS: dict[str, str] = {
    "netflix": "12",
    "youtube": "837",
    "spotify": "19977",
    "prime": "13",
    "hulu": "2285",
    "disney": "291097",
    "appletv": "551012",
    "tubi": "26",
    "peacock": "593099",
    "hbomax": "61322",  # Max
    "max": "61322",
    "paramountplus": "31440",
    "discovery": "valueplus",
    "channel": "tvinput.hdmi1",  # placeholder
}

# ECP deep-link mediaType values accepted by Roku channels
MEDIA_TYPES = frozenset({"movie", "series", "episode", "shortformvideo", "live"})

# Default timeout for all HTTP requests (seconds)
_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=5)

# SSDP constants
_SSDP_ADDR = "239.255.255.250"
_SSDP_PORT = 1900
_SSDP_ST = "roku:ecp"
_SSDP_MX = 3

_SSDP_MSG = (
    "M-SEARCH * HTTP/1.1\r\n"
    f"HOST: {_SSDP_ADDR}:{_SSDP_PORT}\r\n"
    'MAN: "ssdp:discover"\r\n'
    f"MX: {_SSDP_MX}\r\n"
    f"ST: {_SSDP_ST}\r\n"
    "\r\n"
)


# ---------------------------------------------------------------------------
# SSDP discovery (module-level helper, mirrors discovery.py style)
# ---------------------------------------------------------------------------

async def discover(timeout: float = 5.0) -> list[dict[str, str]]:
    """Discover Roku devices on the local network via SSDP.

    Returns a list of dicts with keys: ``ip``, ``name``, ``location``.

    The Roku SSDP response includes a ``Location`` header pointing to the ECP
    base URL (``http://<IP>:8060/``) and a ``USN`` header with the serial number.
    """
    found: dict[str, dict[str, str]] = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(timeout)

    try:
        sock.sendto(_SSDP_MSG.encode(), (_SSDP_ADDR, _SSDP_PORT))
        loop = asyncio.get_event_loop()
        end = loop.time() + timeout

        while loop.time() < end:
            try:
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(None, sock.recvfrom, 4096),
                    timeout=max(0.1, end - loop.time()),
                )
            except (TimeoutError, asyncio.TimeoutError, OSError):
                break

            ip = addr[0]
            if ip in found:
                continue

            text = data.decode(errors="ignore")

            # Extract Location header → base URL
            loc_match = re.search(r"(?i)^location:\s*(\S+)", text, re.MULTILINE)
            location = loc_match.group(1).strip() if loc_match else f"http://{ip}:8060/"

            # Try to extract friendly name from USN (contains serial, not name)
            # We'll fill the name from device-info after discovery if needed
            usn_match = re.search(r"(?i)^usn:\s*uuid:roku:ecp:(\S+)", text, re.MULTILINE)
            serial = usn_match.group(1).strip() if usn_match else ""

            found[ip] = {
                "ip": ip,
                "location": location,
                "name": f"Roku ({serial or ip})",
            }
    finally:
        sock.close()

    # Enrich with friendly device names via device-info (best-effort)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
        async def _enrich(entry: dict[str, str]) -> None:
            try:
                url = f"http://{entry['ip']}:8060/query/device-info"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        xml_text = await resp.text()
                        root = ET.fromstring(xml_text)
                        friendly = root.findtext("friendly-device-name") or ""
                        model = root.findtext("model-name") or ""
                        if friendly:
                            entry["name"] = friendly
                        elif model:
                            entry["name"] = model
            except Exception:
                pass  # enrichment is best-effort

        await asyncio.gather(*[_enrich(e) for e in found.values()])

    return list(found.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_hms(text: str | None) -> int | None:
    """Parse Roku media-player time string 'H:MM:SS.mmm' → integer seconds."""
    if not text:
        return None
    try:
        parts = text.split(".")[0].split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Roku Driver
# ---------------------------------------------------------------------------

class RokuDriver(TVDriver):
    """Roku TV driver using raw ECP (HTTP on port 8060).

    No external Roku library required — ECP is plain HTTP.

    Volume/mute limitation
    ----------------------
    Roku's ECP has no endpoint to *read* the current volume level or muted
    state. ``get_volume()`` and ``get_muted()`` raise ``NotImplementedError``
    with an explanatory message. Use ``volume_up()``, ``volume_down()``, and
    ``set_mute()`` for adjustment.

    ``set_volume()`` is implemented via repeated VolumeDown (to reach 0) then
    repeated VolumeUp keypresses to reach the requested level. This is a
    best-effort approximation; it works reliably only when the caller also
    controls the initial volume state.
    """

    platform = "roku"

    def __init__(self, ip: str, port: int = 8060, mac: str = "") -> None:
        self.ip = ip
        self.port = port
        self.mac = mac  # used for Wake-on-LAN if available
        self._base = f"http://{ip}:{port}"
        self._session: aiohttp.ClientSession | None = None
        # Roku ECP has no volume query, so we track the value we last
        # *set* and issue delta keypresses on subsequent set_volume calls.
        # None = unknown (next call still has to drive to zero first).
        self._known_volume: int | None = None

    # -- Session management ---------------------------------------------------

    async def connect(self) -> None:
        """Create the aiohttp session. No handshake needed for ECP."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=_HTTP_TIMEOUT)

    async def disconnect(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _session_or_new(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            await self.connect()
        return self._session  # type: ignore[return-value]

    # -- Low-level helpers ----------------------------------------------------

    async def _post(self, path: str) -> int:
        """POST to an ECP endpoint. Returns HTTP status code."""
        session = await self._session_or_new()
        async with session.post(f"{self._base}{path}", data=b"") as resp:
            return resp.status

    async def _get_xml(self, path: str) -> ET.Element:
        """GET an ECP query endpoint and parse the XML response body."""
        session = await self._session_or_new()
        async with session.get(f"{self._base}{path}") as resp:
            resp.raise_for_status()
            text = await resp.text()
            return ET.fromstring(text)

    async def _keypress(self, key: str) -> None:
        """Send a single ECP keypress."""
        await self._post(f"/keypress/{key}")

    # -- Power ----------------------------------------------------------------

    async def power_on(self) -> None:
        """Power on via ECP PowerOn keypress.

        If a MAC address was supplied and the device is truly off (not in
        standby), Wake-on-LAN is sent first, then a PowerOn keypress.
        """
        if self.mac:
            _send_wol(self.mac)
            await asyncio.sleep(2)  # give device time to wake before ECP
        await self._keypress("PowerOn")

    async def power_off(self) -> None:
        """Power off via ECP PowerOff keypress (puts device in standby)."""
        await self._keypress("PowerOff")

    # -- Volume ---------------------------------------------------------------

    async def get_volume(self) -> int:
        """Not supported — Roku ECP has no volume query endpoint.

        Raises:
            NotImplementedError: Always. Use volume_up/volume_down instead.
        """
        raise NotImplementedError(
            "Roku ECP does not expose a volume query endpoint. "
            "Use volume_up() / volume_down() / set_mute() instead."
        )

    async def set_volume(self, level: int) -> None:
        """Approximate volume set via delta keypresses.

        Roku ECP exposes no volume query, so we track what we last set
        and issue only the delta on subsequent calls:

        * First call (state unknown): drive down 100 times to pin to 0,
          then step up ``level`` times.
        * Subsequent calls: send ``|target - _known_volume|`` keypresses
          in the right direction.

        Each keypress is a sequential HTTP round-trip (the TV serialises
        them), so the first call can take several seconds on a slow LAN
        — but subsequent calls are fast.

        Clamps ``level`` to [0, 100]. If the user touches the remote
        between calls, state drifts; call this method again (or
        reinstantiate the driver) to resync.
        """
        level = max(0, min(100, level))
        # We update _known_volume after every keypress instead of only on
        # the success path. A network blip mid-loop used to leave
        # _known_volume stale — the next set_volume() then over- or
        # under-shot by the number of presses already sent before the
        # exception. Keeping the running estimate accurate matters more
        # than rolling back the partial change (which we can't do
        # anyway: the TV already processed the presses we did send).
        if self._known_volume is None:
            for _ in range(100):
                await self._keypress("VolumeDown")
            # At this point we've hit the floor (or tried to); pin the
            # estimate here so any mid-loop exception leaves a sane state.
            self._known_volume = 0
            for _ in range(level):
                await self._keypress("VolumeUp")
                self._known_volume += 1
        else:
            delta = level - self._known_volume
            key = "VolumeUp" if delta > 0 else "VolumeDown"
            step = 1 if delta > 0 else -1
            for _ in range(abs(delta)):
                await self._keypress(key)
                self._known_volume += step

    async def volume_up(self) -> None:
        """Increase volume by one step."""
        await self._keypress("VolumeUp")
        if self._known_volume is not None:
            self._known_volume = min(100, self._known_volume + 1)

    async def volume_down(self) -> None:
        """Decrease volume by one step."""
        await self._keypress("VolumeDown")
        if self._known_volume is not None:
            self._known_volume = max(0, self._known_volume - 1)

    async def set_mute(self, mute: bool) -> None:
        """Toggle mute via VolumeMute keypress.

        Roku ECP only has a mute *toggle* — there is no separate mute/unmute
        command. This method sends one VolumeMute keypress regardless of the
        ``mute`` argument value. The caller should track state externally if
        idempotent mute/unmute is required.
        """
        await self._keypress("VolumeMute")

    async def get_muted(self) -> bool:
        """Not supported — Roku ECP has no mute state query endpoint.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "Roku ECP does not expose a mute state query endpoint. "
            "Track mute state externally or use set_mute() as a toggle."
        )

    # -- Apps & Deep Linking --------------------------------------------------

    async def launch_app(self, app_id: str) -> None:
        """Launch an installed Roku channel by its ECP app ID.

        Args:
            app_id: Numeric string ECP app ID (e.g. "12" for Netflix).
                    Human-readable aliases from ROKU_APP_IDS are also accepted.
        """
        resolved = ROKU_APP_IDS.get(app_id.lower(), app_id)
        await self._post(f"/launch/{resolved}")

    async def launch_app_deep(
        self,
        app_id: str,
        content_id: str,
        media_type: str = "movie",
    ) -> None:
        """Launch a Roku channel with ECP deep-link parameters.

        ECP deep links pass ``contentId`` and ``mediaType`` as query parameters
        to ``POST /launch/{appId}``. The channel's ``Main()`` entry point
        receives them and navigates directly to the content.

        Args:
            app_id: ECP numeric app ID or friendly alias.
            content_id: Platform-specific content identifier (e.g. Netflix
                        content ID, YouTube video ID, Spotify URI).
            media_type: One of: ``movie``, ``series``, ``episode``,
                        ``shortformvideo``, ``live``. Defaults to ``"movie"``.
        """
        resolved = ROKU_APP_IDS.get(app_id.lower(), app_id)
        if media_type not in MEDIA_TYPES:
            media_type = "movie"
        params = urlencode({"contentId": content_id, "mediaType": media_type})
        await self._post(f"/launch/{resolved}?{params}")

    async def close_app(self, app_id: str) -> None:
        """Press the Home key to exit any running app and return to the home screen.

        Roku ECP has no per-app close command. The Home key is the universal
        "go back to home" equivalent on every Roku device.
        """
        await self._keypress("Home")

    async def list_apps(self) -> list[App]:
        """Return all installed Roku channels from GET /query/apps.

        XML response::

            <apps>
              <app id="12" subtype="ndka" type="appl" version="4.1.218">Netflix</app>
              ...
            </apps>
        """
        root = await self._get_xml("/query/apps")
        return [
            App(id=el.get("id", ""), name=el.text or "")
            for el in root.findall("app")
        ]

    # -- Media Playback -------------------------------------------------------

    async def play(self) -> None:
        """Resume playback (ECP Play key)."""
        await self._keypress("Play")

    async def pause(self) -> None:
        """Pause playback (ECP Play key — toggles play/pause on Roku)."""
        await self._keypress("Play")

    async def stop(self) -> None:
        """Stop playback by pressing Back then Home."""
        await self._keypress("Back")
        await asyncio.sleep(0.3)
        await self._keypress("Home")

    # -- Status & Info --------------------------------------------------------

    async def status(self) -> TVStatus:
        """Return current TV status from ECP query endpoints.

        ``volume`` and ``muted`` are always ``None`` because Roku ECP provides
        no volume or mute query endpoints.
        """
        current_app: str | None = None
        powered: bool | None = None
        title: str | None = None
        position_s: int | None = None
        duration_s: int | None = None
        play_state: str | None = None

        try:
            root = await self._get_xml("/query/active-app")
            app_el = root.find("app")
            if app_el is not None:
                app_id = app_el.get("id", "")
                app_name = app_el.text or ""
                # If screensaver is active and app is home, device is on but idle
                powered = True
                current_app = app_name if app_name else app_id
        except Exception:
            powered = False

        try:
            mp = await self._get_xml("/query/media-player")
            state_el = mp.find("state")
            if state_el is not None:
                play_state = state_el.text
            title_el = mp.find("title")
            if title_el is not None:
                title = title_el.text or None
            position_s = _parse_hms(mp.findtext("position"))
            duration_s = _parse_hms(mp.findtext("duration"))
        except Exception:
            pass

        return TVStatus(
            current_app=current_app,
            volume=None,   # not available via ECP
            muted=None,    # not available via ECP
            powered=powered,
            title=title,
            position_s=position_s,
            duration_s=duration_s,
            play_state=play_state,
        )

    async def info(self) -> TVInfo:
        """Return device information from ECP GET /query/device-info.

        XML fields extracted:

        - ``friendly-device-name`` → name
        - ``model-name`` or ``model-number`` → model
        - ``software-version`` → firmware
        - ``ethernet-mac`` or ``wifi-mac`` → mac
        """
        root = await self._get_xml("/query/device-info")

        def _text(tag: str) -> str:
            el = root.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        name = _text("friendly-device-name") or _text("model-name") or f"Roku ({self.ip})"
        model = _text("model-name") or _text("model-number")
        firmware = _text("software-version")
        # Prefer ethernet MAC, fall back to wifi
        mac = _text("ethernet-mac") or _text("wifi-mac") or self.mac

        return TVInfo(
            platform="roku",
            model=model,
            firmware=firmware,
            ip=self.ip,
            mac=mac,
            name=name,
        )

    # -- Input (HDMI / TV tuner) ----------------------------------------------

    async def set_input(self, source: str) -> None:
        """Switch to a named input source using ECP launch endpoints.

        Supported ``source`` values (case-insensitive):
        ``hdmi1``, ``hdmi2``, ``hdmi3``, ``hdmi4``, ``av1``, ``tuner``/``tv``.

        Roku input switching is done via ``POST /launch/tvinput.<source>``.
        Not all Roku devices have all inputs.
        """
        _INPUT_MAP: dict[str, str] = {
            "hdmi1": "tvinput.hdmi1",
            "hdmi2": "tvinput.hdmi2",
            "hdmi3": "tvinput.hdmi3",
            "hdmi4": "tvinput.hdmi4",
            "av1": "tvinput.av1",
            "tuner": "tvinput.dtv",
            "tv": "tvinput.dtv",
            "dtv": "tvinput.dtv",
        }
        key = source.lower().strip()
        ecp_id = _INPUT_MAP.get(key, f"tvinput.{key}")
        await self._post(f"/launch/{ecp_id}")

    async def list_inputs(self) -> list[dict[str, Any]]:
        """Return a static list of standard Roku input sources.

        Roku ECP has no query endpoint for available inputs. Returns the
        canonical set; not all will be present on every device.
        """
        return [
            {"id": "tvinput.hdmi1", "label": "HDMI 1"},
            {"id": "tvinput.hdmi2", "label": "HDMI 2"},
            {"id": "tvinput.hdmi3", "label": "HDMI 3"},
            {"id": "tvinput.hdmi4", "label": "HDMI 4"},
            {"id": "tvinput.av1",   "label": "AV"},
            {"id": "tvinput.dtv",   "label": "TV Tuner"},
        ]

    # -- Channels (TV tuner) --------------------------------------------------

    async def channel_up(self) -> None:
        """Next channel (Roku TV tuner, ChannelUp key)."""
        await self._keypress("ChannelUp")

    async def channel_down(self) -> None:
        """Previous channel (Roku TV tuner, ChannelDown key)."""
        await self._keypress("ChannelDown")

    # -- Navigation (Roku-specific extras, not on base class) -----------------

    async def home(self) -> None:
        """Press the Home key."""
        await self._keypress("Home")

    async def back(self) -> None:
        """Press the Back key."""
        await self._keypress("Back")

    async def select(self) -> None:
        """Press the Select/OK key."""
        await self._keypress("Select")

    async def up(self) -> None:
        await self._keypress("Up")

    async def down(self) -> None:
        await self._keypress("Down")

    async def left(self) -> None:
        await self._keypress("Left")

    async def right(self) -> None:
        await self._keypress("Right")

    async def info_key(self) -> None:
        """Press the Info/asterisk (*) key."""
        await self._keypress("Info")

    async def instant_replay(self) -> None:
        await self._keypress("InstantReplay")

    async def rewind(self) -> None:
        await self._keypress("Rev")

    async def fast_forward(self) -> None:
        await self._keypress("Fwd")

    async def search(self) -> None:
        """Open Roku search."""
        await self._keypress("Search")

    async def send_text(self, text: str) -> None:
        """Type text by sending individual Lit_ keypresses.

        ASCII printable characters are sent as ``Lit_<char>`` (URL-encoded).
        Use this to fill search boxes after navigating to an input field.
        """
        from urllib.parse import quote
        for char in text:
            encoded = quote(char, safe="")
            await self._keypress(f"Lit_{encoded}")
            await asyncio.sleep(0.05)  # small delay between characters

    # -- Screen ---------------------------------------------------------------

    async def screen_off(self) -> None:
        """Not natively supported by ECP. Sends PowerOff as best-effort."""
        await self._keypress("PowerOff")

    async def screen_on(self) -> None:
        """Wake screen via PowerOn keypress."""
        await self._keypress("PowerOn")

    # -- Context manager support ----------------------------------------------

    async def __aenter__(self) -> "RokuDriver":
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.disconnect()


# ---------------------------------------------------------------------------
# Wake-on-LAN helper
# ---------------------------------------------------------------------------

def _send_wol(mac: str) -> None:
    """Send a Wake-on-LAN magic packet to the broadcast address."""
    mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    magic = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic, ("255.255.255.255", 9))
