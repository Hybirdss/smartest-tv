# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](tests/)

[English](README.md) | [한국어](docs/i18n/README.ko.md) | [中文](docs/i18n/README.zh.md) | [日本語](docs/i18n/README.ja.md) | [Español](docs/i18n/README.es.md) | [Deutsch](docs/i18n/README.de.md) | [Português](docs/i18n/README.pt-br.md) | [Français](docs/i18n/README.fr.md)

**Talk to your TV. It listens.**

Other tools open Netflix. smartest-tv plays *Frieren season 2 episode 8*.

<p align="center">
  <img src="docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## Quick Start

```bash
pip install stv
stv setup          # auto-discovers your TV, pairs, done
```

That's it. No developer mode. No API keys. No env vars. Say what you want to watch.

## What can you do?

```
You: Play Frieren season 2 episode 8 on Netflix
You: Put on Baby Shark for the kids
You: Ye's new album on Spotify
You: Screen off, play my jazz playlist
You: Good night
```

The AI finds the content ID (Netflix episode, YouTube video, Spotify URI), calls `stv`, and your TV plays it.

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Install

```bash
pip install stv                 # LG (default, batteries included)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Everything
```

## CLI

```bash
# Play content by name — stv finds the ID automatically
stv play netflix "Frieren" s2e8            # Resolve + deep link in one shot
stv play youtube "baby shark"              # Search + play
stv play spotify "Ye White Lines"          # Find on Spotify + play

# Search without playing
stv search netflix "Stranger Things"       # Shows all seasons + episode counts
stv search youtube "lofi hip hop"          # Top 3 results
stv resolve netflix "Frieren" s2e8         # Just get the episode ID

# Continue watching
stv next                                   # Play next episode from history
stv next "Frieren"                         # Next episode of specific show
stv history                                # Recent plays with timestamps

# TV control
stv status                                 # What's on, volume, mute state
stv volume 25                              # Set volume
stv mute                                   # Toggle mute
stv notify "Dinner's ready"               # Toast notification on screen
stv off                                    # Goodnight

# Direct deep link (if you already know the ID)
stv launch netflix 82656797
```

Every command supports `--format json` — designed for scripts and AI agents.

### How Content Resolution Works

`stv play` and `stv resolve` find streaming IDs so you don't have to:

```bash
stv resolve netflix "Frieren" s2e8         # → 82656797
stv resolve youtube "lofi hip hop"         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify "Ye White Lines"       # → spotify:track:3bbjDFVu...
```

Netflix resolution is a single `curl` request to the title page. Netflix server-renders `__typename:"Episode"` metadata in `<script>` tags. Episode IDs within a season are consecutive integers, so one HTTP request resolves every season of a show. No Playwright, no headless browser, no login required.

Results are cached in three tiers:
1. **Local cache** — `~/.config/smartest-tv/cache.json`, instant (~0.1s)
2. **Community cache** — crowdsourced IDs via GitHub raw CDN (29 Netflix shows, 11 YouTube videos pre-seeded), zero server cost
3. **Web search fallback** — Brave Search discovers unknown title IDs automatically

### Cache

```bash
stv cache show                                # View all cached IDs
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8     # → 82656797
stv cache contribute                          # Export for community cache PR
```

## Agent Skills

smartest-tv ships one skill that teaches AI assistants everything about TV control. Install into Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

The `tv` skill covers all platforms (Netflix, YouTube, Spotify), all commands (`play`, `search`, `resolve`, `cache`, `volume`, `off`), and composite workflows (movie night, kids mode, sleep timer). It's a single Markdown file — portable to any AI agent in minutes.

## Works With

Any AI agent that can run shell commands:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · or just `bash`

## Real World

**It's 2am.** You're in bed. You tell Claude: "Play where I left off on Frieren." The living room TV turns on, Netflix opens, the episode starts. You never touched the remote. You barely opened your eyes.

**Saturday morning.** "Put on Cocomelon for the baby." YouTube finds it, TV plays it. You keep making breakfast.

**Friends are over.** "Game mode, HDMI 2, volume down." One sentence, three changes, done before anyone noticed.

**Cooking dinner.** "Screen off, play my jazz playlist." Screen goes dark, music flows through the speakers.

**Falling asleep.** "Sleep timer 45 minutes." The TV turns itself off. You don't.

## What smartest-tv is

- **Deep link resolver** — finds the Netflix episode ID, YouTube video, Spotify URI
- **Universal remote** — one CLI across 4 TV platforms
- **AI-native** — designed for agents to call, not just humans

## What it isn't

- Not a remote control app (no channel surfing, no arrow keys)
- Not an HDMI-CEC controller
- Not a screen mirroring tool

<details>
<summary><strong>Deep Linking</strong> — how it actually works</summary>

The same content ID works across every TV platform:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Same
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Same
```

Each driver translates the ID into the platform's native deep link format:

| TV | How it sends the deep link |
|----|---------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

You never think about any of this. The driver handles it.

</details>

<details>
<summary><strong>Platforms</strong> — supported TVs and drivers</summary>

| Platform | Driver | Connection | Status |
|----------|--------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Tested** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Community testing |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Community testing |
| Roku | HTTP ECP | REST :8060 | Community testing |

LG is the primary tested platform. No developer mode required on any of them.

</details>

## Zero-config Setup

```bash
stv setup
```

Scans your network for LG, Samsung, Roku, and Android/Fire TV simultaneously (SSDP + ADB). Auto-detects the platform, pairs, saves config, and sends a test notification — all in one command. If your TV isn't discovered, pass the IP directly:

```bash
stv setup --ip 192.168.1.100
```

Everything lands in `~/.config/smartest-tv/config.toml`. If something looks wrong, `stv doctor` tells you exactly what's up.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, for Wake-on-LAN
```

On first connection, the TV shows a pairing prompt. Accept once — the key is saved and never asked again.

## MCP Server

### Local (stdio)

For Claude Desktop, Cursor, or other MCP clients — connect to stv as a local process:

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

### Remote (HTTP)

Run stv as a network-accessible MCP server. Useful for shared setups or AI agents running on a different machine:

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

Connect from any MCP client:

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
    }
  }
}
```

## Architecture

```
You (natural language)
  → AI + stv resolve (finds content ID via HTTP scraping / yt-dlp / cache)
    → stv play (formats deep link and dispatches)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

<p align="center">
  <img src="docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## Documentation

| Guide | What's inside |
|-------|---------------|
| [Setup Guide](docs/setup-guide.md) | Brand-specific TV setup (LG pairing, Samsung remote access, ADB, Roku ECP) |
| [MCP Integration](docs/mcp-integration.md) | Claude Code, Cursor, and other MCP client configuration |
| [API Reference](docs/api-reference.md) | All CLI commands + all 20 MCP tools with parameters |
| [Contributing Cache](docs/contributing-cache.md) | How to find Netflix IDs and submit a PR to the community cache |

## Contributing

| Status | Area | What's needed |
|--------|------|---------------|
| **Ready** | LG webOS driver | Tested and working |
| **Needs testing** | Samsung, Android TV, Roku drivers | Real hardware reports welcome |
| **Wanted** | Disney+, Hulu, Prime Video | Deep link ID resolution |
| **Wanted** | Community cache entries | [Add your favorite shows](docs/contributing-cache.md) |

The [driver interface](src/smartest_tv/drivers/base.py) is defined — implement `TVDriver` for your platform and open a PR.

### Running tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

55 unit tests covering the content resolver, cache, and CLI parser. No TV or network required — all external calls are mocked.

## License

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
