<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">The CLI your TV has been waiting for.</h4>

<p align="center">
  <b>Play Netflix by name. Cast URLs. Multi-room audio. AI concierge. All from your terminal.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-211%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
</p>

<p align="center">
  <a href="docs/i18n/README.ko.md">한국어</a> · <a href="docs/i18n/README.zh.md">中文</a> · <a href="docs/i18n/README.ja.md">日本語</a> · <a href="docs/i18n/README.es.md">Español</a> · <a href="docs/i18n/README.de.md">Deutsch</a> · <a href="docs/i18n/README.pt-br.md">Português</a> · <a href="docs/i18n/README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>Runs on your local network. No cloud. No API keys. No subscriptions.</sub></p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 Without stv</th>
<th>😎 With stv</th>
</tr>
<tr>
<td>

1. Pick up remote
2. Open Netflix app
3. Search for show
4. Pick the season
5. Pick the episode
6. Press play

**~30 seconds**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
```

**~3 seconds**

</td>
</tr>
</table>

<br>

---

## ✨ What it does

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Play by name
```bash
stv play netflix "Dark" s1e1
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
Say the name. stv finds the ID, opens the app, starts playback.

</td>
<td width="33%" valign="top">

### 🔗 Cast any URL
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
Friend sends a link. Paste it. TV plays it.

</td>
<td width="33%" valign="top">

### 🎵 Queue & party
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
Everyone adds their pick. TV plays in order.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 Scene presets
```bash
stv scene movie-night   # volume 20, cinema
stv scene kids          # volume 15, Cocomelon
stv scene sleep         # rain sounds, auto-off
```
One command sets the vibe.

</td>
<td width="33%" valign="top">

### 🔊 Multi-room audio
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
Screens off. Music everywhere.<br>**Free Sonos.**

</td>
<td width="33%" valign="top">

### 📺 TV as display
```bash
stv display message "Dinner!"
stv display clock
stv display dashboard "Temp:22°C"
```
Dashboards, clocks, signage.<br>**$0/month.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 Watch intelligence
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
Is your Netflix worth $18/month?

</td>
<td width="33%" valign="top">

### 🌐 Sync party
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # good night
```
Every TV. At once. Even remote friends.

</td>
<td width="33%" valign="top">

### 🤖 AI concierge
```
"Play something chill"
→ tv_recommend → tv_play
→ Playing The Queen's Gambit
```
21 MCP tools. One sentence is enough.

</td>
</tr>
</table>

---

## 🤖 Tell your AI to control your TV

stv is an **MCP server**. Claude, GPT, Cursor, or any MCP client can control your TV with natural language.

<table>
<tr>
<td width="50%" valign="top">

**Setup (one line):**

```json
{
  "mcpServers": {
    "tv": {
      "command": "uvx",
      "args": ["stv"]
    }
  }
}
```

Or via [OpenClaw](docs/integrations/openclaw.md):
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**Then just talk:**

```
You: "I just got home, set up movie night"

Claude: 🎬 Movie night activated.
  Volume → 20, cinema mode on.
  
  Based on your history:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

You: "Play 1, put a clock on kitchen TV"

Claude: ✓ Playing The Queen's Gambit
         ✓ Clock on kitchen TV
