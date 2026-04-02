# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Deutsch** | [Português](README.pt-br.md) | [Français](README.fr.md)

Sprich mit deinem Fernseher. Er hört zu.

CLI und KI-Agenten-Skill zur Steuerung deines Smart TVs per natürlicher Sprache. Deep Links für Netflix, YouTube und Spotify — sag, was du sehen willst, und es läuft.

> „Spiel Folge 8 der zweiten Staffel Frieren ab"
>
> *Netflix öffnet sich und die Episode beginnt.*

Unterstützt **LG**, **Samsung**, **Android TV**, **Fire TV** und **Roku**.

## Installation

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # Alles
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # Aktueller Status (App, Lautstärke, Stummschaltung)
tv launch netflix 82656797         # Bestimmten Inhalt auf Netflix abspielen
tv launch youtube dQw4w9WgXcQ     # YouTube-Video abspielen
tv launch spotify spotify:album:x # Spotify abspielen
tv volume 25                       # Lautstärke einstellen
tv mute                            # Stummschaltung umschalten
tv apps --format json              # Liste installierter Apps
tv notify "Essen ist fertig!"      # Benachrichtigung auf dem TV anzeigen
tv off                             # TV ausschalten
```

Alle Befehle unterstützen `--format json` — strukturierte Ausgabe für KI-Agenten.

## KI-Agenten-Skill

Skill in Claude Code installieren:

```bash
cd smartest-tv && ./install-skills.sh
```

Dann einfach in natürlicher Sprache mit Claude reden:

```
Du: Spiel Frieren Staffel 2, Folge 8 auf Netflix
Du: Mach YouTube für die Kinder an
Du: Spiel das neue Album von Ye auf Spotify
Du: Bildschirm aus und Jazz an
Du: Gute Nacht
```

Der Skill übernimmt die komplizierte Arbeit — Netflix-Episoden-IDs suchen, YouTube via yt-dlp durchsuchen, Spotify-URIs auflösen — und ruft dann die `tv` CLI auf, um den Fernseher zu steuern.

## Deep Links

Das ist das entscheidende Alleinstellungsmerkmal von smartest-tv. Andere Tools öffnen Netflix nur. Wir *spielen Folge 36 von Frieren ab*.

Dieselbe Inhalts-ID funktioniert auf allen TV-Plattformen:

```bash
tv launch netflix 82656797       # Egal ob LG, Samsung oder Roku
tv launch youtube dQw4w9WgXcQ    # Genauso
tv launch spotify spotify:album:x  # Genauso
```

## Praxisbeispiele

**Nachts um 2 Uhr.** Im Bett sagst du Claude: „Weiter mit Frieren." Der Fernseher im Wohnzimmer geht an, Netflix öffnet sich, die Episode beginnt. Keine Fernbedienung nötig.

**Samstagmorgen.** „Mach Cocomelon für die Kleinen an." Es findet es auf YouTube und spielt es auf dem Fernseher ab. Mach einfach weiter mit dem Frühstück.

**Wenn Freunde zu Besuch kommen.** „Gaming-Modus, HDMI 2, Lautstärke runter." Drei Änderungen mit einem Satz.

## Lizenz

MIT
