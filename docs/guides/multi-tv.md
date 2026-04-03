# Multi-TV Setup

stv supports multiple TVs in one config — local TVs on your network and remote TVs at a friend's house.

## Adding TVs

```bash
stv multi add living-room --platform lg --ip 192.168.1.100 --default
stv multi add bedroom --platform samsung --ip 192.168.1.101
stv multi add kids-room --platform roku --ip 192.168.1.102
stv multi add friend --platform remote --url http://203.0.113.50:8911
```

Supported platforms: `lg`, `samsung`, `android`, `firetv`, `roku`, `remote`.

## Configuration

```toml
# ~/.config/smartest-tv/config.toml

[tv.living-room]
platform = "lg"
ip = "192.168.1.100"
default = true

[tv.bedroom]
platform = "samsung"
ip = "192.168.1.101"

[tv.friend]
platform = "remote"
url = "http://203.0.113.50:8911"

[groups]
home = ["living-room", "bedroom"]
party = ["living-room", "bedroom", "friend"]
```

The TV with `default = true` is used when no `--tv` flag is passed.

## Targeting a single TV

Use `--tv NAME` before the subcommand:

```bash
stv --tv bedroom play netflix "Dark" s1e1
stv --tv bedroom volume 20
stv --tv kids-room off
```

## Targeting multiple TVs

### --all: every configured TV

```bash
stv --all off                    # good night
stv --all volume 15              # quiet everywhere
stv --all notify "Dinner!"      # toast on every screen
```

### --group: a named set of TVs

```bash
stv --group home play youtube "lo-fi beats"
stv --group party play netflix "Wednesday" s1e1
stv --group home mute
```

## Managing groups

```bash
stv group create party living-room bedroom friend
stv group list
stv group delete party
```

Groups are stored in the `[groups]` section of `config.toml`.

## Managing TVs

```bash
stv multi list                   # show all TVs + default status
stv multi add NAME --platform PLATFORM --ip IP [--mac MAC] [--default]
stv multi add NAME --platform remote --url URL
stv multi remove NAME
stv multi default NAME           # change default TV
```

## Remote TVs

A remote TV is a friend's TV controlled through their `stv serve` instance. See [Sync & Party Mode](sync-party.md) for the full setup guide.

```bash
# Friend runs:
stv serve --host 0.0.0.0        # exposes MCP + REST API

# You add:
stv multi add friend --platform remote --url http://friend-ip:8911

# Now friend's TV works like any other:
stv --tv friend play spotify "chill vibes"
stv --group party play netflix "Squid Game" s2e3
```

## MCP tools

All tools accept an optional `tv_name` parameter:

```
tv_status(tv_name="bedroom")
tv_play_content(platform="netflix", query="Dark", season=1, episode=1, tv_name="bedroom")
tv_set_volume(level=20, tv_name="living-room")
tv_list_tvs()       → list all configured TVs
tv_group_list()     → list all groups
tv_sync_play(platform="netflix", query="Wednesday", season=1, episode=1, group="party")
```

## Environment variable override

For single-shot commands without a config file:

```bash
TV_PLATFORM=lg TV_IP=192.168.1.100 stv status
```

Environment variables only apply in legacy single-TV mode.