```

</td>
</tr>
</table>

<details>
<summary><b>All 21 MCP tools</b></summary>
<br>

| Category | Tool | What it does |
|----------|------|-------------|
| **Play** | `tv_play` | Search + play by name |
| | `tv_cast` | Cast any URL |
| | `tv_next` | Continue watching |
| | `tv_launch` | Launch app with ID |
| | `tv_resolve` | Get content ID only |
| **Discover** | `tv_whats_on` | Trending content |
| | `tv_recommend` | Personalized picks |
| **Control** | `tv_power` | On/off |
| | `tv_volume` | Get/set/step/mute |
| | `tv_screen` | Screen on/off |
| | `tv_notify` | Toast notification |
| | `tv_status` | Current state |
| **Organize** | `tv_queue` | Play queue |
| | `tv_scene` | Scene presets |
| | `tv_history` | Watch history |
| **Intelligence** | `tv_insights` | Viewing stats |
| | `tv_display` | TV as display |
| | `tv_audio` | Multi-room audio |
| **Multi-TV** | `tv_sync` | Play on all TVs |
| | `tv_list_tvs` | List TVs |
| | `tv_groups` | TV groups |

</details>

---

## 📅 A day with stv

| Time | What happens |
|------|-------------|
| **7am** | `stv display dashboard "Weather:18°C" "Meeting:10am"` on kitchen TV |
| **8am** | `stv scene kids --tv kids-room` -- Cocomelon, volume 15 |
| **12pm** | Friend sends Netflix link → `stv cast <url>` |
| **5pm** | `stv screen-time` → kids watched 2h 15m today |
| **6:30pm** | `stv scene movie-night` -- volume 20, cinema mode |
| **7pm** | `stv recommend --mood chill` → suggests Ozark |
| **9pm** | `stv audio play "friday vibes" -p spotify` -- music everywhere |
| **10pm** | `stv --group party play netflix "Wednesday" s1e1` -- sync |
| **11:30pm** | `stv scene sleep` → `stv --all off` -- good night |

---

## 🔥 Killer combos

<table>
<tr>
<td width="33%" valign="top">

**🌙 Bedtime autopilot**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
Ambient sound, screen off, auto-timer, every other TV killed.

</td>
<td width="33%" valign="top">

**🎧 Free Sonos**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
Every TV is a speaker. Per-room volume. Screens off.

</td>
<td width="33%" valign="top">

**💰 Subscription audit**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — consider canceling

stv sub-value youtube --cost 13.99
# → $1.20/hr — good value
```

</td>
</tr>
</table>

> [**10 more recipes →**](docs/guides/recipes.md)

---

## ⚙️ How it works

```
  "Play Dark S1E1"
        │
        ▼
  ┌─── Resolution ───┐
  │ Cache → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 TV plays it
  └───────────────────┘       │
                         Deep link via
                    LG / Samsung / Roku / Android
```

Say a name. stv resolves it to a content ID, deep-links into the app on your TV. No browser automation, no API keys, no cloud dependency. Results are cached so repeat plays are instant.

---

## 📦 Install

```bash
pip install stv                    # LG webOS (default)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # Everything
```

```bash
stv setup                          # auto-discover + pair your TV
```

> Supports **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 Works with

| Integration | How |
|------------|-----|
| **Claude Code / Cursor** | Add MCP config → `"play Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → Telegram bot |
| **Home Assistant** | Shell commands in automations |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Shell scripts** | `sleep-mode`, `party-mode` one-liners |
| **Any MCP client** | 21 tools, stdio or HTTP (`stv serve`) |

---

## 📚 Docs

| | |
|---|---|
| [Getting Started](docs/getting-started/installation.md) | Setup for any TV brand |
| [Playing Content](docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Scenes](docs/guides/scenes.md) | movie-night, kids, sleep, custom |
| [Sync & Party](docs/guides/sync-party.md) | Multi-TV, remote watch party |
| [Recipes](docs/guides/recipes.md) | **10 powerful feature combos** |
| [AI Agents](docs/guides/ai-agents.md) | MCP for Claude, Cursor, OpenClaw |
| [CLI Reference](docs/reference/cli.md) | Every command and option |
| [MCP Tools](docs/reference/mcp-tools.md) | All 21 tools with parameters |

---

## 🤝 Contributing

211 tests. No TV needed to run them.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Samsung, Roku, and Android TV drivers need real-world testing. If you have one, [your feedback matters](https://github.com/Hybirdss/smartest-tv/issues).

[Cache Contributions](docs/contributing/cache-contributions.md) · [Driver Development](docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Made with Python · No cloud required</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
