<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">The CLI your TV has been waiting for.</h4>

<p align="center">
  <b>Play Netflix / Apple TV+ / YouTube / Spotify by name. Cast URLs. Multi-room audio. AI concierge. All from your terminal.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI: stv"></a>
  <a href="https://pepy.tech/project/stv"><img src="https://static.pepy.tech/badge/stv" alt="Total Downloads"></a>
  <a href="https://pepy.tech/project/stv"><img src="https://static.pepy.tech/badge/stv/month" alt="Downloads/month"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-252%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
  <a href="https://glama.ai/mcp/servers/Hybirdss/smartest-tv"><img src="https://img.shields.io/badge/Glama-A%20A%20A-00d992?style=flat-square" alt="Glama Score"></a>
  <a href="https://github.com/vitalets/awesome-smart-tv"><img src="https://img.shields.io/badge/awesome--smart--tv-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome Smart TV"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square" alt="HACS"></a>
</p>

<p align="center">
  <a href="docs/i18n/README.ko.md">한국어</a> · <a href="docs/i18n/README.zh.md">中文</a> · <a href="docs/i18n/README.ja.md">日本語</a> · <a href="docs/i18n/README.es.md">Español</a> · <a href="docs/i18n/README.de.md">Deutsch</a> · <a href="docs/i18n/README.pt-br.md">Português</a> · <a href="docs/i18n/README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>Runs on your local network. No cloud. No API keys. No subscriptions.</sub></p>

<p align="center">
  <img src="docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

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

## 🛋 Vibe-code and chill

Vibe-coding at 2am. Claude writes your code. You tell it to put on a show. It does.

```
you: play frieren on the living room tv
claude: Playing Frieren s2e8 on Living Room. (3s)

you: bit quieter
claude: Volume → 18.

you: good night
claude: All 3 TVs off.
```

Already installed stv? Just tell Claude:

```bash
# Option 1 — just talk (zero config)
"run stv play netflix Frieren s2e8"

# Option 2 — install the Skill for auto-trigger
clawhub install smartest-tv
# now "play Frieren", "good night", "next episode" just work mid-session
```

<sub>Also available as an MCP server (21 tools) for Claude Code, Codex, Antigravity, and other MCP clients.</sub>

---

## 🎯 Just type `stv`

<p align="center">
  <img src="docs/assets/screenshots/12-home-connected.png" alt="stv home dashboard" width="720">
</p>

No subcommand? You get a Now Playing card and three contextual next-actions
based on your watch history — not a 30-command help dump.

```bash
$ stv "play dark on netflix"     # natural language works
$ stv youtube lofi beats         # platform shorthand
$ stv next                       # continue last show
$ stv stats                      # → insights
```

Unknown input? You get a friendly hint, not an error.

---

## 🎨 A CLI that looks like a product

<table>
<tr>
<td width="50%"><img src="docs/assets/screenshots/01-status.png" alt="stv status"></td>
<td width="50%"><img src="docs/assets/screenshots/07-insights.png" alt="stv insights"></td>
</tr>
<tr>
<td><img src="docs/assets/screenshots/03-scenes.png" alt="stv scene list"></td>
<td><img src="docs/assets/screenshots/02-multi-list.png" alt="stv multi list"></td>
</tr>
<tr>
<td><img src="docs/assets/screenshots/06-doctor.png" alt="stv doctor"></td>
<td><img src="docs/assets/screenshots/16-nl-demo.png" alt="natural language"></td>
</tr>
</table>

Every command renders with Catppuccin Mocha colors, semantic icons, and real
visual hierarchy. Prefer another palette? Set `STV_THEME=nord` or `STV_THEME=gruvbox`.

`--format json` is always available when you need to pipe to `jq`.

---

## ✨ What it does

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Play by name
```bash
stv play netflix "Dark" s1e1
stv play disney "Percy Jackson" s1e1
stv play prime "The Boys" s1e1
stv play "Frieren" s2e8          # auto-detects platform
```
Say the name. stv finds the ID, opens the app, starts playback. Netflix and Apple TV+ resolve via HTML parsing. Disney+, Max, Prime, Hulu, Paramount+, Peacock, Crunchyroll, and [every platform on JustWatch](https://www.justwatch.com/) resolve via their API — no login, no API key. Skip the platform name and stv auto-detects where it's streaming in your region.

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

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
  <br>
  <sub>▲ Click to watch the full demo</sub>
</p>

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

### Home Assistant (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)

Add as a custom repository (HACS default listing pending):

```
HACS → ⋮ (top right) → Custom repositories
  URL: https://github.com/Hybirdss/smartest-tv
  Category: Integration → Add
Then: Install → Restart HA
Settings → Integrations → Add → "Smartest TV" → auto-discovers your TVs
```

Then use in automations:

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room
data:
  media_content_type: stv
  media_content_id: "netflix:Frieren:s2e8"
```

This does what HA's built-in `media_player.play_media` can't: resolve a show by name and deep-link into the streaming app. Power, volume, and playback controls also work as standard HA media player entities.

---

## 🔌 Works with

| Integration | How |
|------------|-----|
| **Home Assistant** | HACS custom integration → `media_player.play_media` with content resolution |
| **Claude Code / Cursor** | Add MCP config → `"play Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → Telegram bot |
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

## 🔓 Open source

Every line of stv is on GitHub — the CLI, resolvers (Netflix, Apple TV+, YouTube, Spotify, Disney+, Max, Prime Video, Paramount+, Hulu, Peacock, Crunchyroll, and more via JustWatch), all 4 TV drivers (LG, Samsung, Roku, Android), cache, sync engine, scenes, and all 253 tests. Streaming availability data powered by [JustWatch](https://www.justwatch.com/).

---

## 🔒 Privacy

stv runs on your **local network**. No telemetry, no analytics, no cloud
sync, no phoning home about what you watch. There is no `posthog`, no
`amplitude`, no `sentry`, no `mixpanel` — grep the source.

**One exception — community cache contribution.** When you play content
that isn't in the local cache, stv resolves it (via web parsing) and
submits the resolved ID to a shared community cache so the next user
gets an instant lookup. This is the same pattern as Wikipedia or a
package mirror — many small contributions, anonymous.

What's sent (background HTTPS, fire-and-forget, never blocks playback):

- Platform name (`netflix` / `youtube` / `spotify`)
- Content slug (e.g. `frieren`)
- Resolved content ID (Netflix title ID, YouTube video ID, Spotify URI)

What's **not** sent:

- Your name, email, or any user identifier
- Your IP address (the CDN sees a connection IP per standard HTTP, but
  the client never reads or transmits it)
- Your watch history or play timestamps
- Your TV's IP address or hardware info
- Anything about how often or when you use stv

To disable cache contribution entirely:

```bash
export STV_NO_CONTRIBUTE=1
```

Source: [`src/smartest_tv/cache.py`](src/smartest_tv/cache.py) — search for `_contribute`.

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
  <img src="docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

<p align="center">
  <sub>MIT License · Made with Python · No cloud required</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
