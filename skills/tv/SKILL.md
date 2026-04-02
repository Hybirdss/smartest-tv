---
name: tv
description: "Control a smart TV with natural language. Play Netflix episodes/movies, YouTube videos, Spotify music. Also handles volume, power, notifications, history, 'continue watching', scenes, recommendations, cast URLs, queue, and multi-TV management. Triggers on: 'play', 'watch', '틀어줘', '재생', 'TV', 'Netflix', 'YouTube', 'Spotify', 'volume', 'mute', 'good night', 'movie night', '이어서', 'continue', 'next episode', 'scene', 'recommend', 'what's on', 'cast'."
version: 0.6.0
metadata:
  openclaw:
    requires:
      env:
        - TV_PLATFORM
        - TV_IP
      bins:
        - python3
        - stv
      anyBins: []
      config: []
    primaryEnv: TV_IP
    emoji: "📺"
    homepage: https://github.com/Hybirdss/smartest-tv
    os: [macos, linux]
    install:
      - kind: uv
        package: stv
        bins: [stv]
---

# smartest-tv

Control a smart TV via the `stv` CLI. One command per action.

## Platform Detection

The user won't always say the platform. Infer it:

| User says | Platform | Why |
|-----------|----------|-----|
| "Play Frieren S2E8" | **netflix** | TV series with season/episode |
| "Play Inception" | **netflix** | Movie title |
| "Play baby shark" | **youtube** | Kids content, music video, general video |
| "Play Ye White Lines" | **spotify** | Song/artist name + music context |
| "Play jazz playlist" | **spotify** | Playlist/music genre |
| "Play lofi hip hop radio" | **youtube** | Live stream / radio |

When ambiguous, prefer: Netflix (series/movies) > YouTube (videos) > Spotify (music).

## Play Content

```bash
stv play netflix "Frieren" s2e8          # Netflix episode
stv play netflix "Inception"             # Netflix movie (auto title ID)
stv play youtube "baby shark"            # YouTube video
stv play spotify "Ye White Lines"        # Spotify track
```

Everything is automatic: search → resolve → cache → deep link → launch.

## Continue Watching / Next Episode

```bash
stv next                    # Continue the most recent Netflix show
stv next Frieren            # Next episode of Frieren specifically
stv history                 # Show recent plays
```

"이어서 봐", "다음 화", "continue watching" → use `stv next`.

## Search & Resolve

```bash
stv search netflix "Jujutsu Kaisen"   # Title ID + all seasons
stv resolve netflix "Frieren" s2e8    # → 82656797
```

## TV Control

```bash
stv status       # Current app, volume, mute
stv volume 25    # Set volume
stv mute         # Toggle mute
stv on / off     # Power
stv notify "msg" # Toast on screen
```

## Composite Workflows

**Movie night**: `stv volume 20 && stv play netflix "Inception"`

**Kids mode**: `stv volume 15 && stv play youtube "cocomelon"`

**Music mode**: `stv scene run music`

**Sleep timer**: `(sleep 2700 && stv off) &`

**Good night**: `stv off`

## Scene Presets

```bash
stv scene list                  # Show all scenes (built-in + custom)
stv scene run movie-night       # Dim volume, launch Netflix
stv scene run kids              # Lower volume, launch YouTube
stv scene run sleep             # Start sleep timer
stv scene run music             # Play Spotify, screen off
```

Built-in scenes: `movie-night`, `kids`, `sleep`, `music`. Custom scenes go in `~/.config/smartest-tv/scenes.json`.

## Recommendations

```bash
stv recommend                   # Personalized picks from watch history
stv recommend --mood chill      # Filtered: chill, action, kids, random
```

Combines watch history + trending content. Set `STV_LLM_URL` to enable AI-powered reasons (Ollama).

## What's On (Trending)

```bash
stv whats-on                    # Netflix + YouTube trending
stv whats-on --platform netflix # Netflix only
stv whats-on --platform youtube # YouTube only
```

## Cast a URL

```bash
stv cast https://www.netflix.com/watch/82656797
stv cast https://www.youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

Paste any Netflix / YouTube / Spotify URL — stv extracts the content ID and deep-links directly.

## Play Queue

```bash
stv queue add netflix "Bridgerton" s2e1   # Add to queue
stv queue show                            # View queue
stv queue play                            # Play next item
stv queue skip                            # Skip current
stv queue clear                           # Clear all
```

## Multi-TV Management

```bash
stv multi list                  # Show all configured TVs
stv multi add living-room lg 192.168.1.100 --default
stv multi remove bedroom
stv multi default living-room

stv --tv bedroom volume 20      # Target a specific TV with any command
stv --tv living-room play netflix "Frieren" s2e8
```

## Setup

If `stv status` fails with "No TV configured":

```bash
stv setup              # Auto-discover TV on network + pair
stv setup --ip X.X.X.X # Skip discovery, connect directly
stv doctor             # Diagnose connection issues
```

## Remote MCP (HTTP mode)

For web-based MCP clients (Cursor, VS Code, etc.) that need a URL instead of a command:

```bash
stv serve                                    # SSE on http://127.0.0.1:8910/sse
stv serve --host 0.0.0.0 --port 9000         # Expose on all interfaces
stv serve --transport streamable-http        # streamable-http on /mcp
```

Claude Code uses stdio mode automatically (`uvx stv`). Only use `stv serve` for HTTP clients.

## MCP Tools (for AI agents using stdio/HTTP mode)

| Tool | What it does |
|------|-------------|
| `tv_on` / `tv_off` | Power on/off |
| `tv_volume` / `tv_set_volume` | Get / set volume |
| `tv_volume_up` / `tv_volume_down` | Step volume |
| `tv_mute` | Mute / unmute / toggle |
| `tv_launch` | Launch app with optional deep link |
| `tv_close` | Close a running app |
| `tv_apps` | List installed apps |
| `tv_play` / `tv_pause` / `tv_stop` | Media playback controls |
| `tv_status` | Current app, volume, mute |
| `tv_info` | Model, firmware, IP |
| `tv_notify` | Toast notification on screen |
| `tv_screen_off` / `tv_screen_on` | Screen only (audio continues) |
| `tv_cast` | Cast a Netflix/YouTube/Spotify URL |
| `tv_resolve` | Resolve content name → ID (no playback) |
| `tv_play_content` | Resolve + play in one step |
| `tv_history` | Recent play history |
| `tv_whats_on` | Trending content (Netflix/YouTube) |
| `tv_queue_add` / `tv_queue_show` / `tv_queue_play` / `tv_queue_clear` | Play queue |
| `tv_next` | Play next Netflix episode |
| `tv_recommend` | Personalized recommendations |
| `tv_list_tvs` | List all configured TVs |
| `tv_scene_list` / `tv_scene_run` | Scene presets |

## Notes

- All commands support `--format json`
- First Netflix play: ~2-3s (web search). After that: ~0.1s (cached)
- Netflix profile selection happens on TV (can't skip)
- If auto-search fails: `stv play netflix "X" --title-id XXXXX`

## OpenClaw MCP Configuration

Add to your OpenClaw MCP config:

```json
{
  "mcpServers": {
    "tv": {
      "command": "python3",
      "args": ["-m", "smartest_tv"],
      "env": {
        "TV_PLATFORM": "lg",
        "TV_IP": "192.168.1.100"
      }
    }
  }
}
```

Or use `uvx` to run without a local install:

```json
{
  "mcpServers": {
    "tv": {
      "command": "uvx",
      "args": ["stv"]
    }
  }
}
```
