# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Deutsch** | [Português](README.pt-br.md) | [Français](README.fr.md)

**Sprich mit deinem Fernseher. Er hört zu.**

Andere Tools öffnen Netflix. smartest-tv spielt *The Queen's Gambit Folge 5*.

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
Du: Spiel Squid Game Staffel 2 Folge 3 auf Netflix
Du: Mach Baby Shark für die Kinder an
Du: Den Wednesday-Soundtrack auf Spotify
Du: Finde Glass Onion auf Netflix          (Filme funktionieren auch)
Du: Bildschirm aus, lo-fi Beats an
Du: Gute Nacht
```

Die KI findet die Inhalts-ID (Netflix-Episode, YouTube-Video, Spotify-URI), ruft `stv` auf, und dein Fernseher spielt es ab.

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Installation

```bash
pip install stv                 # LG (Standard, direkt einsatzbereit)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Alles
```

## CLI

```bash
# Inhalte nach Name abspielen — stv findet die ID automatisch
stv play netflix "Bridgerton" s3e4         # Auflösen + Deep Link in einem Schritt
stv play youtube "baby shark"              # Suchen + abspielen
stv play spotify "Ye White Lines"          # Auf Spotify suchen + abspielen

# Suchen ohne Abspielen
stv search netflix "Money Heist"           # Zeigt alle Staffeln + Episodenanzahl
stv search youtube "lofi hip hop"          # Top 3 Ergebnisse
stv resolve netflix "The Witcher" s2e5     # Nur die Episoden-ID ermitteln

# Weiterschauen
stv next                                   # Nächste Episode aus dem Verlauf abspielen
stv next "Breaking Bad"                    # Nächste Episode einer bestimmten Serie
stv history                                # Zuletzt abgespielt mit Zeitstempel

# TV-Steuerung
stv status                                 # Was läuft, Lautstärke, Stummschaltung
stv volume 25                              # Lautstärke einstellen
stv mute                                   # Stummschaltung umschalten
stv notify "Essen ist fertig!"            # Benachrichtigung auf dem Bildschirm
stv off                                    # Gute Nacht

# Direkter Deep Link (wenn du die ID kennst)
stv launch netflix 82656797
```

Alle Befehle unterstützen `--format json` — konzipiert für Skripte und KI-Agenten.

### Wie die Inhaltsauflösung funktioniert

`stv play` und `stv resolve` finden Streaming-IDs, damit du es nicht musst:

```bash
stv resolve netflix "The Witcher" s2e5     # → 80189693
stv resolve youtube "lofi hip hop"         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify "Ye White Lines"       # → spotify:track:3bbjDFVu...
```

Die Netflix-Auflösung ist eine einzige `curl`-Anfrage an die Titelseite. Netflix rendert `__typename:"Episode"`-Metadaten serverseitig in `<script>`-Tags. Episoden-IDs innerhalb einer Staffel sind aufeinanderfolgende Ganzzahlen, sodass eine HTTP-Anfrage jede Staffel einer Serie auflöst. Kein Playwright, kein Browser, kein Login.

Ergebnisse werden in drei Ebenen gecacht:
1. **Lokaler Cache** — `~/.config/smartest-tv/cache.json`, sofort (~0,1 s)
2. **Community-Cache** — Crowdsourced IDs via GitHub raw CDN (29 Netflix-Serien, 11 YouTube-Videos vorgeladen), keine Serverkosten
3. **Websuch-Fallback** — Brave Search findet automatisch unbekannte Titel-IDs

### Cache

```bash
stv cache show                                # Alle gecachten IDs anzeigen
stv cache set netflix "Narcos" -s 1 --first-ep-id 80025173 --count 10
stv cache get netflix "Narcos" -s 1 -e 5      # → 80025177
stv cache contribute                          # Für Community-Cache-PR exportieren
```

## Agent Skills

smartest-tv bringt einen Skill mit, der KI-Assistenten alles über die TV-Steuerung beibringt. In Claude Code installieren:

```bash
cd smartest-tv && ./install-skills.sh
```

Der `tv`-Skill deckt alle Plattformen (Netflix, YouTube, Spotify), alle Befehle (`play`, `search`, `resolve`, `cache`, `volume`, `off`) und kombinierte Workflows (Kinoabend, Kindermodus, Einschlaftimer) ab. Eine einzige Markdown-Datei — in wenigen Minuten auf jeden KI-Agenten portierbar.

## Works With

Jeder KI-Agent, der Shell-Befehle ausführen kann:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · oder einfach `bash`

## Alltag

**Nachts um 2 Uhr.** Du liegst im Bett. Du sagst Claude: „Weiter mit Stranger Things." Der Fernseher im Wohnzimmer geht an, Netflix öffnet sich, die Episode beginnt. Fernbedienung nicht angefasst, Augen kaum aufgemacht.

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

Scannt gleichzeitig nach LG, Samsung, Roku und Android/Fire TV im Netzwerk (SSDP + ADB). Erkennt die Plattform, koppelt sich, speichert die Konfiguration und sendet eine Testbenachrichtigung — alles in einem Schritt. Falls der Fernseher nicht automatisch gefunden wird, IP direkt angeben:

```bash
stv setup --ip 192.168.1.100
```

Alles landet in `~/.config/smartest-tv/config.toml`. Wenn etwas nicht stimmt, erklärt `stv doctor` genau, was los ist.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, für Wake-on-LAN
```

Beim ersten Verbindungsaufbau erscheint eine Kopplungsaufforderung auf dem Fernseher. Einmal bestätigen — der Schlüssel wird gespeichert und nie wieder abgefragt.

## MCP-Server

### Lokal (stdio)

Für Claude Desktop, Cursor oder andere MCP-Clients — als lokaler Prozess verbinden:

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

### Remote (HTTP)

stv als netzwerkzugänglichen MCP-Server starten. Nützlich für KI-Agenten auf anderen Maschinen:

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

Von beliebigen MCP-Clients verbinden:

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
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

## Dokumentation

| Anleitung | Inhalt |
|-----------|--------|
| [Einrichtungsanleitung](docs/setup-guide.md) | Markenspezifische TV-Einrichtung (LG-Kopplung, Samsung-Fernzugriff, ADB, Roku ECP) |
| [MCP-Integration](docs/mcp-integration.md) | Konfiguration für Claude Code, Cursor und andere MCP-Clients |
| [API-Referenz](docs/api-reference.md) | Alle CLI-Befehle + alle 20 MCP-Tools mit Parametern |
| [Cache beitragen](docs/contributing-cache.md) | Wie man Netflix-IDs findet und einen PR zum Community-Cache einreicht |

## Mitmachen

| Status | Bereich | Was gebraucht wird |
|--------|---------|-------------------|
| **Bereit** | LG webOS-Treiber | Getestet und funktionsfähig |
| **Braucht Tests** | Samsung, Android TV, Roku-Treiber | Erfahrungsberichte mit echter Hardware willkommen |
| **Gesucht** | Disney+, Hulu, Prime Video | Deep-Link-ID-Auflösung |
| **Gesucht** | Community-Cache-Einträge | [Füge deine Lieblingsserien hinzu](docs/contributing-cache.md) |

Das [Treiber-Interface](src/smartest_tv/drivers/base.py) ist definiert — implementiere `TVDriver` für deine Plattform und öffne einen PR.

### Tests ausführen

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

55 Unit-Tests für den Content-Resolver, den Cache und den CLI-Parser. Kein Fernseher und keine Netzwerkverbindung erforderlich — alle externen Aufrufe sind gemockt.

## Lizenz

MIT
