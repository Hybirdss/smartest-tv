# Driver Development

This guide explains how to add support for a new TV platform.

## Overview

Each TV platform is implemented as a `TVDriver` subclass in `src/smartest_tv/drivers/`. The base class defines the interface; drivers implement platform-specific communication.

## The TVDriver Interface

**File:** `src/smartest_tv/drivers/base.py`

All drivers must implement these methods:

```python
class TVDriver:
    platform: str          # "lg", "samsung", "android", "firetv", "roku"

    async def connect(self) -> None: ...
    async def power_on(self) -> None: ...
    async def power_off(self) -> None: ...
    async def get_volume(self) -> int: ...
    async def set_volume(self, level: int) -> None: ...
    async def get_muted(self) -> bool: ...
    async def set_mute(self, mute: bool) -> None: ...
    async def volume_up(self) -> None: ...
    async def volume_down(self) -> None: ...
    async def launch_app(self, app_id: str) -> None: ...
    async def launch_app_deep(self, app_id: str, content_id: str) -> None: ...
    async def close_app(self, app_id: str) -> None: ...
    async def list_apps(self) -> list[AppInfo]: ...
    async def play(self) -> None: ...
    async def pause(self) -> None: ...
    async def stop(self) -> None: ...
    async def status(self) -> TVStatus: ...
    async def info(self) -> TVInfo: ...
    async def notify(self, message: str) -> None: ...
    async def screen_off(self) -> None: ...
    async def screen_on(self) -> None: ...
```

## Return types

```python
@dataclass
class AppInfo:
    id: str
    name: str

@dataclass
class TVStatus:
    current_app: str | None
    volume: int
    muted: bool
    sound_output: str | None

@dataclass
class TVInfo:
    platform: str
    model: str
    firmware: str
    ip: str
    name: str
```

## Creating a driver

1. Create `src/smartest_tv/drivers/myplatform.py`
2. Subclass `TVDriver` and implement all methods
3. Register the platform in `src/smartest_tv/drivers/factory.py` (or the driver selection in `cli.py` and `server.py`)
4. Add app IDs in `src/smartest_tv/apps.py`
5. Add the optional dependency to `pyproject.toml` under `[project.optional-dependencies]`

## Example skeleton

```python
from smartest_tv.drivers.base import TVDriver, AppInfo, TVStatus, TVInfo

class MyPlatformDriver(TVDriver):
    platform = "myplatform"

    def __init__(self, ip: str, mac: str = ""):
        self.ip = ip
        self.mac = mac
        self._client = None

    async def connect(self) -> None:
        # Establish connection (WebSocket, HTTP, ADB, etc.)
        self._client = await MyPlatformClient.connect(self.ip)

    async def power_on(self) -> None:
        # Wake-on-LAN if mac is set, otherwise platform-specific
        ...

    async def launch_app_deep(self, app_id: str, content_id: str) -> None:
        # Format deep link for your platform and launch
        # Netflix: platform-specific format varies
        # YouTube: platform-specific format varies
        ...

    # ... implement remaining methods
```

## App ID mapping

Add your platform's app IDs to `src/smartest_tv/apps.py`:

```python
APP_IDS = {
    "myplatform": {
        "netflix": "com.netflix.ninja",    # your platform's app ID
        "youtube": "com.google.android.youtube",
        "spotify": "com.spotify.music",
        # ...
    }
}
```

## Deep link formats

Reference for existing platforms:

| Platform | Netflix | YouTube |
|----------|---------|---------|
| LG webOS | SSAP `launch_app_with_content_id` | SSAP `launch_app_with_params` |
| Samsung | `run_app(id, "DEEP_LINK", meta_tag)` | same |
| Android/Fire TV | `am start -d 'netflix://title/{id}'` | `am start -d 'youtube://{id}'` |
| Roku | `POST /launch/12?contentId={id}` | `POST /launch/837?contentId={id}` |

## Testing

Unit tests do not require a physical TV. Mock the driver for all tests:

```bash
python -m pytest tests/ -v
```

For integration tests, use `stv status` and `stv doctor` against a real TV.

## Submitting

Open a pull request with:
- The driver implementation
- App ID mappings
- A note on which TV model was tested
- Any known limitations (e.g., `close_app` not supported)
