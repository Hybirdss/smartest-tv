# smartest-tv

Talk to your TV. It listens.

A CLI and agent skills for controlling smart TVs with natural language. Deep links into Netflix, YouTube, Spotify — say what you want to watch and it plays.

> "Play Frieren season 2 episode 8"
>
> *Netflix opens. Episode starts playing.*

Works with **LG**, **Samsung**, **Android TV**, **Fire TV**, and **Roku**.

## Install

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # Everything
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # What's playing, volume, mute
tv launch netflix 82656797         # Deep link to specific content
tv launch youtube dQw4w9WgXcQ     # Play a YouTube video
tv launch spotify spotify:album:x # Play on Spotify
tv volume 25                       # Set volume
tv mute                            # Toggle mute
tv apps --format json              # List apps (structured output)
tv notify "Dinner's ready"         # Toast notification on screen
tv off                             # Goodnight
```

Every command supports `--format json` for structured output — designed for scripts and AI agents.

## Agent Skills

smartest-tv ships skills that teach AI assistants how to control your TV intelligently. Install them into Claude Code:

```bash
# Auto-install skills from the repo
cd smartest-tv && ./install-skills.sh

# Or manually symlink
ln -s $(pwd)/skills/tv-shared ~/.claude/skills/tv-shared
ln -s $(pwd)/skills/tv-netflix ~/.claude/skills/tv-netflix
ln -s $(pwd)/skills/tv-youtube ~/.claude/skills/tv-youtube
ln -s $(pwd)/skills/tv-spotify ~/.claude/skills/tv-spotify
```

Then just talk to Claude:

```
You: 프리렌 2기 8화 넷플릭스에서 틀어줘
You: Play Baby Shark on YouTube for the kids
You: Put on Ye's new album on Spotify
You: Screen off, play jazz playlist
You: Good night
```

The skills handle the hard part — finding Netflix episode IDs, searching YouTube with yt-dlp, resolving Spotify URIs — then call the `tv` CLI to control your TV.

### Skill Index

| Skill | What it does |
|-------|-------------|
| `tv-shared` | CLI reference, auth, config, common patterns |
| `tv-netflix` | Episode ID lookup via Playwright page scraping |
| `tv-youtube` | Video search via yt-dlp, format resolution |
| `tv-spotify` | Album/track/playlist URI resolution |
| `tv-workflow` | Composite actions: movie night, kids mode, sleep timer |

Skills follow the same pattern as [gws](https://github.com/googleworkspace/cli) skills — each one teaches the AI *how* and *when* to use specific CLI commands.

## Deep Linking

This is what makes smartest-tv different. Other tools open Netflix. We play *Frieren episode 36*.

The same content ID works on every TV platform:

```bash
tv launch netflix 82656797                           # Works on LG, Samsung, Roku, Android TV
tv launch youtube dQw4w9WgXcQ                        # Same
tv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Same
```

Each driver translates the ID into the platform's native deep link format:

| TV | How it sends the deep link |
|----|---------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

You never think about this. The driver handles it.

## Platforms

| Platform | Driver | Connection | Status |
|----------|--------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Working** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Planned |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Planned |
| Roku | HTTP ECP | REST :8060 | Planned |

## Configuration

```bash
export TV_PLATFORM=lg              # lg, samsung, android, roku
export TV_IP=192.168.1.100         # Or auto-discovered via SSDP
export TV_MAC=AA:BB:CC:DD:EE:FF    # For Wake-on-LAN (optional)
```

On first connection the TV shows a pairing prompt. Accept once — the key is saved to `~/.config/smartest-tv/`.

## Real World

**It's 2am.** You're in bed. You tell Claude: "Play where I left off on Frieren." The living room TV turns on, Netflix opens, the episode starts. You never touched the remote.

**Saturday morning.** "Put on Cocomelon for the baby." YouTube finds it, TV plays it. You keep making breakfast.

**Friends are over.** "Game mode, HDMI 2, volume down." One sentence, three changes.

**Cooking dinner.** "Screen off, play my jazz playlist." Screen goes dark, music continues through the speakers.

## MCP Server

For Claude Desktop, Cursor, or other MCP clients:

```json
{
  "mcpServers": {
    "tv": {
      "command": "uvx",
      "args": ["smartest-tv"],
      "env": { "TV_PLATFORM": "lg", "TV_IP": "192.168.1.100" }
    }
  }
}
```

18 tools: `tv_on`, `tv_off`, `tv_launch`, `tv_close`, `tv_volume`, `tv_set_volume`, `tv_mute`, `tv_play`, `tv_pause`, `tv_stop`, `tv_status`, `tv_info`, `tv_notify`, `tv_apps`, `tv_volume_up`, `tv_volume_down`, `tv_screen_on`, `tv_screen_off`.

## Architecture

```
You (natural language)
  → AI + Skills (finds content ID via yt-dlp / Playwright / web search)
    → tv CLI (formats and dispatches)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contributing

**Drivers** for Samsung, Android TV, and Roku are the biggest opportunity. The [driver interface](src/smartest_tv/drivers/base.py) is defined — implement `TVDriver` for your platform.

**Skills** for new streaming services (Disney+, Hulu, Prime Video) are welcome too.

## License

MIT
