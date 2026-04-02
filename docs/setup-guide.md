# Setup Guide

This guide walks through first-time setup for each supported TV platform.
After completing setup for your platform, run `stv status` to confirm the connection.

## Prerequisites

```bash
pip install stv
stv setup   # interactive wizard — auto-detects TVs on the network
```

`stv setup` handles pairing automatically for most TVs. Use the
platform-specific sections below if the wizard fails or you want to
configure manually.

---

## LG webOS

### Find the IP address

- On the TV: **Settings → All Settings → Network → Wired/Wi-Fi Connection → Check connection** — the IP is shown at the bottom.
- Or check your router's DHCP client list.

### Enable pairing

1. Open the LG Developer Mode app or simply run `stv setup` — it sends a pairing request automatically.
2. A dialog appears on the TV: **"Allow access?"** — press **OK** on the remote.
3. The pairing key is stored in `~/.config/smartest-tv/config.toml`.

### Manual config

```toml
# ~/.config/smartest-tv/config.toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, needed for Wake-on-LAN
```

### Driver install

```bash
pip install "stv[lg]"   # installs bscpylgtv
```

### Notes

- LG uses WebSocket SSAP (port 3000/3001).
- Some firmware versions return 403 on `closeApp` — the CLI falls back to launching the home screen automatically.
- Wake-on-LAN (`stv on`) requires the MAC address and the TV to be in standby (not fully off).

---

## Samsung Tizen

### Enable Remote Device Access

1. Go to **Settings → General → External Device Manager → Device Connect Manager**.
2. Set **Access Notification** to **First Time Only** (or **Always**).
3. On first connection a pairing dialog appears on screen — accept it.

### Find the IP address

**Settings → General → Network → Network Status → IP Settings** — the IP is shown here.

### Manual config

```toml
[tv]
platform = "samsung"
ip = "192.168.1.101"
mac = "11:22:33:44:55:66"
```

### Driver install

```bash
pip install "stv[samsung]"   # installs samsungtvws[encrypted]
```

### Notes

- Samsung uses an encrypted WebSocket (port 8002).
- Newer 2022+ models require the encrypted driver — `samsungtvws[encrypted]` covers this.
- Deep linking uses `run_app("DEEP_LINK", meta_tag)` with a platform-specific meta format.

---

## Android TV / Fire TV

### Enable ADB Debugging

**Android TV:**
1. Go to **Settings → Device Preferences → About → Build** — tap Build 7 times to unlock developer options.
2. Go to **Settings → Device Preferences → Developer Options → USB Debugging** — enable it.
3. Also enable **Network Debugging** (ADB over TCP).

**Fire TV:**
1. Go to **Settings → My Fire TV → About** — tap Build 7 times.
2. **Settings → My Fire TV → Developer Options → ADB Debugging** — enable.
3. **Settings → My Fire TV → Developer Options → Apps from Unknown Sources** — enable if needed.

### Find the IP address

**Settings → My Fire TV → About → Network** (Fire TV) or **Settings → Device Preferences → About → Network** (Android TV).

### Manual config

```toml
[tv]
platform = "android"   # or "firetv"
ip = "192.168.1.102"
```

### Driver install

```bash
pip install "stv[android]"   # installs adb-shell
```

### Notes

- No pairing key is needed — ADB TCP connects directly.
- The first connection prompts an "Allow ADB debugging?" dialog on screen — accept it.
- Deep links are sent via `am start -d 'netflix://title/{id}'`.

---

## Roku

### Verify ECP is Enabled

Roku enables External Control Protocol (ECP) on port 8060 by default on all models.
No special setup is needed for most users.

If ECP is disabled:
1. Go to **Settings → System → Advanced System Settings → External Control** — set to **Enabled**.

### Find the IP address

**Settings → Network → About** — the IP address is listed here.

### Manual config

```toml
[tv]
platform = "roku"
ip = "192.168.1.103"
```

### Driver install

```bash
pip install "stv[roku]"   # installs aiohttp
```

### Notes

- Roku ECP uses plain HTTP on port 8060 — no authentication required.
- Deep linking uses `POST /launch/{channel_id}?contentId={id}&mediaType=series`.
- Roku channel IDs: Netflix=12, YouTube=837, Spotify=19977.

---

## Verify Setup

```bash
stv status       # shows platform, current app, volume
stv doctor       # connectivity + app availability check
stv notify "Hello from stv!"   # sends a toast notification to the TV
```

## Environment Variable Overrides

For scripting or CI, you can skip the config file entirely:

```bash
export TV_PLATFORM=lg
export TV_IP=192.168.1.100
export TV_MAC=AA:BB:CC:DD:EE:FF
stv status
```
