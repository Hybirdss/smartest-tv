# smartest-tv

CLI + MCP server for controlling smart TVs with natural language. Deep links into Netflix, YouTube, Spotify.

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: Click
- **MCP**: FastMCP
- **Build**: Hatchling
- **TV drivers**: bscpylgtv (LG), samsungtvws (Samsung), adb-shell (Android), aiohttp (Roku)

## Commands

```bash
# Install (editable, LG driver)
pip install -e ".[lg]"

# CLI
stv setup                                    # First-time TV setup
stv status                                   # TV state
stv play netflix "Frieren" s2e8              # Find + play (auto title ID)
stv play youtube "baby shark"                # Search + play
stv play spotify "Ye White Lines"            # Search + play
stv resolve netflix "Jujutsu Kaisen" s3e10   # Just get the content ID
stv cache show                               # View cached IDs
stv launch netflix 82656797                  # Direct deep link (known ID)

# MCP server
python -m smartest_tv.server

# Build + publish
uvx --from build pyproject-build
uvx twine upload dist/*
```

## Project Structure

```
src/smartest_tv/
  cli.py          — Click CLI (stv command)
  server.py       — FastMCP server (20 MCP tools)
  resolve.py      — Content ID resolver (Netflix/YouTube/Spotify)
  cache.py        — Local JSON cache (~/.config/smartest-tv/cache.json)
  config.py       — TOML config (~/.config/smartest-tv/config.toml)
  apps.py         — App name → platform-specific ID mapping
  discovery.py    — SSDP network discovery
  setup.py        — Interactive setup wizard
  drivers/
    base.py       — TVDriver ABC (22 methods)
    lg.py         — LG webOS via bscpylgtv (WebSocket SSAP)
    samsung.py    — Samsung Tizen via samsungtvws
    android.py    — Android TV / Fire TV via ADB TCP
    roku.py       — Roku via HTTP ECP (:8060)
skills/tv/        — Single unified AI agent skill (Markdown)
docs/i18n/        — 7 language README translations
```

## Key Architecture

### Content Resolution (resolve.py)

Three-tier: cache → HTTP scrape → web search fallback.

- **Netflix**: curl the title page → parse `__typename:"Episode"` from `<script>` tags → group sequential IDs into seasons. Brave Search fallback for title ID discovery. All seasons resolved in one HTTP request.
- **YouTube**: yt-dlp `ytsearch1:{query}` → video ID.
- **Spotify**: Brave Search `site:open.spotify.com` → URI.

All results cached in `~/.config/smartest-tv/cache.json`. Repeat plays are instant (0.1s).

### Deep Linking

Each driver translates a content ID into the platform's native format:
- LG: SSAP WebSocket (`launch_app_with_content_id` / `launch_app_with_params`)
- Samsung: WebSocket `run_app("DEEP_LINK", meta_tag)`
- Android: ADB `am start -d 'netflix://title/{id}'`
- Roku: HTTP `POST /launch/{ch}?contentId={id}`

Netflix requires close → relaunch for deep links. `stv play` handles this automatically.

### Cache Format

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
  "youtube": {"baby-shark": "XqZsoesa55w"},
  "spotify": {"ye-white-lines": "spotify:track:3bbjDFVu9BtFtGD2fZpVfz"}
}
```

## Key Decisions

- No Playwright dependency — Netflix scraping works via curl + `__typename` parsing
- DuckDuckGo was unreliable (rate limits) — switched to Brave Search with DDG fallback
- Netflix episode IDs are sequential — find first ID, calculate the rest
- `close_app` returns 403 on some webOS firmware → fallback to home screen launch
- Config uses TOML (stdlib in 3.11+), cache uses JSON
- Skills are plain Markdown — portable to any AI agent

## Testing

```bash
# Resolve tests (no TV needed)
stv resolve netflix "Frieren" s2e8
stv resolve youtube "baby shark"
stv resolve spotify "Ye White Lines"

# TV tests (requires LG TV on network)
stv status
stv play netflix "Frieren" s2e8
```

## PyPI

Package name: `stv`. Published at https://pypi.org/project/stv/
