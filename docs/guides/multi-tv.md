# Multi-TV Setup

stv supports multiple TVs in one config. Each TV gets a name; commands target the primary TV by default.

## Configuration

```toml
# ~/.config/smartest-tv/config.toml

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

## CLI

Use `--tv NAME` to target a specific TV:

```bash
stv --tv bedroom status
stv --tv bedroom play netflix "Frieren" s2e8
stv --tv living-room volume 20
```

The `--tv` flag applies globally and must come before the subcommand:

```bash
stv --tv bedroom off
stv --tv living-room notify "Dinner's ready"
```

## MCP tools

All tools accept an optional `tv_name` parameter:

```
tv_status(tv_name="bedroom")
tv_play_content(platform="netflix", query="Frieren", season=2, episode=8, tv_name="bedroom")
tv_set_volume(level=20, tv_name="living-room")

tv_list_tvs()    → list all configured TVs
```

`tv_list_tvs()` returns:

```json
[
  {"name": "living-room", "platform": "lg", "ip": "192.168.1.100", "default": true},
  {"name": "bedroom", "platform": "samsung", "ip": "192.168.1.101", "default": false}
]
```

## Environment variable override

For single-shot commands without a config file:

```bash
TV_PLATFORM=lg TV_IP=192.168.1.100 stv status
```

Environment variables always take precedence over `config.toml`.
