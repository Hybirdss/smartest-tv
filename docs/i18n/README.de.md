<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">Die CLI, auf die dein Fernseher gewartet hat.</h4>

<p align="center">
  <b>Netflix beim Namen nennen. URLs casten. Mehrzimmer-Audio. KI-Concierge. Alles vom Terminal aus.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="../../tests/"><img src="https://img.shields.io/badge/tests-211%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <b>Deutsch</b> · <a href="README.pt-br.md">Português</a> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>Läuft in deinem lokalen Netzwerk. Keine Cloud. Keine API-Keys. Keine Abonnements.</sub></p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 Ohne stv</th>
<th>😎 Mit stv</th>
</tr>
<tr>
<td>

1. Fernbedienung nehmen
2. Netflix-App öffnen
3. Nach der Serie suchen
4. Staffel auswählen
5. Folge auswählen
6. Play drücken

**~30 Sekunden**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
```

**~3 Sekunden**

</td>
</tr>
</table>

<br>

---

## ✨ Was es kann

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Nach Name abspielen
```bash
stv play netflix "Dark" s1e1
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
Sag den Namen. stv findet die ID, öffnet die App, startet die Wiedergabe.

</td>
<td width="33%" valign="top">

### 🔗 Beliebige URL casten
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
Freund schickt einen Link. Einfügen. Fernseher spielt ihn ab.

</td>
<td width="33%" valign="top">

### 🎵 Queue und Party
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
Jeder fügt seinen Song hinzu. Fernseher spielt sie der Reihe nach ab.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 Szenen-Presets
```bash
stv scene movie-night   # Lautstärke 20, Kino
stv scene kids          # Lautstärke 15, Cocomelon
stv scene sleep         # Regengeräusche, Auto-Aus
```
Ein Befehl setzt die Stimmung.

</td>
<td width="33%" valign="top">

### 🔊 Mehrzimmer-Audio
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
Bildschirme aus. Musik überall.<br>**Kostenloses Sonos.**

</td>
<td width="33%" valign="top">

### 📺 TV als Display
```bash
stv display message "Essen ist fertig!"
stv display clock
stv display dashboard "Temp:22°C"
```
Dashboards, Uhren, Beschilderung.<br>**$0/Monat.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 Sehverhalten-Analyse
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
Ist dein Netflix $18 im Monat wert?

</td>
<td width="33%" valign="top">

### 🌐 Sync-Party
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # gute Nacht
```
Jeder Fernseher. Gleichzeitig. Auch entfernte Freunde.

</td>
<td width="33%" valign="top">

### 🤖 KI-Concierge
```
"Spiel etwas Entspanntes"
→ tv_recommend → tv_play
→ Spielt The Queen's Gambit
```
21 MCP-Tools. Ein Satz reicht.

</td>
</tr>
</table>

---

## 🤖 Lass deine KI deinen Fernseher steuern

stv ist ein **MCP-Server**. Claude, GPT, Cursor oder jeder MCP-Client kann deinen Fernseher mit natürlicher Sprache steuern.

<table>
<tr>
<td width="50%" valign="top">

**Einrichtung (eine Zeile):**

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

Oder über [OpenClaw](../../docs/integrations/openclaw.md):
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**Dann einfach sprechen:**

```
Du: "Ich bin gerade heimgekommen, richte Filmabend ein"

Claude: 🎬 Filmabend aktiviert.
  Lautstärke → 20, Kinomodus an.
  
  Basierend auf deinem Verlauf:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

Du: "Spiel 1, stell eine Uhr auf den Küchen-TV"

Claude: ✓ Spielt The Queen's Gambit
         ✓ Uhr auf Küchen-TV
