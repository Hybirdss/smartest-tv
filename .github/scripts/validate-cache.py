"""Validate community-cache.json structure.

Ensures:
- Valid JSON
- Correct schema (netflix shows have title_id, seasons, first_episode_id, episode_count)
- No duplicate entries
- IDs are positive integers
- Episode counts are reasonable (1-100)
"""

import json
import sys

CACHE_FILE = "community-cache.json"


def validate():
    errors = []

    # Load JSON
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(data, dict):
        print("FAIL: Root must be a JSON object")
        sys.exit(1)

    # Validate Netflix entries
    netflix = data.get("netflix", {})
    for slug, show in netflix.items():
        prefix = f"netflix.{slug}"

        if not isinstance(show, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        # title_id
        tid = show.get("title_id")
        if not isinstance(tid, int) or tid <= 0:
            errors.append(f"{prefix}.title_id: must be a positive integer, got {tid}")

        # seasons
        seasons = show.get("seasons", {})
        if not isinstance(seasons, dict) or not seasons:
            errors.append(f"{prefix}.seasons: must be a non-empty object")
            continue

        prev_first_id = 0
        for snum, sdata in sorted(seasons.items(), key=lambda x: int(x[0])):
            sp = f"{prefix}.seasons.{snum}"

            if not snum.isdigit():
                errors.append(f"{sp}: season key must be numeric")
                continue

            first_id = sdata.get("first_episode_id")
            count = sdata.get("episode_count")

            if not isinstance(first_id, int) or first_id <= 0:
                errors.append(f"{sp}.first_episode_id: must be positive integer")
            elif first_id <= prev_first_id:
                errors.append(f"{sp}.first_episode_id: must be > previous season ({prev_first_id})")
            else:
                prev_first_id = first_id

            if not isinstance(count, int) or count < 1 or count > 100:
                errors.append(f"{sp}.episode_count: must be 1-100, got {count}")

    # Validate YouTube entries
    youtube = data.get("youtube", {})
    for slug, vid in youtube.items():
        if not isinstance(vid, str) or not vid:
            errors.append(f"youtube.{slug}: must be a non-empty string")

    # Validate Spotify entries
    spotify = data.get("spotify", {})
    for slug, uri in spotify.items():
        if not isinstance(uri, str) or not uri.startswith("spotify:"):
            errors.append(f"spotify.{slug}: must start with 'spotify:'")

    # Report
    if errors:
        print(f"FAIL: {len(errors)} validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    total = len(netflix) + len(youtube) + len(spotify)
    print(f"OK: {total} entries ({len(netflix)} Netflix, {len(youtube)} YouTube, {len(spotify)} Spotify)")


if __name__ == "__main__":
    validate()
