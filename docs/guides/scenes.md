# Scene Presets

Scenes run a sequence of TV actions in one command. Use them for common setups like movie night, kids mode, or sleep.

## Built-in scenes

| Scene | What it does |
|-------|-------------|
| `movie-night` | Dim lights cue + volume set + launch app |
| `kids` | Lower volume + launch YouTube |
| `sleep` | Lower volume + screen off |
| `music` | Screen off + launch Spotify |

Run a scene:

```bash
# CLI — not yet exposed as a stv command; use MCP or call directly
```

Via MCP (from Claude or any MCP client):

```
tv_scene_list()        → list all scenes with steps
tv_scene_run("movie-night")
tv_scene_run("sleep")
```

## Custom scenes

Define your own scenes in `~/.config/smartest-tv/scenes.json`:

```json
{
  "gaming": {
    "description": "Switch to HDMI 2 and crank the volume",
    "steps": [
      {"action": "launch", "app": "hdmi2"},
      {"action": "set_volume", "level": 40}
    ]
  },
  "morning": {
    "description": "Wake up: screen on, low volume, YouTube",
    "steps": [
      {"action": "power_on"},
      {"action": "set_volume", "level": 15},
      {"action": "launch", "app": "youtube"}
    ]
  }
}
```

Supported step actions:

| Action | Parameters |
|--------|-----------|
| `power_on` | — |
| `power_off` | — |
| `set_volume` | `level: int` |
| `mute` | `mute: bool` (optional) |
| `launch` | `app: str`, `content_id: str` (optional) |
| `close` | `app: str` |
| `screen_off` | — |
| `screen_on` | — |
| `notify` | `message: str` |

## MCP tools

```
tv_scene_list() → list[dict]
    Returns all scenes (built-in + custom) with name, description, steps.

tv_scene_run(name: str, tv_name: str | None = None) → str
    Executes all steps of the named scene in order.
    Built-in: "movie-night", "kids", "sleep", "music"
    Custom scenes: defined in ~/.config/smartest-tv/scenes.json
```
