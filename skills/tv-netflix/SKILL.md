---
name: tv-netflix
description: "Play Netflix content on TV — resolves episode IDs automatically via HTTP scraping. Use when the user asks to play a Netflix show, specific episode, or movie on their TV. Triggers on: 'play X on Netflix', 'Netflix episode', show name + episode number."
---

# tv-netflix — Netflix Content Resolver

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference.

Play specific Netflix episodes or movies on the TV.

## The Simple Way

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714
```

One command. Resolves the episode ID, closes Netflix, relaunches with deep link. Done.

## How It Works

### Step 1: Find the title ID

Web search for `{show name} site:netflix.com` → extract from URL `netflix.com/title/{titleId}`.

### Step 2: Play

```bash
# Episodes
stv play netflix "Frieren" s2e8 --title-id 81726714
stv play netflix "Jujutsu Kaisen" s3e10 --title-id 81278456

# Movies (title ID = video ID)
stv play netflix "Inception" --title-id 70131314
```

### Step 3: There is no step 3

`stv` handles everything:
1. Fetches Netflix title page via `curl` (no browser needed)
2. Parses `__typename:"Episode"` from embedded JSON to find episode IDs
3. Groups sequential IDs into seasons automatically
4. Caches all seasons — second play is instant (0.1s)
5. Closes Netflix and relaunches with deep link

## Cached Playback

After first resolve, the title ID is no longer needed:

```bash
stv play netflix "Frieren" s2e8     # cached, 0.1s
stv cache show                       # see all cached shows
```

## Manual Cache (fallback)

If auto-resolve fails for a specific show:

```bash
stv cache set netflix "Show Name" -s 2 --first-ep-id 82656790 --count 10 --title-id 81726714
```

## Notes

- User must select Netflix profile on TV (can't be bypassed externally)
- After profile selection, content plays automatically
- Deep links require close-then-relaunch — `stv play` handles this automatically
