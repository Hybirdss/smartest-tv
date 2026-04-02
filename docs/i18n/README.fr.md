# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | **Français**

Parlez à votre TV. Elle écoute.

Un CLI et des skills d'agent pour contrôler les smart TV en langage naturel. Deep link vers Netflix, YouTube, Spotify — dites ce que vous voulez regarder et ça se lance.

> "Joue Frieren saison 2 épisode 8"
>
> *Netflix s'ouvre. L'épisode commence.*

Compatible **LG**, **Samsung**, **Android TV**, **Fire TV** et **Roku**.

## Installation

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # Tout
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # État actuel (app, volume, sourdine)
tv launch netflix 82656797         # Deep link vers un contenu spécifique
tv launch youtube dQw4w9WgXcQ     # Lire une vidéo YouTube
tv volume 25                       # Régler le volume
tv off                             # Bonne nuit
```

## Skills d'agent

Installez les skills dans Claude Code :

```bash
cd smartest-tv && ./install-skills.sh
```

Puis parlez simplement à Claude :

```
Vous : Mets Frieren saison 2 épisode 8 sur Netflix
Vous : Mets Baby Shark sur YouTube pour les enfants
Vous : Éteins l'écran et mets du jazz sur Spotify
Vous : Bonne nuit
```

## Licence

MIT
