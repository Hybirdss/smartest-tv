# AI Agents (MCP Integration)

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

### Local (stdio)

Default transport — used by Claude Desktop, Cursor, and most MCP clients:

```bash
python -m smartest_tv.server
```

The server reads TV config from `~/.config/smartest-tv/config.toml` or from environment variables.

### Remote (HTTP)

Run stv as a network-accessible MCP server:

```bash
stv serve                                    # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910        # bind to all interfaces
stv serve --transport streamable-http        # streamable-http transport
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

---

## Claude Code

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

Or use `uvx` (no local install required):

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

After saving, restart Claude Code. The TV tools appear in the tool list.

**Verify:** Ask Claude: "What apps are on my TV?" — it should call `tv_apps` and return the list.

### With environment variable overrides

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

Any client that supports MCP stdio transport works. The server command is always:

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
|----------|-------------|---------|
| `TV_PLATFORM` | TV brand: `lg`, `samsung`, `android`, `firetv`, `roku` | `lg` |
| `TV_IP` | TV IP address | `192.168.1.100` |
| `TV_MAC` | MAC address (for Wake-on-LAN) | `AA:BB:CC:DD:EE:FF` |
| `STV_CONFIG_DIR` | Override config directory | `/custom/path` |

Environment variables always take precedence over `config.toml`.

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

> "Add Breaking Bad season 3 to the queue"

Claude calls:
1. `tv_queue_add(platform="netflix", query="Breaking Bad", season=3, episode=1)`

> "What's trending on Netflix?"

Claude calls:
1. `tv_whats_on(platform="netflix")`

---

## Available MCP Tools

See [MCP Tools Reference](../reference/mcp-tools.md) for the complete list with all parameters.

Quick reference:

| Tool | What it does |
|------|-------------|
| `tv_status` | Current app, volume, mute state |
| `tv_play_content` | Resolve + launch in one step |
| `tv_cast` | Cast a streaming URL directly |
| `tv_resolve` | Get content ID without playing |
| `tv_launch` | Launch app with optional deep link |
| `tv_set_volume` | Set volume 0–100 |
| `tv_next` | Play next episode from history |
| `tv_history` | Recent play history |
| `tv_queue_add` | Add to play queue |
| `tv_queue_play` | Play next item in queue |
| `tv_whats_on` | Trending on Netflix/YouTube |
| `tv_recommend` | Personalized recommendations |
| `tv_scene_run` | Run a scene preset |
| `tv_list_tvs` | List all configured TVs |
