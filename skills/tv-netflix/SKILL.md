---
name: tv-netflix
description: "Play specific Netflix content on TV — finds episode IDs automatically via page scraping. Use when the user asks to play a Netflix show, specific episode, or movie on their TV. Triggers on: 'play X on Netflix', 'Netflix episode', show name + episode number, any language requesting Netflix playback on TV."
---

# tv-netflix — Netflix Deep Link Resolver

> **PREREQUISITE:** Read `../tv-shared/SKILL.md` for CLI reference and deep link rules.

Play specific Netflix episodes or movies on the TV by finding their internal IDs.

## The Problem

Netflix doesn't expose episode IDs publicly. You can't just say "Frieren S2E8" — you need the numeric ID `82656797`. This skill teaches you how to find it.

## Workflow

### Step 1: Find the show's title ID

Web search for `{show name} netflix` to find `netflix.com/title/{titleId}`.

### Step 2: Get episode videoIds via Playwright

Navigate to the title page (works without login):

```
mcp__playwright-plus__browser_navigate(url="https://www.netflix.com/title/{titleId}")
```

For multi-season shows, select the season:

```
mcp__playwright-plus__browser_select_option(
  element="Season selector dropdown",
  ref="{combobox_ref}",
  values=["Season 2"]       # Or localized: "시즌 2", "シーズン 2", etc.
)
```

### Step 3: Extract IDs from page JavaScript

```javascript
mcp__playwright-plus__browser_evaluate(function=`() => {
  const scripts = document.querySelectorAll('script');
  let ids = [];
  scripts.forEach(s => {
    const text = s.textContent || '';
    const matches = text.match(/"videoId":(\d+)/g);
    if (matches) ids.push(...matches.map(m => m.match(/(\d+)/)[0]));
  });
  return [...new Set(ids)];
}`)
```

### Step 4: Map episode number to ID

Episode IDs are sequential. Filter out:
- The show's title ID (e.g. `81726714`)
- Recommended title IDs (random, non-sequential)

Find the sequential cluster. First sequential ID = Episode 1.

**Shortcut:** `first_episode_id + (episode_number - 1)`

### Step 5: Play on TV

```bash
stv close netflix
sleep 2
stv launch netflix {episodeId}
```

## Example

User: "Play Frieren season 2 episode 8"

1. Search → `netflix.com/title/81726714`
2. Playwright → select Season 2 → extract videoIds
3. Sequential cluster: `82656790`–`82656799`
4. S2E8 = `82656790 + 7` = `82656797`
5. `stv close netflix && sleep 2 && stv launch netflix 82656797`

## Movies

Movies are simpler — the title ID is also the watch ID:

1. Search → `netflix.com/title/{id}`
2. `stv launch netflix {id}`

No need for the Playwright step.