```

</td>
</tr>
</table>

<details>
<summary><b>Alle 21 MCP-Tools</b></summary>
<br>

| Kategorie | Tool | Was es tut |
|----------|------|-------------|
| **Abspielen** | `tv_play` | Suchen + nach Name abspielen |
| | `tv_cast` | Beliebige URL casten |
| | `tv_next` | Weiterschauen |
| | `tv_launch` | App per ID starten |
| | `tv_resolve` | Nur Inhalts-ID abrufen |
| **Entdecken** | `tv_whats_on` | Trendige Inhalte |
| | `tv_recommend` | Personalisierte Vorschläge |
| **Steuern** | `tv_power` | Ein/Aus |
| | `tv_volume` | Abrufen/Setzen/Schritt/Stummschalten |
| | `tv_screen` | Bildschirm ein/aus |
| | `tv_notify` | Toast-Benachrichtigung |
| | `tv_status` | Aktueller Zustand |
| **Organisieren** | `tv_queue` | Wiedergabeliste |
| | `tv_scene` | Szenen-Presets |
| | `tv_history` | Sehverlauf |
| **Analyse** | `tv_insights` | Sehstatistiken |
| | `tv_display` | TV als Display |
| | `tv_audio` | Mehrzimmer-Audio |
| **Multi-TV** | `tv_sync` | Auf allen TVs abspielen |
| | `tv_list_tvs` | TVs auflisten |
| | `tv_groups` | TV-Gruppen |

</details>

---

## 📅 Ein Tag mit stv

| Zeit | Was passiert |
|------|-------------|
| **7 Uhr** | `stv display dashboard "Wetter:18°C" "Meeting:10Uhr"` auf dem Küchen-TV |
| **8 Uhr** | `stv scene kids --tv kids-room` — Cocomelon, Lautstärke 15 |
| **12 Uhr** | Freund schickt Netflix-Link → `stv cast <url>` |
| **17 Uhr** | `stv screen-time` → Kinder haben heute 2h 15m geschaut |
| **18:30 Uhr** | `stv scene movie-night` — Lautstärke 20, Kinomodus |
| **19 Uhr** | `stv recommend --mood chill` → schlägt Ozark vor |
| **21 Uhr** | `stv audio play "friday vibes" -p spotify` — Musik überall |
| **22 Uhr** | `stv --group party play netflix "Wednesday" s1e1` — synchron |
| **23:30 Uhr** | `stv scene sleep` → `stv --all off` — gute Nacht |

---

## 🔥 Killer-Kombos

<table>
<tr>
<td width="33%" valign="top">

**🌙 Schlafens-Autopilot**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
Umgebungsklang, Bildschirm aus, Auto-Timer, alle anderen TVs aus.

</td>
<td width="33%" valign="top">

**🎧 Kostenloses Sonos**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
Jeder TV ist ein Lautsprecher. Lautstärke pro Zimmer. Bildschirme aus.

</td>
<td width="33%" valign="top">

**💰 Abonnement-Audit**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/Std — Kündigung erwägen

stv sub-value youtube --cost 13.99
# → $1.20/Std — guter Wert
```

</td>
</tr>
</table>

> [**10 weitere Rezepte →**](../../docs/guides/recipes.md)

---

## ⚙️ Wie es funktioniert

```
  "Spiel Dark S1E1"
        │
        ▼
  ┌─── Auflösung ───┐
  │ Cache → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 TV spielt es ab
  └───────────────────┘       │
                         Deep link via
                    LG / Samsung / Roku / Android
```

Sag einen Namen. stv löst ihn zu einer Inhalts-ID auf und deep-linkt in die App auf deinem TV. Keine Browser-Automatisierung, keine API-Keys, keine Cloud-Abhängigkeit. Ergebnisse werden gecacht, sodass wiederholte Abspielungen sofort funktionieren.

---

## 📦 Installation

```bash
pip install stv                    # LG webOS (Standard)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # Alles
```

```bash
stv setup                          # TV automatisch entdecken und koppeln
```

> Unterstützt **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 Funktioniert mit

| Integration | Wie |
|------------|-----|
| **Claude Code / Cursor** | MCP-Config hinzufügen → `"spiel Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → Telegram-Bot |
| **Home Assistant** | Shell-Befehle in Automationen |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Shell-Skripte** | `sleep-mode`-, `party-mode`-Einzeiler |
| **Jeder MCP-Client** | 21 Tools, stdio oder HTTP (`stv serve`) |

---

## 📚 Dokumentation

| | |
|---|---|
| [Erste Schritte](../../docs/getting-started/installation.md) | Einrichtung für jede TV-Marke |
| [Inhalte abspielen](../../docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Szenen](../../docs/guides/scenes.md) | movie-night, kids, sleep, eigene |
| [Sync & Party](../../docs/guides/sync-party.md) | Multi-TV, Remote-Watch-Party |
| [Rezepte](../../docs/guides/recipes.md) | **10 leistungsstarke Funktionskombos** |
| [KI-Agenten](../../docs/guides/ai-agents.md) | MCP für Claude, Cursor, OpenClaw |
| [CLI-Referenz](../../docs/reference/cli.md) | Alle Befehle und Optionen |
| [MCP-Tools](../../docs/reference/mcp-tools.md) | Alle 21 Tools mit Parametern |

---

## 🤝 Mitmachen

211 Tests. Kein TV nötig, um sie auszuführen.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Samsung-, Roku- und Android-TV-Treiber brauchen Tests in der Praxis. Wenn du einen hast, [zählt dein Feedback](https://github.com/Hybirdss/smartest-tv/issues).

[Cache beitragen](../../docs/contributing/cache-contributions.md) · [Treiberentwicklung](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Mit Python erstellt · Keine Cloud erforderlich</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
