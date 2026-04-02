# MCP Integration Guide

smartest-tv ships an MCP (Model Context Protocol) server that exposes all TV
controls as tools. Any MCP-compatible AI client can control your TV, play
content, and check status without any manual configuration beyond the initial
`stv setup`.

## Prerequisites

```bash
pip install "stv[mcp]"   # installs fastmcp
stv setup                # configure your TV first
```

## Starting the MCP Server

```bash
python -m smartest_tv.server
```

The server runs over stdio (standard MCP transport). It reads TV config from
`~/.config/smartest-tv/config.toml` or from environment variables.

---

## Claude Code (claude.ai/code)

Add the server to your Claude Code settings:

**File:** `~/.claude/settings.json`

```json
{
  "mcpServers": {
    "smartest-tv": {
      "command": "python",
      "args": ["-m", "smartest_tv.server"],
      "env": {}
    }
  }
}
```

After saving, restart Claude Code. The TV tools will appear in the tool list.

**Verify in Claude Code:**
Ask Claude: "What apps are on my TV?" — it should call `tv_apps` and return the list.

### With environment variable overrides

If you want to control a specific TV without a config file:

```json
{
  "mcpServers": {
    "smartest-tv": {
      "command": "python",
      "args": ["-m", "smartest_tv.server"],
      "env": {
        "TV_PLATFORM": "lg",
        "TV_IP": "192.168.1.100",
        "TV_MAC": "AA:BB:CC:DD:EE:FF"
      }
    }
  }
}
```

---

## Other MCP Clients

Any client that supports the MCP stdio transport works. The server command is always:

```
python -m smartest_tv.server
```

### mcp-cli

```bash
mcp run "python -m smartest_tv.server"
```

### Custom Python client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "smartest_tv.server"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("tv_status", {})
        print(result)
```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `TV_PLATFORM` | TV brand: `lg`, `samsung`, `android`, `firetv`, `roku` | `lg` |
| `TV_IP` | TV IP address | `192.168.1.100` |
| `TV_MAC` | MAC address (for Wake-on-LAN) | `AA:BB:CC:DD:EE:FF` |
| `STV_CONFIG_DIR` | Override config directory | `/custom/path` |

Environment variables always take precedence over `config.toml`.

---

## Available MCP Tools

See [api-reference.md](api-reference.md) for the complete tool list with all parameters.

Quick reference of the most-used tools:

| Tool | What it does |
|---|---|
| `tv_status` | Current app, volume, mute state |
| `tv_play_content` | Resolve + launch in one step |
| `tv_resolve` | Get content ID without playing |
| `tv_launch` | Launch app with optional deep link |
| `tv_set_volume` | Set volume 0–100 |
| `tv_next` | Play next episode from history |
| `tv_history` | Recent play history |

---

## Example AI Interaction

Once the MCP server is connected to Claude:

> "Play Frieren season 2 episode 8 on Netflix"

Claude calls:
1. `tv_play_content(platform="netflix", query="Frieren", season=2, episode=8)`

The tool resolves the Netflix episode ID (from cache or via HTTP scrape),
closes the Netflix app, relaunches with the deep link, and records the play
to history.

> "What episode was I on?"

Claude calls:
1. `tv_history(limit=1)` — returns the last played entry with season/episode.
