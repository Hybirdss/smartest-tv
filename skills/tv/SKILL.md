---
name: tv
description: "Control a smart TV with natural language. Play Netflix episodes/movies, YouTube videos, Spotify music. Also handles volume, power, notifications, and composite workflows (movie night, kids mode, sleep timer). Triggers on: 'play', 'watch', '틀어줘', '재생', 'TV', 'Netflix', 'YouTube', 'Spotify', 'volume', 'mute', 'good night', 'movie night', 'kids mode'."
---

# smartest-tv

Control a smart TV via the `stv` CLI. One command per action, no API keys, no browser needed.

## Play Content

```bash
stv play netflix "Frieren" s2e8              # Netflix episode (auto title ID lookup)
stv play netflix "Inception" --title-id 70131314  # Netflix movie
stv play youtube "baby shark"                # YouTube (yt-dlp search)
stv play spotify "Ye White Lines"            # Spotify (web search)
stv play spotify spotify:album:5poA9SAx0X... # Spotify direct URI
```

`stv play` does everything: search → resolve ID → cache → close app (Netflix) → deep link → launch.

## Search (find IDs without playing)

```bash
stv search netflix "Jujutsu Kaisen"   # Shows title ID + all seasons
stv search spotify "Kendrick Lamar"   # Shows URI
stv search youtube "lofi hip hop"     # Shows top results with IDs
```

## Resolve (get bare content ID)

```bash
stv resolve netflix "Frieren" s2e8    # → 82656797
stv resolve youtube "baby shark"      # → XqZsoesa55w
```

## TV Control

```bash
stv status          # Current app, volume, mute
stv volume 25       # Set volume
stv mute            # Toggle mute
stv on              # Wake-on-LAN
stv off             # Power off
stv notify "msg"    # Toast notification on screen
stv apps            # List installed apps
```

## Cache

Results are cached locally. Second play is instant (~0.1s).

```bash
stv cache show      # View all cached IDs
stv cache set netflix "Show" -s 2 --first-ep-id 12345 --count 10  # Manual seed
```

## Composite Workflows

Combine commands for complex requests:

**Movie night**: `stv volume 20 && stv play netflix "Inception" --title-id 70131314`

**Kids mode**: `stv volume 15 && stv play youtube "cocomelon nursery rhymes"`

**Music mode**: `stv play spotify "jazz playlist" && stv screen-off` (screen off, audio continues)

**Sleep timer**: `(sleep 2700 && stv off) &` (45 min timer)

**Good night**: `stv off`

**Game mode**: `stv launch hdmi2`

## Netflix Notes

- First time playing a show requires web search (~2-3s). After that, cached.
- User must select Netflix profile on TV (can't bypass externally).
- For shows not found by auto-search, pass `--title-id` from the URL: `netflix.com/title/XXXXX`

## Output

All commands support `--format json` for structured output.
