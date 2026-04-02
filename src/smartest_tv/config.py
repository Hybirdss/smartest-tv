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

    # Env var overrides
    tv = config.get("tv", {})
    if os.environ.get("TV_PLATFORM"):
        tv["platform"] = os.environ["TV_PLATFORM"]
    if os.environ.get("TV_IP"):
        tv["ip"] = os.environ["TV_IP"]
    if os.environ.get("TV_MAC"):
        tv["mac"] = os.environ["TV_MAC"]
    config["tv"] = tv

    return config


def save(platform: str, ip: str, mac: str = "", name: str = "") -> Path:
    """Save config to file."""
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


def get_tv_config() -> dict[str, str]:
    """Get TV config as flat dict. Used by CLI and MCP server."""
    config = load()
    tv = config.get("tv", {})
    return {
        "platform": tv.get("platform", ""),
        "ip": tv.get("ip", ""),
        "mac": tv.get("mac", ""),
        "name": tv.get("name", ""),
    }
