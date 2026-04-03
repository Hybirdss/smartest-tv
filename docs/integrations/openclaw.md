# OpenClaw Integration Guide

smartest-tv integrates with [OpenClaw](https://openclaw.dev) via ClawHub, letting you control any smart TV directly from your OpenClaw agent.

## Install via ClawHub

```bash
clawhub install smartest-tv
```

This installs the `stv` CLI and registers the `tv` skill into your OpenClaw agent.

## Manual Install

If you prefer to install manually:

```bash
pip install stv          # LG (default)
pip install "stv[all]"   # All TV platforms
```

Then copy the skill file into your OpenClaw skills directory:

```bash
cp skills/tv/SKILL.md ~/.openclaw/skills/tv.md
```

## MCP Configuration

OpenClaw connects to smartest-tv as an MCP server. Add the following to your OpenClaw MCP config (typically `~/.openclaw/mcp.json`):

### Recommended: uvx (no local install required)

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

### With explicit TV credentials

```json
{
  "mcpServers": {
    "tv": {
      "command": "python3",
      "args": ["-m", "smartest_tv"],
      "env": {
        "TV_PLATFORM": "lg",
        "TV_IP": "192.168.1.100"
      }
    }
  }
}
```

Supported platforms for `TV_PLATFORM`: `lg`, `samsung`, `android`, `firetv`, `roku`.

## First-Time Setup

Before using the MCP server, pair with your TV:

```bash
stv setup              # Auto-discover TV on local network
stv setup --ip X.X.X.X # Connect directly if auto-discovery fails
stv doctor             # Diagnose connection issues
```

The TV will show a pairing prompt on first connection. Accept once — the key is saved permanently.

## Usage Examples

Once the MCP server is connected, your OpenClaw agent can control the TV with natural language:

### Play content

```
Play Squid Game season 2 episode 3 on Netflix
Put on Baby Shark for the kids
Play the Wednesday soundtrack on Spotify
Screen off, play lo-fi beats
```

The agent calls `tv_play_content`, which resolves the content ID and deep-links directly to the episode/video/track.

### TV control

```
Turn down the volume
Good night (turns TV off)
What's on TV right now?
```

### Continue watching

```
Continue where I left off on Stranger Things
What episode am I on?
```

## Telegram Integration

smartest-tv + OpenClaw + Telegram lets you control your TV from anywhere:

1. Set up OpenClaw with the `tv` skill and Telegram channel.
2. Send a message from Telegram: `"Play Inception on Netflix"`
3. OpenClaw routes the request to the MCP server.
4. Your TV starts playing — no remote needed.

Example Telegram → TV workflow:

```
You (Telegram): Play where I left off on Frieren
OpenClaw: [calls tv_next("Frieren")] → Playing Frieren S2E8 on your LG TV
```

## Available MCP Tools

| Tool | What it does |
|------|-------------|
| `tv_status` | Current app, volume, mute state |
| `tv_play_content` | Resolve + launch content in one step |
| `tv_resolve` | Get content ID without playing |
| `tv_launch` | Launch app with optional deep link |
| `tv_set_volume` | Set volume 0–100 |
| `tv_mute` | Toggle mute |
| `tv_off` | Turn TV off |
| `tv_next` | Play next episode from history |
| `tv_history` | Recent play history |
| `tv_notify` | Show toast notification on screen |

See [MCP Tools Reference](../reference/mcp-tools.md) for the full list with parameters.

## Troubleshooting

**TV not found:**
```bash
stv doctor          # shows what's wrong
stv setup --ip X.X.X.X
```

**MCP server not starting:**
```bash
python3 -m smartest_tv  # run directly to see errors
```

**Content not found:**
```bash
stv resolve netflix "Show Name" s1e1   # test resolution manually
stv cache show                          # check what's cached
```
