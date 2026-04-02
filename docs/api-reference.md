# API Reference

Complete reference for all `stv` CLI commands and MCP tools.

---

## CLI Commands

Run `stv --help` or `stv <command> --help` for inline help.

### Global Options

| Option | Default | Description |
|---|---|---|
| `--format [text\|json]` | `text` | Output format for commands that return data |

### Setup & Diagnostics

#### `stv setup`
Interactive wizard. Discovers TVs on the network, handles pairing, and writes
`~/.config/smartest-tv/config.toml`.

#### `stv doctor`
Checks connectivity, queries TV status, and verifies Netflix/YouTube/Spotify
apps are installed.

### Power

#### `stv on`
Turn on the TV via Wake-on-LAN (requires `mac` in config).

#### `stv off`
Put the TV into standby.

### Volume

#### `stv volume [LEVEL]`
Get current volume (no argument) or set to `LEVEL` (0–100).

```bash
stv volume         # print current volume + mute state
stv volume 30      # set to 30
```

#### `stv mute`
Toggle mute on/off.

### Apps

#### `stv launch APP [CONTENT_ID]`
Launch an app. Pass `CONTENT_ID` for deep linking.

```bash
stv launch netflix
stv launch netflix 82656797      # deep link to episode
stv launch youtube dQw4w9WgXcQ   # deep link to video
```

`APP` accepts friendly names: `netflix`, `youtube`, `spotify`, `disney`,
`prime`, `appletv`, `hulu`, `tving`, `wavve`, `coupang`, `browser`,
`hdmi1`, `hdmi2`.

#### `stv close APP`
Close a running app.

#### `stv apps`
List all installed apps (id + name).

### Media Playback

#### `stv play`
Resume playback (sends Play key).

#### `stv pause`
Pause playback (sends Pause key).

### Status

#### `stv status`
Show current TV state: platform, current app, volume, mute, sound output.

#### `stv info`
Show system info: platform, model, firmware, IP, name.

### Notifications

#### `stv notify MESSAGE`
Show a toast notification on the TV screen.

### Content Search

#### `stv search PLATFORM QUERY`
Search for content and show what stv found (does not play anything).

```bash
stv search netflix Frieren
stv search spotify "Ye White Lines"
stv search youtube "baby shark"
```

`PLATFORM`: `netflix`, `youtube`, `spotify`

### Content Resolution

#### `stv resolve PLATFORM QUERY [OPTIONS]`
Resolve a content name to a platform-specific ID without playing it.

```bash
stv resolve netflix Frieren -s 2 -e 8
stv resolve netflix Frieren s2e8            # inline S/E notation
stv resolve youtube "baby shark"
stv resolve netflix "The Glory" --title-id 81519223 -s 1 -e 1
```

**Options:**

| Option | Description |
|---|---|
| `-s, --season INT` | Season number (Netflix) |
| `-e, --episode INT` | Episode number (Netflix) |
| `--title-id INT` | Netflix title ID — skips web search |

**Inline S/E notation** — append to the query as the last argument:

| Format | Example | Result |
|---|---|---|
| `sNeM` | `s2e8` | season=2, episode=8 |
| `SNNEM` (zero-padded) | `S02E08` | season=2, episode=8 |
| `NxM` | `2x8` | season=2, episode=8 |

### Play Content

#### `stv play PLATFORM QUERY [OPTIONS]`
Resolve content and play it on TV in one step.

```bash
stv play netflix Frieren s2e8
stv play netflix Frieren -s 2 -e 8 --title-id 81726714
stv play youtube "baby shark"
stv play spotify "spotify:album:5poA9SAx0Xiz1cd17fWBLS"
```

Same options as `stv resolve`. For Netflix, automatically closes the app
first (required for deep links to work), then relaunches with the content ID.
Records the play to local history.

### History

#### `stv history [-n LIMIT]`
Show recent play history. Default limit: 10.

```bash
stv history
stv history -n 5
```

#### `stv next [QUERY]`
Play the next episode of a Netflix show based on history.

```bash
stv next Frieren    # next episode after last watched Frieren
stv next            # continues most recently watched Netflix show
```

### Cache Management

#### `stv cache set PLATFORM QUERY [OPTIONS]`
Save a content ID to the local cache manually.

```bash
# Netflix season data
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714

# Direct ID (YouTube/Spotify)
stv cache set youtube "baby shark" --content-id XqZsoesa55w
stv cache set spotify "Ye Vultures" --content-id "spotify:album:xxx"
```

| Option | Description |
|---|---|
| `-s, --season INT` | Season number (Netflix) |
| `--first-ep-id INT` | First episode videoId of the season |
| `--count INT` | Number of episodes in the season |
| `--title-id INT` | Netflix title ID |
| `--content-id STR` | Direct content ID (YouTube/Spotify) |

#### `stv cache get PLATFORM QUERY [OPTIONS]`
Look up a cached content ID.

```bash
stv cache get netflix Frieren -s 2 -e 8
stv cache get youtube "baby shark"
```

#### `stv cache show`
Print the full contents of the local cache JSON.

