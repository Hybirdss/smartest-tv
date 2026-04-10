# smartest-tv

CLI + MCP server for controlling smart TVs with natural language. Play, cast, queue, recommend, scene presets, multi-TV sync, remote party mode. Deep links into Netflix, YouTube, Spotify.

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: Click
- **MCP**: FastMCP (18 tools)
- **Build**: Hatchling
- **Tests**: pytest (270+ tests, no TV required)
- **TV drivers**: bscpylgtv (LG), samsungtvws (Samsung), adb-shell (Android), aiohttp (Roku), RemoteDriver (HTTP)

## Commands

```bash
# Install
pip install -e ".[lg]"

# Setup
stv setup                                    # Auto-discover + pair
stv setup --ip 192.168.1.100                 # Direct IP

# Play content
stv play netflix "Stranger Things" s4e7      # Series episode
stv play netflix "Glass Onion"               # Movie
stv play youtube "baby shark"                # YouTube
stv play spotify "Ye White Lines"            # Spotify

# Cast URLs
stv cast https://youtube.com/watch?v=...     # Any Netflix/YouTube/Spotify URL

# Queue
stv queue add youtube "Gangnam Style"
stv queue play                               # Play in order

# Trending + Recommend
stv whats-on netflix                         # What's popular
stv recommend --mood chill                   # Based on history

# Scenes
stv scene movie-night                        # Preset: volume + mode
stv scene list                               # All scenes

# Continue watching
stv next                                     # Next episode
stv history                                  # Recent plays

# Multi-TV
stv play netflix "Dark" --tv bedroom         # Target specific TV
stv multi list                               # All TVs
stv multi add friend --platform remote --url http://friend:8911

# Sync / Party
stv --all play youtube "lo-fi beats"         # Every TV at once
stv --group party play netflix "Wednesday" s1e1  # Named group
stv group create party living-room friend    # Mix local + remote

# TV control
stv status / stv volume 25 / stv mute / stv off
stv notify "Dinner's ready"
stv --all off                                # Good night, all TVs

# MCP server
python -m smartest_tv                        # stdio (Claude Code)
stv serve --port 8910                        # MCP :8910 + REST API :8911

# Build + publish
python -m build && twine upload dist/*
```

## Project Structure

```
src/smartest_tv/
  cli.py          — Click CLI (30+ commands, --all/--group sync support)
  server.py       — FastMCP server (18 MCP tools)
  resolve.py      — Public resolver wrapper (cache → _engine → API fallback)
  cache.py        — Local cache + play history + queue + API client
  sync.py         — Concurrent multi-TV broadcast engine (asyncio.gather)
  api.py          — REST API server for remote TV control (party mode)
  scenes.py       — Scene preset system (built-in + custom)
  config.py       — TOML config (single + multi-TV + groups)
  apps.py         — App name → platform-specific ID mapping
  discovery.py    — SSDP network discovery (LG/Samsung/Roku/Android)
  setup.py        — Interactive setup wizard
  drivers/
    base.py       — TVDriver ABC (22 methods)
    factory.py    — Driver factory (create_driver(), used by CLI + MCP + scenes)
    lg.py         — Wrapper → _engine/drivers/lg.py
    samsung.py    — Wrapper → _engine/drivers/samsung.py
    android.py    — Wrapper → _engine/drivers/android.py
    roku.py       — Wrapper → _engine/drivers/roku.py
    remote.py     — Remote TV via friend's stv REST API (HTTP)
  _engine/        — Resolution logic + driver implementations (open source)
skills/tv/        — AI agent skill (Markdown, ClawHub-compatible)
custom_components/smartest_tv/ — Home Assistant HACS integration (media_player entity)
tests/            — 253 unit tests (pytest, no TV required)
docs/
  getting-started/  — Installation, first TV setup
  guides/           — Playing, scenes, multi-TV, AI agents, recommendations
  reference/        — CLI reference, MCP tools, config format, cache format
  integrations/     — OpenClaw, Home Assistant
  contributing/     — Cache contributions, driver development
  i18n/             — 7 language README translations
```

## Key Architecture

### Content Resolution (resolve.py + _engine/)

Public `resolve.py` is a thin wrapper: cache → _engine (local) → API fallback.
`_engine/resolve.py` contains the actual resolution logic (JustWatch, Netflix HTML parsing, etc.).

Resolution chain: local cache → API single-entry → community cache → web resolution.

### Scenes (scenes.py)

Built-in presets: movie-night, kids, sleep, music. Each scene is a sequence of steps (volume, notify, play, screen_off, webhook). Custom scenes stored in `~/.config/smartest-tv/scenes.json`.

### Queue (cache.py)

Play queue stored in `~/.config/smartest-tv/queue.json`. FIFO: add → show → play (pop + resolve + launch) → skip → clear.

### Multi-TV + Groups + Remote (config.py)

```toml
[tv.living-room]
platform = "lg"
ip = "192.168.1.100"
default = true

[tv.bedroom]
platform = "samsung"
ip = "192.168.1.101"

[tv.friend]
platform = "remote"
url = "http://203.0.113.50:8911"

[groups]
home = ["living-room", "bedroom"]
party = ["living-room", "bedroom", "friend"]
```

Legacy single-TV config (`[tv]` with `platform` key directly) auto-detected and supported.

### Sync / Party Mode (sync.py + api.py + drivers/remote.py)

`--all`/`--group` resolves content ID once, then launches on all target TVs via `asyncio.gather`. Partial failures don't stop the rest.

Remote TVs: `stv serve` runs MCP + REST API (port+1). RemoteDriver sends HTTP POST to friend's API, which uses their local driver. The RemoteDriver implements the full TVDriver interface so local/remote TVs are interchangeable in groups.

### Deep Linking (drivers/_engine)

Each driver (in `_engine/drivers/`) translates a content ID into the platform's native deep link format. The public `drivers/` directory contains thin wrappers that import from `_engine`.

### Driver Factory (drivers/factory.py)

`create_driver(tv_name=None)` creates the right driver from config. Used by cli.py, server.py, scenes.py. Never calls sys.exit().

## Key Decisions

- Config: TOML (stdlib 3.11+). Cache/queue/scenes: JSON
- Skills: single Markdown file, ClawHub-compatible frontmatter
- Driver factory pattern to avoid cli.py dependency in scenes/server
- Remote API: stdlib http.server (no new dependency), separate port from MCP
- `_engine/` — resolution and driver logic, fully open source

## Testing

```bash
# Unit tests (no TV, no network)
python -m pytest tests/ -v                   # 270+ tests

# Manual smoke tests
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv whats-on netflix
stv recommend --mood chill
stv scene list
stv queue add youtube "test" && stv queue show && stv queue clear

# Remote MCP + API smoke test
stv serve --port 8910 &
curl http://127.0.0.1:8910/sse     # MCP SSE stream
curl http://127.0.0.1:8911/api/ping # REST API health check
kill %1

# Group management
stv group create test living-room bedroom
stv group list
stv group delete test
```

## PyPI + Registry

- PyPI: `stv` at https://pypi.org/project/stv/
- MCP Registry: `io.github.Hybirdss/smartest-tv`
- ClawHub: `clawhub install smartest-tv`
