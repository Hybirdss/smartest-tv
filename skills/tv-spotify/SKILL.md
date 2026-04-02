---
name: tv-spotify
description: "Play Spotify music on TV — finds album/track/playlist URIs via web search. Use when the user asks to play music, an album, artist, or playlist on their TV via Spotify. Triggers on: 'play X on Spotify', artist/album name + music on TV, any language requesting Spotify playback."
---

# tv-spotify — Spotify URI Resolver

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference.

## Workflow

### Step 1: Find the Spotify URI

Web search for `{artist} {album/track} Spotify` and find the URL:

```
https://open.spotify.com/album/5poA9SAx0Xiz1cd17fWBLS
                          ^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^
                          type   ID
```

Convert URL to URI: `spotify:album:5poA9SAx0Xiz1cd17fWBLS`

### Step 2: Play on TV

```bash
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS
```

## URI Formats

| Type | URI format | Example |
|------|-----------|---------|
| Album | `spotify:album:{id}` | `spotify:album:5poA9SAx0Xiz1cd17fWBLS` |
| Track | `spotify:track:{id}` | `spotify:track:4cOdK2wGLETKBW3PvgPWqT` |
| Playlist | `spotify:playlist:{id}` | `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M` |
| Artist | `spotify:artist:{id}` | `spotify:artist:0Y5tJX1MQlPlqiwlOH1tJY` |

## Example

User: "Play Ye's BULLY album on Spotify"

```bash
# Web search: "Ye BULLY album Spotify"
# → https://open.spotify.com/album/5poA9SAx0Xiz1cf17fWBLS

stv launch spotify spotify:album:5poA9SAx0Xiz1cf17fWBLS
```

## Tips

- "Screen off, play jazz" → `stv screen-off && stv launch spotify spotify:playlist:{id}`
- Spotify deep links work without closing the app first
- For "play some jazz" or vague requests, search for popular curated playlists
