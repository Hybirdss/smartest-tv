# smartest-tv

[English](README.md) | [한국어](docs/i18n/README.ko.md) | [中文](docs/i18n/README.zh.md) | [日本語](docs/i18n/README.ja.md) | [Español](docs/i18n/README.es.md) | [Deutsch](docs/i18n/README.de.md) | [Português](docs/i18n/README.pt-br.md) | [Français](docs/i18n/README.fr.md)

**Talk to your TV. It listens.**

A CLI and agent skills for controlling smart TVs with natural language. Deep links into Netflix, YouTube, Spotify — say what you want to watch and it plays. No developer mode. No API keys. No cursed env vars. Just `stv setup` and go.

> "Play Frieren season 2 episode 8"
>
> *Netflix opens. Episode starts playing.*

Works with **LG** (tested), **Samsung**, **Android TV / Fire TV**, and **Roku** (community testing).

## Install

```bash
pip install stv
```

That's it. No extras needed for LG — the default install covers it.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # Everything
```

## Zero-config Setup

Run this once and you're done:

```bash
stv setup
```

It auto-discovers your TV on the network, detects the platform (LG? Samsung? Roku?), pairs automatically — no developer mode required, no IP hunting — and writes everything to `~/.config/smartest-tv/config.toml`. After that, every `stv` command just works.

If something looks wrong, `stv doctor` will tell you exactly what's up.

## CLI

```bash
stv status                          # What's on, volume, mute state
stv launch netflix 82656797         # Deep link to specific content
stv launch youtube dQw4w9WgXcQ     # Play a YouTube video
stv launch spotify spotify:album:x  # Play on Spotify
stv volume 25                       # Set volume
stv mute                            # Toggle mute
stv apps --format json              # List apps (structured output)
stv notify "Dinner's ready"         # Toast notification on screen
stv off                             # Goodnight
```

Every command supports `--format json` — designed for scripts and AI agents.

## Agent Skills

stv ships five skills that teach AI assistants how to control your TV intelligently. Install them into Claude Code:

```bash
# Auto-install all skills
cd smartest-tv && ./install-skills.sh
```

Then just talk to Claude:

```
You: Play Frieren season 2 episode 8 on Netflix
You: Put on Baby Shark for the kids
You: Ye's new album on Spotify
You: Screen off, play my jazz playlist
You: Good night
```

The skills handle the hard part — finding Netflix episode IDs, searching YouTube via yt-dlp, resolving Spotify URIs — and call `stv` to control your TV.

### Skills

| Skill | What it does |
|-------|-------------|
| `tv-shared` | CLI reference, auth, config, common patterns |
| `tv-netflix` | Episode ID lookup via Playwright scraping |
| `tv-youtube` | Video search via yt-dlp, format resolution |
| `tv-spotify` | Album/track/playlist URI resolution |
| `tv-workflow` | Composite actions: movie night, kids mode, sleep timer |

## Deep Linking

This is what makes stv different from everything else. Other tools open Netflix. stv plays *Frieren episode 36*.

The same content ID works across every TV platform:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Same
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Same
```

Each driver translates the ID into the platform's native deep link format under the hood:

| TV | How it sends the deep link |
|----|---------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

You never think about any of this. The driver handles it.

## Platforms

| Platform | Driver | Connection | Status |
|----------|--------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Tested** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Community testing |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Community testing |
| Roku | HTTP ECP | REST :8060 | Community testing |

LG is the primary tested platform. Samsung, Android TV, and Roku should work — no developer mode required on any of them — but real-world reports are welcome.

## Configuration

Config lives at `~/.config/smartest-tv/config.toml`. After `stv setup`, it looks something like:

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, for Wake-on-LAN
```

On first connection, the TV shows a pairing prompt. Accept once — the key is saved and never asked again.

## Real World

**It's 2am.** You're in bed. You tell Claude: "Play where I left off on Frieren." The living room TV turns on, Netflix opens, the episode starts. You never touched the remote. You barely opened your eyes.

**Saturday morning.** "Put on Cocomelon for the baby." YouTube finds it, TV plays it. You keep making breakfast. Coffee's getting cold anyway.

**Friends are over.** "Game mode, HDMI 2, volume down." One sentence, three changes, done before anyone noticed you did it.

**Cooking dinner.** "Screen off, play my jazz playlist." Screen goes dark, music flows through the speakers. You didn't need to pause, navigate, or squint at a menu.

**Falling asleep.** "Sleep timer 45 minutes." The TV turns itself off. You don't.

## MCP Server

For Claude Desktop, Cursor, or other MCP clients — this is optional, the CLI is the primary interface:

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

18 tools available: `tv_on`, `tv_off`, `tv_launch`, `tv_close`, `tv_volume`, `tv_set_volume`, `tv_mute`, `tv_play`, `tv_pause`, `tv_stop`, `tv_status`, `tv_info`, `tv_notify`, `tv_apps`, `tv_volume_up`, `tv_volume_down`, `tv_screen_on`, `tv_screen_off`.

Config is read from `~/.config/smartest-tv/config.toml` automatically — no env vars needed.

## Architecture

```
You (natural language)
  → AI + Skills (finds content ID via yt-dlp / Playwright / web search)
    → stv CLI (formats and dispatches)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contributing

**Drivers** for Samsung, Android TV, and Roku are the highest-leverage contribution. The [driver interface](src/smartest_tv/drivers/base.py) is defined — implement `TVDriver` for your platform and open a PR.

**Skills** for new streaming services (Disney+, Hulu, Prime Video) are welcome too.

## License

MIT
