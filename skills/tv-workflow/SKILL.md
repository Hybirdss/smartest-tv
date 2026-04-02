---
name: tv-workflow
description: "Composite TV workflows — movie night, kids mode, sleep timer, morning routine. Use when the user wants multiple TV actions at once, or asks for a 'mode' or 'routine'. Triggers on: 'movie night', 'kids mode', 'good night', 'morning TV', composite requests like 'game mode on HDMI 2 and lower volume'."
---

# tv-workflow — Composite TV Actions

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference.

Combine multiple `tv` commands to handle complex requests in one shot.

## Recipes

### Movie Night

User: "Movie night" / "영화 모드"

```bash
stv volume 20
stv launch netflix {contentId}     # if they named a title
# Or just: stv launch netflix      # if no specific title
```

### Kids Mode

User: "Put on something for the kids"

1. Search for age-appropriate content via yt-dlp:
   ```bash
   yt-dlp "ytsearch5:cocomelon nursery rhymes official" --get-id --get-title --no-download
   ```
2. Pick the best result
3. Launch:
   ```bash
   stv volume 15
   stv launch youtube {videoId}
   ```

### Music Mode

User: "Screen off, play music"

```bash
stv launch spotify {uri}
stv screen-off                  # screen off, audio continues
```

### Sleep Timer

User: "Turn off TV in 30 minutes"

```bash
sleep 1800 && stv off
```

Run in background if needed: `(sleep 1800 && stv off) &`

### Game Mode

User: "Switch to game mode on HDMI 2"

```bash
stv launch hdmi2
# Picture mode may require platform-specific commands
```

### Good Night

User: "Good night"

```bash
stv off
```

### Morning Routine

User: "TV 켜고 뉴스 틀어줘"

```bash
stv on
sleep 5                        # wait for boot
stv volume 15
stv launch youtube {newsVideoId}
```

## Pattern

When the user asks for something composite:

1. Parse into individual actions (volume, app, input, screen, power)
2. Order them logically (power on → wait → set volume → launch app)
3. Execute via `tv` CLI commands in sequence
4. Report what was done

The AI decides the sequence. These recipes are starting points, not rigid scripts.
