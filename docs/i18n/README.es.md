# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | **Español** | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**Habla con tu tele. Te escucha.**

Otras herramientas abren Netflix. smartest-tv pone *la temporada 2 episodio 8 de Frieren*.

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## Inicio rápido

```bash
pip install stv
stv setup          # detecta tu tele automáticamente, empareja, listo
```

Eso es todo. Sin modo desarrollador. Sin API keys. Sin variables de entorno. Di lo que quieres ver.

## ¿Qué puedes hacer?

```
Tú: Pon la temporada 2 episodio 8 de Frieren en Netflix
Tú: Pon Baby Shark para los chicos
Tú: El nuevo álbum de Ye en Spotify
Tú: Apaga la pantalla y pon mi playlist de jazz
Tú: Buenas noches
```

La IA encuentra el ID del contenido (episodio de Netflix, video de YouTube, URI de Spotify), llama a `stv`, y tu tele lo pone.

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Instalación

```bash
pip install stv                 # LG (por defecto, todo incluido)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Todo
```

## CLI

```bash
# Reproducir contenido por nombre — stv encuentra el ID automáticamente
stv play netflix "Frieren" s2e8            # Resolver + deep link en un paso
stv play youtube "baby shark"              # Buscar + reproducir
stv play spotify "Ye White Lines"          # Buscar en Spotify + reproducir

# Buscar sin reproducir
stv search netflix "Stranger Things"       # Muestra todas las temporadas + episodios
stv search youtube "lofi hip hop"          # Top 3 resultados
stv resolve netflix "Frieren" s2e8         # Solo obtener el ID del episodio

# Continuar viendo
stv next                                   # Reproducir el siguiente episodio del historial
stv next "Frieren"                         # Siguiente episodio de una serie específica
stv history                                # Reproducciones recientes con marca de tiempo

# Control del TV
stv status                                 # Qué está sonando, volumen, silencio
stv volume 25                              # Ajustar volumen
stv mute                                   # Activar/desactivar silencio
stv notify "La cena está lista"           # Notificación en pantalla
stv off                                    # Buenas noches

# Deep link directo (si ya conoces el ID)
stv launch netflix 82656797
```

Todos los comandos admiten `--format json` — diseñado para scripts y agentes de IA.

### Cómo funciona la resolución de contenido

`stv play` y `stv resolve` encuentran los IDs de streaming para que no tengas que hacerlo tú:

```bash
stv resolve netflix "Frieren" s2e8         # → 82656797
stv resolve youtube "lofi hip hop"         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify "Ye White Lines"       # → spotify:track:3bbjDFVu...
```

La resolución de Netflix es una única petición `curl` a la página del título. Netflix renderiza en el servidor los metadatos `__typename:"Episode"` en etiquetas `<script>`. Los IDs de episodio dentro de una temporada son enteros consecutivos, así que una sola petición HTTP resuelve cada temporada de una serie. Sin Playwright, sin navegador, sin login.

Los resultados se cachean en tres niveles:
1. **Caché local** — `~/.config/smartest-tv/cache.json`, instantáneo (~0,1 s)
2. **Caché comunitario** — IDs en colaboración vía GitHub raw CDN (29 series de Netflix, 11 vídeos de YouTube precargados), sin coste de servidor
3. **Búsqueda web de respaldo** — Brave Search descubre automáticamente IDs de títulos desconocidos

### Caché

```bash
stv cache show                                # Ver todos los IDs cacheados
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8     # → 82656797
stv cache contribute                          # Exportar para PR del caché comunitario
```

## Skills para agentes

smartest-tv incluye un skill que enseña a los asistentes de IA todo lo necesario para controlar tu tele. Instálalo en Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

El skill `tv` cubre todas las plataformas (Netflix, YouTube, Spotify), todos los comandos (`play`, `search`, `resolve`, `cache`, `volume`, `off`) y flujos de trabajo compuestos (noche de cine, modo niños, temporizador). Es un único archivo Markdown — portable a cualquier agente IA en minutos.

## Funciona con

Cualquier agente de IA que pueda ejecutar comandos de shell:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · o simplemente `bash`

## En el mundo real

**Son las 2 de la mañana.** Estás en la cama y le dices a Claude: "Sigue Frieren donde lo dejé." El televisor del salón se enciende, Netflix se abre, el episodio empieza. Nunca tocaste el control. Apenas abriste los ojos.

**Sábado en la mañana.** "Pon Cocomelon para el bebé." YouTube lo encuentra, la tele lo pone. Tú sigues haciendo el desayuno.

