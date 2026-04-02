# Changelog

## [0.4.0] - 2026-04-03

### Added

- **`stv setup` wizard** — zero-config first-time setup. Auto-discovers LG, Samsung, Roku, and Android/Fire TV on the local network via SSDP + ADB port scan. Detects platform, pairs, saves config, sends a test notification, and detects installed AI clients (Claude Code, Cursor) — all in one command. `--ip` flag skips discovery for manual IP entry.
- **`stv serve` remote MCP server** — run stv as an HTTP MCP server (`stv serve --host 0.0.0.0 --port 8910`). Supports both `sse` and `streamable-http` transports, enabling remote AI agent access over the network.
- **Multi-platform SSDP discovery** — `discovery.py` now searches for LG (`urn:lge-com:service:webos-second-screen:1`), Samsung (`urn:samsung.com:device:RemoteControlReceiver:1`), and Roku (`roku:ecp`) simultaneously. Android/Fire TV discovered via ADB port 5555 scan.
- **Unit tests** — `pytest` test suite covering `resolve`, `cache`, and CLI commands.
- **Community cache expansion** — `community-cache.json` seeded with 50+ popular Netflix shows.
- **`docs/` folder** — structured documentation: setup guide, MCP integration guide, demo script, and i18n README files.

### Changed

- `discovery.py` timeout reduced from 5s to 3s for faster setup UX.
- `setup.py` `_detect_platform()` consolidated into `discovery.py` `_extract_name()`.

## [0.3.0] - 2026-04-03

### Added

- `stv next` — play the next episode of a Netflix show using play history.
- `stv history` — show recent play history.
- `stv cache contribute` — export local cache as community-cache.json format for sharing.
- Community cache (`community-cache.json`) — pre-resolved content IDs contributed by users.
- 7-language README translations (ko, zh, ja, es, de, pt-br, fr).
- Agent skill (`skills/tv/`) — single unified Markdown skill for AI assistants.

### Changed

- Netflix resolution: switched from DuckDuckGo (rate-limited) to Brave Search with DDG fallback.
- `stv play` now records to history automatically.

## [0.2.0]

### Added

- Samsung Tizen driver (`samsungtvws`).
- Android TV / Fire TV driver (`adb-shell`).
- Roku driver (HTTP ECP).
- `stv doctor` — connection diagnostics.
- `stv cache set/get/show` — manual cache management.

## [0.1.0]

### Added

- Initial release. LG webOS driver via `bscpylgtv`.
- `stv play`, `stv resolve`, `stv launch`, `stv status`, `stv volume`, `stv mute`, `stv off`.
- Netflix deep link resolver (curl + `__typename` parsing, no Playwright).
- YouTube resolver via `yt-dlp`.
- Spotify resolver via Brave Search.
- FastMCP server (`stv` as MCP tool provider).
- TOML config (`~/.config/smartest-tv/config.toml`).
- JSON cache (`~/.config/smartest-tv/cache.json`).
