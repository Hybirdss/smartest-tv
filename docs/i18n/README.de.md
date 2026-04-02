# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Deutsch** | [Português](README.pt-br.md) | [Français](README.fr.md)

**Sprich mit deinem Fernseher. Er hört zu.**

CLI und KI-Agenten-Skills zur Steuerung deines Smart TVs per natürlicher Sprache. Deep Links für Netflix, YouTube und Spotify — sag, was du sehen willst, und es läuft. Kein Entwicklermodus. Keine API-Keys. Einmal `stv setup` und fertig.

> „Spiel Frieren Staffel 2, Folge 8"
>
> *Netflix öffnet sich. Die Episode beginnt.*

Unterstützt **LG** (getestet), **Samsung**, **Android TV / Fire TV** und **Roku** (Community-Tests).

## Installation

```bash
pip install stv
```

Das war's. Für LG brauchst du nichts weiter.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # Alles
```

## Einrichtung in einem Schritt

Einmal ausführen, nie wieder anfassen:

```bash
stv setup
```

Erkennt den Fernseher automatisch im Netzwerk, identifiziert die Plattform (LG? Samsung? Roku?), koppelt sich selbstständig — kein Entwicklermodus nötig, keine IP-Adresse suchen — und schreibt alles in `~/.config/smartest-tv/config.toml`. Danach funktioniert jeder `stv`-Befehl sofort.

Wenn etwas nicht stimmt, erklärt `stv doctor` genau, was los ist.

## CLI

```bash
stv status                          # Was läuft, Lautstärke, Stummschaltung
stv launch netflix 82656797         # Deep Link zu bestimmtem Inhalt
stv launch youtube dQw4w9WgXcQ     # YouTube-Video abspielen
stv launch spotify spotify:album:x  # Spotify abspielen
stv volume 25                       # Lautstärke einstellen
stv mute                            # Stummschaltung umschalten
stv apps --format json              # Installierte Apps auflisten
stv notify "Essen ist fertig!"      # Benachrichtigung auf dem Bildschirm
stv off                             # Fernseher aus
```

Alle Befehle unterstützen `--format json` — strukturierte Ausgabe für Skripte und KI-Agenten.

## KI-Agenten-Skills

stv bringt fünf Skills mit, die KI-Assistenten beibringen, wie man einen Fernseher intelligent steuert. Alles auf einmal in Claude Code installieren:

```bash
cd smartest-tv && ./install-skills.sh
```

Dann einfach mit Claude reden:

```
Du: Frieren Staffel 2, Folge 8 auf Netflix
Du: Mach YouTube für die Kinder an
Du: Das neue Album von Ye auf Spotify
Du: Bildschirm aus und Jazz an
Du: Gute Nacht
```

Die Skills erledigen die komplizierte Arbeit — Netflix-Episoden-IDs suchen, YouTube via yt-dlp durchsuchen, Spotify-URIs auflösen — und rufen dann `stv` auf, um den Fernseher zu steuern.

### Skill-Übersicht

| Skill | Funktion |
|-------|----------|
| `tv-shared` | CLI-Referenz, Authentifizierung, Konfiguration, häufige Muster |
| `tv-netflix` | Episoden-ID-Abfrage per Playwright |
| `tv-youtube` | Videosuche per yt-dlp |
| `tv-spotify` | Auflösung von Album-/Track-/Playlist-URIs |
| `tv-workflow` | Kombinierte Aktionen: Kinoabend, Kindermodus, Einschlaftimer |

## Warum Deep Links den Unterschied machen

Andere Tools *öffnen* Netflix. stv *spielt Frieren Folge 36 ab*. Das ist der entscheidende Unterschied.

Dieselbe Inhalts-ID funktioniert auf allen TV-Plattformen:

```bash
stv launch netflix 82656797                          # Egal ob LG, Samsung oder Roku
stv launch youtube dQw4w9WgXcQ                       # Genauso
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # Genauso
```

Jeder Treiber übersetzt die Inhalts-ID in das plattformspezifische Deep-Link-Format:

| TV | Wie der Deep Link gesendet wird |
|----|-------------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Darum musst du dich nie kümmern. Der Treiber erledigt das.

## Plattformen

| Plattform | Treiber | Verbindung | Status |
|-----------|---------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Getestet** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Community-Tests |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Community-Tests |
| Roku | HTTP ECP | REST :8060 | Community-Tests |

LG ist die primär getestete Plattform. Samsung, Android TV und Roku sollten funktionieren — kein Entwicklermodus auf keiner Plattform erforderlich — Erfahrungsberichte aus der Community sind willkommen.

## Konfiguration

Die Konfiguration liegt in `~/.config/smartest-tv/config.toml`. Nach `stv setup` sieht sie ungefähr so aus:

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optional, für Wake-on-LAN
```

Beim ersten Verbindungsaufbau erscheint eine Koppelungsaufforderung auf dem TV. Einmal bestätigen — der Schlüssel wird gespeichert und nie wieder abgefragt.

## Alltagsszenarien

**Nachts um 2 Uhr.** Im Bett sagst du Claude: „Weiter mit Frieren." Der Fernseher im Wohnzimmer geht an, Netflix öffnet sich, die Episode beginnt. Fernbedienung nicht angefasst, Augen kaum aufgemacht.

**Samstagmorgen.** „Mach Cocomelon für die Kleinen an." Es findet es auf YouTube und spielt es ab. Du machst einfach weiter mit dem Frühstück.

**Wenn Freunde kommen.** „Gaming-Modus, HDMI 2, Lautstärke runter." Drei Änderungen in einem Satz, bevor es jemand bemerkt.

**Beim Kochen.** „Bildschirm aus und Jazz an." Der Bildschirm geht aus, Musik läuft. Kein Menü durchsuchen, keine App starten.

**Vor dem Einschlafen.** „Schalte in 45 Minuten aus." Der Fernseher schaltet sich selbst ab. Du musst es nicht.

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

18 Tools verfügbar: `tv_on`, `tv_off`, `tv_launch`, `tv_close`, `tv_volume`, `tv_set_volume`, `tv_mute`, `tv_play`, `tv_pause`, `tv_stop`, `tv_status`, `tv_info`, `tv_notify`, `tv_apps`, `tv_volume_up`, `tv_volume_down`, `tv_screen_on`, `tv_screen_off`.

Die Konfiguration wird automatisch aus `~/.config/smartest-tv/config.toml` gelesen — keine Umgebungsvariablen nötig.

## Architektur

```
Du (natürliche Sprache)
  → KI + Skills (findet Inhalts-ID via yt-dlp / Playwright / Websuche)
    → stv CLI (formatiert und sendet)
      → Treiber (WebSocket / ADB / HTTP)
        → Fernseher
```

## Mitmachen

**Treiber** für Samsung, Android TV und Roku sind der wirkungsvollste Beitrag. Die [Treiber-Schnittstelle](src/smartest_tv/drivers/base.py) ist definiert — implementiere `TVDriver` für deine Plattform und öffne einen PR.

**Skills** für neue Streaming-Dienste (Disney+, Hulu, Prime Video) sind ebenfalls willkommen.

## Lizenz

MIT
