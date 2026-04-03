# Sync & Party Mode

Play the same content on multiple TVs simultaneously — in the same house or across the internet.

## How it works

```
stv --group party play netflix "Squid Game" s2e3
```

1. **Resolve once** — `stv resolve` finds the Netflix episode ID (`82656797`). This is a single HTTP request. The ID is universal across all TVs, all platforms, all countries.

2. **Connect all** — stv creates a driver for each TV in the group concurrently. Local TVs connect via WebSocket/ADB/HTTP. Remote TVs connect via the friend's REST API.

3. **Launch simultaneously** — `asyncio.gather` sends the deep link command to every TV at the same time. One TV failing doesn't stop the others.

```
Your stv CLI
  │
  ├─ resolve("Squid Game", s2e3) → 82656797
  │
  ├─ asyncio.gather:
  │   ├─ LGDriver → WebSocket → Your TV
  │   ├─ SamsungDriver → WebSocket → Bedroom TV
  │   └─ RemoteDriver → HTTP POST → Friend's stv → Friend's TV
  │
  └─ record_play() → history
```

### Why content IDs make this possible

Netflix episode ID `82656797` means the same thing everywhere. LG, Samsung, Roku, Android TV — the driver translates it into the platform's native deep link format, but the ID itself is universal. This is what makes cross-platform, cross-network sync trivial.

## Local: same house, multiple TVs

### 1. Add your TVs

```bash
stv multi add living-room --platform lg --ip 192.168.1.100 --default
stv multi add bedroom --platform samsung --ip 192.168.1.101
stv multi add kids-room --platform roku --ip 192.168.1.102
```

### 2. Create groups

```bash
stv group create home living-room bedroom
stv group create everywhere living-room bedroom kids-room
```

Groups are saved in `~/.config/smartest-tv/config.toml`:

```toml
[tv.living-room]
platform = "lg"
ip = "192.168.1.100"
default = true

[tv.bedroom]
platform = "samsung"
ip = "192.168.1.101"

[tv.kids-room]
platform = "roku"
ip = "192.168.1.102"

[groups]
home = ["living-room", "bedroom"]
everywhere = ["living-room", "bedroom", "kids-room"]
```

### 3. Use --group or --all

```bash
stv --group home play youtube "lo-fi beats"    # living-room + bedroom
stv --all volume 20                             # every TV
stv --all off                                   # good night, all TVs
stv --group home notify "Dinner's ready!"      # toast on 2 TVs
```

## Remote: watch with friends

### Prerequisites

- Both you and your friend have `stv` installed and a TV configured
- Friend's machine is reachable over the network (same LAN, VPN, or port-forwarded)

### 1. Friend starts their server

```bash
stv serve --host 0.0.0.0
```

Output:
```
MCP server:  http://0.0.0.0:8910/sse
REST API:    http://0.0.0.0:8911/api/ping
Friends can add your TV:  stv multi add friend --platform remote --url http://YOUR_IP:8911
```

The REST API on port 8911 is what your stv will talk to.

### 2. You add their TV

```bash
stv multi add jake --platform remote --url http://203.0.113.50:8911
```

### 3. Create a watch party group

```bash
stv group create watch-party living-room jake
```

### 4. Sync play

```bash
stv --group watch-party play netflix "Wednesday" s1e1
```

Both TVs start playing the same episode. Content is resolved once on your side; the friend's stv receives the content ID and handles the deep link locally.

### How the remote chain works

```
You:  stv --group watch-party play netflix "Wednesday" s1e1
        │
        ├─ resolve → 81231974 (one HTTP request)
        │
        ├─ LGDriver.launch_app_deep("netflix", "81231974")
        │   → WebSocket to your TV → Netflix opens
        │
        └─ RemoteDriver._post("/api/launch", {app:"netflix", content_id:"81231974"})
            → HTTP POST to http://203.0.113.50:8911/api/launch
            → Friend's api.py receives the request
            → Friend's LGDriver.launch_app_deep("netflix", "81231974")
            → WebSocket to friend's TV → Netflix opens
```

The RemoteDriver implements the same `TVDriver` interface as LG/Samsung/Roku/Android. From the perspective of `asyncio.gather`, it's just another TV — local or remote doesn't matter.

### Network requirements

| Setup | What you need |
|-------|---------------|
| Same LAN | Nothing extra — direct IP works |
| Tailscale / WireGuard | Use the VPN IP (e.g. `100.x.x.x`) |
| Over the internet | Port-forward 8911 on friend's router, or use a reverse tunnel |

### Security note

The REST API has no authentication. Only expose it on trusted networks or behind a VPN. It controls the TV — anyone with access can play content or turn it off.

## MCP tools for AI agents

```python
# Play on multiple TVs at once
tv_sync_play(
    platform="netflix",
    query="Bridgerton",
    season=3, episode=4,
    group="watch-party"
)

# Or specify TV names directly
tv_sync_play(
    platform="youtube",
    query="lo-fi hip hop",
    tv_names=["living-room", "bedroom"]
)

# List groups
tv_group_list()
# → [{"name": "watch-party", "members": ["living-room", "jake"]}]
```

## Supported commands with --all / --group

| Command | Multi-TV | What happens |
|---------|----------|-------------|
| `stv play` | `--all` / `--group` | Same content on all TVs |
| `stv off` | `--all` / `--group` | Turn off all TVs |
| `stv on` | `--all` / `--group` | Wake all TVs |
| `stv volume N` | `--all` / `--group` | Same volume everywhere |
| `stv mute` | `--all` / `--group` | Toggle mute on all |
| `stv notify MSG` | `--all` / `--group` | Toast on every screen |
