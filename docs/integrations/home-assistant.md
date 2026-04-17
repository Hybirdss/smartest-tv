# Home Assistant Integration

> **Status: Available now** via HACS as a custom repository.
> Default HACS store listing is pending review ([hacs/default#6907](https://github.com/hacs/default/pull/6907)) — once merged, the install will be a one-click search.

The integration ships as a HACS custom repository with:

- TV as a full `media_player` entity (power, volume, mute, app name, play state)
- Auto-discovery of LG / Samsung / Roku / Android TV / Fire TV on your LAN
- `media_player.play_media` with content resolution — `"netflix:Frieren:s2e8"`, `"youtube:lofi beats"`, `"spotify:track name"`
- Interruption-aware pause/duck on configurable sensors (phone ringing → pause, doorbell → duck to 10%)

## Install (today)

```
HACS → ⋮ (top right) → Custom repositories
  Repository: https://github.com/Hybirdss/smartest-tv
  Category:   Integration
```

Then in Home Assistant:

```
Settings → Devices & Services → Add integration → Smartest TV
```

The integration will scan your network for TVs and walk you through pairing. Manual IP entry is also available.

## Requirements

The HA host must be able to install `stv[all]` (pulled automatically by the manifest). Python 3.11+ is required for the stv package itself — Home Assistant OS 2024.1+ ships with a compatible Python.

For LG webOS TVs you'll see a pairing popup on the TV the first time HA tries to connect; approve it once and the client key is saved to `~/.homeassistant/.storage/smartest_tv_keys/` (or the equivalent under your HA config dir).

## Entities

Each configured TV produces one `media_player.<tv_name>` entity with:

- `state`: `on` / `off`
- `volume_level`: 0.0–1.0
- `is_volume_muted`: bool
- `app_name`: currently foregrounded app
- `supported_features`: TURN_ON, TURN_OFF, VOLUME_SET, VOLUME_MUTE, VOLUME_STEP, PLAY_MEDIA, PLAY, PAUSE, STOP

## Automation examples

Play something on TV at sunset:

```yaml
automation:
  - alias: "Movie at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: media_player.play_media
      target:
        entity_id: media_player.living_room_tv
      data:
        media_content_type: video
        media_content_id: "netflix:Wednesday:s1e1"
```

Duck TV volume when the doorbell rings (requires configuring the doorbell sensor in the integration's options flow):

```yaml
# Options → Interrupt sensors → add:
# {"entity_id": "binary_sensor.doorbell", "action": "duck", "duck_volume": 0.1}
```

TV off at midnight:

```yaml
automation:
  - alias: "TV off at midnight"
    trigger:
      platform: time
      at: "00:00:00"
    action:
      service: media_player.turn_off
      target:
        entity_id: media_player.living_room_tv
```

## Shell-command fallback (if you prefer not to install the integration)

If you'd rather keep HA clean and drive the TV from shell commands, the `stv` CLI works too:

```yaml
# configuration.yaml
shell_command:
  tv_off: "stv off"
  tv_volume_night: "stv volume 15"
  tv_play_kids: "stv play youtube 'baby shark'"
```

This needs `stv` installed in the HA Python environment and `~/.config/smartest-tv/config.toml` populated. For multi-TV homes, pass `--tv <name>` on each command or use environment variables:

```yaml
shell_command:
  bedroom_tv_off: "TV_PLATFORM=samsung TV_IP=192.168.1.101 stv off"
  living_room_tv_off: "TV_PLATFORM=lg TV_IP=192.168.1.100 stv off"
```

The native integration is preferred — it exposes proper entities, supports play_media, and participates in HA's power/state model.
