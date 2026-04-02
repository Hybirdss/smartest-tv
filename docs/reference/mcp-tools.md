# MCP Tools Reference

All MCP tools exposed by the smartest-tv server. Start the server with:

```bash
python -m smartest_tv.server
```

All tools accept an optional `tv_name` parameter to target a specific TV in multi-TV setups. See [Multi-TV Setup](../guides/multi-tv.md).

---

## Power

### `tv_on(tv_name?)`
Turn on the TV (Wake-on-LAN or platform equivalent).

### `tv_off(tv_name?)`
Turn off the TV (standby).

---

## Volume

### `tv_volume(tv_name?) → dict`
Get current volume and mute state.

```json
{"volume": 25, "muted": false}
```

### `tv_set_volume(level: int, tv_name?) → str`
Set volume 0–100.

### `tv_volume_up(tv_name?) → str`
Increase volume by one step.

### `tv_volume_down(tv_name?) → str`
Decrease volume by one step.

### `tv_mute(mute: bool | None = None, tv_name?) → str`
Mute, unmute, or toggle. Pass `true`/`false` to force a state, omit to toggle.

---

## Apps

### `tv_launch(app: str, content_id?: str, tv_name?) → str`
Launch an app with optional deep link.

| Parameter | Description |
|-----------|-------------|
| `app` | App name (`netflix`, `youtube`, `spotify`, etc.) or raw app ID |
| `content_id` | Netflix episode ID, YouTube video ID, or Spotify URI |

### `tv_close(app: str, tv_name?) → str`
Close a running app.

### `tv_apps(tv_name?) → list[dict]`
List installed apps.

```json
[{"id": "netflix", "name": "Netflix"}, ...]
```

---

## Media Playback

### `tv_play(tv_name?) → str`
Resume playback.

### `tv_pause(tv_name?) → str`
Pause playback.

### `tv_stop(tv_name?) → str`
Stop playback.

---

## Status & Info

### `tv_status(tv_name?) → dict`
Current TV state.

```json
{
  "platform": "lg",
  "current_app": "netflix",
  "volume": 20,
  "muted": false,
  "sound_output": "tv_speaker"
}
```

### `tv_info(tv_name?) → dict`
System info.

```json
{
  "platform": "lg",
  "model": "OLED55C3",
  "firmware": "04.30.04",
  "ip": "192.168.1.100",
  "name": "Living Room TV"
}
```

---

## Notifications

### `tv_notify(message: str, tv_name?) → str`
Show a toast notification on screen.

---

## Screen

### `tv_screen_off(tv_name?) → str`
Turn off the screen while keeping audio playing.

### `tv_screen_on(tv_name?) → str`
Turn the screen back on.

---

## Content Resolution & Playback

### `tv_cast(url: str, tv_name?) → str`
Cast a streaming URL to the TV. Accepts Netflix, YouTube, and Spotify links.

| Parameter | Description |
|-----------|-------------|
| `url` | `https://www.netflix.com/watch/ID`, `https://www.youtube.com/watch?v=ID`, `https://open.spotify.com/track/ID`, etc. |

Netflix `/title/` URLs are resolved to an episode ID automatically.

### `tv_resolve(platform, query, season?, episode?, title_id?) → str`
Resolve content to a platform-specific ID without playing it.

| Parameter | Description |
|-----------|-------------|
| `platform` | `netflix`, `youtube`, or `spotify` |
| `query` | Content name |
| `season` | Season number (Netflix TV shows) |
| `episode` | Episode number (Netflix TV shows) |
| `title_id` | Netflix title ID — skips web search |

Returns the content ID string (e.g. `"82656797"` for Netflix, `"dQw4w9WgXcQ"` for YouTube).

### `tv_play_content(platform, query, season?, episode?, title_id?, tv_name?) → str`
Resolve and play in one step. For Netflix, closes the app first automatically.
Records the play to history. Same parameters as `tv_resolve`.

---

## History

### `tv_history(limit: int = 10) → list[dict]`
Return recent play history.

```json
[{
  "platform": "netflix",
  "query": "Frieren",
  "content_id": "82656797",
  "time": 1743700000,
  "season": 2,
  "episode": 8
}]
```

`season` and `episode` are only present for Netflix TV shows.

### `tv_next(query?: str, tv_name?) → str`
Play the next episode of a Netflix show from history. If `query` is omitted,
continues the most recently watched Netflix show.

---

## Queue

### `tv_queue_add(platform, query, season?, episode?) → str`
Add content to the play queue.

### `tv_queue_show() → list[dict]`
Show the current play queue.

### `tv_queue_play(tv_name?) → str`
Pop the first item from the queue, resolve it, and play it on TV.

### `tv_queue_clear() → str`
Clear the entire play queue.

---

## Trending & Recommendations

### `tv_whats_on(platform?: str, limit: int = 10) → str`
Show trending content on Netflix or YouTube.

| Parameter | Description |
|-----------|-------------|
| `platform` | `"netflix"`, `"youtube"`, or `None` for both |
| `limit` | Number of results per platform |

### `tv_recommend(mood?: str, limit: int = 5) → str`
Get personalized content recommendations based on watch history.

| Parameter | Description |
|-----------|-------------|
| `mood` | `"chill"`, `"action"`, `"kids"`, `"random"`, or omit |
| `limit` | Number of recommendations |

---

## Scenes

### `tv_scene_list() → list[dict]`
List all available scene presets (built-in and custom).

Built-in scenes: `movie-night`, `kids`, `sleep`, `music`.

### `tv_scene_run(name: str, tv_name?) → str`
Run a scene preset — executes all steps in order.

Custom scenes are defined in `~/.config/smartest-tv/scenes.json`.

---

## Multi-TV

### `tv_list_tvs() → list[dict]`
List all configured TVs.

```json
[
  {"name": "living-room", "platform": "lg", "ip": "192.168.1.100", "default": true},
  {"name": "bedroom", "platform": "samsung", "ip": "192.168.1.101", "default": false}
]
```
