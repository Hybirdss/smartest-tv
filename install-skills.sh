#!/bin/bash
# Install smartest-tv skills into Claude Code
# Usage: cd smartest-tv && ./install-skills.sh

SKILLS_DIR="${HOME}/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$SKILLS_DIR"

for skill in tv-shared tv-netflix tv-youtube tv-spotify tv-workflow; do
    src="$REPO_DIR/skills/$skill"
    dest="$SKILLS_DIR/$skill"

    if [ -L "$dest" ]; then
        rm "$dest"
    fi

    if [ -d "$dest" ]; then
        echo "skip: $dest exists (not a symlink)"
        continue
    fi

    ln -s "$src" "$dest"
    echo "installed: $skill → $dest"
done

echo "done. Skills available in next Claude Code session."
