"""Keep stv's state inside Home Assistant's persistent /config.

stv reads and writes everything it owns — the TV list (config.toml), the
Android pairing certificate, Samsung tokens, the LG key — under
``~/.config/smartest-tv`` unless ``STV_CONFIG_DIR`` points elsewhere. On
HA OS and HA Container that home directory lives inside the core container
and is wiped by every core update. After a wipe ``create_driver(tv_name)``
finds no TV and quietly returns the "browser" driver, which only calls
``webbrowser.open`` on the HA host: the media_player stays ``on`` with
``app_name: browser`` and nothing reaches the TV (issue #15 asked users to
set ``STV_CONFIG_DIR`` themselves, which is not possible for the core
container on HA OS).

So the integration points stv at ``/config/smartest-tv`` itself before it
imports anything from stv, copies whatever state the old location still
holds over to the new one once, and re-registers the TV from the config
entry's own data when config.toml is missing. An explicit
``STV_CONFIG_DIR`` in the environment still wins.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import threading
from pathlib import Path

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

STV_CONFIG_DIR_ENV = "STV_CONFIG_DIR"
STV_REGION_ENV = "STV_REGION"
CONFIG_SUBDIR = "smartest-tv"
LEGACY_CONFIG_DIR = Path.home() / ".config" / CONFIG_SUBDIR

# Module attributes stv computes from CONFIG_DIR at import time; fixed up
# when the module was imported before the environment was pointed here.
_DERIVED_PATHS = {
    "smartest_tv.config": {"CONFIG_FILE": "config.toml"},
    "smartest_tv.cache": {"CACHE_FILE": "cache.json", "QUEUE_FILE": "queue.json"},
    "smartest_tv.scenes": {"SCENES_FILE": "scenes.json"},
}

# config.toml is read-modify-written; entries of several TVs are set up
# concurrently, each in its own executor thread.
_LOCK = threading.Lock()


def ensure_stv_env(hass: HomeAssistant) -> None:
    """Point stv at ``<config>/smartest-tv`` and the HA country. Idempotent.

    Safe on the event loop: only environment variables and module
    attributes, no I/O. Also fixes up stv modules that were imported before
    this ran (their paths are computed at import time). ``STV_REGION``
    (JustWatch catalogue for ``auto:`` ids) defaults to the HA country
    instead of a timezone guess.
    """
    config_dir = os.environ.get(STV_CONFIG_DIR_ENV) or hass.config.path(CONFIG_SUBDIR)
    os.environ[STV_CONFIG_DIR_ENV] = config_dir

    country = getattr(hass.config, "country", None)
    if country and not os.environ.get(STV_REGION_ENV):
        os.environ[STV_REGION_ENV] = country

    if (config_mod := sys.modules.get("smartest_tv.config")) is not None:
        path = Path(config_dir).expanduser()
        if getattr(config_mod, "CONFIG_DIR", None) != path:
            config_mod.CONFIG_DIR = path
            for mod_name, attrs in _DERIVED_PATHS.items():
                if (mod := sys.modules.get(mod_name)) is not None:
                    for attr, filename in attrs.items():
                        setattr(mod, attr, path / filename)
        # Re-read STV_REGION through stv's own validation on the next call.
        config_mod.clear_region_cache()


def migrate_legacy_state() -> bool:
    """Copy stv's state from ``~/.config/smartest-tv`` once (runs in executor).

    Installs that paired before the integration pointed stv at /config keep
    their TV list and pairing credentials in the old location; without the
    copy the TV would be re-registered from the entry but report "not
    paired". Returns True when something was copied.
    """
    new_dir = Path(os.environ.get(STV_CONFIG_DIR_ENV, "")).expanduser()
    if not str(new_dir) or new_dir == LEGACY_CONFIG_DIR:
        return False
    with _LOCK:
        if (new_dir / "config.toml").exists() or not (LEGACY_CONFIG_DIR / "config.toml").exists():
            return False
        try:
            shutil.copytree(LEGACY_CONFIG_DIR, new_dir, dirs_exist_ok=True)
        except OSError as err:
            _LOGGER.warning("Could not copy stv's state from %s to %s: %s", LEGACY_CONFIG_DIR, new_dir, err)
            return False
    _LOGGER.info("Copied stv's state from %s to %s", LEGACY_CONFIG_DIR, new_dir)
    return True


def ensure_tv_registered(tv_name: str, platform: str, ip: str, mac: str) -> str:
    """Make sure the TV exists in stv's config.toml (runs in executor).

    Returns the key stv knows the TV by: ``add_tv`` sanitises the name
    ("android_10.0.0.5" is stored as "android_10-0-0-5"), while the config
    entry keeps the name as typed, so lookups have to go through the same
    sanitising or ``create_driver`` never finds the TV. The entry already
    holds platform / ip / mac, so a config.toml lost to a container rebuild
    is rebuilt from it instead of letting ``create_driver`` fall back to
    the browser driver.
    """
    from smartest_tv.config import _sanitize_tv_name, add_tv, get_tv_config

    key = _sanitize_tv_name(tv_name)
    with _LOCK:
        try:
            current = get_tv_config(key)
        except KeyError:
            current = {}
        if current.get("platform"):
            return key

        _LOGGER.warning(
            "%s is missing from stv's config (%s); re-registering it from the "
            "config entry. Pairing credentials are kept next to it, so if the "
            "TV now reports 'not paired', remove and re-add the entry.",
            tv_name,
            os.environ.get(STV_CONFIG_DIR_ENV, "~/.config/smartest-tv"),
        )
        add_tv(name=tv_name, platform=platform, ip=ip, mac=mac, default=False)
    return key
