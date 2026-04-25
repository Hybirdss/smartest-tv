# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed

- **Samsung driver — `AttributeError: SamsungTVWSAsyncRemote` has no
  attribute `run_app`/`send_key`.** `samsungtvws>=3.0` dropped both
  methods from the async class; only `send_command`/`send_commands`
  remain. Every Samsung control path (power, volume, mute, play/pause/
  stop, channel, app launch, deep link) was raising in production —
  first surfaced as Disney+/Netflix deep-link failure on Tizen 9 via
  HACS. All 13 callsites now dispatch via `SendRemoteKey.click(...)`
  and `ChannelEmitCommand.launch_app(...)` payload builders. `set_volume`
  batches via `send_commands(plural)` so 100 sequential awaits collapse
  to two batched sends. (Closes #6, PR #7.)

### Added

- **Samsung driver — DIAL deep-link path for Netflix and YouTube.**
  Tizen 9 firmware silently ignores `metaTag` on `ed.apps.launch
  DEEP_LINK`. DIAL is the protocol Chromecast uses; Netflix and YouTube
  co-developed it, so launch parameters are interpreted by the app, not
  Tizen, and survive the firmware regression. The driver now SSDP-
  discovers the TV's `Application-URL`, POSTs an
  `m=https://www.netflix.com/watch/{id}&source_type=4` body to
  `{Application-URL}/Netflix` (or `v=<videoId>` to `/YouTube`), and
  caches the discovered URL on the driver instance. Falls back to the
  existing Tizen `DEEP_LINK` path on any DIAL failure, so Tizen 7/8
  behavior is unchanged. Disney+, Hulu, Apple TV+ etc. stay on the
  Tizen path because they're not DIAL receivers — Tier 2 (SmartThings +
  Bixby voice) tracked in #8. (Refs #8, PR #9.)

## [1.1.2] - 2026-04-17

### Fixed

- **Cast URL parsing — strict host match.** `parse_cast_url` used
  `.lstrip("www.")` (strips the char set `{w, .}`, not the prefix) plus
  substring `"netflix.com" in host`, so `wnetflix.com/watch/123` was
  classified as Netflix. Now uses `parsed.hostname` +
  `removeprefix("www.")` + exact-or-suffix domain match; explicit ports
  and uppercase hosts still work.
- **Cache — concurrent-write data loss.** `cache.json` and `queue.json`
  writes went through bare `write_text()`. A multi-TV broadcast spawned
  background revalidate/contribute threads while the foreground wrote
  history; the later write overwrote the earlier and a reader could
  catch a torn file that reset the whole cache to `{}`. All public
  mutators now hold an `RLock` across load → mutate → save and the
  write itself goes through a tempfile + `os.replace()`.
- **Display — HTML/CSS injection via `tv_display` MCP tool.** Message
  text, dashboard titles/cards, and photo URLs were pasted verbatim
  into the served page, letting an AI agent inject `<script>` or
  break out of `url('{raw}')` via `'); }</style><script>…`. Every
  user-controlled field is now HTML-escaped; iframe URLs are gated to
  http/https only and attribute-escaped; photo URLs additionally reject
  the quote/paren/CRLF set that would break the CSS string. The HTTP
  handler is now built per `serve()` call (was a class-level singleton
  that let two concurrent calls overwrite each other's HTML) and the
  returned URL matches the actual bind host.
- **API server — CORS preflight bypass.** `_respond` dropped the
  wildcard CORS default in 1.1.0 but `do_OPTIONS` still defaulted to
  `*`, so preflight passed and any website the user visited while
  `stv serve` was running could POST to the no-auth localhost API.
  Both paths now return no CORS headers unless `STV_CORS_ORIGIN` is
  set explicitly.
- **Scenes — crash mid-scene on malformed step.** A custom scene
  missing a required key raised `KeyError` and aborted the rest of
  the steps, leaving volume changed but app unlaunched. Every step
  now runs inside its own try/except and reports
  `[N] 'action' failed: missing required field 'message' — skipped`.
  Webhook steps also refuse non-http(s) URLs to block SSRF through a
  poisoned `scenes.json`.
- **Roku `set_volume` — up to 200 sequential HTTP round-trips per
  call.** Reworked to track `_known_volume` and issue only the delta
  on subsequent calls (first call still does the 100-down reset).
  State is updated after each successful keypress so a network error
  mid-loop can't leave the tracked value stale.
- **LG webOS — `close_app` on firmware that returns 403.** Falls back
  to the home-screen launch path.
- **Setup — out-of-range int crashed with `IndexError`.** TV selection
  uses `click.IntRange(1, len(tvs))`; invalid input re-prompts.
- **SSDP discovery — malicious device name could inject Rich markup
  or split headers.** `friendlyName` / `DLNADeviceName` / `SERVER`
  values pass through a char allow-list + CRLF guard before being
  stored in `config.toml`.
- **Region cache stuck in long-lived processes.** Added
  `config.clear_region_cache()` so `stv serve` can pick up
  `STV_REGION` changes without restart.

### Home Assistant (HACS integration)

- **Docs — `docs/integrations/home-assistant.md` was still marked
  "Planned / not yet available"** while the integration has been
  shipping for weeks and is under HACS review
  ([hacs/default#6907](https://github.com/hacs/default/pull/6907)).
  Rewritten with install instructions, entity list, and automation
  examples.
- **Manifest version synced to stv package (1.0.1 → 1.1.2)** so HACS
  users see the upgrade; `requirements` pinned to `stv[all]>=1.1.2`.
- **Polling resilience.** A single transient poll failure no longer
  flips the entity to OFF and triggers a full LG 8-subscription
  reconnect. After one or two failures the entity is marked
  unavailable with last-known state; only after three consecutive
  failures do we conclude the TV is really off.
- **Scan interval** bumped from HA's default 10 s to 30 s; webOS SSAP
  state polling doesn't need sub-minute granularity and the old
  cadence was noticeably warming the TV.
- **`async_turn_on` with no MAC** now logs a clear warning instead of
  surfacing a raw `ValueError` through the HA UI.
- **`PLATFORMS` naming collision** in `const.py` renamed to
  `TV_PLATFORMS` so it doesn't shadow HA's `Platform` enum in
  `__init__.py`.

## [1.1.1] - 2026-04-15

### Fixed

- **LG connect() survives webOS 24/25 permission rejections on any
  subscription (issue #4).** v1.1.0 narrowed the 401 tolerance to
  `subscribe_media_foreground_app`, but aiowebostv fires 8 subscriptions
  in parallel and the rejecting one is non-deterministic — on a 2024 LG
  the failing message id landed on a different sub and killed connect
  again. `_SmarTestWebOsClient` now overrides
  `_get_states_and_subscribe_state_updates` to suppress
  `WebOsTvCommandError` on every subscription's result, matching how
  aiowebostv itself already wraps `subscribe_channels` /
  `subscribe_current_channel` upstream. Real network failures still
  propagate — only TV-side permission rejections degrade gracefully.

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
