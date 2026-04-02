# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | **Français**

**Parle à ta TV. Elle écoute.**

Les autres outils ouvrent Netflix. smartest-tv lance *Frieren saison 2 épisode 8*.

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

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

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Installation

```bash
pip install stv                 # LG (défaut, batteries incluses)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Tout
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # Rechercher + lancer en une étape
stv play youtube "baby shark"                          # Rechercher + lancer
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # Juste récupérer l'ID
stv launch netflix 82656797         # Deep link direct (si tu connais déjà l'ID)
stv status                          # Ce qui tourne, volume, sourdine
stv volume 25                       # Régler le volume
stv mute                            # Activer/désactiver la sourdine
stv apps --format json              # Lister les apps (sortie structurée)
stv notify "Le dîner est prêt"      # Notification toast à l'écran
stv off                             # Bonne nuit
```

Chaque commande accepte `--format json` — conçu pour les scripts et les agents IA.

### Résolution de contenu

`stv resolve` trouve les IDs de streaming à ta place. `stv play` fait la même chose et lance directement sur la TV en une seule étape.

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → transmis tel quel
```

La résolution Netflix fonctionne en extrayant les métadonnées de l'épisode depuis la page du titre avec une seule requête `curl` — sans Playwright, sans navigateur, sans connexion. Toutes les saisons sont résolues en une fois et mises en cache localement. La deuxième recherche est instantanée (~0,1 s).

### Cache

Une fois un ID trouvé, il est mis en cache définitivement dans `~/.config/smartest-tv/cache.json`. Tu peux aussi alimenter le cache manuellement :

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # Afficher tous les IDs en cache
```

## Skills d'agent

smartest-tv est livré avec un skill qui apprend tout sur le contrôle de la TV aux assistants IA. Pour l'installer dans Claude Code :

```bash
cd smartest-tv && ./install-skills.sh
```

Le skill `tv` couvre toutes les plateformes (Netflix, YouTube, Spotify), toutes les commandes (`play`, `search`, `resolve`, `cache`, `volume`, `off`) et les workflows composites (soirée ciné, mode enfants, minuteur sommeil). Un seul fichier Markdown — portable vers n'importe quel agent IA en quelques minutes.

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

Scanne simultanément le réseau à la recherche de LG, Samsung, Roku et Android/Fire TV (SSDP + ADB). Détecte la plateforme, fait le jumelage, sauvegarde la config et envoie une notification de test — le tout en une seule commande. Si la TV n'est pas découverte automatiquement, indique l'IP directement :

```bash
stv setup --ip 192.168.1.100
```

Tout est sauvegardé dans `~/.config/smartest-tv/config.toml`. Si quelque chose cloche, `stv doctor` te dit exactement ce qui ne va pas.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optionnel, pour Wake-on-LAN
```

Lors de la première connexion, la TV affiche une invite de jumelage. Accepte une fois — la clé est sauvegardée et on ne te le redemandera plus jamais.

## Serveur MCP

### Local (stdio)

Pour Claude Desktop, Cursor, ou d'autres clients MCP — connexion en tant que processus local :

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

### Distant (HTTP)

Lance stv comme serveur MCP accessible par réseau. Idéal pour les agents IA tournant sur une autre machine :

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

Connexion depuis n'importe quel client MCP :

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
    }
  }
}
```

## Architecture

```
Toi (langage naturel)
  → IA + stv resolve (trouve l'ID du contenu via scraping HTTP / yt-dlp / cache)
    → stv play (formate le deep link et envoie)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## Contribuer

| Statut | Domaine | Ce qu'il faut |
|--------|---------|--------------|
| **Prêt** | Driver LG webOS | Testé et fonctionnel |
| **À tester** | Drivers Samsung, Android TV, Roku | Retours sur matériel réel bienvenus |
| **Recherché** | Skill Disney+ | Résolution d'ID de deep link |
| **Recherché** | Skills Hulu, Prime Video | Résolution d'ID de deep link |

L'[interface driver](src/smartest_tv/drivers/base.py) est définie — implémente `TVDriver` pour ta plateforme et ouvre une PR.

### Lancer les tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

55 tests unitaires couvrant le résolveur de contenu, le cache et le parser CLI. Aucune TV ni connexion réseau requises — tous les appels externes sont mockés.

## Licence

MIT
