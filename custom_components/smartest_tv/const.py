"""Constants for the Smartest TV integration."""

from datetime import timedelta

DOMAIN = "smartest_tv"

CONF_TV_NAME = "tv_name"
CONF_PLATFORM = "platform"
CONF_IP = "ip"
CONF_MAC = "mac"

# TV platform slugs accepted in the config flow.  This is a TV-vendor
# list — not to be confused with ``homeassistant.const.Platform`` which
# lists HA entity platforms (media_player, sensor, …). Kept under a
# distinct name so both can be imported without shadowing each other.
TV_PLATFORMS = ["lg", "samsung", "android", "firetv", "roku"]

# How often the media_player polls the TV. HA's default 10 s is too
# aggressive for webOS SSAP (each poll opens the WS and reads state);
# 30 s keeps dashboards responsive without hammering the TV.
SCAN_INTERVAL = timedelta(seconds=30)
