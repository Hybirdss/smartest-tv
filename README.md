# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

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

https://github.com/user-attachments/assets/PLACEHOLDER_DEMO_VIDEO

## Install

```bash
pip install stv                 # LG (default, batteries included)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Everything
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # Find + play in one shot
stv play youtube "baby shark"                          # Search + play
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # Just get the ID
stv launch netflix 82656797         # Direct deep link (if you know the ID)
stv status                          # What's on, volume, mute state
stv volume 25                       # Set volume
stv mute                            # Toggle mute
stv apps --format json              # List apps (structured output)
stv notify "Dinner's ready"         # Toast notification on screen
stv off                             # Goodnight
```

Every command supports `--format json` — designed for scripts and AI agents.

### Content Resolution

`stv resolve` finds streaming IDs so you don't have to. `stv play` does the same and launches on TV in one step.

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → passthrough
```

Netflix resolution works by scraping episode metadata from the title page with a single `curl` request — no Playwright, no browser, no login. All seasons are resolved at once and cached locally. Second lookup is instant (~0.1s).

### Cache

Once an ID is found, it's cached forever at `~/.config/smartest-tv/cache.json`. You can also seed the cache manually:

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # Show all cached IDs
```

## Agent Skills

smartest-tv ships five skills that teach AI assistants how to control your TV. Install them into Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

| Skill | What it does |
|-------|-------------|
| `tv-shared` | CLI reference, auth, config, common patterns |
| `tv-netflix` | Episode ID lookup via HTTP scraping |
| `tv-youtube` | Video search via yt-dlp, format resolution |
| `tv-spotify` | Album/track/playlist URI resolution |
| `tv-workflow` | Composite actions: movie night, kids mode, sleep timer |

Skills are plain Markdown files. Port them to any agent in minutes.

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

It auto-discovers your TV on the network, detects the platform, pairs automatically, and writes everything to `~/.config/smartest-tv/config.toml`. If something looks wrong, `stv doctor` will tell you exactly what's up.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, for Wake-on-LAN
```

On first connection, the TV shows a pairing prompt. Accept once — the key is saved and never asked again.

## MCP Server

For Claude Desktop, Cursor, or other MCP clients — optional, the CLI is the primary interface:

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

## Contributing

| Status | Area | What's needed |
|--------|------|---------------|
| **Ready** | LG webOS driver | Tested and working |
| **Needs testing** | Samsung, Android TV, Roku drivers | Real hardware reports welcome |
| **Wanted** | Disney+ skill | Deep link ID resolution |
| **Wanted** | Hulu, Prime Video skills | Deep link ID resolution |

The [driver interface](src/smartest_tv/drivers/base.py) is defined — implement `TVDriver` for your platform and open a PR.

## License

MIT
