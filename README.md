# smartest-tv

Talk to your TV. It listens.

The first multi-platform MCP server for smart TVs. Deep links into Netflix, YouTube, Spotify — say what you want to watch and it plays.

> "Play Frieren season 2 episode 8"
>
> *Netflix opens. Episode starts playing.*

Works with **LG**, **Samsung**, **Android TV**, **Fire TV**, and **Roku**.

## Quick Start

### CLI

```bash
pip install smartest-tv
export TV_IP=192.168.1.100

tv status
tv launch youtube dQw4w9WgXcQ
tv volume 30
tv off
```

### Claude Code

```bash
claude mcp add smartest-tv -- uvx smartest-tv
```

Then just talk:

```
You: Play Baby Shark on YouTube for the kids
You: Put on some jazz on Spotify, screen off
You: Switch to HDMI 2 game mode
```

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "tv": {
      "command": "uvx",
      "args": ["smartest-tv"],
      "env": {
        "TV_PLATFORM": "lg",
        "TV_IP": "192.168.1.100"
      }
    }
  }
}
```

## Deep Linking

This is what makes smartest-tv different. Other tools open Netflix. We play *Frieren episode 36*.

| Platform | Example |
|----------|---------|
| Netflix | `tv launch netflix 82656797` |
| YouTube | `tv launch youtube dQw4w9WgXcQ` |
| Spotify | `tv launch spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS` |

The same content ID works on any TV. The driver handles each platform's protocol:

| TV | Netflix | YouTube | Spotify |
|----|---------|---------|---------|
| LG webOS | DIAL URL via contentId | params.contentTarget | URI via contentId |
| Samsung Tizen | metaTag DEEP_LINK | metaTag video ID | metaTag URI |
| Android / Fire TV | `netflix://` intent | `vnd.youtube:` intent | `spotify:` intent |
| Roku | ECP contentId POST | ECP contentId POST | ECP URI POST |

You don't think about any of this. Just pass the ID.

## Platforms

| Platform | Library | Status |
|----------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | Working |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Planned |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Planned |
| Roku | [ECP HTTP](https://developer.roku.com/docs/developer-program/discovery/external-control-api.md) | Planned |

Install only what you need:

```bash
pip install "smartest-tv[lg]"         # LG only
pip install "smartest-tv[samsung]"    # Samsung only
pip install "smartest-tv[all]"        # Everything
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TV_PLATFORM` | `lg` | `lg`, `samsung`, `android`, `roku` |
| `TV_IP` | Auto-discover | TV IP address |
| `TV_MAC` | — | For Wake-on-LAN |
| `TV_KEY_FILE` | `~/.config/smartest-tv/` | Pairing key storage |

## CLI

```
tv status                          # What's playing, volume, mute
tv launch netflix 82656797         # Deep link Netflix
tv launch youtube dQw4w9WgXcQ     # Play YouTube video
tv launch spotify spotify:album:x # Play on Spotify
tv volume 25                       # Set volume
tv mute                            # Toggle mute
tv apps --format json              # List apps (JSON for AI)
tv notify "Dinner's ready"         # Toast notification
tv off                             # Goodnight
```

`--format json` on any command for structured output.

## MCP Tools

18 tools when running as MCP server:

| Category | Tools |
|----------|-------|
| Power | `tv_on`, `tv_off`, `tv_screen_on`, `tv_screen_off` |
| Volume | `tv_volume`, `tv_set_volume`, `tv_volume_up`, `tv_volume_down`, `tv_mute` |
| Apps | `tv_launch`, `tv_close`, `tv_apps` |
| Media | `tv_play`, `tv_pause`, `tv_stop` |
| Info | `tv_status`, `tv_info`, `tv_notify` |

## Real World

**It's 2am.** You're in bed, phone in hand. You tell Claude: "Play where I left off on Frieren." The living room TV turns on, Netflix opens, the episode starts. You never touched the remote.

**Saturday morning.** "Put on Cocomelon for the baby." YouTube finds it, TV plays it. You keep making breakfast.

**Friends are over.** "Switch to game mode on HDMI 2, volume down." One sentence, three changes.

**Cooking dinner.** "Screen off, play my jazz playlist on Spotify." Screen goes dark, music continues.

## Architecture

```
You (natural language)
  → AI (finds content ID via search / yt-dlp / scraping)
    → smartest-tv (formats deep link per platform)
      → TV Driver (WebSocket / ADB / HTTP)
        → TV
```

Built on [FastMCP](https://gofastmcp.com) + [Click](https://click.palletsprojects.com). Each platform has an async driver implementing a [common interface](src/smartest_tv/drivers/base.py).

## Contributing

Samsung, Android TV, and Roku drivers are the biggest opportunity. The abstract interface is defined — pull requests welcome.

## License

MIT
