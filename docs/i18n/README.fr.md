# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | **Français**

**Parle à ta TV. Elle écoute.**

Les autres outils ouvrent Netflix. smartest-tv lance *Frieren saison 2 épisode 8*.

<!-- TODO: Add terminal demo GIF here -->
<!-- ![demo](docs/assets/demo.gif) -->

## Démarrage rapide

```bash
pip install stv
stv setup          # détecte ta TV automatiquement, fait le jumelage, c'est tout
```

C'est tout. Pas de mode développeur. Pas de clé API. Pas de variables d'environnement. Dis ce que tu veux regarder.

## Qu'est-ce qu'on peut faire ?

```
Toi : Play Frieren season 2 episode 8 on Netflix
Toi : Put on Baby Shark for the kids
Toi : Ye's new album on Spotify
Toi : Screen off, play my jazz playlist
Toi : Good night
```

L'IA trouve l'ID du contenu (épisode Netflix, vidéo YouTube, URI Spotify), appelle `stv`, et la TV lance. 

## Installation

```bash
pip install stv                 # LG (défaut, batteries incluses)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Tout
```

## CLI

```bash
stv status                          # Ce qui tourne, volume, sourdine
stv launch netflix 82656797         # Deep link vers un contenu précis
stv launch youtube dQw4w9WgXcQ     # Lancer une vidéo YouTube
stv launch spotify spotify:album:x  # Lancer sur Spotify
stv volume 25                       # Régler le volume
stv mute                            # Activer/désactiver la sourdine
stv apps --format json              # Lister les apps (sortie structurée)
stv notify "Dinner's ready"         # Notification toast à l'écran
stv off                             # Bonne nuit
```

Chaque commande accepte `--format json` — conçu pour les scripts et les agents IA.

## Skills d'agent

smartest-tv est livré avec cinq skills qui apprennent aux assistants IA à contrôler ta TV. Pour les installer dans Claude Code :

```bash
cd smartest-tv && ./install-skills.sh
```

| Skill | Ce qu'il fait |
|-------|--------------|
| `tv-shared` | Référence CLI, auth, config, patterns courants |
| `tv-netflix` | Récupération d'ID d'épisodes via scraping Playwright |
| `tv-youtube` | Recherche de vidéos via yt-dlp, résolution de format |
| `tv-spotify` | Résolution d'URI d'albums, pistes et playlists |
| `tv-workflow` | Actions combinées : soirée ciné, mode enfants, minuteur sommeil |

Les skills sont de simples fichiers Markdown. Portables vers n'importe quel agent en quelques minutes.

## Compatible avec

Tout agent IA capable d'exécuter des commandes shell :

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · ou tout simplement `bash`

## En pratique

**2h du matin.** Tu es dans ton lit. Tu dis à Claude : « Lance Frieren où j'en étais. » La TV du salon s'allume, Netflix s'ouvre, l'épisode commence. Tu n'as jamais touché la télécommande. Tu as à peine ouvert les yeux.

**Samedi matin.** « Mets Cocomelon pour le bébé. » YouTube le trouve, la TV le lance. Toi, tu continues de préparer le petit-déjeuner.

**Des amis sont là.** « Mode jeu, HDMI 2, baisse le son. » Une phrase, trois changements, avant que personne ne s'en soit aperçu.

**En cuisinant.** « Éteins l'écran et mets du jazz. » L'écran s'éteint, la musique coule des haut-parleurs.

**Tu t'endors.** « Éteins dans 45 minutes. » La TV s'éteint toute seule. Pas toi.

## Ce qu'est smartest-tv

- **Résolveur de deep links** — trouve l'ID d'épisode Netflix, la vidéo YouTube, l'URI Spotify
- **Télécommande universelle** — un seul CLI pour 4 plateformes TV
- **Conçu pour les agents** — pensé pour être appelé par des agents IA, pas seulement des humains

## Ce que ce n'est pas

- Pas une appli de télécommande (pas de zapping, pas de touches directionnelles)
- Pas un contrôleur HDMI-CEC
- Pas un outil de mirroring d'écran

<details>
<summary><strong>Deep Linking</strong> — comment ça marche vraiment</summary>

Le même ID de contenu fonctionne sur toutes les plateformes TV :

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Pareil
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Pareil
```

Chaque driver traduit l'ID dans le format de deep link natif de la plateforme :

| TV | Comment le deep link est envoyé |
|----|--------------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Tu n'as jamais à y penser. Le driver s'en charge.

</details>

<details>
<summary><strong>Plateformes</strong> — TV et drivers supportés</summary>

| Plateforme | Driver | Connexion | Statut |
|------------|--------|----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Testé** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Tests communautaires |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Tests communautaires |
| Roku | HTTP ECP | REST :8060 | Tests communautaires |

LG est la plateforme principale testée. Aucune d'elles ne nécessite de mode développeur.

</details>

## Configuration zéro

```bash
stv setup
```

Détecte automatiquement ta TV sur le réseau, identifie la plateforme, fait le jumelage, et écrit tout dans `~/.config/smartest-tv/config.toml`. Si quelque chose cloche, `stv doctor` te dit exactement ce qui ne va pas.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optionnel, pour Wake-on-LAN
```

Lors de la première connexion, la TV affiche une invite de jumelage. Accepte une fois — la clé est sauvegardée et on ne te le redemandera plus jamais.

## Serveur MCP

Pour Claude Desktop, Cursor, ou d'autres clients MCP — optionnel, le CLI reste l'interface principale :

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

## Architecture

```
Toi (langage naturel)
  → IA + Skills (trouve l'ID du contenu via yt-dlp / Playwright / recherche web)
    → stv CLI (formate et envoie)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contribuer

| Statut | Domaine | Ce qu'il faut |
|--------|---------|--------------|
| **Prêt** | Driver LG webOS | Testé et fonctionnel |
| **À tester** | Drivers Samsung, Android TV, Roku | Retours sur matériel réel bienvenus |
| **Recherché** | Skill Disney+ | Résolution d'ID de deep link |
| **Recherché** | Skills Hulu, Prime Video | Résolution d'ID de deep link |

L'[interface driver](src/smartest_tv/drivers/base.py) est définie — implémente `TVDriver` pour ta plateforme et ouvre une PR.

## Licence

MIT
