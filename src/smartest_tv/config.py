"""Config file management for smartest-tv.

All config lives in ~/.config/smartest-tv/config.toml.
Created by `stv setup`, read by everything else.
Environment variables override config for scripting.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(os.environ.get("STV_CONFIG_DIR", "~/.config/smartest-tv")).expanduser()
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load() -> dict[str, Any]:
    """Load config from file, with env var overrides."""
    config: dict[str, Any] = {}

    if CONFIG_FILE.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # type: ignore
        config = tomllib.loads(CONFIG_FILE.read_text())

    # Env var overrides — only apply in legacy/single-tv mode
    tv = config.get("tv", {})
    if _is_legacy(tv):
        if os.environ.get("TV_PLATFORM"):
            tv["platform"] = os.environ["TV_PLATFORM"]
        if os.environ.get("TV_IP"):
            tv["ip"] = os.environ["TV_IP"]
        if os.environ.get("TV_MAC"):
            tv["mac"] = os.environ["TV_MAC"]
        config["tv"] = tv

    return config


def _is_legacy(tv: dict[str, Any]) -> bool:
    """Return True if [tv] section uses legacy single-TV format (platform key at top level)."""
    return "platform" in tv


def save(platform: str, ip: str, mac: str = "", name: str = "") -> Path:
    """Save config to file (legacy single-TV format)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# smartest-tv config — created by stv setup",
        "# https://github.com/Hybirdss/smartest-tv",
        "",
        "[tv]",
        f'platform = "{platform}"',
        f'ip = "{ip}"',
    ]
    if mac:
        lines.append(f'mac = "{mac}"')
    if name:
        lines.append(f'name = "{name}"')
    lines.append("")

    CONFIG_FILE.write_text("\n".join(lines))
    return CONFIG_FILE


def get_tv_config(tv_name: str | None = None) -> dict[str, str]:
    """Get config for a specific TV, or the default one.

    Handles both legacy single-TV format ([tv] with platform key) and
    multi-TV format ([tv.living-room], [tv.bedroom], etc.).

    Args:
        tv_name: Name of TV to get config for. If None, returns default TV.

    Returns:
        Flat dict with keys: platform, ip, mac, name.
    """
    config = load()
    tv_section = config.get("tv", {})

    if _is_legacy(tv_section):
        # Legacy single-TV mode: [tv] has platform directly
        if tv_name is not None:
            # In legacy mode, there's only one TV; ignore tv_name
            pass
        return {
            "platform": tv_section.get("platform", ""),
            "ip": tv_section.get("ip", ""),
            "mac": tv_section.get("mac", ""),
            "name": tv_section.get("name", ""),
        }

    # Multi-TV mode: [tv.name] sections
    # Filter out non-dict values to get actual TV entries
    tvs = {k: v for k, v in tv_section.items() if isinstance(v, dict)}

    if not tvs:
        return {"platform": "", "ip": "", "mac": "", "name": ""}

    if tv_name is not None:
        tv = tvs.get(tv_name)
        if tv is None:
            raise KeyError(f"TV '{tv_name}' not found. Available: {', '.join(tvs)}")
        return {
            "platform": tv.get("platform", ""),
            "ip": tv.get("ip", ""),
            "mac": tv.get("mac", ""),
            "name": tv.get("name", tv_name),
        }

    # Find default TV: first with default=true, else the only one, else first
    for name, tv in tvs.items():
        if tv.get("default", False):
            return {
                "platform": tv.get("platform", ""),
                "ip": tv.get("ip", ""),
                "mac": tv.get("mac", ""),
                "name": tv.get("name", name),
            }

    if len(tvs) == 1:
        name, tv = next(iter(tvs.items()))
        return {
            "platform": tv.get("platform", ""),
            "ip": tv.get("ip", ""),
            "mac": tv.get("mac", ""),
            "name": tv.get("name", name),
        }

    # Multiple TVs, none marked default — return first
    name, tv = next(iter(tvs.items()))
    return {
        "platform": tv.get("platform", ""),
        "ip": tv.get("ip", ""),
        "mac": tv.get("mac", ""),
        "name": tv.get("name", name),
    }


