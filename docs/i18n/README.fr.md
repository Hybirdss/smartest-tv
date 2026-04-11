<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">La CLI que ta TV attendait.</h4>

<p align="center">
  <b>Lance Netflix par son nom. Caste des URLs. Audio multi-pièces. Concierge IA. Tout depuis le terminal.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="../../tests/"><img src="https://img.shields.io/badge/tests-270%2B%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
  <a href="https://glama.ai/mcp/servers/Hybirdss/smartest-tv"><img src="https://img.shields.io/badge/Glama-A%20A%20A-00d992?style=flat-square" alt="Glama Score"></a>
  <a href="https://github.com/punkpeye/awesome-mcp-servers"><img src="https://img.shields.io/badge/awesome--mcp--servers-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome MCP Servers"></a>
  <a href="https://github.com/vitalets/awesome-smart-tv"><img src="https://img.shields.io/badge/awesome--smart--tv-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome Smart TV"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square" alt="HACS"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.pt-br.md">Português</a> · <b>Français</b>
</p>

<br>

<p align="center"><code>pip install stv && stv play "Frieren"</code></p>

<p align="center"><sub>Pas de TV ? Ouvre dans le navigateur. TV disponible ? <code>stv setup</code> pour le connecter.</sub></p>

<p align="center">
  <img src="../assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 Sans stv</th>
<th>😎 Avec stv</th>
</tr>
<tr>
<td>

1. Prendre la télécommande
2. Ouvrir l'app Netflix
3. Chercher la série
4. Choisir la saison
5. Choisir l'épisode
6. Appuyer sur play

**~30 secondes**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
```

**~3 secondes**

</td>
</tr>
</table>

<br>

---

## ✨ Ce que ça fait

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Lance par son nom
```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
Dis le nom. stv trouve l'ID, ouvre l'app, lance la lecture.

</td>
<td width="33%" valign="top">

### 🔗 Caste n'importe quelle URL
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
Un ami t'envoie un lien. Tu le colles. La TV le joue.

</td>
<td width="33%" valign="top">

### 🎵 File d'attente et soirée
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
Tout le monde ajoute son choix. La TV joue dans l'ordre.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 Scènes prédéfinies
```bash
stv scene movie-night   # volume 20, cinéma
stv scene kids          # volume 15, Cocomelon
stv scene sleep         # pluie, extinction auto
```
Une commande crée l'ambiance.

</td>
<td width="33%" valign="top">

### 🔊 Audio multi-pièces
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
Écrans éteints. Musique partout.<br>**Sonos gratuit.**

</td>
<td width="33%" valign="top">

### 📺 La TV comme écran d'affichage
```bash
stv display message "À table !"
stv display clock
stv display dashboard "Temp:22°C"
```
Tableaux de bord, horloges, affichage.<br>**0€/mois.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 Intelligence de visionnage
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
Ton Netflix vaut-il 18$/mois ?

</td>
<td width="33%" valign="top">

### 🌐 Soirée synchronisée
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # bonne nuit
```
Toutes les TV. En même temps. Même les amis à distance.

</td>
<td width="33%" valign="top">

### 🤖 Concierge IA
```
"Lance quelque chose de calme"
→ tv_recommend → tv_play
→ Lecture de The Queen's Gambit
```
21 outils MCP. Une phrase suffit.

</td>
</tr>
</table>

---

## 🤖 Laisse ton IA contrôler ta TV

stv est un **serveur MCP**. Claude, GPT, Cursor ou n'importe quel client MCP peut contrôler ta TV en langage naturel.

<table>
<tr>
<td width="50%" valign="top">

**Configuration (une ligne) :**

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

Ou via [OpenClaw](../../docs/integrations/openclaw.md) :
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**Puis parle simplement :**

```
Toi : "Je viens de rentrer, prépare la soirée ciné"

Claude : 🎬 Soirée ciné activée.
  Volume → 20, mode cinéma activé.
  
  D'après ton historique :
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

Toi : "Lance le 1, mets une horloge sur la TV cuisine"

Claude : ✓ Lecture de The Queen's Gambit
         ✓ Horloge sur la TV cuisine
