# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Deutsch** | [Português](README.pt-br.md) | [Français](README.fr.md)

**Sprich mit deinem Fernseher. Er hört zu.**

| Ohne stv | Mit stv |
|:--------:|:-------:|
| Netflix-App auf dem Handy öffnen | `stv play netflix "Dark" s1e1` |
| Nach der Serie suchen | (automatisch aufgelöst) |
| Staffel auswählen | (berechnet) |
| Folge auswählen | (deep-linked) |
| Play drücken | |
| **~30 Sekunden** | **~3 Sekunden** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Klicken für das vollständige Video mit Ton*

## Schnellstart

```bash
pip install stv
stv setup          # findet deinen Fernseher, koppelt, fertig
```

## Was Leute mit stv machen

### "Diesen Link auf meinen Fernseher casten"

Ein Freund schickt dir einen YouTube-Link. Du fügst ihn ein. Der Fernseher spielt ihn ab.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "Songs für die Party in die Warteschlange"

Jeder fügt seinen Song hinzu. Der Fernseher spielt sie der Reihe nach ab.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # startet die Wiedergabe in der Reihenfolge
stv queue skip                     # nächster Song
```

### "Was sollen wir schauen?"

Hör auf, 30 Minuten auf Netflix zu suchen. Frag, was gerade angesagt ist. Lass dir etwas empfehlen.

```bash
stv whats-on netflix               # Top 10 Trends gerade jetzt
stv recommend --mood chill         # basierend auf deinem Verlauf
stv recommend --mood action        # andere Stimmung, andere Vorschläge
```

### "Filmabend"

Ein Befehl setzt die Stimmung: Lautstärke, Benachrichtigungen, Inhalt.

```bash
stv scene movie-night              # Lautstärke 20, Kinomodus
stv scene kids                     # Lautstärke 15, spielt Cocomelon
stv scene sleep                    # Ambient-Sounds, automatisches Ausschalten
stv scene create date-night        # eigene Scene erstellen
```

### "Spiel es auf dem Schlafzimmer-Fernseher ab"

Steuere jeden Fernseher im Haus über eine CLI.

```bash
stv multi list                     # Wohnzimmer (LG), Schlafzimmer (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### "Weiter wo ich aufgehört habe"

```bash
stv next                           # setzt bei der letzten Folge fort
stv next "Breaking Bad"            # bestimmte Serie
stv history                        # anzeigen, was du zuletzt geschaut hast
```

## Ein Tag mit stv

**7:00 Uhr** -- Wecker klingelt. "Was ist im Trend?" `stv whats-on youtube` zeigt die Morgennachrichten. Fernseher spielt sie ab.

**8:00 Uhr** -- Kinder wachen auf. `stv scene kids` -- Lautstärke 15, Cocomelon startet.

**12:00 Uhr** -- Ein Freund schickt einen Netflix-Link. `stv cast https://netflix.com/watch/...` -- Fernseher spielt ihn ab.

**18:30 Uhr** -- Heimkommen von der Arbeit. `stv scene movie-night` -- Lautstärke runter, Kinomodus.

**19:00 Uhr** -- "Was schauen wir?" `stv recommend --mood chill` -- empfiehlt The Queen's Gambit.

**21:00 Uhr** -- Freunde kommen vorbei. Alle führen `stv queue add ...` aus -- Fernseher spielt sie der Reihe nach ab.

**23:30 Uhr** -- "Gute Nacht." `stv scene sleep` -- Ambient-Sounds, Fernseher schaltet sich in 45 Minuten aus.

<details>
<summary><b>Wie findet stv eine Netflix-Folge mit einer einzigen HTTP-Anfrage?</b></summary>

Netflix rendert `__typename:"Episode"`-Metadaten serverseitig in `<script>`-Tags. Folgen-IDs innerhalb einer Staffel sind aufeinanderfolgende Ganzzahlen. Eine einzige `curl`-Anfrage an eine Titelseite extrahiert jede Folgen-ID jeder Staffel. Kein Playwright, kein Headless-Browser, kein API-Key, kein Login.

Ergebnisse werden in drei Ebenen gecacht:
1. **Lokaler Cache** -- `~/.config/smartest-tv/cache.json`, sofort (~0,1 s)
2. **Community-Cache** -- Crowdsourced IDs via GitHub raw CDN (über 40 vorgeladene Einträge), keine Serverkosten
3. **Websuch-Fallback** -- Brave Search findet automatisch unbekannte Titel-IDs

</details>

<details>
<summary><b>Deep Linking -- wie stv mit deinem Fernseher kommuniziert</b></summary>

Jeder Treiber übersetzt eine Inhalts-ID in das plattformspezifische Format:

| Fernseher | Protokoll | Deep-Link-Format |
|-----------|----------|-----------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

Darum musst du dich nie kümmern. Der Treiber erledigt das.

</details>

<details>
<summary><b>Unterstützte Plattformen</b></summary>

| Plattform | Treiber | Status |
|-----------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **Getestet** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Community-Tests |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Community-Tests |
| Roku | HTTP ECP | Community-Tests |

</details>

## Installation

```bash
pip install stv                 # LG (Standard)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Alles
```

## Funktioniert mit allem

| Integration | Was passiert |
|------------|-------------|
| **Claude Code** | "Spiel Breaking Bad s1e1" -- Fernseher spielt es ab |
| **OpenClaw** | Telegram: "Ich bin zu Hause" -- scene + recommend + play |
| **Home Assistant** | Tür geht auf -- Fernseher geht an -- Trends erscheinen |
| **Cursor / Codex** | KI schreibt Code, steuert deinen Fernseher in der Pause |
| **cron / Skripte** | 7 Uhr: Nachrichten auf dem Schlafzimmer-TV. 21 Uhr: Kinder-TV aus |
| **Jeder MCP-Client** | 32 Tools über stdio oder HTTP |

### MCP-Server

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

Oder als HTTP-Server für Remote-Zugriff starten:

```bash
stv serve --port 8910              # SSE auf http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## Dokumentation

| | |
|---|---|
| [Erste Schritte](docs/getting-started/installation.md) | Ersteinrichtung für jede TV-Marke |
| [Inhalte abspielen](docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Scenes](docs/guides/scenes.md) | Presets: movie-night, kids, sleep, custom |
| [Multi-TV](docs/guides/multi-tv.md) | Mehrere Fernseher mit `--tv` steuern |
| [KI-Agenten](docs/guides/ai-agents.md) | MCP-Einrichtung für Claude, Cursor, OpenClaw |
| [Empfehlungen](docs/guides/recommendations.md) | KI-gestützte Inhaltsvorschläge |
| [CLI-Referenz](docs/reference/cli.md) | Alle Befehle und Optionen |
| [MCP-Tools](docs/reference/mcp-tools.md) | Alle 32 MCP-Tools mit Parametern |
| [OpenClaw](docs/integrations/openclaw.md) | ClawHub-Skill + Telegram-Szenarien |

## Mitmachen

Samsung-, Roku- und Android-TV-Treiber brauchen Tests in der Praxis. Wenn du einen dieser Fernseher hast, ist dein Feedback sehr wertvoll.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 Tests, kein Fernseher erforderlich
```

Möchtest du deine Lieblingsserien zum Community-Cache hinzufügen? Siehe [Cache beitragen](docs/contributing/cache-contributions.md).

Möchtest du einen Treiber für einen neuen Fernseher schreiben? Siehe [Treiberentwicklung](docs/contributing/driver-development.md).

## Lizenz

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
