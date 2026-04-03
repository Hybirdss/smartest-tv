# smartest-tv

CLI + MCP server for controlling smart TVs with natural language. Play, cast, queue, recommend, scene presets, multi-TV. Deep links into Netflix, YouTube, Spotify.

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: Click
- **MCP**: FastMCP (32 tools)
- **Build**: Hatchling
- **Tests**: pytest (132 tests, no TV required)
- **TV drivers**: bscpylgtv (LG), samsungtvws (Samsung), adb-shell (Android), aiohttp (Roku)

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

# TV control
stv status / stv volume 25 / stv mute / stv off
stv notify "Dinner's ready"

# MCP server
python -m smartest_tv                        # stdio (Claude Code)
stv serve --port 8910                        # HTTP (Cursor, remote)

# Build + publish
python -m build && twine upload dist/*
```

## Project Structure

```
src/smartest_tv/
  cli.py          — Click CLI (30+ commands)
  server.py       — FastMCP server (32 MCP tools)
  resolve.py      — Content resolver + trending + recommendations
  cache.py        — Local cache + play history + queue
  scenes.py       — Scene preset system (built-in + custom)
  config.py       — TOML config (single + multi-TV)
  apps.py         — App name → platform-specific ID mapping
  discovery.py    — SSDP network discovery (LG/Samsung/Roku/Android)
  setup.py        — Interactive setup wizard
  drivers/
    base.py       — TVDriver ABC (22 methods)
    factory.py    — Driver factory (create_driver(), used by CLI + MCP + scenes)
    lg.py         — LG webOS via bscpylgtv (WebSocket SSAP)
    samsung.py    — Samsung Tizen via samsungtvws
    android.py    — Android TV / Fire TV via ADB TCP
    roku.py       — Roku via HTTP ECP (:8060)
skills/tv/        — AI agent skill (Markdown, ClawHub-compatible)
tests/            — 132 unit tests (pytest, no TV required)
docs/
  getting-started/  — Installation, first TV setup
  guides/           — Playing, scenes, multi-TV, AI agents, recommendations
  reference/        — CLI reference, MCP tools, config format, cache format
  integrations/     — OpenClaw, Home Assistant
  contributing/     — Cache contributions, driver development
  i18n/             — 7 language README translations
```

## Key Architecture

### Content Resolution (resolve.py)

Three-tier: cache → HTTP scrape → web search fallback.

- **Netflix**: curl the title page → parse `__typename:"Episode"` from `<script>` tags → group sequential IDs into seasons. One HTTP request resolves all seasons.
- **YouTube**: yt-dlp `ytsearch1:{query}` → video ID.
- **Spotify**: Brave Search `site:open.spotify.com` → URI.
- **Trending**: Netflix top10 page + YouTube trending via yt-dlp. 24h/1h cache.
- **Recommend**: History analysis + trending interleave + optional LLM (STV_LLM_URL).

### Scenes (scenes.py)

Built-in presets: movie-night, kids, sleep, music. Each scene is a sequence of steps (volume, notify, play, screen_off, webhook). Custom scenes stored in `~/.config/smartest-tv/scenes.json`.

### Queue (cache.py)

Play queue stored in `~/.config/smartest-tv/queue.json`. FIFO: add → show → play (pop + resolve + launch) → skip → clear.

### Multi-TV (config.py)

```toml
[tv.living-room]
platform = "lg"
ip = "192.168.1.100"
default = true

[tv.bedroom]
platform = "samsung"
ip = "192.168.1.101"
```

Legacy single-TV config (`[tv]` with `platform` key directly) auto-detected and supported.

### Deep Linking

Each driver translates a content ID into the platform's native format:
- LG: SSAP WebSocket (`launch_app_with_content_id` / `launch_app_with_params`)
- Samsung: WebSocket `run_app("DEEP_LINK", meta_tag)`
- Android: ADB `am start -d 'netflix://title/{id}'`
- Roku: HTTP `POST /launch/{ch}?contentId={id}`

Netflix requires close → relaunch for deep links. `stv play` handles this automatically.

### Driver Factory (drivers/factory.py)

`create_driver(tv_name=None)` creates the right driver from config. Used by cli.py (wraps with ClickException), server.py (wraps with MCP error), and scenes.py (direct). Never calls sys.exit().

## Key Decisions

- No Playwright — Netflix scraping via curl + `__typename` parsing
- Brave Search primary (DuckDuckGo rate-limits)
- Netflix episode IDs are sequential — find first, calculate rest
- `close_app` 403 on some webOS → fallback to home screen launch
- Config: TOML (stdlib 3.11+). Cache/queue/scenes: JSON
- Skills: single Markdown file, ClawHub-compatible frontmatter
- Driver factory pattern to avoid cli.py dependency in scenes/server

## Testing

```bash
# Unit tests (no TV, no network)
python -m pytest tests/ -v                   # 132 tests

# Manual smoke tests
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv whats-on netflix
stv recommend --mood chill
stv scene list
stv queue add youtube "test" && stv queue show && stv queue clear

# Remote MCP smoke test
stv serve --port 8910 &
curl http://127.0.0.1:8910/sse
kill %1
```

## PyPI + Registry

- PyPI: `stv` at https://pypi.org/project/stv/
- MCP Registry: `io.github.Hybirdss/smartest-tv`
- ClawHub: `clawhub install smartest-tv`
