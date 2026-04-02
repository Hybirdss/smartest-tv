# Contributing to the Community Cache

The community cache (`community-cache.json`) stores Netflix content IDs that
have been discovered and verified by users. Once an ID is in the cache, every
`stv` user gets instant playback for that title — no HTTP scraping required.

This document explains how to find the IDs yourself and how to submit them.

---

## How the Cache Works

Netflix episode IDs are sequential integers. Each season starts at a
`first_episode_id` and the IDs increment by 1 for each episode:

- S1E1 = `first_episode_id`
- S1E2 = `first_episode_id + 1`
- S1E10 = `first_episode_id + 9`

The cache format stores only the first ID and the episode count per season:

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
  }
}
```

---

## Finding the Netflix title_id

The `title_id` is the number in the Netflix URL when you open a show's page.

1. Open Netflix in a browser and navigate to the show's page (not a specific episode).
2. Look at the URL: `https://www.netflix.com/title/81726714`
3. The number after `/title/` is the `title_id`.

You can also use `stv search`:

```bash
stv search netflix "Frieren"
# Output:
#   Netflix ID: 81726714
#   URL: https://www.netflix.com/title/81726714
#   2 seasons: ...
```

---

## Finding episode_id (first_episode_id)

### Method 1: stv search (recommended)

`stv search` scrapes the Netflix title page and shows you all season episode IDs:

```bash
stv search netflix "Frieren"
# Output:
#   S1: 81726716–81726725 (10 eps)
#   S2: 82656790–82656799 (10 eps)
```

The first number in each range is `first_episode_id`.

### Method 2: Browser DevTools

1. Open the Netflix title page in Chrome or Firefox.
2. Open DevTools → Network tab.
3. Reload the page and filter by `title` in the URL bar.
4. Look at the HTML response — search for `"__typename":"Episode","videoId":` in the page source.
5. The Episode videoIds appear in sequential groups, one group per season.

### Method 3: curl

```bash
curl -s "https://www.netflix.com/title/81726714" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Accept-Language: en-US,en;q=0.9" \
  | grep -oP '"__typename":"Episode","videoId":\K\d+'
```

This prints all episode videoIds for the title. Sort them — consecutive runs
are individual seasons.

---

## Submitting a PR

### Step 1 — Verify IDs work

Before submitting, verify the IDs resolve correctly:

```bash
stv cache set netflix "Frieren" -s 1 --first-ep-id 81726716 --count 10 --title-id 81726714
stv resolve netflix "Frieren" -s 1 -e 1    # should return 81726716
stv resolve netflix "Frieren" -s 1 -e 10   # should return 81726725
```

### Step 2 — Export your local cache

```bash
stv cache contribute
```

This prints your local cache in community-cache.json format, with personal
play history stripped.

### Step 3 — Add entries to community-cache.json

Open `community-cache.json` in the repository and merge your entries into the
`netflix` section. The slug key must match `_slugify(title)` — lowercase,
spaces replaced with hyphens, special characters removed.

Example: "Jujutsu Kaisen" → `"jujutsu-kaisen"`

### Step 4 — Open a pull request

PR title format: `cache: add [N] Netflix titles`

---

## PR Rules

- **Do not modify existing entries.** If you believe an existing entry is wrong,
  open an issue instead of changing it — incorrect IDs affect all users.
- **One entry per show.** Do not add duplicate slugs.
- **Episodes only.** Do not add season or show container IDs as episode IDs.
  Use `stv search` which filters these automatically.
- **Verify before submitting.** Run `stv resolve` on at least the first and
  last episode of each season you're adding.

---

## CI Validation

Pull requests that modify `community-cache.json` run an automated validation
that checks:

1. Valid JSON structure.
2. All slugs match the expected lowercase-hyphenated format.
3. `first_episode_id` and `episode_count` are positive integers.
4. `title_id` is a positive integer.
5. No existing entries were modified (detected by diffing against base branch).

If CI fails, check the error output — it identifies which entries are malformed.