def list_tvs() -> list[dict[str, Any]]:
    """List all configured TVs.

    Returns list of dicts with keys: name, platform, ip, mac, default.
    """
    config = load()
    tv_section = config.get("tv", {})

    if _is_legacy(tv_section):
        return [{
            "name": tv_section.get("name", "default"),
            "platform": tv_section.get("platform", ""),
            "ip": tv_section.get("ip", ""),
            "mac": tv_section.get("mac", ""),
            "default": True,
        }]

    tvs = {k: v for k, v in tv_section.items() if isinstance(v, dict)}
    result = []
    for name, tv in tvs.items():
        result.append({
            "name": name,
            "platform": tv.get("platform", ""),
            "ip": tv.get("ip", ""),
            "mac": tv.get("mac", ""),
            "default": tv.get("default", False),
        })
    return result


def _load_raw_toml() -> str:
    """Load raw TOML text, or empty string if file doesn't exist."""
    if CONFIG_FILE.exists():
        return CONFIG_FILE.read_text()
    return ""


def _save_raw_toml(text: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(text)


def _sanitize_tv_name(name: str) -> str:
    """Sanitize TV name for use as TOML key. Only allow alphanumeric, dash, underscore."""
    import re
    clean = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip())
    if not clean:
        raise ValueError("TV name must contain at least one alphanumeric character")
    return clean


def add_tv(name: str, platform: str, ip: str, mac: str = "", default: bool = False) -> Path:
    """Add a TV to multi-TV config.

    If config is currently legacy single-TV, migrates it to multi-TV format first.
    """
    name = _sanitize_tv_name(name)
    config = load()
    tv_section = config.get("tv", {})

    if _is_legacy(tv_section):
        # Migrate legacy to multi-TV
        existing_name = tv_section.get("name", "default") or "default"
        existing = {
            "platform": tv_section.get("platform", ""),
            "ip": tv_section.get("ip", ""),
        }
        if tv_section.get("mac"):
            existing["mac"] = tv_section["mac"]
        existing["default"] = True  # existing becomes default unless new one is marked default

        # If new TV is default, unset old one
        if default:
            existing["default"] = False

        tvs: dict[str, Any] = {existing_name: existing}
    else:
        tvs = {k: v for k, v in tv_section.items() if isinstance(v, dict)}
        # If new TV is default, remove default from others
        if default:
            for tv in tvs.values():
                tv.pop("default", None)

    new_tv: dict[str, Any] = {"platform": platform, "ip": ip}
    if mac:
        new_tv["mac"] = mac
    if default:
        new_tv["default"] = True
    tvs[name] = new_tv

    _write_multi_tv_config(tvs)
    return CONFIG_FILE


def remove_tv(name: str) -> None:
    """Remove a TV from config by name."""
    config = load()
    tv_section = config.get("tv", {})

    if _is_legacy(tv_section):
        raise KeyError(f"No multi-TV config. Only single TV configured.")

    tvs = {k: v for k, v in tv_section.items() if isinstance(v, dict)}
    if name not in tvs:
        raise KeyError(f"TV '{name}' not found. Available: {', '.join(tvs)}")

    del tvs[name]
    _write_multi_tv_config(tvs)


def set_default_tv(name: str) -> None:
    """Set a TV as the default."""
    config = load()
    tv_section = config.get("tv", {})

    if _is_legacy(tv_section):
        raise KeyError(f"No multi-TV config. Only single TV configured.")

    tvs = {k: v for k, v in tv_section.items() if isinstance(v, dict)}
    if name not in tvs:
        raise KeyError(f"TV '{name}' not found. Available: {', '.join(tvs)}")

    for tv_name, tv in tvs.items():
        if tv_name == name:
            tv["default"] = True
        else:
            tv.pop("default", None)

    _write_multi_tv_config(tvs)


def _write_multi_tv_config(tvs: dict[str, Any]) -> None:
    """Write multi-TV config to file."""
    lines = [
        "# smartest-tv config",
        "# https://github.com/Hybirdss/smartest-tv",
        "",
    ]
    for name, tv in tvs.items():
        lines.append(f"[tv.{name}]")
        lines.append(f'platform = "{tv.get("platform", "")}"')
        lines.append(f'ip = "{tv.get("ip", "")}"')
        if tv.get("mac"):
            lines.append(f'mac = "{tv["mac"]}"')
        if tv.get("name"):
            lines.append(f'name = "{tv["name"]}"')
        if tv.get("default"):
            lines.append("default = true")
        lines.append("")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text("\n".join(lines))
