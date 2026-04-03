# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](README.md) | [한국어](docs/i18n/README.ko.md) | [中文](docs/i18n/README.zh.md) | [日本語](docs/i18n/README.ja.md) | [Español](docs/i18n/README.es.md) | [Deutsch](docs/i18n/README.de.md) | [Português](docs/i18n/README.pt-br.md) | [Français](docs/i18n/README.fr.md)

**Talk to your TV. It listens.**

| Without stv | With stv |
|:-----------:|:--------:|
| Open Netflix app on phone | `stv play netflix "Dark" s1e1` |
| Search for the show | (resolved automatically) |
| Pick the season | (calculated) |
| Pick the episode | (deep-linked) |
| Tap play | |
| **~30 seconds** | **~3 seconds** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Quick Start

```bash
pip install stv
stv setup          # finds your TV, pairs, done
```

## What people do with stv

### "Cast this link to my TV"

Friend sends a YouTube link. You paste it. TV plays it.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "Queue up songs for the party"

Everyone adds their pick. TV plays them in order.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # starts playing in order
stv queue skip                     # next song
```

### "What should we watch?"

Stop scrolling Netflix for 30 minutes. Ask what's trending. Get a recommendation.

```bash
stv whats-on netflix               # top 10 trending right now
stv recommend --mood chill         # based on your watch history
stv recommend --mood action        # different mood, different picks
```

### "Movie night"

One command sets the vibe: volume, notifications, content.

```bash
stv scene movie-night              # volume 20, cinema mode
stv scene kids                     # volume 15, plays Cocomelon
stv scene sleep                    # ambient sounds, auto-off
stv scene create date-night        # make your own
```

### "Play it on the bedroom TV"

Control every TV in the house from one CLI.

```bash
stv multi list                     # living-room (LG), bedroom (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### "Play where I left off"

```bash
stv next                           # continues from your last episode
stv next "Breaking Bad"            # specific show
stv history                        # see what you've been watching
```

## A day with stv

**7:00am** -- alarm goes off. "What's trending?" `stv whats-on youtube` shows morning news. TV plays it.

**8:00am** -- kids wake up. `stv scene kids` -- volume 15, Cocomelon starts.

**12:00pm** -- friend texts a Netflix link. `stv cast https://netflix.com/watch/...` -- TV plays it.

**6:30pm** -- home from work. `stv scene movie-night` -- volume down, cinema mode.

**7:00pm** -- "what should we watch?" `stv recommend --mood chill` -- suggests The Queen's Gambit.

**9:00pm** -- friends come over. Everyone runs `stv queue add ...` -- TV plays them in order.

**11:30pm** -- "good night." `stv scene sleep` -- ambient sounds, TV turns off in 45 minutes.

<details>
<summary><b>How does stv find a Netflix episode with one HTTP request?</b></summary>

Netflix server-renders `__typename:"Episode"` metadata in `<script>` tags. Episode IDs within a season are consecutive integers. One `curl` request to a title page extracts every episode ID for every season. No Playwright, no headless browser, no API key, no login.

Results are cached in three tiers:
1. **Local cache** -- `~/.config/smartest-tv/cache.json`, instant (~0.1s)
2. **Community cache** -- crowdsourced IDs via GitHub raw CDN (40+ entries pre-seeded), zero server cost
3. **Web search fallback** -- Brave Search discovers unknown title IDs automatically

</details>

<details>
<summary><b>Deep linking -- how stv talks to your TV</b></summary>

Each driver translates a content ID into the platform's native format:

| TV | Protocol | Deep link format |
|----|----------|-----------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

You never think about any of this. The driver handles it.

</details>

<details>
<summary><b>Supported platforms</b></summary>

| Platform | Driver | Status |
|----------|--------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **Tested** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Community testing |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Community testing |
| Roku | HTTP ECP | Community testing |

</details>

## Install

```bash
pip install stv                 # LG (default)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Everything
```

## Works with everything

| Integration | What happens |
|------------|-------------|
| **Claude Code** | "Play Breaking Bad s1e1" -- TV plays it |
| **OpenClaw** | Telegram: "I'm home" -- scene + recommend + play |
| **Home Assistant** | Door opens -- TV turns on -- trending shows appear |
| **Cursor / Codex** | AI writes code, controls your TV on break |
| **cron / scripts** | 7am: news on bedroom TV. 9pm: kids TV off |
| **Any MCP client** | 32 tools over stdio or HTTP |

### MCP Server

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

Or run as an HTTP server for remote access:

```bash
stv serve --port 8910              # SSE on http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## Documentation

| | |
|---|---|
| [Getting Started](docs/getting-started/installation.md) | First-time setup for any TV brand |
| [Playing Content](docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Scenes](docs/guides/scenes.md) | Presets: movie-night, kids, sleep, custom |
| [Multi-TV](docs/guides/multi-tv.md) | Control multiple TVs with `--tv` |
| [AI Agents](docs/guides/ai-agents.md) | MCP setup for Claude, Cursor, OpenClaw |
| [Recommendations](docs/guides/recommendations.md) | AI-powered content suggestions |
| [CLI Reference](docs/reference/cli.md) | Every command and option |
| [MCP Tools](docs/reference/mcp-tools.md) | All 32 MCP tools with parameters |
| [OpenClaw](docs/integrations/openclaw.md) | ClawHub skill + Telegram scenarios |

## Contributing

Samsung, Roku, and Android TV drivers need real-world testing. If you have one of these TVs, your feedback is incredibly valuable.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 tests, no TV needed
```

Want to add your favorite shows to the community cache? See [Contributing Cache](docs/contributing/cache-contributions.md).

Want to write a driver for a new TV? See [Driver Development](docs/contributing/driver-development.md).

## License

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
