# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | **Español** | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**Habla con tu tele. Te escucha.**

| Sin stv | Con stv |
|:-------:|:-------:|
| Abre la app de Netflix en el móvil | `stv play netflix "Dark" s1e1` |
| Busca la serie | (resuelto automáticamente) |
| Elige la temporada | (calculado) |
| Elige el episodio | (deep-linked) |
| Pulsa play | |
| **~30 segundos** | **~3 segundos** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Haz clic para ver el vídeo completo con sonido*

## Inicio rápido

```bash
pip install stv
stv setup          # encuentra tu tele, empareja, listo
```

## Lo que la gente hace con stv

### "Pon este enlace en mi tele"

Un amigo te manda un enlace de YouTube. Lo pegas. La tele lo pone.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "Pon canciones en cola para la fiesta"

Todos añaden su canción. La tele las pone en orden.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # empieza a reproducir en orden
stv queue skip                     # siguiente canción
```

### "¿Qué vemos?"

Para de buscar en Netflix 30 minutos. Pregunta qué está en tendencia. Consigue una recomendación.

```bash
stv whats-on netflix               # top 10 en tendencia ahora mismo
stv recommend --mood chill         # según tu historial
stv recommend --mood action        # diferente estado, diferentes sugerencias
```

### "Noche de película"

Un comando pone el ambiente: volumen, notificaciones, contenido.

```bash
stv scene movie-night              # volumen 20, modo cine
stv scene kids                     # volumen 15, pone Cocomelon
stv scene sleep                    # sonidos ambientales, apagado automático
stv scene create date-night        # crea el tuyo
```

### Reproduce en todas partes

Sincroniza todas las teles a la vez o crea grupos para fiestas.

```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wednesday" s1e1
stv --all off
```

### "Pon donde lo dejé"

```bash
stv next                           # continúa desde tu último episodio
stv next "Breaking Bad"            # serie específica
stv history                        # mira qué has estado viendo
```

## Un día con stv

**7:00am** -- suena el despertador. "¿Qué hay en tendencia?" `stv whats-on youtube` muestra las noticias de la mañana. La tele las pone.

**8:00am** -- se despiertan los niños. `stv scene kids` -- volumen 15, empieza Cocomelon.

**12:00pm** -- un amigo te manda un enlace de Netflix. `stv cast https://netflix.com/watch/...` -- la tele lo pone.

**6:30pm** -- llegas del trabajo. `stv scene movie-night` -- volumen bajo, modo cine.

**7:00pm** -- "¿qué vemos?" `stv recommend --mood chill` -- sugiere The Queen's Gambit.

**9:00pm** -- llegan los amigos. `stv --group party play netflix "Wednesday" s1e1` -- todas las teles sincronizan al instante.

**11:30pm** -- "buenas noches." `stv scene sleep` -- sonidos ambientales, la tele se apaga en 45 minutos.

<details>
<summary><b>¿Cómo encuentra stv un episodio de Netflix con una sola petición HTTP?</b></summary>

Netflix renderiza en el servidor los metadatos `__typename:"Episode"` en etiquetas `<script>`. Los IDs de episodio dentro de una temporada son enteros consecutivos. Una sola petición `curl` a la página del título extrae cada ID de episodio de cada temporada. Sin Playwright, sin navegador headless, sin API key, sin login.

Los resultados se cachean en tres niveles:
1. **Caché local** -- `~/.config/smartest-tv/cache.json`, instantáneo (~0,1 s)
2. **Caché comunitario** -- IDs en colaboración vía GitHub raw CDN (más de 40 entradas precargadas), sin coste de servidor
3. **Búsqueda web de respaldo** -- Brave Search descubre automáticamente IDs de títulos desconocidos

</details>

<details>
<summary><b>Deep linking -- cómo habla stv con tu tele</b></summary>

Cada driver traduce un ID de contenido al formato nativo de la plataforma:

| TV | Protocolo | Formato del deep link |
|----|----------|----------------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

Nunca tienes que pensar en esto. El driver se encarga.

</details>

<details>
<summary><b>Plataformas compatibles</b></summary>

| Plataforma | Driver | Estado |
|------------|--------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **Probado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Pruebas de la comunidad |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Pruebas de la comunidad |
| Roku | HTTP ECP | Pruebas de la comunidad |

</details>

## Instalación

```bash
pip install stv                 # LG (por defecto)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Todo
```

## Funciona con todo

| Integración | Qué ocurre |
|------------|------------|
| **Claude Code** | "Pon Breaking Bad s1e1" -- la tele lo pone |
| **OpenClaw** | Telegram: "Estoy en casa" -- scene + recommend + play |
| **Home Assistant** | Se abre la puerta -- se enciende la tele -- aparecen series en tendencia |
| **Cursor / Codex** | La IA escribe código, controla tu tele en el descanso |
| **cron / scripts** | 7am: noticias en la tele del dormitorio. 9pm: tele de los niños apagada |
| **Cualquier cliente MCP** | 18 herramientas por stdio o HTTP |

### Servidor MCP

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

O ejecútalo como servidor HTTP para acceso remoto:

```bash
stv serve --port 8910              # SSE en http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## Documentación

| | |
|---|---|
| [Primeros pasos](docs/getting-started/installation.md) | Configuración inicial para cualquier marca de TV |
| [Reproducir contenido](docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Escenas](docs/guides/scenes.md) | Presets: movie-night, kids, sleep, custom |
| [Multi-TV](docs/guides/multi-tv.md) | Controla varias teles con `--tv` |
| [Agentes IA](docs/guides/ai-agents.md) | Configuración MCP para Claude, Cursor, OpenClaw |
| [Recomendaciones](docs/guides/recommendations.md) | Sugerencias de contenido con IA |
| [Referencia CLI](docs/reference/cli.md) | Todos los comandos y opciones |
| [Herramientas MCP](docs/reference/mcp-tools.md) | Las 18 herramientas MCP con parámetros |
| [OpenClaw](docs/integrations/openclaw.md) | ClawHub skill + escenarios de Telegram |
| [Sync Party](docs/guides/sync-party.md) | Reproducción sincronizada en varias teles y grupos remotos |

## Contribuir

Los drivers de Samsung, Roku y Android TV necesitan pruebas reales. Si tienes una de estas teles, tu opinión es muy valiosa.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 169 tests, no hace falta tele
```

¿Quieres añadir tus series favoritas al caché comunitario? Mira [Contribuir al caché](docs/contributing/cache-contributions.md).

¿Quieres escribir un driver para una nueva tele? Mira [Desarrollo de drivers](docs/contributing/driver-development.md).

## Licencia

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
