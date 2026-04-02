"""Abstract base class for TV platform drivers.

Every platform (LG, Samsung, Android TV, Roku) implements this interface.
The CLI, MCP server, and skills all talk to this — never to a platform directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TVStatus:
    """Unified TV status across all platforms."""

    current_app: str | None = None
    volume: int | None = None
    muted: bool | None = None
    powered: bool | None = None
    sound_output: str | None = None


@dataclass
class TVInfo:
    """Unified TV system info."""

    platform: str = ""  # lg, samsung, android, roku
    model: str = ""
    firmware: str = ""
    ip: str = ""
    mac: str = ""
    name: str = ""


@dataclass
class App:
    """Installed app info."""

    id: str = ""
    name: str = ""


class TVDriver(ABC):
    """Abstract interface for controlling a smart TV.

    Subclasses handle platform-specific protocols:
    - LG: WebSocket SSAP via bscpylgtv
    - Samsung: WebSocket via samsungtvws
    - Android/Fire TV: ADB TCP via adb-shell
    - Roku: HTTP ECP on port 8060
    """

    platform: str = ""

    # -- Connection -----------------------------------------------------------

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the TV. May trigger a pairing prompt."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect cleanly."""

    # -- Power ----------------------------------------------------------------

    @abstractmethod
    async def power_on(self) -> None:
        """Turn on the TV (WoL or equivalent)."""

    @abstractmethod
    async def power_off(self) -> None:
        """Turn off the TV (standby)."""

    # -- Volume ---------------------------------------------------------------

    @abstractmethod
    async def get_volume(self) -> int:
        """Get current volume level (0-100)."""

    @abstractmethod
    async def set_volume(self, level: int) -> None:
        """Set volume level (0-100)."""

    @abstractmethod
    async def volume_up(self) -> None:
        """Increase volume by one step."""

    @abstractmethod
    async def volume_down(self) -> None:
        """Decrease volume by one step."""

    @abstractmethod
    async def set_mute(self, mute: bool) -> None:
        """Mute or unmute."""

    @abstractmethod
    async def get_muted(self) -> bool:
        """Check if muted."""

    # -- Apps & Deep Linking --------------------------------------------------

    @abstractmethod
    async def launch_app(self, app_id: str) -> None:
        """Launch an app by its platform-specific ID."""

    @abstractmethod
    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        """Launch an app with deep link to specific content.

        The content_id format is platform-specific — the driver handles
        formatting (e.g., Netflix DIAL URL for LG, meta_tag for Samsung).
        """

    @abstractmethod
    async def close_app(self, app_id: str) -> None:
        """Close a running app."""

    @abstractmethod
    async def list_apps(self) -> list[App]:
        """List all installed apps."""

    # -- Media Playback -------------------------------------------------------

    @abstractmethod
    async def play(self) -> None:
        """Resume playback."""

    @abstractmethod
    async def pause(self) -> None:
        """Pause playback."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop playback."""

    # -- Status & Info --------------------------------------------------------

    @abstractmethod
    async def status(self) -> TVStatus:
        """Get current TV status."""

    @abstractmethod
    async def info(self) -> TVInfo:
        """Get TV system information."""

    # -- Input ----------------------------------------------------------------

    async def set_input(self, source: str) -> None:
        """Switch input source. Optional — not all platforms support direct input switching."""
        raise NotImplementedError(f"{self.platform} does not support direct input switching")

    async def list_inputs(self) -> list[dict[str, Any]]:
        """List available input sources."""
        return []

    # -- Channels -------------------------------------------------------------

    async def channel_up(self) -> None:
        """Next channel."""
        raise NotImplementedError

    async def channel_down(self) -> None:
        """Previous channel."""
        raise NotImplementedError

    # -- Notifications --------------------------------------------------------

    async def notify(self, message: str) -> None:
        """Show a notification on the TV screen. Not all platforms support this."""
        raise NotImplementedError(f"{self.platform} does not support notifications")

    # -- Screen ---------------------------------------------------------------

    async def screen_off(self) -> None:
        """Turn off screen (keep audio). Not all platforms support this."""
        raise NotImplementedError

    async def screen_on(self) -> None:
        """Turn on screen."""
        raise NotImplementedError
