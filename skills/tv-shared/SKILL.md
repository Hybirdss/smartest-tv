---
name: tv-shared
description: "smartest-tv CLI reference: auth, config, commands, output formats, and common patterns. Read this first before using any tv-* skill. Prerequisite for tv-netflix, tv-youtube, tv-spotify, tv-workflow skills."
---

# tv — Shared Reference

## Prerequisites

The `stv` CLI must be on `$PATH`. Install: `pip install "stv[lg]"` (or `[samsung]`, `[android]`, `[all]`).

## Environment

```bash
export TV_PLATFORM=lg         # lg, samsung, android, roku
export TV_IP=192.168.1.100    # TV IP (or auto-discovered)
export TV_MAC=AA:BB:CC:DD:EE  # For Wake-on-LAN (optional)
```

## CLI Syntax

```bash
stv <command> [args] [--format json|text]
```

## Commands

| Command | Args | Description |
|---------|------|-------------|
| `stv status` | — | Current app, volume, mute |
| `stv launch <app> [content_id]` | app name + optional deep link | Launch app with deep link |
| `stv close <app>` | app name | Close running app |
| `stv volume [level]` | 0-100 or empty to read | Get or set volume |
| `stv mute` | — | Toggle mute |
| `stv apps` | — | List installed apps |
| `stv play` | — | Resume playback |
| `stv pause` | — | Pause playback |
| `stv on` | — | Wake-on-LAN |
| `stv off` | — | Power off |
| `stv notify <message>` | text | Toast notification on TV |
| `stv info` | — | Model, firmware, platform |

## App Name Aliases

Common names that resolve to platform-specific IDs automatically:

`netflix`, `youtube`, `spotify`, `disney`, `prime`, `appletv`, `hulu`, `tving`, `wavve`, `coupang`, `browser`, `hdmi1`, `hdmi2`

## Deep Link Content IDs

Content IDs are the same across all TV platforms. The driver formats them:

| Service | Content ID format | Where to find |
|---------|------------------|---------------|
| Netflix | Numeric episode/movie ID | `netflix.com/watch/{id}` URL |
| YouTube | 11-char video ID | `youtube.com/watch?v={id}` URL |
| Spotify | Full URI | `open.spotify.com/{type}/{id}` → `spotify:{type}:{id}` |

## Output

`--format json` returns structured JSON on every command. Use this when piping to other tools or when the AI needs to parse output.

## Netflix Deep Link Rule

Netflix requires close-then-relaunch for deep links to work:

```bash
stv close netflix
sleep 2
stv launch netflix 82656797
```

YouTube and Spotify work without closing first.
