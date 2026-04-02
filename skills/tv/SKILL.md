---
name: tv
description: "Control a smart TV with natural language. Play Netflix episodes/movies, YouTube videos, Spotify music. Also handles volume, power, notifications, history, 'continue watching', and composite workflows. Triggers on: 'play', 'watch', '틀어줘', '재생', 'TV', 'Netflix', 'YouTube', 'Spotify', 'volume', 'mute', 'good night', 'movie night', '이어서', 'continue', 'next episode'."
---

# smartest-tv

Control a smart TV via the `stv` CLI. One command per action.

## Platform Detection

The user won't always say the platform. Infer it:

| User says | Platform | Why |
|-----------|----------|-----|
| "Play Frieren S2E8" | **netflix** | TV series with season/episode |
| "Play Inception" | **netflix** | Movie title |
| "Play baby shark" | **youtube** | Kids content, music video, general video |
| "Play Ye White Lines" | **spotify** | Song/artist name + music context |
| "Play jazz playlist" | **spotify** | Playlist/music genre |
| "Play lofi hip hop radio" | **youtube** | Live stream / radio |

When ambiguous, prefer: Netflix (series/movies) > YouTube (videos) > Spotify (music).

## Play Content

```bash
stv play netflix "Frieren" s2e8          # Netflix episode
stv play netflix "Inception"             # Netflix movie (auto title ID)
stv play youtube "baby shark"            # YouTube video
stv play spotify "Ye White Lines"        # Spotify track
```

Everything is automatic: search → resolve → cache → deep link → launch.

## Continue Watching / Next Episode

```bash
stv next                    # Continue the most recent Netflix show
stv next Frieren            # Next episode of Frieren specifically
stv history                 # Show recent plays
```

"이어서 봐", "다음 화", "continue watching" → use `stv next`.

## Search & Resolve

```bash
stv search netflix "Jujutsu Kaisen"   # Title ID + all seasons
stv resolve netflix "Frieren" s2e8    # → 82656797
```

## TV Control

```bash
stv status       # Current app, volume, mute
stv volume 25    # Set volume
stv mute         # Toggle mute
stv on / off     # Power
stv notify "msg" # Toast on screen
```

## Composite Workflows

**Movie night**: `stv volume 20 && stv play netflix "Inception"`

**Kids mode**: `stv volume 15 && stv play youtube "cocomelon"`

**Music mode**: `stv play spotify "jazz" && sleep 1 && stv screen-off`

**Sleep timer**: `(sleep 2700 && stv off) &`

**Good night**: `stv off`

## Notes

- All commands support `--format json`
- First Netflix play: ~2-3s (web search). After that: ~0.1s (cached)
- Netflix profile selection happens on TV (can't skip)
- If auto-search fails: `stv play netflix "X" --title-id XXXXX`
