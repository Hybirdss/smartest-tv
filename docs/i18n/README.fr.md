# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | **Français**

**Parlez à votre TV. Elle écoute.**

Un CLI et des skills d'agent pour contrôler les smart TV en langage naturel. Deep links vers Netflix, YouTube, Spotify — dites ce que vous voulez regarder et ça se lance. Pas de mode développeur. Pas de clé API. Un `stv setup` et c'est parti.

> « Joue Frieren saison 2 épisode 8 »
>
> *Netflix s'ouvre. L'épisode commence.*

Compatible **LG** (testé), **Samsung**, **Android TV / Fire TV** et **Roku** (tests communautaires).

## Installation

```bash
pip install stv
```

C'est tout. Pour LG, rien d'autre n'est nécessaire.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # Tout
```

## Configuration zéro

À faire une seule fois :

```bash
stv setup
```

Détecte automatiquement la TV sur le réseau, identifie la plateforme (LG ? Samsung ? Roku ?), effectue le jumelage — sans mode développeur, sans chercher l'adresse IP — et écrit tout dans `~/.config/smartest-tv/config.toml`. Ensuite, chaque commande `stv` fonctionne sans rien toucher.

Quelque chose cloche ? `stv doctor` vous dit exactement ce qui ne va pas.

## CLI

```bash
stv status                          # Ce qui tourne, volume, sourdine
stv launch netflix 82656797         # Deep link vers un contenu précis
stv launch youtube dQw4w9WgXcQ     # Lire une vidéo YouTube
stv launch spotify spotify:album:x  # Lancer Spotify
stv volume 25                       # Régler le volume
stv mute                            # Activer/désactiver la sourdine
stv apps --format json              # Lister les apps installées
stv notify "À table !"              # Notification à l'écran
stv off                             # Bonne nuit
```

Toutes les commandes acceptent `--format json` — sortie structurée pour les scripts et les agents IA.

## Skills d'agent

stv est livré avec cinq skills qui apprennent aux assistants IA à piloter votre TV intelligemment. Tout installer en une commande dans Claude Code :

```bash
cd smartest-tv && ./install-skills.sh
```

Parlez ensuite à Claude comme vous le feriez à un ami :

```
Vous : Mets Frieren saison 2 épisode 8 sur Netflix
Vous : Mets Cocomelon pour les enfants
Vous : Le nouvel album de Ye sur Spotify
Vous : Éteins l'écran et mets du jazz
Vous : Bonne nuit
```

Les skills s'occupent de la partie fastidieuse — trouver l'ID de l'épisode sur Netflix, chercher sur YouTube via yt-dlp, résoudre les URI Spotify — puis appellent `stv` pour contrôler la TV.

### Liste des skills

| Skill | Rôle |
|-------|------|
| `tv-shared` | Référence CLI, authentification, configuration, patterns courants |
| `tv-netflix` | Récupération d'ID d'épisodes via Playwright |
| `tv-youtube` | Recherche de vidéos via yt-dlp |
| `tv-spotify` | Résolution d'URI d'albums, pistes et playlists |
| `tv-workflow` | Actions combinées : soirée ciné, mode enfants, minuteur sommeil |

## Ce que les deep links changent vraiment

Les autres outils *ouvrent* Netflix. stv *lance l'épisode 36 de Frieren*. C'est là toute la différence.

Le même identifiant de contenu fonctionne sur toutes les plateformes TV :

```bash
stv launch netflix 82656797                          # LG, Samsung, Roku — pareil
stv launch youtube dQw4w9WgXcQ                       # Pareil
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # Pareil
```

Chaque driver traduit l'identifiant de contenu dans le format de deep link natif de la plateforme :

| TV | Comment le deep link est envoyé |
|----|-------------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Vous n'avez jamais à y penser. Le driver s'en charge.

## Plateformes

| Plateforme | Driver | Connexion | Statut |
|------------|--------|----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Testé** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Tests communautaires |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Tests communautaires |
| Roku | HTTP ECP | REST :8060 | Tests communautaires |

LG est la plateforme principale testée. Samsung, Android TV et Roku devraient fonctionner — aucune ne nécessite de mode développeur — les retours de la communauté sont les bienvenus.

## Configuration

La configuration est dans `~/.config/smartest-tv/config.toml`. Après `stv setup`, ça ressemble à ceci :

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # optionnel, pour Wake-on-LAN
```

Lors de la première connexion, la TV affiche une invite de jumelage. Acceptez une fois — la clé est sauvegardée, on ne vous le demandera plus.

## En pratique

**2h du matin.** Dans votre lit, vous dites à Claude : « Lance Frieren où j'en étais. » La TV du salon s'allume, Netflix s'ouvre, l'épisode commence. Télécommande jamais touchée. Les yeux à moitié fermés.

**Samedi matin.** « Mets Cocomelon pour le bébé. » Trouvé sur YouTube, lancé sur la TV. Vous continuez le petit-déjeuner.

**Des amis arrivent.** « Mode jeu, HDMI 2, baisse le son. » Trois changements en une phrase, avant que personne ne s'en aperçoive.

**En cuisinant.** « Éteins l'écran et mets du jazz. » L'écran s'éteint, la musique commence. Sans parcourir aucun menu.

**Avant de dormir.** « Éteins dans 45 minutes. » La TV s'éteint toute seule. Pas vous.

## Serveur MCP

Pour Claude Desktop, Cursor ou d'autres clients MCP — optionnel, le CLI reste l'interface principale :

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

18 outils disponibles : `tv_on`, `tv_off`, `tv_launch`, `tv_close`, `tv_volume`, `tv_set_volume`, `tv_mute`, `tv_play`, `tv_pause`, `tv_stop`, `tv_status`, `tv_info`, `tv_notify`, `tv_apps`, `tv_volume_up`, `tv_volume_down`, `tv_screen_on`, `tv_screen_off`.

La configuration est lue automatiquement dans `~/.config/smartest-tv/config.toml` — aucune variable d'environnement requise.

## Architecture

```
Vous (langage naturel)
  → IA + Skills (trouve l'ID du contenu via yt-dlp / Playwright / recherche web)
    → stv CLI (formate et envoie)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contribuer

Les **drivers** pour Samsung, Android TV et Roku sont la contribution la plus impactante. L'[interface driver](src/smartest_tv/drivers/base.py) est définie — implémentez `TVDriver` pour votre plateforme et ouvrez une PR.

Les **skills** pour de nouveaux services de streaming (Disney+, Hulu, Prime Video) sont également les bienvenus.

## Licence

MIT