```

</td>
</tr>
</table>

<details>
<summary><b>Les 21 outils MCP</b></summary>
<br>

| Catégorie | Outil | Ce qu'il fait |
|----------|------|-------------|
| **Lire** | `tv_play` | Cherche + lance par nom |
| | `tv_cast` | Caste n'importe quelle URL |
| | `tv_next` | Continue de regarder |
| | `tv_launch` | Lance une app par ID |
| | `tv_resolve` | Récupère seulement l'ID du contenu |
| **Découvrir** | `tv_whats_on` | Contenus tendance |
| | `tv_recommend` | Recommandations personnalisées |
| **Contrôler** | `tv_power` | Allumer/éteindre |
| | `tv_volume` | Obtenir/définir/ajuster/couper |
| | `tv_screen` | Écran allumé/éteint |
| | `tv_notify` | Notification toast |
| | `tv_status` | État actuel |
| **Organiser** | `tv_queue` | File de lecture |
| | `tv_scene` | Scènes prédéfinies |
| | `tv_history` | Historique de visionnage |
| **Intelligence** | `tv_insights` | Statistiques de visionnage |
| | `tv_display` | TV comme écran d'affichage |
| | `tv_audio` | Audio multi-pièces |
| **Multi-TV** | `tv_sync` | Jouer sur toutes les TV |
| | `tv_list_tvs` | Lister les TV |
| | `tv_groups` | Groupes de TV |

</details>

---

## 📅 Une journée avec stv

| Heure | Ce qui se passe |
|------|-------------|
| **7h** | `stv display dashboard "Météo:18°C" "Réunion:10h"` sur la TV cuisine |
| **8h** | `stv scene kids --tv kids-room` — Cocomelon, volume 15 |
| **12h** | Un ami envoie un lien Netflix → `stv cast <url>` |
| **17h** | `stv screen-time` → les enfants ont regardé 2h15 aujourd'hui |
| **18h30** | `stv scene movie-night` — volume 20, mode cinéma |
| **19h** | `stv recommend --mood chill` → suggère Ozark |
| **21h** | `stv audio play "friday vibes" -p spotify` — musique partout |
| **22h** | `stv --group party play netflix "Wednesday" s1e1` — synchronisé |
| **23h30** | `stv scene sleep` → `stv --all off` — bonne nuit |

---

## 🔥 Combos imbattables

<table>
<tr>
<td width="33%" valign="top">

**🌙 Pilote automatique du coucher**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
Son ambiant, écran éteint, minuterie auto, toutes les autres TV éteintes.

</td>
<td width="33%" valign="top">

**🎧 Sonos gratuit**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
Chaque TV est une enceinte. Volume par pièce. Écrans éteints.

</td>
<td width="33%" valign="top">

**💰 Audit des abonnements**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/h — envisager de résilier

stv sub-value youtube --cost 13.99
# → $1.20/h — bon rapport qualité-prix
```

</td>
</tr>
</table>

> [**10 recettes supplémentaires →**](../../docs/guides/recipes.md)

---

## ⚙️ Comment ça marche

```
  "Lance Dark S1E1"
        │
        ▼
  ┌─── Résolution ───┐
  │ Cache → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 La TV le joue
  └───────────────────┘       │
                         Deep link via
                    LG / Samsung / Roku / Android
```

Dis un nom. stv le résout en ID de contenu et fait un deep-link dans l'app sur ta TV. Pas d'automatisation de navigateur, pas de clés API, pas de dépendance cloud. Les résultats sont mis en cache, donc les lectures répétées sont instantanées.

---

## 📦 Installation

```bash
pip install stv                    # LG webOS (défaut)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # Tout
```

```bash
stv setup                          # découverte auto + jumelage de ta TV
```

> Compatible avec **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 Compatible avec

| Intégration | Comment |
|------------|-----|
| **Claude Code / Cursor** | Ajoute la config MCP → `"lance Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → bot Telegram |
| **Home Assistant** | Commandes shell dans les automatisations |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Scripts shell** | One-liners `sleep-mode`, `party-mode` |
| **N'importe quel client MCP** | 21 outils, stdio ou HTTP (`stv serve`) |

---

## 📚 Documentation

| | |
|---|---|
| [Premiers pas](../../docs/getting-started/installation.md) | Configuration pour n'importe quelle marque de TV |
| [Lire du contenu](../../docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Scènes](../../docs/guides/scenes.md) | movie-night, kids, sleep, personnalisées |
| [Sync & Soirée](../../docs/guides/sync-party.md) | Multi-TV, soirée de visionnage à distance |
| [Recettes](../../docs/guides/recipes.md) | **10 combos de fonctionnalités puissants** |
| [Agents IA](../../docs/guides/ai-agents.md) | MCP pour Claude, Cursor, OpenClaw |
| [Référence CLI](../../docs/reference/cli.md) | Toutes les commandes et options |
| [Outils MCP](../../docs/reference/mcp-tools.md) | Les 21 outils avec paramètres |

---

## 🤝 Contribuer

211 tests. Pas besoin de TV pour les exécuter.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Les drivers Samsung, Roku et Android TV ont besoin de tests en conditions réelles. Si tu en as un, [ton retour compte](https://github.com/Hybirdss/smartest-tv/issues).

[Contributions au cache](../../docs/contributing/cache-contributions.md) · [Développement de drivers](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Fait avec Python · Aucun cloud requis</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
