from __future__ import annotations

import shutil
from pathlib import Path


def _find_skill_src() -> Path | None:
    # Primary: next to this file's package root (editable / source install)
    candidate = Path(__file__).resolve().parent.parent.parent / "skills" / "stv-concierge"
    if candidate.is_dir():
        return candidate

    # Fallback: importlib.resources (installed wheel)
    try:
        import importlib.resources as pkg_resources
        ref = pkg_resources.files("smartest_tv")
        # Wheel ships skills/ two levels up from the package
        pkg_path = Path(str(ref))
        candidate2 = pkg_path.parent.parent / "skills" / "stv-concierge"
        if candidate2.is_dir():
            return candidate2
    except Exception:
        pass

    return None


def main() -> int:
    claude_dir = Path.home() / ".claude"
    if not claude_dir.exists():
        return 0

    try:
        src = _find_skill_src()
        if src is None:
            print("Warning: stv-concierge skill source not found — skipping install")
            return 1

        skill_file = src / "SKILL.md"
        if not skill_file.exists():
            print("Warning: stv-concierge/SKILL.md not found — skipping install")
            return 1

        dst_dir = claude_dir / "skills" / "stv-concierge"
        dst = dst_dir / "SKILL.md"

        dst_dir.mkdir(parents=True, exist_ok=True)

        # Idempotent: already correct symlink or identical file
        if dst.is_symlink():
            if dst.resolve() == skill_file.resolve():
                return 0
            dst.unlink()
        elif dst.exists():
            if dst.read_bytes() == skill_file.read_bytes():
                return 0
            dst.unlink()

        try:
            dst.symlink_to(skill_file)
        except OSError:
            shutil.copy2(skill_file, dst)

        print(f"✓ Installed stv-concierge skill → {dst_dir}/")
    except Exception as e:
        print(f"Warning: skill install failed ({e}) — skipping")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
