#!/bin/bash
# Install smartest-tv skill into Claude Code
# Usage: cd smartest-tv && ./install-skills.sh

SKILLS_DIR="${HOME}/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$SKILLS_DIR"

skill="tv"
src="$REPO_DIR/skills/$skill"
dest="$SKILLS_DIR/$skill"

if [ -L "$dest" ]; then
    rm "$dest"
fi

if [ -d "$dest" ]; then
    echo "skip: $dest exists (not a symlink)"
else
    ln -s "$src" "$dest"
    echo "installed: $skill → $dest"
fi

echo "done. Skill available in next Claude Code session."
