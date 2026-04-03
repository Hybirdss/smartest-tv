# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | **Français**

**Parle à ta TV. Elle écoute.**

| Sans stv | Avec stv |
|:--------:|:--------:|
| Ouvrir l'app Netflix sur le téléphone | `stv play netflix "Dark" s1e1` |
| Chercher la série | (résolu automatiquement) |
| Choisir la saison | (calculé) |
| Choisir l'épisode | (deep-linked) |
| Appuyer sur play | |
| **~30 secondes** | **~3 secondes** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Clique pour la vidéo complète avec le son*

## Démarrage rapide

```bash
pip install stv
stv setup          # trouve ta TV, fait le jumelage, c'est tout
```

## Ce que les gens font avec stv

### "Lance ce lien sur ma TV"

Un ami t'envoie un lien YouTube. Tu le colles. La TV le joue.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "Ajoute des chansons à la file pour la fête"

Tout le monde ajoute son choix. La TV les joue dans l'ordre.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # commence à jouer dans l'ordre
stv queue skip                     # chanson suivante
```

### "Qu'est-ce qu'on regarde ?"

Arrête de scroller sur Netflix pendant 30 minutes. Demande ce qui est en tendance. Obtiens une recommandation.

```bash
stv whats-on netflix               # top 10 des tendances en ce moment
stv recommend --mood chill         # basé sur ton historique
stv recommend --mood action        # humeur différente, suggestions différentes
```

### "Soirée ciné"

Une commande crée l'ambiance : volume, notifications, contenu.

```bash
stv scene movie-night              # volume 20, mode cinéma
stv scene kids                     # volume 15, lance Cocomelon
stv scene sleep                    # sons ambiants, extinction automatique
stv scene create date-night        # crée le tien
```

### "Lance-le sur la TV de la chambre"

Contrôle chaque TV de la maison depuis une seule CLI.

```bash
stv multi list                     # salon (LG), chambre (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### "Continue là où j'en étais"

```bash
stv next                           # reprend depuis ton dernier épisode
stv next "Breaking Bad"            # série spécifique
stv history                        # voir ce que tu as regardé
```

## Une journée avec stv

**7h00** -- le réveil sonne. "Qu'est-ce qui est en tendance ?" `stv whats-on youtube` affiche les informations du matin. La TV les joue.

**8h00** -- les enfants se réveillent. `stv scene kids` -- volume 15, Cocomelon démarre.

**12h00** -- un ami t'envoie un lien Netflix. `stv cast https://netflix.com/watch/...` -- la TV le joue.

**18h30** -- retour du travail. `stv scene movie-night` -- volume en baisse, mode cinéma.

**19h00** -- "qu'est-ce qu'on regarde ?" `stv recommend --mood chill` -- suggère The Queen's Gambit.

**21h00** -- des amis arrivent. Tout le monde lance `stv queue add ...` -- la TV les joue dans l'ordre.

**23h30** -- "bonne nuit." `stv scene sleep` -- sons ambiants, la TV s'éteint dans 45 minutes.

<details>
<summary><b>Comment stv trouve un épisode Netflix avec une seule requête HTTP ?</b></summary>

Netflix rend côté serveur les métadonnées `__typename:"Episode"` dans des balises `<script>`. Les IDs d'épisode au sein d'une saison sont des entiers consécutifs. Une seule requête `curl` vers une page de titre extrait chaque ID d'épisode de chaque saison. Pas de Playwright, pas de navigateur headless, pas de clé API, pas de connexion.

Les résultats sont mis en cache en trois niveaux :
1. **Cache local** -- `~/.config/smartest-tv/cache.json`, instantané (~0,1 s)
2. **Cache communautaire** -- IDs collaboratifs via GitHub raw CDN (plus de 40 entrées pré-chargées), sans coût serveur
3. **Recherche web de secours** -- Brave Search découvre automatiquement les IDs de titres inconnus

</details>

<details>
<summary><b>Deep linking -- comment stv parle à ta TV</b></summary>

Chaque driver traduit un ID de contenu dans le format natif de la plateforme :

| TV | Protocole | Format du deep link |
|----|----------|---------------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

Tu n'as jamais à y penser. Le driver s'en charge.

</details>

<details>
<summary><b>Plateformes supportées</b></summary>

| Plateforme | Driver | Statut |
|------------|--------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **Testé** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Tests communautaires |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Tests communautaires |
| Roku | HTTP ECP | Tests communautaires |

</details>

## Installation

```bash
pip install stv                 # LG (défaut)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Tout
```

## Compatible avec tout

| Intégration | Ce qui se passe |
|------------|----------------|
| **Claude Code** | "Lance Breaking Bad s1e1" -- la TV le joue |
| **OpenClaw** | Telegram : "Je suis à la maison" -- scene + recommend + play |
| **Home Assistant** | La porte s'ouvre -- la TV s'allume -- les tendances apparaissent |
| **Cursor / Codex** | L'IA écrit du code, contrôle ta TV pendant la pause |
| **cron / scripts** | 7h : actualités sur la TV de la chambre. 21h : TV des enfants éteinte |
| **N'importe quel client MCP** | 32 outils via stdio ou HTTP |

### Serveur MCP

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

Ou lance-le comme serveur HTTP pour un accès distant :

```bash
stv serve --port 8910              # SSE sur http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## Documentation

| | |
|---|---|
| [Premiers pas](docs/getting-started/installation.md) | Configuration initiale pour n'importe quelle marque de TV |
| [Lire du contenu](docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Scenes](docs/guides/scenes.md) | Présets : movie-night, kids, sleep, custom |
| [Multi-TV](docs/guides/multi-tv.md) | Contrôle plusieurs TV avec `--tv` |
| [Agents IA](docs/guides/ai-agents.md) | Configuration MCP pour Claude, Cursor, OpenClaw |
| [Recommandations](docs/guides/recommendations.md) | Suggestions de contenu par IA |
| [Référence CLI](docs/reference/cli.md) | Toutes les commandes et options |
| [Outils MCP](docs/reference/mcp-tools.md) | Les 32 outils MCP avec paramètres |
| [OpenClaw](docs/integrations/openclaw.md) | ClawHub skill + scénarios Telegram |

## Contribuer

Les drivers Samsung, Roku et Android TV ont besoin de tests en conditions réelles. Si tu as une de ces TV, ton retour est précieux.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 tests, aucune TV nécessaire
```

Tu veux ajouter tes séries préférées au cache communautaire ? Voir [Contribuer au cache](docs/contributing/cache-contributions.md).

Tu veux écrire un driver pour une nouvelle TV ? Voir [Développement de drivers](docs/contributing/driver-development.md).

## Licence

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
