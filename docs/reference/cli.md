# CLI Reference

Complete reference for all `stv` commands.

Run `stv --help` or `stv <command> --help` for inline help.

## Global Options

| Option | Default | Description |
|--------|---------|-------------|
| `--format [text\|json]` | `text` | Output format for commands that return data |
| `--tv NAME` | primary | Target TV name (for multi-TV setups) |

---

## Setup & Diagnostics

### `stv setup [--ip IP]`

Interactive wizard. Discovers TVs on the network (SSDP), handles pairing, and writes
`~/.config/smartest-tv/config.toml`.

```bash
stv setup                    # auto-discovery
stv setup --ip 192.168.1.100 # direct IP, skip discovery
```

### `stv doctor`

Checks connectivity, queries TV status, and verifies Netflix/YouTube/Spotify
apps are installed.

### `stv serve`

Start stv as a remote MCP server (HTTP transport).

```bash
stv serve                               # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

---

## Power

### `stv on`

Turn on the TV via Wake-on-LAN (requires `mac` in config).

### `stv off`

Put the TV into standby.

---

## Volume

### `stv volume [LEVEL]`

Get current volume (no argument) or set to `LEVEL` (0–100).

```bash
stv volume         # print current volume + mute state
stv volume 30      # set to 30
```

### `stv mute`

Toggle mute on/off.

---

## Apps

### `stv launch APP [CONTENT_ID]`

Launch an app. Pass `CONTENT_ID` for deep linking.

```bash
stv launch netflix
stv launch netflix 82656797      # deep link to episode
stv launch youtube dQw4w9WgXcQ   # deep link to video
```

`APP` accepts friendly names: `netflix`, `youtube`, `spotify`, `disney`,
`prime`, `appletv`, `hulu`, `tving`, `wavve`, `coupang`, `browser`,
`hdmi1`, `hdmi2`.

### `stv close APP`

Close a running app.

### `stv apps`

List all installed apps (id + name).

---

## Media Playback

### `stv play`

Resume playback (sends Play key).

### `stv pause`

Pause playback (sends Pause key).

---

## Status

### `stv status`

Show current TV state: platform, current app, volume, mute, sound output.

### `stv info`

Show system info: platform, model, firmware, IP, name.

---

## Notifications

### `stv notify MESSAGE`

Show a toast notification on the TV screen.

---

## What's On

### `stv whats-on [PLATFORM] [-n LIMIT]`

Show trending content on Netflix or YouTube.

```bash
stv whats-on
stv whats-on netflix
stv whats-on youtube
stv whats-on netflix -n 5
```

`PLATFORM`: `netflix`, `youtube` (or omit for both)

---

## Content Search

### `stv search PLATFORM QUERY`

Search for content and show what stv found (does not play anything).

```bash
stv search netflix Frieren
stv search spotify "Ye White Lines"
stv search youtube "baby shark"
```

`PLATFORM`: `netflix`, `youtube`, `spotify`

---

## Content Resolution

### `stv resolve PLATFORM QUERY [OPTIONS]`

Resolve a content name to a platform-specific ID without playing it.

```bash
stv resolve netflix Frieren -s 2 -e 8
stv resolve netflix Frieren s2e8            # inline S/E notation
stv resolve youtube "baby shark"
stv resolve netflix "The Glory" --title-id 81519223 -s 1 -e 1
```

**Options:**

| Option | Description |
|--------|-------------|
| `-s, --season INT` | Season number (Netflix) |
| `-e, --episode INT` | Episode number (Netflix) |
| `--title-id INT` | Netflix title ID — skips web search |

**Inline S/E notation** — append to the query as the last argument:

| Format | Example | Result |
|--------|---------|--------|
| `sNeM` | `s2e8` | season=2, episode=8 |
| `SNNEM` (zero-padded) | `S02E08` | season=2, episode=8 |
| `NxM` | `2x8` | season=2, episode=8 |

---

## Play Content

### `stv play PLATFORM QUERY [OPTIONS]`

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

---

## Cast

### `stv cast URL`

Cast a streaming URL to the TV. Accepts Netflix, YouTube, and Spotify links.

```bash
stv cast https://www.netflix.com/watch/82656797
stv cast https://www.netflix.com/title/81726714
stv cast https://www.youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://youtu.be/dQw4w9WgXcQ
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

Netflix `/title/` URLs are resolved to an episode ID automatically.

---

## History

### `stv history [-n LIMIT]`

Show recent play history. Default limit: 10.

```bash
stv history
stv history -n 5
```

### `stv next [QUERY]`

Play the next episode of a Netflix show based on history.

```bash
stv next Frieren    # next episode after last watched Frieren
stv next            # continues most recently watched Netflix show
```

---

## Cache Management

### `stv cache set PLATFORM QUERY [OPTIONS]`

Save a content ID to the local cache manually.

```bash
# Netflix season data
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714

# Direct ID (YouTube/Spotify)
stv cache set youtube "baby shark" --content-id XqZsoesa55w
stv cache set spotify "Ye Vultures" --content-id "spotify:album:xxx"
```

| Option | Description |
|--------|-------------|
| `-s, --season INT` | Season number |
| `--first-ep-id INT` | First episode videoId of the season |
| `--count INT` | Number of episodes in the season |
| `--title-id INT` | Netflix title ID |
| `--content-id STR` | Direct content ID (YouTube/Spotify) |

### `stv cache get PLATFORM QUERY [OPTIONS]`

Look up a cached content ID.

```bash
stv cache get netflix Frieren -s 2 -e 8
stv cache get youtube "baby shark"
```

### `stv cache show`

Print the full contents of the local cache JSON.

### `stv cache contribute`

Print local cache in `community-cache.json` format (history stripped).
Pipe to a file to submit a PR.
