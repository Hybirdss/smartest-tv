---
name: tv-youtube
description: "Play YouTube videos on TV — finds video IDs via yt-dlp search. Use when the user asks to play a YouTube video, specific anime episode, music video, or any video content on their TV. Triggers on: 'YouTube에서 틀어', 'play X on YouTube', video name + 'TV에서'."
---

# tv-youtube — YouTube Video Resolver

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference. Requires `yt-dlp` on PATH.

## Workflow

### Step 1: Search with yt-dlp

```bash
yt-dlp "ytsearch5:{search query}" --get-id --get-title --no-download
```

Returns up to 5 results with title + video ID pairs. Pick the best match.

### Step 2: Play on TV

```bash
tv launch youtube {videoId}
```

No need to close YouTube first — deep links work on an already-open app.

## Search Tips

Good search queries make or break the results:

| Want | Search query |
|------|-------------|
| Official anime episode | `"gundam witch from mercury episode 2 official gundam.info"` |
| Music video | `"NewJeans How Sweet official MV"` |
| Kids content | `"baby shark pinkfong official"` |
| Live stream | `"lofi hip hop radio live"` |
| Specific channel | `"veritasium latest"` |

Add `official` to avoid fan re-uploads. Add the channel name if you know it.

### For Korean content

Try both Korean and English titles — English often gets better results for official uploads:

```bash
# Korean title
yt-dlp "ytsearch5:수성의마녀 2화 공식" --get-id --get-title --no-download

# English title (often better for official channels)
yt-dlp "ytsearch5:gundam witch from mercury episode 2 official" --get-id --get-title --no-download
```

## Example

User: "유튜브에서 수성의마녀 2화 틀어줘"

```bash
yt-dlp "ytsearch5:gundam witch from mercury episode 2 official gundam.info" \
  --get-id --get-title --no-download
# → GRSbJFWP7pc (Mobile Suit Gundam the Witch from Mercury #2)

tv launch youtube GRSbJFWP7pc
```
