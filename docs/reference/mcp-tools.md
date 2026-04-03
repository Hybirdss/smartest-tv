# MCP Tools Reference

18 tools optimized for AI agents. Each tool does more so agents make fewer decisions.

Start the server:

```bash
python -m smartest_tv          # stdio (Claude Code)
stv serve --port 8910          # HTTP (remote agents)
```

All tools accept an optional `tv_name` parameter to target a specific TV. Omit it to use the default TV. See [Multi-TV Setup](../guides/multi-tv.md).

---

## Content Playback

### `tv_play(platform, query, season?, episode?, title_id?, tv_name?)`

**The primary tool.** Find content by name and play it on TV. Resolves the content ID automatically, deep-links into the app.

| Parameter | Description |
|-----------|-------------|
| `platform` | `"netflix"`, `"youtube"`, or `"spotify"` |
| `query` | Content name (e.g. "Stranger Things", "baby shark") |
| `season` | Season number (Netflix series only) |
| `episode` | Episode number (Netflix series only) |
| `title_id` | Netflix title ID if already known (skips search) |

```
tv_play("netflix", "Stranger Things", season=4, episode=7)
tv_play("youtube", "baby shark")
tv_play("spotify", "Ye White Lines")
```

### `tv_cast(url, tv_name?)`

Cast a Netflix/YouTube/Spotify URL directly. No need to parse the platform or ID — stv handles it.

```
tv_cast("https://youtube.com/watch?v=dQw4w9WgXcQ")
tv_cast("https://netflix.com/watch/82656797")
tv_cast("https://open.spotify.com/track/3bbjDFVu...")
```

### `tv_next(query?, tv_name?)`

Play the next episode. Continues from watch history.

- Omit `query` to continue the most recent Netflix show.
- Provide `query` to continue a specific show.

### `tv_launch(app, content_id?, tv_name?)`

Launch an app with optional deep link. Use `tv_play` instead if you have a content name (not an ID).

| Parameter | Description |
|-----------|-------------|
| `app` | App name (`netflix`, `youtube`, `spotify`) or raw app ID |
| `content_id` | Platform-specific content ID for deep linking |

### `tv_resolve(platform, query, season?, episode?, title_id?) -> str`

Resolve a content name to its platform ID **without playing**. Returns the content ID string.

---

## Discovery

### `tv_whats_on(platform?, limit?) -> str`

Show trending content on Netflix and/or YouTube.

| Parameter | Description |
|-----------|-------------|
| `platform` | `"netflix"`, `"youtube"`, or omit for both |
| `limit` | Number of results per platform (default 10) |

### `tv_recommend(mood?, limit?) -> str`

Get personalized recommendations based on watch history + trending.

| Parameter | Description |
|-----------|-------------|
| `mood` | `"chill"`, `"action"`, `"kids"`, `"random"`, or omit for auto |
| `limit` | Number of recommendations (default 5) |

---

## TV Control

### `tv_power(on, tv_name?)`

Turn TV on or off.

- `on=True` — power on (Wake-on-LAN or platform equivalent)
- `on=False` — power off (standby)

### `tv_volume(level?, direction?, mute?, tv_name?)`

All volume control in one tool:

| Usage | What it does |
|-------|-------------|
| No args | Returns current volume + mute status |
| `level=25` | Set volume to 25 |
| `direction="up"` | Step volume up |
| `direction="down"` | Step volume down |
| `mute=True` | Mute |
| `mute=False` | Unmute |

### `tv_screen(on, tv_name?)`

Turn screen on or off. Audio continues when screen is off.

- `on=True` — screen on
- `on=False` — screen off (audio continues)

### `tv_notify(message, tv_name?)`

Show a toast notification on the TV screen.

### `tv_status(tv_name?) -> dict`

Get current TV state: app, volume, mute, model.

```json
{
  "platform": "lg",
  "model": "OLED55C3",
  "current_app": "netflix",
  "volume": 20,
  "muted": false
}
```

---

## Queue

### `tv_queue(action, platform?, query?, season?, episode?, tv_name?)`

Manage the play queue — all operations in one tool.

| Action | Required params | Description |
|--------|----------------|-------------|
| `"add"` | `platform`, `query` | Add content to queue |
| `"show"` | — | Show current queue |
| `"play"` | — | Pop first item, resolve, and play |
| `"skip"` | — | Skip first item |
| `"clear"` | — | Clear entire queue |

```
tv_queue("add", "youtube", "Gangnam Style")
tv_queue("add", "netflix", "Dark", season=1, episode=1)
tv_queue("show")
tv_queue("play")
tv_queue("clear")
```

---

## Scenes

### `tv_scene(action?, name?, tv_name?)`

Run or list scene presets — all operations in one tool.

| Action | Description |
|--------|-------------|
| `"list"` (default) | Show all available scenes |
| `"run"` | Execute a scene (requires `name`) |

Built-in scenes: `movie-night`, `kids`, `sleep`, `music`.

```
tv_scene("list")
tv_scene("run", "movie-night")
tv_scene("run", "kids", tv_name="kids-room")
```

Custom scenes: `~/.config/smartest-tv/scenes.json`. See [Scenes Guide](../guides/scenes.md).

---

## History

### `tv_history(limit?) -> list[dict]`

Return recent play history.

```json
[{
  "platform": "netflix",
  "query": "Wednesday",
  "content_id": "82656797",
  "time": 1743700000,
  "season": 2,
  "episode": 8
}]
```

---

## Multi-TV & Sync

### `tv_list_tvs() -> list[dict]`

List all configured TVs (local and remote).

```json
[
  {"name": "living-room", "platform": "lg", "ip": "192.168.1.100", "default": true},
  {"name": "bedroom", "platform": "samsung", "ip": "192.168.1.101", "default": false},
  {"name": "friend", "platform": "remote", "ip": "", "default": false}
]
```

### `tv_groups() -> list[dict]`

List all TV groups and their members.

```json
[{"name": "home", "members": ["living-room", "bedroom"]}]
```

### `tv_sync(platform, query, tv_names?, group?, season?, episode?, title_id?)`

Play content on multiple TVs simultaneously. Resolves the content ID once, then launches on all targets via asyncio.gather.

| Parameter | Description |
|-----------|-------------|
| `platform` | `netflix`, `youtube`, or `spotify` |
| `query` | Content name |
| `tv_names` | List of TV names. Or use `group`. |
| `group` | TV group name (e.g. `"party"`) |
| `season` | Netflix season number |
| `episode` | Netflix episode number |
| `title_id` | Netflix title ID if known |

```
tv_sync("netflix", "Wednesday", season=1, episode=1, group="party")
tv_sync("youtube", "lo-fi beats", tv_names=["living-room", "bedroom"])
```

---

## Tool Count Summary

| Category | Tools | Names |
|----------|-------|-------|
| Content | 5 | tv_play, tv_cast, tv_next, tv_launch, tv_resolve |
| Discovery | 2 | tv_whats_on, tv_recommend |
| Control | 5 | tv_power, tv_volume, tv_screen, tv_notify, tv_status |
| Queue | 1 | tv_queue (5 actions) |
| Scenes | 1 | tv_scene (2 actions) |
| History | 1 | tv_history |
| Multi-TV | 3 | tv_list_tvs, tv_groups, tv_sync |
| **Total** | **18** | |
