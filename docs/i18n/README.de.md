# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Deutsch** | [Português](README.pt-br.md) | [Français](README.fr.md)

**Sprich mit deinem Fernseher. Er hört zu.**

Andere Tools öffnen Netflix. smartest-tv spielt *Frieren Staffel 2, Folge 8*.

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## Schnellstart

```bash
pip install stv
stv setup          # erkennt deinen Fernseher automatisch, koppelt, fertig
```

Das war's. Kein Entwicklermodus. Keine API-Keys. Keine Umgebungsvariablen. Sag einfach, was du sehen willst.

## Was kannst du damit machen?

```
Du: Spiel Frieren Staffel 2, Folge 8 auf Netflix
Du: Mach Baby Shark für die Kinder an
Du: Das neue Album von Ye auf Spotify
Du: Bildschirm aus, Jazz an
Du: Gute Nacht
```

Die KI findet die Inhalts-ID (Netflix-Episode, YouTube-Video, Spotify-URI), ruft `stv` auf, und dein Fernseher spielt es ab.

### See it in action

https://github.com/Hybirdss/smartest-tv/raw/main/docs/assets/demo.mp4

## Installation

```bash
pip install stv                 # LG (Standard, direkt einsatzbereit)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Alles
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # Suchen + in einem Schritt abspielen
stv play youtube "baby shark"                          # Suchen + abspielen
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # Nur die ID ermitteln
stv launch netflix 82656797         # Direkter Deep Link (wenn du die ID kennst)
stv status                          # Was läuft, Lautstärke, Stummschaltung
stv volume 25                       # Lautstärke einstellen
stv mute                            # Stummschaltung umschalten
stv apps --format json              # Apps auflisten (strukturierte Ausgabe)
stv notify "Essen ist fertig!"      # Benachrichtigung auf dem Bildschirm
stv off                             # Gute Nacht
```

Alle Befehle unterstützen `--format json` — konzipiert für Skripte und KI-Agenten.

### Inhaltsauflösung

`stv resolve` findet Streaming-IDs, damit du es nicht musst. `stv play` erledigt dasselbe und startet den Inhalt in einem Schritt direkt auf dem Fernseher.

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → wird direkt weitergegeben
```

Die Netflix-Auflösung funktioniert durch Scraping der Episodenmetadaten von der Titelseite mit einer einzigen `curl`-Anfrage — kein Playwright, kein Browser, kein Login. Alle Staffeln werden auf einmal aufgelöst und lokal gecacht. Die zweite Suche ist sofort (~0,1 s).

### Cache

Sobald eine ID gefunden wurde, wird sie dauerhaft unter `~/.config/smartest-tv/cache.json` gecacht. Du kannst den Cache auch manuell befüllen:

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # Alle gecachten IDs anzeigen
```

## Agent Skills

smartest-tv bringt fünf Skills mit, die KI-Assistenten beibringen, wie man einen Fernseher steuert. In Claude Code installieren:

```bash
cd smartest-tv && ./install-skills.sh
```

| Skill | Funktion |
|-------|----------|
| `tv-shared` | CLI-Referenz, Authentifizierung, Konfiguration, häufige Muster |
| `tv-netflix` | Episoden-ID-Abfrage per HTTP-Scraping |
| `tv-youtube` | Videosuche per yt-dlp, Format-Auflösung |
| `tv-spotify` | Auflösung von Album-/Track-/Playlist-URIs |
| `tv-workflow` | Kombinierte Aktionen: Kinoabend, Kindermodus, Einschlaftimer |

Skills sind einfache Markdown-Dateien. In wenigen Minuten auf jeden Agenten portierbar.

## Works With

Jeder KI-Agent, der Shell-Befehle ausführen kann:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · oder einfach `bash`

## Alltag

**Nachts um 2 Uhr.** Du liegst im Bett. Du sagst Claude: „Weiter mit Frieren." Der Fernseher im Wohnzimmer geht an, Netflix öffnet sich, die Episode beginnt. Fernbedienung nicht angefasst, Augen kaum aufgemacht.

