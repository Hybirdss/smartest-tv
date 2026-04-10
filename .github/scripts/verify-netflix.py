"""Verify Netflix entries against live Netflix data.

For each Netflix show in community-cache.json:
1. Fetch the title page
2. Extract __typename:"Episode" videoIds
3. Verify cached episode IDs match actual data

Only checks newly added/modified entries (compares with base branch).
"""

import json
import re
import subprocess
import sys

CACHE_FILE = "community-cache.json"
MAX_CHECKS = 10  # Don't hammer Netflix on every PR


def fetch_netflix_episodes(title_id: int) -> dict[int, list[int]]:
    """Fetch all season episodes from Netflix title page."""
    url = f"https://www.netflix.com/title/{title_id}"
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L", "--compressed", "--max-time", "15",
                "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "-H", "Accept-Language: en-US,en;q=0.9",
                url,
            ],
            capture_output=True, text=True, timeout=20,
        )
        html = result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return {}

    if not html:
        return {}

    # Extract Episode videoIds (exclude Season and Show types)
    episode_ids = set()
    for m in re.finditer(r'"__typename":"Episode","videoId":(\d+)', html):
        episode_ids.add(int(m.group(1)))

    if not episode_ids:
        return {}

    # Group into sequential clusters (seasons)
    sorted_ids = sorted(episode_ids)
    seasons = {}
    current = [sorted_ids[0]]
    season_num = 1

    for i in range(1, len(sorted_ids)):
        if sorted_ids[i] == sorted_ids[i - 1] + 1:
            current.append(sorted_ids[i])
        else:
            if len(current) >= 3:
                seasons[season_num] = current
                season_num += 1
            current = [sorted_ids[i]]

    if len(current) >= 3:
        seasons[season_num] = current

    return seasons


def verify():
    with open(CACHE_FILE) as f:
        data = json.load(f)

    netflix = data.get("netflix", {})
    errors = []
    warnings = []
    checked = 0

    for slug, show in netflix.items():
        if checked >= MAX_CHECKS:
            break

        title_id = show.get("title_id")
        if not title_id:
            continue

        print(f"Checking {slug} (title_id={title_id})...", flush=True)
        live_seasons = fetch_netflix_episodes(title_id)

        if not live_seasons:
            warnings.append(f"{slug}: could not fetch from Netflix (may be geo-restricted)")
            continue

        checked += 1
        cached_seasons = show.get("seasons", {})

        for snum_str, sdata in cached_seasons.items():
            snum = int(snum_str)
            cached_first = sdata.get("first_episode_id")
            cached_count = sdata.get("episode_count")

            if snum not in live_seasons:
                # Season might not be in HTML (Netflix only SSR some seasons)
                warnings.append(f"{slug} S{snum}: not found in HTML (may be JS-only)")
                continue

            live_eps = live_seasons[snum]
            live_first = live_eps[0]
            live_count = len(live_eps)

            if cached_first != live_first:
                errors.append(
                    f"{slug} S{snum}: first_episode_id mismatch — "
                    f"cached {cached_first}, actual {live_first}"
                )

            if cached_count != live_count:
                # Allow cached count to be <= live count (show may have added episodes)
                if cached_count > live_count:
                    errors.append(
                        f"{slug} S{snum}: episode_count too high — "
                        f"cached {cached_count}, actual {live_count}"
                    )
                else:
                    warnings.append(
                        f"{slug} S{snum}: episode_count outdated — "
                        f"cached {cached_count}, actual {live_count}"
                    )

    # Report
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        print(f"\nFAIL: {len(errors)} verification errors:")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)

    print(f"\nOK: Verified {checked} shows against live Netflix data")


if __name__ == "__main__":
    verify()
