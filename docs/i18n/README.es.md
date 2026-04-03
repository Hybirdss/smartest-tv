<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">La CLI que tu tele estaba esperando.</h4>

<p align="center">
  <b>Pon Netflix por nombre. Castea URLs. Audio en todas las habitaciones. Concierge IA. Todo desde tu terminal.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="../../tests/"><img src="https://img.shields.io/badge/tests-211%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a> · <b>Español</b> · <a href="README.de.md">Deutsch</a> · <a href="README.pt-br.md">Português</a> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>Corre en tu red local. Sin nube. Sin claves API. Sin suscripciones.</sub></p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 Sin stv</th>
<th>😎 Con stv</th>
</tr>
<tr>
<td>

1. Coger el mando
2. Abrir la app de Netflix
3. Buscar la serie
4. Elegir la temporada
5. Elegir el episodio
6. Dar play

**~30 segundos**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
```

**~3 segundos**

</td>
</tr>
</table>

<br>

---

## ✨ Qué hace

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Reproduce por nombre
```bash
stv play netflix "Dark" s1e1
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
Di el nombre. stv encuentra el ID, abre la app, empieza a reproducir.

</td>
<td width="33%" valign="top">

### 🔗 Castea cualquier URL
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
Un amigo te manda un enlace. Lo pegas. La tele lo pone.

</td>
<td width="33%" valign="top">

### 🎵 Cola y fiesta
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
Todos añaden su canción. La tele las pone en orden.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 Escenas preestablecidas
```bash
stv scene movie-night   # volumen 20, cine
stv scene kids          # volumen 15, Cocomelon
stv scene sleep         # lluvia, apagado automático
```
Un comando pone el ambiente.

</td>
<td width="33%" valign="top">

### 🔊 Audio en todas las habitaciones
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
Pantallas apagadas. Música en todas partes.<br>**Sonos gratis.**

</td>
<td width="33%" valign="top">

### 📺 La tele como pantalla
```bash
stv display message "¡A cenar!"
stv display clock
stv display dashboard "Temp:22°C"
```
Dashboards, relojes, señalética.<br>**$0/mes.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 Inteligencia de visionado
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
¿Vale tu Netflix $18 al mes?

</td>
<td width="33%" valign="top">

### 🌐 Fiesta sincronizada
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # buenas noches
```
Todas las teles. A la vez. Incluso amigos remotos.

</td>
<td width="33%" valign="top">

### 🤖 Concierge IA
```
"Pon algo tranquilo"
→ tv_recommend → tv_play
→ Poniendo The Queen's Gambit
```
21 herramientas MCP. Una frase es suficiente.

</td>
</tr>
</table>

---

## 🤖 Di a tu IA que controle tu tele

stv es un **servidor MCP**. Claude, GPT, Cursor o cualquier cliente MCP puede controlar tu tele con lenguaje natural.

<table>
<tr>
<td width="50%" valign="top">

**Configuración (una línea):**

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

O vía [OpenClaw](../../docs/integrations/openclaw.md):
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**Luego solo habla:**

```
Tú: "Acabo de llegar a casa, prepara la noche de película"

Claude: 🎬 Noche de película activada.
  Volumen → 20, modo cine activado.
  
  Según tu historial:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

Tú: "Pon el 1, y un reloj en la tele de la cocina"

Claude: ✓ Poniendo The Queen's Gambit
         ✓ Reloj en la tele de la cocina
