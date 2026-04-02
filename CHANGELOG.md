# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.6.0] - 2026-04-03

### Added
- `stv scene`: Preset system with movie-night, kids, sleep, music built-in scenes + custom scene support
- `stv recommend`: AI-powered content recommendations based on watch history (optional Ollama LLM enhancement)
- OpenClaw/ClawHub skill integration (`clawhub install smartest-tv`)
- `docs/` restructured into 3-layer hierarchy (getting-started, guides, reference, integrations, contributing)
- Driver factory pattern (`drivers/factory.py`) for clean driver instantiation

### Fixed
- scenes.py dependency on cli.py's `_get_driver` (now uses `drivers/factory.py`)
- Incorrect `stv screen-off` reference in SKILL.md

## [0.5.0] - 2026-04-03

### Added
- `stv cast <URL>`: Paste Netflix/YouTube/Spotify URLs to play on TV
- `stv queue`: Play queue system (add/show/play/skip/clear)
- `stv whats-on`: Netflix and YouTube trending content
- `stv multi`: Multi-TV management with `--tv` flag on all commands
- 62 new unit tests (55 → 117 total)

### Fixed
- Season 0 (specials) silently dropped in `record_play` (`if season:` → `if season is not None:`)
- TV name TOML injection vulnerability in `config.py`
- Overly broad exception handling in trending fetch

## [0.4.1] - 2026-04-03

### Added
- MCP Registry metadata (`server.json`)
- `mcp-name` comment in README for PyPI ownership verification

## [0.4.0] - 2026-04-03

### Added
- `stv setup`: Interactive TV setup wizard with SSDP multi-platform discovery
- `stv serve`: Remote MCP server mode (SSE/streamable-http)
- 55 unit tests with CI workflow
- Community cache expanded to 40 entries (29 Netflix, 11 YouTube)
- `docs/` folder with setup guide, MCP integration, API reference, contributing guide
- CHANGELOG.md

## [0.3.0] - 2026-04-02

### Added
- `stv search`: Content search without playing
- `stv next`: Continue watching
- `stv history`: Play history
- Community cache system (GitHub raw CDN)
- Web search fallback (Brave Search)
- CLAUDE.md for AI agent context
- PyPI publication (`pip install stv`)

## [0.2.0] - 2026-04-02

### Added
- Netflix content resolution via `__typename` HTML parsing
- YouTube resolution via yt-dlp
- Spotify resolution via web search
- Deep linking for LG, Samsung, Roku, Android TV

## [0.1.0] - 2026-04-01

### Added
- Initial release
- LG webOS driver
- Basic CLI (play, launch, status, volume, off)