#### `stv cache contribute`
Print local cache in `community-cache.json` format (history stripped).
Pipe to a file to submit a PR.

---

## MCP Tools

The MCP server exposes all controls as tools. Start with:

```bash
python -m smartest_tv.server
```

### Power

#### `tv_on() → str`
Turn on the TV.

#### `tv_off() → str`
Turn off the TV (standby).

### Volume

#### `tv_volume() → dict`
Get current volume and mute state. Returns `{"volume": int, "muted": bool}`.

#### `tv_set_volume(level: int) → str`
Set volume 0–100.

#### `tv_volume_up() → str`
Increase volume by one step.

#### `tv_volume_down() → str`
Decrease volume by one step.

#### `tv_mute(mute: bool | None = None) → str`
Mute, unmute, or toggle. Pass `true`/`false` to force a state, omit to toggle.

### Apps

#### `tv_launch(app: str, content_id: str | None = None) → str`
Launch an app with optional deep link.

| Parameter | Description |
|---|---|
| `app` | App name (`netflix`, `youtube`, `spotify`, etc.) or raw app ID |
| `content_id` | Netflix episode ID, YouTube video ID, or Spotify URI |

#### `tv_close(app: str) → str`
Close a running app.

#### `tv_apps() → list[dict]`
List installed apps. Returns `[{"id": str, "name": str}, ...]`.

### Media Playback

#### `tv_play() → str`
Resume playback.

#### `tv_pause() → str`
Pause playback.

#### `tv_stop() → str`
Stop playback.

### Status & Info

#### `tv_status() → dict`
Current TV state.

```json
{
  "platform": "lg",
  "current_app": "netflix",
  "volume": 20,
  "muted": false,
  "sound_output": "tv_speaker"
}
```

#### `tv_info() → dict`
System info.

```json
{
  "platform": "lg",
  "model": "OLED55C3",
  "firmware": "04.30.04",
  "ip": "192.168.1.100",
  "name": "Living Room TV"
}
```

### Notifications

#### `tv_notify(message: str) → str`
Show a toast notification on screen.

### Screen

#### `tv_screen_off() → str`
Turn off the screen while keeping audio playing.

#### `tv_screen_on() → str`
Turn the screen back on.

### Content Resolution & Playback

#### `tv_resolve(platform: str, query: str, season: int | None = None, episode: int | None = None, title_id: int | None = None) → str`
Resolve content to a platform-specific ID without playing it.

| Parameter | Description |
|---|---|
| `platform` | `netflix`, `youtube`, or `spotify` |
| `query` | Content name |
| `season` | Season number (Netflix TV shows) |
| `episode` | Episode number (Netflix TV shows) |
| `title_id` | Netflix title ID — skips web search |

Returns the content ID string (e.g. `"82656797"` for Netflix, `"dQw4w9WgXcQ"` for YouTube).

#### `tv_play_content(platform: str, query: str, season: int | None = None, episode: int | None = None, title_id: int | None = None) → str`
Resolve and play in one step. For Netflix, closes the app first automatically.
Records the play to history.

Same parameters as `tv_resolve`.

### History

#### `tv_history(limit: int = 10) → list[dict]`
Return recent play history. Each entry contains:

```json
{
  "platform": "netflix",
  "query": "Frieren",
  "content_id": "82656797",
  "time": 1743700000,
  "season": 2,
  "episode": 8
}
```

`season` and `episode` are only present for Netflix TV shows.

#### `tv_next(query: str | None = None) → str`
Play the next episode of a Netflix show from history. If `query` is omitted,
continues the most recently watched Netflix show.

---

## Config File Reference

**Location:** `~/.config/smartest-tv/config.toml`

```toml
# Created by stv setup
[tv]
platform = "lg"        # lg | samsung | android | firetv | roku
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, for Wake-on-LAN
name = "Living Room"        # optional, display name
```

**Environment variable overrides** (take precedence over config file):

| Variable | Config key |
|---|---|
| `TV_PLATFORM` | `tv.platform` |
| `TV_IP` | `tv.ip` |
| `TV_MAC` | `tv.mac` |
| `STV_CONFIG_DIR` | Config directory path |

---

## Cache File Reference

**Location:** `~/.config/smartest-tv/cache.json`

```json
{
  "netflix": {
    "frieren": {
      "title_id": 81726714,
      "seasons": {
        "1": {"first_episode_id": 81726716, "episode_count": 10},
        "2": {"first_episode_id": 82656790, "episode_count": 10}
      }
    }
  },
  "youtube": {
    "baby-shark": "XqZsoesa55w"
  },
  "spotify": {
    "ye-white-lines": "spotify:track:3bbjDFVu9BtFtGD2fZpVfz"
  },
  "_history": [
    {
      "platform": "netflix",
      "query": "Frieren",
      "content_id": "82656797",
      "time": 1743700000,
      "season": 2,
      "episode": 8
    }
  ]
}
```

Cache keys are slugified versions of the query: lowercase, spaces replaced
with hyphens, special characters stripped.