**Llegaron los amigos.** "Modo juego, HDMI 2, baja el volumen." Una frase, tres cambios, antes de que alguien lo note.

**Cocinando.** "Apaga la pantalla y pon mi playlist de jazz." La pantalla se apaga, la música fluye por los parlantes.

**Cayéndote de sueño.** "Temporizador de 45 minutos." La tele se apaga sola. Tú, no.

## Qué es smartest-tv

- **Resolvedor de deep links** — encuentra el ID del episodio en Netflix, el video en YouTube, la URI en Spotify
- **Control universal** — un solo CLI para 4 plataformas de TV
- **Hecho para agentes** — diseñado para que lo llamen los agentes, no solo los humanos

## Qué no es

- No es una app de control remoto (sin zapping de canales, sin teclas de dirección)
- No es un controlador HDMI-CEC
- No es una herramienta de screen mirroring

<details>
<summary><strong>Deep Linking</strong> — cómo funciona por dentro</summary>

El mismo ID de contenido funciona en todas las plataformas de TV:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Igual
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Igual
```

Cada driver traduce el ID al formato de deep link nativo de la plataforma:

| TV | Cómo envía el deep link |
|----|------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Nunca tienes que pensar en esto. El driver se encarga.

</details>

<details>
<summary><strong>Plataformas</strong> — TVs y drivers compatibles</summary>

| Plataforma | Driver | Conexión | Estado |
|------------|--------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Probado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Pruebas de la comunidad |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Pruebas de la comunidad |
| Roku | HTTP ECP | REST :8060 | Pruebas de la comunidad |

LG es la plataforma principal probada. Ninguna requiere modo desarrollador.

</details>

## Configuración sin complicaciones

```bash
stv setup
```

Escanea la red buscando LG, Samsung, Roku y Android/Fire TV simultáneamente (SSDP + ADB). Detecta la plataforma, empareja, guarda la configuración y envía una notificación de prueba — todo en un solo comando. Si el TV no se descubre automáticamente, indica la IP directamente:

```bash
stv setup --ip 192.168.1.100
```

Todo queda en `~/.config/smartest-tv/config.toml`. Si algo no cuadra, `stv doctor` te dice exactamente qué está pasando.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # opcional, para Wake-on-LAN
```

En la primera conexión la tele muestra un aviso de emparejamiento. Lo aceptas una vez y la clave se guarda para siempre.

## Servidor MCP

### Local (stdio)

Para Claude Desktop, Cursor u otros clientes MCP — conecta como proceso local:

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

### Remoto (HTTP)

Ejecuta stv como servidor MCP accesible por red. Útil para agentes de IA que corren en otra máquina:

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

Conecta desde cualquier cliente MCP:

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
    }
  }
}
```

## Arquitectura

```
Tú (lenguaje natural)
  → IA + stv resolve (busca el ID del contenido via scraping HTTP / yt-dlp / caché)
    → stv play (formatea el deep link y lo envía)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## Documentación

| Guía | Contenido |
|------|-----------|
| [Guía de configuración](docs/setup-guide.md) | Configuración específica por marca (emparejamiento LG, acceso remoto Samsung, ADB, Roku ECP) |
| [Integración MCP](docs/mcp-integration.md) | Configuración de Claude Code, Cursor y otros clientes MCP |
| [Referencia de API](docs/api-reference.md) | Todos los comandos CLI + las 20 herramientas MCP con parámetros |
| [Contribuir al caché](docs/contributing-cache.md) | Cómo encontrar IDs de Netflix y enviar una PR al caché comunitario |

## Contribuir

| Estado | Área | Qué se necesita |
|--------|------|-----------------|
| **Listo** | Driver LG webOS | Probado y funcionando |
| **Necesita pruebas** | Drivers Samsung, Android TV, Roku | Se agradecen reportes con hardware real |
| **Se busca** | Disney+, Hulu, Prime Video | Resolución de IDs de deep link |
| **Se busca** | Entradas del caché comunitario | [Añade tus series favoritas](docs/contributing-cache.md) |

La [interfaz del driver](src/smartest_tv/drivers/base.py) ya está definida — implementa `TVDriver` para tu plataforma y abre una PR.

### Ejecutar los tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

55 tests unitarios que cubren el resolvedor de contenido, la caché y el parser de CLI. No se necesita TV ni conexión de red — todas las llamadas externas están mockeadas.

## Licencia

MIT