```

</td>
</tr>
</table>

<details>
<summary><b>Las 21 herramientas MCP</b></summary>
<br>

| Categoría | Herramienta | Qué hace |
|----------|------|-------------|
| **Reproducir** | `tv_play` | Busca y reproduce por nombre |
| | `tv_cast` | Castea cualquier URL |
| | `tv_next` | Continúa viendo |
| | `tv_launch` | Lanza app por ID |
| | `tv_resolve` | Obtiene solo el ID del contenido |
| **Descubrir** | `tv_whats_on` | Contenido en tendencia |
| | `tv_recommend` | Recomendaciones personalizadas |
| **Controlar** | `tv_power` | Encender/apagar |
| | `tv_volume` | Obtener/establecer/ajustar/silenciar |
| | `tv_screen` | Pantalla encendida/apagada |
| | `tv_notify` | Notificación toast |
| | `tv_status` | Estado actual |
| **Organizar** | `tv_queue` | Cola de reproducción |
| | `tv_scene` | Escenas preestablecidas |
| | `tv_history` | Historial de visionado |
| **Inteligencia** | `tv_insights` | Estadísticas de visionado |
| | `tv_display` | La tele como pantalla |
| | `tv_audio` | Audio en todas las habitaciones |
| **Multi-tele** | `tv_sync` | Reproducir en todas las teles |
| | `tv_list_tvs` | Listar teles |
| | `tv_groups` | Grupos de teles |

</details>

---

## 📅 Un día con stv

| Hora | Qué pasa |
|------|-------------|
| **7am** | `stv display dashboard "Tiempo:18°C" "Reunión:10am"` en la tele de la cocina |
| **8am** | `stv scene kids --tv kids-room` — Cocomelon, volumen 15 |
| **12pm** | Un amigo manda un enlace de Netflix → `stv cast <url>` |
| **5pm** | `stv screen-time` → los niños han visto 2h 15m hoy |
| **6:30pm** | `stv scene movie-night` — volumen 20, modo cine |
| **7pm** | `stv recommend --mood chill` → sugiere Ozark |
| **9pm** | `stv audio play "friday vibes" -p spotify` — música en todas partes |
| **10pm** | `stv --group party play netflix "Wednesday" s1e1` — sincronizado |
| **11:30pm** | `stv scene sleep` → `stv --all off` — buenas noches |

---

## 🔥 Combos que matan

<table>
<tr>
<td width="33%" valign="top">

**🌙 Piloto automático al dormir**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
Sonido ambiente, pantalla apagada, temporizador, todas las teles apagadas.

</td>
<td width="33%" valign="top">

**🎧 Sonos gratis**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
Cada tele es un altavoz. Volumen por habitación. Pantallas apagadas.

</td>
<td width="33%" valign="top">

**💰 Auditoría de suscripciones**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — considera cancelar

stv sub-value youtube --cost 13.99
# → $1.20/hr — buen valor
```

</td>
</tr>
</table>

> [**10 recetas más →**](../../docs/guides/recipes.md)

---

## ⚙️ Cómo funciona

```
  "Pon Dark S1E1"
        │
        ▼
  ┌─── Resolución ───┐
  │ Caché → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 La tele lo pone
  └───────────────────┘       │
                         Deep link vía
                    LG / Samsung / Roku / Android
```

Di un nombre. stv lo resuelve a un ID de contenido y hace deep-link en la app de tu tele. Sin automatización de navegador, sin claves API, sin dependencia en la nube. Los resultados se cachean, así que las reproducciones repetidas son instantáneas.

---

## 📦 Instalación

```bash
pip install stv                    # LG webOS (por defecto)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # Todo
```

```bash
stv setup                          # autodescubre y empareja tu tele
```

> Compatible con **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 Compatible con

| Integración | Cómo |
|------------|-----|
| **Claude Code / Cursor** | Añade config MCP → `"pon Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → bot de Telegram |
| **Home Assistant** | Comandos shell en automatizaciones |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Scripts de shell** | One-liners de `sleep-mode`, `party-mode` |
| **Cualquier cliente MCP** | 21 herramientas, stdio o HTTP (`stv serve`) |

---

## 📚 Documentación

| | |
|---|---|
| [Primeros pasos](../../docs/getting-started/installation.md) | Configuración para cualquier marca de TV |
| [Reproducir contenido](../../docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Escenas](../../docs/guides/scenes.md) | movie-night, kids, sleep, personalizadas |
| [Sync y fiesta](../../docs/guides/sync-party.md) | Multi-tele, fiesta de visionado remoto |
| [Recetas](../../docs/guides/recipes.md) | **10 combos de funciones potentes** |
| [Agentes IA](../../docs/guides/ai-agents.md) | MCP para Claude, Cursor, OpenClaw |
| [Referencia CLI](../../docs/reference/cli.md) | Todos los comandos y opciones |
| [Herramientas MCP](../../docs/reference/mcp-tools.md) | Las 21 herramientas con parámetros |

---

## 🤝 Contribuir

211 tests. No hace falta tele para ejecutarlos.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Los drivers de Samsung, Roku y Android TV necesitan pruebas reales. Si tienes uno, [tu opinión importa](https://github.com/Hybirdss/smartest-tv/issues).

[Contribuir al caché](../../docs/contributing/cache-contributions.md) · [Desarrollo de drivers](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Hecho con Python · Sin nube requerida</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
