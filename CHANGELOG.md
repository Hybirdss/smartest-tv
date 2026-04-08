# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.9.0] - 2026-04-09

### Added
- **Rich-powered UI across every command** — 56 CLI commands now render with
  Catppuccin Mocha theme, semantic colors, volume bars, app icons, tables, and
  health-check trees. Every screen looks like a product, not a debug log.
- `smartest_tv.ui` package with theme system, semantic icons, and 24 render
  functions (one per page). Pure rendering — zero driver dependencies.
- Three built-in themes: `mocha` (default), `nord`, `gruvbox`. Switch with
  `STV_THEME=nord`.
- App ID → human name mapping (50+ apps): `com.frograms.watchaplay.webos` now
  displays as `Watcha`, `com.webos.app.netflix` as `Netflix`, etc.
- Portfolio screenshots in `docs/assets/screenshots/` (SVG + PNG, 10 pages).
- `STV_NO_COLOR=1` env var to force monochrome output for CI/tests.
- Added `rich>=13.7.0` as a dependency.

### Changed
- `stv status` now shows a Now Playing panel with volume bar, app icon, power
  state, and sound output — instead of a 5-line debug dump.
- `stv multi list` → TV inventory table with default-TV star, platform badges,
  and MAC addresses.
- `stv scene list` → scene grid with step-by-step action icons.
- `stv doctor` → hierarchical health-check tree with ok/warn/fail colored nodes.
- `stv whats-on` → Netflix Top 10 + YouTube Trending tables with view counts.
- `stv insights` → weekly report panel with platform bar chart, top shows,
  peak hour, binge sessions, watch streak.
- `stv history`, `stv queue`, `stv recommend`, `stv sub-value`, `stv apps`,
  `stv cache show`, `stv license status` — all upgraded to Rich panels/tables.
- `stv --all <cmd>` broadcast results now render as a unified panel with an
  `ok_count/total` footer instead of one line per TV.
- Error messages are now bordered panels with optional hints.

### Preserved
- `--format json` still outputs plain JSON with zero Rich markup — pipelines
  and scripts continue to work unchanged.
- All 211 existing tests pass; added 1 new test for JSON-format broadcast
  preservation (212 total).

## [0.8.0] - 2026-04-03

### Added
- Content Resolution API integration: cache lookups now query the hosted API for faster resolution
- Automatic cache contribution: new resolutions are shared back to the API (background, non-blocking)
- Per-entry API lookup (`GET /v1/cache/:platform/:slug`) for faster single-content resolution
- Graceful fallback chain: local → API single → API full → GitHub static → web scrape

### Changed
- RemoteDriver methods now properly async via `asyncio.to_thread` (no longer blocking the event loop)
- Cache module uses `smartest_tv.http.curl` helper instead of raw `subprocess.run`

### Security
- Contributor writes go to a pending queue (not live cache) and require admin approval or 2+ IP consensus
- API write validation: platform whitelist, data shape checks, slug format enforcement
- Rate limiting: 30/hour per IP + 500/hour global cap on contributor writes

## [0.7.0] - 2026-04-03

### Added
- Sync & party mode: `--all` and `--group` flags for multi-TV simultaneous playback
- Remote TV support: `stv serve` exposes REST API, `RemoteDriver` controls friend's TV over HTTP
- TV groups: `stv group create party living-room bedroom friend`
- `stv sync` MCP tool for AI agents to play on multiple TVs at once

### Changed
- MCP tools optimized: 34 → 18 tools (consolidated volume/power/screen/queue/scene into single tools)
- `api.py` uses `drivers/factory.py` instead of inline driver creation
- `cli.py` `_broadcast_action` uses `sync.py` helpers (broadcast/connect_all)
- docs/reference/mcp-tools.md rewritten for 18-tool architecture
- All i18n READMEs updated with sync party, 18 tools, 169 tests

### Fixed
- CLAUDE.md referenced 34 MCP tools instead of 18

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
