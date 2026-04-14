# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [1.1.0] - 2026-04-14

### Added

- **`tv_state()` MCP tool.** Returns a single structured snapshot of the
  target TV: current app, title, playback position, duration, volume,
  mute, HDMI input, power state, driver, and fetched-at timestamp. Fields
  the driver cannot supply are returned as `None`. Previously 17 of 21
  MCP tools returned only "ok" strings, leaving an agent unable to chain
  "play X" with "verify X actually started."
- **`tv_state_watch(tv_name, interval=5, count=12)` MCP tool.** Streams
  `tv_state` snapshots via FastMCP `Context.report_progress` — default
  one minute of watching (12 × 5 s). Callers chain repeated invocations
  for indefinite watching.
- **Now-playing driver state.** Roku pulls title, position, duration, and
  play state from `/query/media-player` (zero-auth ECP). LG pulls
  `mediaId` and `playState` from `aiowebostv.get_media_foreground_app()`.
  Android switches from polling to push callbacks
  (`add_current_app_updated_callback`,
  `add_volume_info_updated_callback`, `add_is_on_updated_callback`).
  Samsung stays status-only due to library limits.
- **`stv-concierge` Claude Code skill.** `stv setup` now installs a
  natural-language TV control skill into `~/.claude/skills/stv-concierge/`
  when Claude Code is detected. Trigger phrases in English and Korean:
  "play Dark on Netflix", "뭐 보여줘", "볼륨 낮춰", "TV 꺼", "몰아보기".
  Maps directly to `stv play`, `stv whats-on`, `stv volume`, `stv off`.
  No extra config — the skill's `description` field drives Claude Code's
  auto-discovery. Manual install available via `stv-install-skill`.
- **Top-3 disambiguation on `stv play`.** When the auto-resolver finds
  multiple matches (e.g. the 2017 series "Dark" vs the 2019 movie
  "Dark"), tty users get a numbered `click.prompt`; non-tty callers pick
  the first match and the alternatives are logged to stderr so an MCP
  host can still see them.
- **Already-watched warning.** `stv play` consults
  `cache.get_last_played_exact` and asks before replaying an episode
  watched in the last 7 days. Non-tty callers skip the prompt and the
  output line is tagged `(replay)`.
- **Interruption-aware Home Assistant integration.** The HACS
  `media_player` entity listens to configured HA sensors (doorbell,
  phone call, kitchen timer) and fires `pause` or `duck` (volume drops
  to a configurable level), auto-resuming on deactivation. Configure via
  the integration's options flow with a JSON list of
  `{entity_id, action, duck_volume?}` objects.

### Fixed

- **webOS 24/25 connect failure — `401 insufficient permissions`.**
  aiowebostv 0.7.5's `_get_states_and_subscribe_state_updates()` fires
  `subscribe_media_foreground_app` during `connect()`, which hits
  `com.webos.media/getForegroundAppInfo`. That endpoint needs a
  permission aiowebostv's registration manifest does not request, so
  webOS 24/25 TVs reject it and the resulting `WebOsTvCommandError`
  propagates through the task-result drain (which only suppresses
  `WebOsTvServiceNotFoundError`) and kills the entire connect.
  `_SmarTestWebOsClient` in `src/smartest_tv/_engine/drivers/lg.py`
  absorbs that one error class on that one subscription, matching
  aiowebostv's own handling of `subscribe_channels` and
  `subscribe_current_channel`. The driver still queries media state
  on-demand in `status()` with a try/except fallback, so no
  functionality is lost. Existing LG pairings keep working — no
  re-pair needed.
- **Multi-TV broadcast error visibility.** `--all` and `--group` now
  render per-TV results with a red ✗ and the error message for failures
  instead of silently reporting a partial success count.

### Changed

- **MCP manifest (`server.json`) — `TV_PLATFORM` and `TV_IP` no longer
  required.** The CLI already falls back to the browser driver when no
  TV is configured; forcing these env vars as required blocked Glama and
  Claude Code clients from loading the tool catalog until pairing was
  complete. Users with a configured TV see no change; users on a fresh
  install can call MCP tools immediately and open content in the browser
  until they pair.

## [0.10.0] - 2026-04-09

### Added

- **Zero-friction home dashboard.** Typing `stv` with no args now shows
  one of four context-aware screens instead of a raw command dump:
  - **First-run:** welcome panel pointing to `stv setup`
  - **Connected:** Now Playing card + three contextual next-action
    suggestions driven by your watch history
  - **Offline:** troubleshooting panel with `stv on` / `stv doctor` / `stv setup`
  - **NL fallback:** friendly hint panel when your input doesn't match
    any command
- **Natural-language fallback parser** (`ui/nl.py`). Unknown first arguments
  are parsed as natural language before giving up. Supports:
  - `stv play dark on netflix`
  - `stv youtube lofi beats`
  - `stv what's on netflix`
  - `stv next`, `stv continue`, `stv resume`
  - `stv stats`, `stv insights`, `stv recommend chill`
  - `stv "the bear"` → search Netflix
  Falls back to a hint panel with typed suggestions for truly ambiguous input.
- **Context-aware suggestions** (`ui/suggest.py`). The home dashboard now
  recommends next actions based on recent history:
  - Suggests `stv next` when you have a Netflix S/E in history (with the
    actual show name and next episode)
  - Suggests `stv whats-on <platform>` based on your most-used service
  - Prioritizes `stv whats-on` when the TV is idle on the home screen
- **Friendly error panels for driver installs.** `ImportError` messages
  now include both pipx and pip fix commands:
  ```
  LG driver requires bscpylgtv.
    pipx inject stv bscpylgtv         (recommended)
    pip install 'stv[lg]'             (alternative)
  ```
- **Rich-powered `stv setup`.** Discovery, pairing, and post-install
  guidance all render through the themed console with live spinners and
  bordered panels. Zero questions when exactly one TV is found.

### Changed

- `cli.py` root command now uses a custom `_NLGroup` that intercepts
  `click.UsageError` to try NL parsing before showing the unknown-command
  error.
- `stv` with no args no longer dumps the full 30-command help menu.
  Click help is still available via `stv --help`.

### Tests

- New test modules: `tests/test_nl.py` (33 cases), `tests/test_suggest.py`
  (7 cases). Covers all NL parser branches and suggestion rules.
- **252/252 tests pass** (up from 212 in v0.9.0).

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
