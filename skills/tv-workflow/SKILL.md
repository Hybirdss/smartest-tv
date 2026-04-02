---
name: tv-workflow
description: "Composite TV workflows — movie night, kids mode, sleep timer, morning routine. Use when the user wants to do multiple TV actions at once, or asks for a 'mode' or 'routine'. Triggers on: 'movie night', 'kids mode', 'good night', '영화 모드', '아이 모드', 'morning TV', composite requests like 'game mode on HDMI 2 and lower volume'."
---

# tv-workflow — Composite TV Actions

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference.

Combine multiple `tv` commands to handle complex requests in one shot.

## Recipes

### Movie Night

User: "Movie night" / "영화 모드"

```bash
tv volume 20
tv launch netflix {contentId}     # if they named a title
# Or just: tv launch netflix      # if no specific title
```

### Kids Mode

User: "아이한테 유튜브 틀어줘" / "Put on something for the kids"

1. Search for age-appropriate content via yt-dlp:
   ```bash
   yt-dlp "ytsearch5:cocomelon nursery rhymes official" --get-id --get-title --no-download
   ```
2. Pick the best result
3. Launch:
   ```bash
   tv volume 15
   tv launch youtube {videoId}
   ```

### Music Mode

User: "음악 모드" / "Screen off, play music"

```bash
tv launch spotify {uri}
tv screen-off                  # screen off, audio continues
```

### Sleep Timer

User: "30분 뒤에 TV 꺼줘" / "Turn off TV in 30 minutes"

```bash
sleep 1800 && tv off
```

Run in background if needed: `(sleep 1800 && tv off) &`

### Game Mode

User: "게임 모드" / "Switch to game mode on HDMI 2"

```bash
tv launch hdmi2
# Picture mode may require platform-specific commands
```

### Good Night

User: "잘자" / "Good night"

```bash
tv off
```

### Morning Routine

User: "TV 켜고 뉴스 틀어줘"

```bash
tv on
sleep 5                        # wait for boot
tv volume 15
tv launch youtube {newsVideoId}
```

## Pattern

When the user asks for something composite:

1. Parse into individual actions (volume, app, input, screen, power)
2. Order them logically (power on → wait → set volume → launch app)
3. Execute via `tv` CLI commands in sequence
4. Report what was done

The AI decides the sequence. These recipes are starting points, not rigid scripts.