**Samstagmorgen.** „Mach Cocomelon für die Kleinen an." YouTube findet es, der Fernseher spielt es ab. Du machst einfach weiter mit dem Frühstück.

**Wenn Freunde kommen.** „Gaming-Modus, HDMI 2, Lautstärke runter." Ein Satz, drei Änderungen, bevor es jemand bemerkt.

**Beim Kochen.** „Bildschirm aus, Jazz an." Der Bildschirm geht aus, Musik läuft durch die Lautsprecher.

**Vor dem Einschlafen.** „Schlaftimer 45 Minuten." Der Fernseher schaltet sich selbst ab. Du nicht.

## Was smartest-tv ist

- **Deep-Link-Resolver** — findet die Netflix-Episoden-ID, das YouTube-Video, die Spotify-URI
- **Universal-Fernbedienung** — eine CLI für 4 TV-Plattformen
- **KI-nativ** — entwickelt, damit Agenten es aufrufen, nicht nur Menschen

## Was es nicht ist

- Keine Fernbedienungs-App (kein Zappen, keine Pfeiltasten)
- Kein HDMI-CEC-Controller
- Kein Screen-Mirroring-Tool

<details>
<summary><strong>Deep Linking</strong> — wie es wirklich funktioniert</summary>

Die gleiche Inhalts-ID funktioniert auf allen TV-Plattformen:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Genauso
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Genauso
```

Jeder Treiber übersetzt die ID in das plattformspezifische Deep-Link-Format:

| Fernseher | Wie der Deep Link gesendet wird |
|-----------|--------------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Darum musst du dich nie kümmern. Der Treiber erledigt das.

</details>

<details>
<summary><strong>Plattformen</strong> — unterstützte Fernseher und Treiber</summary>

| Plattform | Treiber | Verbindung | Status |
|-----------|---------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Getestet** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Community-Tests |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Community-Tests |
| Roku | HTTP ECP | REST :8060 | Community-Tests |

LG ist die primär getestete Plattform. Auf keiner Plattform ist ein Entwicklermodus erforderlich.

</details>

## Zero-config-Einrichtung

```bash
stv setup
```

Erkennt deinen Fernseher automatisch im Netzwerk, identifiziert die Plattform, koppelt sich selbstständig und schreibt alles in `~/.config/smartest-tv/config.toml`. Wenn etwas nicht stimmt, erklärt `stv doctor` genau, was los ist.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, für Wake-on-LAN
```

Beim ersten Verbindungsaufbau erscheint eine Kopplungsaufforderung auf dem Fernseher. Einmal bestätigen — der Schlüssel wird gespeichert und nie wieder abgefragt.

## MCP-Server

Für Claude Desktop, Cursor oder andere MCP-Clients — optional, der CLI ist die primäre Schnittstelle:

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

## Architektur

```
Du (natürliche Sprache)
  → KI + stv resolve (findet Inhalts-ID via HTTP-Scraping / yt-dlp / Cache)
    → stv play (formatiert Deep Link und sendet)
      → Treiber (WebSocket / ADB / HTTP)
        → Fernseher
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## Mitmachen

| Status | Bereich | Was gebraucht wird |
|--------|---------|-------------------|
| **Bereit** | LG webOS-Treiber | Getestet und funktionsfähig |
| **Braucht Tests** | Samsung, Android TV, Roku-Treiber | Erfahrungsberichte mit echter Hardware willkommen |
| **Gesucht** | Disney+-Skill | Deep-Link-ID-Auflösung |
| **Gesucht** | Hulu, Prime Video Skills | Deep-Link-ID-Auflösung |

Das [Treiber-Interface](src/smartest_tv/drivers/base.py) ist definiert — implementiere `TVDriver` für deine Plattform und öffne einen PR.

## Lizenz

MIT
