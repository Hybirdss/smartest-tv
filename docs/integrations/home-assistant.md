# Home Assistant Integration

> **Status: Planned.** This integration is not yet available.
> Track progress or contribute at the project repository.

## Planned approach

smartest-tv will expose a Home Assistant integration that allows:

- TV power, volume, and app control via HA automations
- Content playback from HA scripts and dashboards
- TV state (current app, volume, mute) as HA sensor entities

## Workaround (today)

Until the native integration ships, you can call stv from HA shell commands:

```yaml
# configuration.yaml
shell_command:
  tv_off: "stv off"
  tv_volume_night: "stv volume 15"
  tv_play_kids: "stv play youtube 'baby shark'"
```

Then trigger from automations:

```yaml
automation:
  - alias: "TV off at midnight"
    trigger:
      platform: time
      at: "00:00:00"
    action:
      service: shell_command.tv_off
```

Requires the HA host to have `stv` installed and `~/.config/smartest-tv/config.toml` configured.

## Environment variable approach

For multi-TV homes, use environment variables instead of the config file:

```yaml
shell_command:
  bedroom_tv_off: "TV_PLATFORM=samsung TV_IP=192.168.1.101 stv off"
  living_room_tv_off: "TV_PLATFORM=lg TV_IP=192.168.1.100 stv off"
```
