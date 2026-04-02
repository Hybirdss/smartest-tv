# Cache Format

**Location:** `~/.config/smartest-tv/cache.json`

The local cache stores resolved content IDs and play history. All repeated plays are served from this file (~0.1s).

## Structure

```json
{
  "netflix": {
    "frieren": {
      "title_id": 81726714,
      "seasons": {
        "1": {"first_episode_id": 81726716, "episode_count": 10},
        "2": {"first_episode_id": 82656790, "episode_count": 10}
      }
    }
  },
  "youtube": {
    "baby-shark": "XqZsoesa55w"
  },
  "spotify": {
    "ye-white-lines": "spotify:track:3bbjDFVu9BtFtGD2fZpVfz"
  },
  "_history": [
    {
      "platform": "netflix",
      "query": "Frieren",
      "content_id": "82656797",
      "time": 1743700000,
      "season": 2,
      "episode": 8
    }
  ],
  "_queue": []
}
```

## Keys

Cache keys are slugified versions of the query: lowercase, spaces replaced
with hyphens, special characters stripped.

`"Frieren"` → `"frieren"`  
`"Baby Shark"` → `"baby-shark"`  
`"Jujutsu Kaisen"` → `"jujutsu-kaisen"`

## Netflix episodes

Netflix episode IDs are sequential integers within a season:

- S1E1 = `first_episode_id`
- S1E2 = `first_episode_id + 1`
- S1E10 = `first_episode_id + 9`

Storing `first_episode_id` + `episode_count` per season is enough to compute any episode ID.

## YouTube and Spotify

YouTube: direct video ID string (e.g. `"XqZsoesa55w"`).

Spotify: full URI string (e.g. `"spotify:track:3bbjDFVu9BtFtGD2fZpVfz"`).

## History entries

| Field | Type | Description |
|-------|------|-------------|
| `platform` | str | `netflix`, `youtube`, or `spotify` |
| `query` | str | Original search query |
| `content_id` | str | Resolved content ID |
| `time` | int | Unix timestamp |
| `season` | int | Season number (Netflix only) |
| `episode` | int | Episode number (Netflix only) |

## CLI commands

```bash
stv cache show               # print full cache JSON
stv cache get netflix "Frieren" -s 2 -e 8
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714
stv cache contribute         # export for community cache PR (history stripped)
```
