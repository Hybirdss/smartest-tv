# Configuration Reference

## Config File

**Location:** `~/.config/smartest-tv/config.toml`

Created by `stv setup`. Edit manually if needed.

### Single TV

```toml
[tv]
platform = "lg"        # lg | samsung | android | firetv | roku
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, for Wake-on-LAN
name = "Living Room"        # optional, display name
```

### Multiple TVs

```toml
[tvs.living-room]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"
default = true

[tvs.bedroom]
platform = "samsung"
ip = "192.168.1.101"
mac = "11:22:33:44:55:66"
```

The TV with `default = true` is used when no `--tv` flag is passed.

## Environment Variable Overrides

Take precedence over `config.toml`.

| Variable | Config key | Description |
|----------|------------|-------------|
| `TV_PLATFORM` | `tv.platform` | `lg`, `samsung`, `android`, `firetv`, `roku` |
| `TV_IP` | `tv.ip` | TV IP address |
| `TV_MAC` | `tv.mac` | MAC address for Wake-on-LAN |
| `STV_CONFIG_DIR` | — | Override config directory path |
| `STV_TRANSPORT` | — | MCP transport: `sse` or `streamable-http` |
| `STV_PORT` | — | MCP server port (default: 8910) |
| `STV_LLM_URL` | — | Local LLM URL for AI-powered recommendations |

## Scenes File

**Location:** `~/.config/smartest-tv/scenes.json`

Define custom scene presets. See [Scenes Guide](../guides/scenes.md) for step reference.

```json
{
  "gaming": {
    "description": "Switch to HDMI 2 and set volume",
    "steps": [
      {"action": "launch", "app": "hdmi2"},
      {"action": "set_volume", "level": 40}
    ]
  }
}
```

Built-in scenes (`movie-night`, `kids`, `sleep`, `music`) are always available and do not need to be defined here.
