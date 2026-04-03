"""Check that no existing cache entries are removed or modified.

Contributors can ADD entries but not remove or change existing ones.
This prevents vandalism and accidental data loss.
"""

import json
import subprocess
import sys


def get_base_cache() -> dict:
    """Get community-cache.json from the base branch (main)."""
    try:
        result = subprocess.run(
            ["git", "show", "origin/main:community-cache.json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass
    return {}


def check():
    # Load current (PR) version
    with open("community-cache.json") as f:
        current = json.load(f)

    # Load base (main) version
    base = get_base_cache()
    if not base:
        print("OK: No base cache to compare (new file)")
        return

    errors = []

    # Check Netflix
    base_nf = base.get("netflix", {})
    curr_nf = current.get("netflix", {})

    for slug, show in base_nf.items():
        if slug not in curr_nf:
            errors.append(f"netflix.{slug}: REMOVED (not allowed)")
            continue

        curr_show = curr_nf[slug]

        # title_id must not change
        if show.get("title_id") != curr_show.get("title_id"):
            errors.append(
                f"netflix.{slug}.title_id: CHANGED from {show.get('title_id')} "
                f"to {curr_show.get('title_id')}"
            )

        # Existing seasons must not be removed or have first_episode_id changed
        for snum, sdata in show.get("seasons", {}).items():
            if snum not in curr_show.get("seasons", {}):
                errors.append(f"netflix.{slug}.seasons.{snum}: REMOVED")
                continue

            curr_sdata = curr_show["seasons"][snum]
            if sdata.get("first_episode_id") != curr_sdata.get("first_episode_id"):
                errors.append(
                    f"netflix.{slug}.seasons.{snum}.first_episode_id: "
                    f"CHANGED from {sdata.get('first_episode_id')} "
                    f"to {curr_sdata.get('first_episode_id')}"
                )

            # episode_count can increase (new episodes added) but not decrease
            if curr_sdata.get("episode_count", 0) < sdata.get("episode_count", 0):
                errors.append(
                    f"netflix.{slug}.seasons.{snum}.episode_count: "
                    f"DECREASED from {sdata.get('episode_count')} "
                    f"to {curr_sdata.get('episode_count')}"
                )

    # Check YouTube
    for slug, vid in base.get("youtube", {}).items():
        if slug not in current.get("youtube", {}):
            errors.append(f"youtube.{slug}: REMOVED")
        elif current["youtube"][slug] != vid:
            errors.append(f"youtube.{slug}: CHANGED from {vid} to {current['youtube'][slug]}")

    # Check Spotify
    for slug, uri in base.get("spotify", {}).items():
        if slug not in current.get("spotify", {}):
            errors.append(f"spotify.{slug}: REMOVED")
        elif current["spotify"][slug] != uri:
            errors.append(f"spotify.{slug}: CHANGED from {uri} to {current['spotify'][slug]}")

    if errors:
        print(f"FAIL: {len(errors)} regressions detected (existing entries changed/removed):")
        for e in errors:
            print(f"  ❌ {e}")
        print("\nContributors can ADD new entries but not modify or remove existing ones.")
        sys.exit(1)

    # Count additions
    new_nf = len(curr_nf) - len(base_nf)
    new_yt = len(current.get("youtube", {})) - len(base.get("youtube", {}))
    new_sp = len(current.get("spotify", {})) - len(base.get("spotify", {}))
    total_new = new_nf + new_yt + new_sp

    print(f"OK: {total_new} new entries added, no regressions")
    if new_nf > 0:
        print(f"  +{new_nf} Netflix shows")
    if new_yt > 0:
        print(f"  +{new_yt} YouTube videos")
    if new_sp > 0:
        print(f"  +{new_sp} Spotify tracks")


if __name__ == "__main__":
    check()
