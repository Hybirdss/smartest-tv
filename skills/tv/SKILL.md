---
name: smartest-tv
description: "Control a smart TV with natural language. Play Netflix episodes/movies, YouTube videos, Spotify music. Also handles volume, power, notifications, history, 'continue watching', scenes, recommendations, cast URLs, queue, and multi-TV management. Triggers on: 'play', 'watch', 'TV', 'Netflix', 'YouTube', 'Spotify', 'volume', 'mute', 'good night', 'movie night', 'continue', 'next episode', 'scene', 'recommend', 'trending', 'cast', 'queue'."
version: 0.7.0
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

Control a smart TV via the `stv` CLI. Pick the right command based on what the user wants.

## Decision Tree

Use this to pick the right action:

```
User wants to...
├── Watch something specific → stv play
├── Watch a URL someone shared → stv cast <URL>
├── Continue what they were watching → stv next
├── Know what's popular → stv whats-on
├── Get a suggestion → stv recommend
├── Set a mood → stv scene
├── Build a playlist → stv queue add, then stv queue play
├── Control the TV → stv volume / stv mute / stv on / stv off
├── Send a message to the screen → stv notify
├── Use a different TV → add --tv <name> to any command
├── Play on ALL TVs → add --all to play/off/volume/mute/notify
├── Play on a GROUP of TVs → add --group <name> to play/off/volume/mute/notify
├── Watch with friends (remote) → tv_sync (MCP) or --group with remote TVs
├── Show something on TV screen → stv display (message, clock, dashboard, URL)
├── Play music everywhere → stv audio play (screens off, multi-room)
├── Check viewing habits → stv insights (weekly report, screen time)
├── Is my Netflix worth it? → stv sub-value netflix --cost 17.99
└── Don't know what to do → stv whats-on, then stv recommend
```

## Platform Detection

The user rarely says "netflix" or "youtube". Infer it:

| User says | Platform | Why |
|-----------|----------|-----|
| "Play Stranger Things S4E7" | netflix | Series with season/episode |
| "Play Glass Onion" | netflix | Movie title |
| "Play that cooking video" | youtube | General video content |
| "Play baby shark" | youtube | Kids content, music video |
| "Play Ye White Lines" | spotify | Song/artist name |
| "Play my chill playlist" | spotify | Playlist / music genre |
| "Play lofi hip hop radio" | youtube | Live stream / radio |

When ambiguous: Netflix (series/movies) > YouTube (videos) > Spotify (music).

## Core Commands

### Play something specific

```bash
stv play netflix "Stranger Things" s4e7   # series episode
stv play netflix "Glass Onion"            # movie (auto title ID)
stv play youtube "baby shark"             # YouTube video
stv play spotify "Ye White Lines"         # Spotify track
```

### Cast a URL

User shares a link? Cast it directly. No need to figure out the platform or ID.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu...
```

### Continue watching

"Next episode", "keep watching", "where was I" → use `stv next`.

```bash
stv next                          # most recent show
stv next "Breaking Bad"           # specific show
stv history                       # what they've been watching
```

### What's trending

"What should I watch?", "what's popular?", "anything good on?" → start with whats-on.

```bash
stv whats-on                      # Netflix + YouTube trending
stv whats-on netflix              # Netflix only
stv whats-on youtube              # YouTube only
```

### Recommend based on history

"Recommend something", "I'm bored", "suggest a movie" → use recommend.

```bash
stv recommend                     # based on watch history
stv recommend --mood chill        # relaxing content
stv recommend --mood action       # thriller/action
stv recommend --mood kids         # family-friendly
```

After recommending, ask "want me to play any of these?" and use `stv play` on their choice.

### Scene presets

"Movie night", "kids mode", "sleep mode", "music mode" → use scenes.

```bash
stv scene movie-night             # volume 20 + cinema vibe
stv scene kids                    # volume 15 + Cocomelon
stv scene sleep                   # ambient sounds + auto-off
stv scene music                   # screen off + music
stv scene list                    # all available scenes
stv scene create date-night       # make a custom scene
```

### Play queue (party mode)

Multiple people want to add songs/videos? Use the queue.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night"
stv queue show                    # see the list
stv queue play                    # start playing
stv queue skip                    # next in queue
stv queue clear                   # reset
```

### Multi-TV

"Play on bedroom TV", "turn off the kitchen TV" → use --tv flag.

```bash
stv multi list                    # see all TVs
stv play netflix "Dark" --tv bedroom
stv off --tv kids-room
stv scene kids --tv kids-room
```

### Sync / Party mode

"Play on all TVs", "play in every room", "watch with friends" → use --all or --group.

```bash
stv --all play youtube "lo-fi beats"             # every TV in the house
stv --group party play netflix "Wednesday" s1e1   # group of TVs
stv --all volume 20                               # same volume everywhere
stv --all off                                     # good night, all TVs
stv --group home notify "Dinner's ready!"        # toast on group
```

