# Playing Content

stv finds content IDs and plays them on your TV in one step.

## Play by name

```bash
stv play netflix "Frieren" s2e8
stv play netflix "Frieren" -s 2 -e 8
stv play netflix "Frieren" -s 2 -e 8 --title-id 81726714

stv play youtube "baby shark"
stv play spotify "Ye White Lines"
stv play spotify "spotify:album:5poA9SAx0Xiz1cd17fWBLS"
```

For Netflix, stv resolves the episode ID and closes the app before relaunching with the deep link (required for deep links to work). Play is recorded to history.

**Inline S/E notation** — append to the query as the last argument:

| Format | Example | Result |
|--------|---------|--------|
| `sNeM` | `s2e8` | season=2, episode=8 |
| `SNNEM` | `S02E08` | season=2, episode=8 |
| `NxM` | `2x8` | season=2, episode=8 |

## Cast a URL

```bash
stv cast https://www.netflix.com/watch/82656797
stv cast https://www.netflix.com/title/81726714
stv cast https://www.youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://youtu.be/dQw4w9WgXcQ
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
stv cast https://open.spotify.com/album/xxx
stv cast https://open.spotify.com/playlist/xxx
```

For Netflix `/title/` URLs, stv resolves the title to an episode ID automatically.

## Search without playing

```bash
stv search netflix "Frieren"
# Output:
#   Netflix ID: 81726714
#   URL: https://www.netflix.com/title/81726714
#   2 seasons:
#     S1: 81726716–81726725 (10 eps)
#     S2: 82656790–82656799 (10 eps)

stv search spotify "Ye White Lines"
# Output:
#   URI: spotify:track:3bbjDFVu9BtFtGD2fZpVfz

stv search youtube "baby shark"
# Output:
#   XqZsoesa55w  Baby Shark Dance | #babyshark ...
#   ...
```

## Resolve a content ID

Get the ID without playing:

```bash
stv resolve netflix "Frieren" s2e8
stv resolve netflix "Frieren" -s 2 -e 8
stv resolve netflix "The Glory" --title-id 81519223 -s 1 -e 1
stv resolve youtube "baby shark"
stv resolve spotify "Ye White Lines"
```

All resolution options:

| Option | Description |
|--------|-------------|
| `-s, --season INT` | Season number (Netflix) |
| `-e, --episode INT` | Episode number (Netflix) |
| `--title-id INT` | Netflix title ID — skips web search |

## History and continue watching

```bash
stv history            # recent plays (default: last 10)
stv history -n 5       # last 5

stv next               # play next episode of most recently watched Netflix show
stv next "Frieren"     # next episode of a specific show
```

## Queue

```bash
# Queue is managed via MCP tools — see guides/ai-agents.md
# tv_queue_add, tv_queue_show, tv_queue_play, tv_queue_clear
```

## How resolution works

Three-tier lookup for each platform:

1. **Local cache** — `~/.config/smartest-tv/cache.json`, instant (~0.1s)
2. **Community cache** — crowdsourced IDs via GitHub raw CDN
3. **Web fallback** — Netflix: curl title page + parse `__typename:"Episode"`. YouTube: yt-dlp. Spotify: Brave Search.

Netflix episode IDs within a season are consecutive integers, so one HTTP request resolves every episode of every season. No Playwright, no login required.

## Cache management

```bash
stv cache show                     # print all cached IDs
stv cache get netflix "Frieren" -s 2 -e 8

# Add an entry manually
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714
stv cache set youtube "baby shark" --content-id XqZsoesa55w
stv cache set spotify "Ye Vultures" --content-id "spotify:album:xxx"

stv cache contribute               # export local cache for community PR
```