For AI agents (MCP), use `tv_sync_play` to play on multiple TVs at once:

```
tv_sync_play(platform="netflix", query="Squid Game", season=2, episode=3, group="watch-party")
```

**Remote TVs:** Friends run `stv serve`, you add them as `--platform remote`. Groups can mix local and remote TVs. See [Sync & Party Mode guide](docs/guides/sync-party.md).

### TV control

```bash
stv volume 25                     # set volume
stv mute                          # toggle
stv on / stv off                  # power
stv status                        # what's playing, volume
stv notify "Dinner's ready!"     # toast on screen
```

## Common Scenarios

### "I'm home from work"
1. `stv scene movie-night`
2. `stv recommend --mood chill`
3. User picks one → `stv play netflix "..."` or `stv play youtube "..."`

### "Put something on for the kids"
1. `stv scene kids --tv kids-room`
(scene auto-plays Cocomelon at safe volume)

### "Good night"
1. `stv scene sleep`
(ambient sounds, TV auto-off)

### "Friends are coming over"
1. Everyone: `stv queue add youtube "their song"`
2. `stv queue play`

### "What was I watching?"
1. `stv next` (continues automatically)
Or: `stv history` → show the list → user picks → `stv play`

### "Someone sent me a link"
1. `stv cast <URL>` (auto-detects platform + ID)

### "Watch party with friends"
1. `stv --group watch-party play netflix "Wednesday" s1e1`
Or MCP: `tv_sync_play(platform="netflix", query="Wednesday", season=1, episode=1, group="watch-party")`

### "Play music in every room"
1. `stv --all play youtube "lo-fi hip hop"` or `stv --all play spotify "chill vibes"`

## Setup

If `stv status` fails with "No TV configured":

```bash
stv setup                         # auto-discover + pair
stv setup --ip 192.168.1.100     # direct IP
stv doctor                        # diagnose issues
```

## MCP Tools (21 tools, optimized for AI agents)

| Tool | When to use | Key params |
|------|------------|------------|
| `tv_play` | Play content by name (most common) | `platform`, `query`, `season?`, `episode?`, `tv_name?` |
| `tv_cast` | User shares a URL | `url`, `tv_name?` |
| `tv_next` | "Continue watching", "next episode" | `query?`, `tv_name?` |
| `tv_whats_on` | "What's trending?", "what's popular?" | `platform?`, `limit?` |
| `tv_recommend` | "Suggest something", "I'm bored" | `mood?`, `limit?` |
| `tv_scene` | Scene presets (list or run) | `action: list/run`, `name?`, `tv_name?` |
| `tv_queue` | Play queue (add/show/play/skip/clear) | `action`, `platform?`, `query?`, `tv_name?` |
| `tv_power` | Turn TV on/off | `on: bool`, `tv_name?` |
| `tv_volume` | Get/set volume, step, mute — all in one | `level?`, `direction?`, `mute?`, `tv_name?` |
| `tv_screen` | Screen on/off (audio continues) | `on: bool`, `tv_name?` |
| `tv_status` | Current app, volume, model | `tv_name?` |
| `tv_notify` | Toast notification on screen | `message`, `tv_name?` |
| `tv_launch` | Launch app with known ID | `app`, `content_id?`, `tv_name?` |
| `tv_history` | Recent play history | `limit?` |
| `tv_resolve` | Get content ID without playing | `platform`, `query`, `season?`, `episode?` |
| `tv_sync` | Play on multiple TVs at once | `platform`, `query`, `group?`, `tv_names?` |
| `tv_list_tvs` | Show all configured TVs | |
| `tv_groups` | List TV groups | |
| `tv_insights` | Viewing stats, screen time, sub value | `period?`, `report_type?` |
| `tv_display` | TV as display: dashboards, clocks, messages | `content_type`, `data?`, `tv_name?` |
| `tv_audio` | Multi-room audio, screens off | `action`, `query?`, `platform?`, `rooms?` |

## Notes

- All CLI commands support `--format json` for structured output
- First Netflix resolve: ~2-3s (web fetch). Cached after: ~0.1s
- Netflix profile selection happens on-screen (can't skip)
- If auto-search fails: `stv play netflix "X" --title-id XXXXX`
- `tv_name` is optional on every MCP tool. Omit it to use the default TV

## MCP Configuration

Claude Code (stdio, automatic):
```json
{"mcpServers": {"tv": {"command": "uvx", "args": ["stv"]}}}
```

OpenClaw / other agents:
```json
{"mcpServers": {"tv": {"command": "python3", "args": ["-m", "smartest_tv"], "env": {"TV_PLATFORM": "lg", "TV_IP": "192.168.1.100"}}}}
```

Remote HTTP:
```bash
stv serve --port 8910
# Then connect to http://localhost:8910/sse
```
