# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | **Español** | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**Habla con tu tele. Te escucha.**

CLI y skills para agentes de IA que controlan tu smart TV en lenguaje natural. Deep links para Netflix, YouTube y Spotify — di lo que quieres ver y empieza a reproducirse. Sin modo desarrollador. Sin API keys. Un `stv setup` y listo.

> "Pon el episodio 8 de la temporada 2 de Frieren"
>
> *Netflix se abre y el episodio empieza solo.*

Compatible con **LG** (probado), **Samsung**, **Android TV / Fire TV** y **Roku** (pruebas de la comunidad).

## Instalación

```bash
pip install stv
```

Eso es todo. Para LG no necesitas nada más.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # Todo
```

## Configuración cero

Ejecuta esto una sola vez:

```bash
stv setup
```

Detecta la tele en la red automáticamente, identifica la plataforma (¿LG? ¿Samsung? ¿Roku?), hace el emparejamiento solo — sin modo desarrollador, sin buscar la IP a mano — y guarda todo en `~/.config/smartest-tv/config.toml`. A partir de ahí, cada comando `stv` funciona sin más.

¿Algo no va bien? `stv doctor` te dice exactamente qué está pasando.

## CLI

```bash
stv status                          # Qué está sonando, volumen, silencio
stv launch netflix 82656797         # Deep link a contenido específico
stv launch youtube dQw4w9WgXcQ     # Reproduce un vídeo de YouTube
stv launch spotify spotify:album:x  # Reproduce en Spotify
stv volume 25                       # Ajustar volumen
stv mute                            # Activar/desactivar silencio
stv apps --format json              # Lista de apps instaladas
stv notify "¡A comer!"              # Notificación en pantalla
stv off                             # Apagar la tele
```

Todos los comandos admiten `--format json` — salida estructurada para scripts y agentes de IA.

## Skills para agentes de IA

stv incluye cinco skills que enseñan a los asistentes de IA a controlar tu tele de forma inteligente. Instálalos en Claude Code de una vez:

```bash
cd smartest-tv && ./install-skills.sh
```

Y ya puedes hablar con Claude con total naturalidad:

```
Tú: Pon el episodio 8 de la temporada 2 de Frieren en Netflix
Tú: Pon Cocomelon para el niño
Tú: Pon el nuevo álbum de Ye en Spotify
Tú: Apaga la pantalla y pon jazz
Tú: Buenas noches
```

Los skills se encargan de lo complicado — buscar el ID del episodio en Netflix, buscar en YouTube con yt-dlp, interpretar URIs de Spotify — y llaman al CLI `stv` para controlar la televisión.

### Lista de skills

| Skill | Qué hace |
|-------|----------|
| `tv-shared` | Referencia CLI, autenticación, configuración, patrones comunes |
| `tv-netflix` | Búsqueda de IDs de episodios con Playwright |
| `tv-youtube` | Búsqueda de vídeos con yt-dlp |
| `tv-spotify` | Resolución de URIs de álbumes, canciones y playlists |
| `tv-workflow` | Acciones combinadas: modo cine, modo niños, temporizador |

## Por qué los deep links cambian todo

Otras herramientas solo *abren* Netflix. stv *reproduce el episodio 36 de Frieren*. Esa es la diferencia real.

El mismo ID de contenido funciona en todas las plataformas de TV:

```bash
stv launch netflix 82656797                          # Igual en LG, Samsung o Roku
stv launch youtube dQw4w9WgXcQ                       # Igual
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # Igual
```

Cada plataforma tiene su propio formato de deep link, pero el driver lo traduce por ti. Tú no tienes que pensar en eso.

## Plataformas

| Plataforma | Driver | Conexión | Estado |
|------------|--------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Probado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Pruebas de la comunidad |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Pruebas de la comunidad |
| Roku | HTTP ECP | REST :8060 | Pruebas de la comunidad |

LG es la plataforma principal probada. Samsung, Android TV y Roku deberían funcionar — ninguna requiere modo desarrollador — y se agradecen las experiencias reales de la comunidad.

## Configuración

La configuración se guarda en `~/.config/smartest-tv/config.toml`. Después de `stv setup`, tiene esta pinta:

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # opcional, para Wake-on-LAN
```

En la primera conexión la tele muestra un aviso de emparejamiento. Lo aceptas una vez y la clave se guarda para siempre.

## Casos de uso reales

**Las 2 de la mañana.** En la cama, le dices a Claude: "Sigue con Frieren donde lo dejé." El televisor del salón se enciende, Netflix se abre y el episodio empieza. Sin buscar el mando. Con los ojos medio cerrados.

**Sábado por la mañana.** "Pon Cocomelon para el bebé." Lo encuentra en YouTube y lo pone en la tele. Tú sigues con el desayuno.

**Cuando vienen amigos.** "Modo juego, HDMI 2, baja el volumen." Tres cambios en una frase, antes de que nadie note nada.

**Cocinando.** "Apaga la pantalla y pon jazz." La pantalla se apaga, la música suena. Sin navegar por menús ni buscar la app.

**Antes de dormir.** "Apaga en 45 minutos." La tele se apaga sola. Tú, no.

## Servidor MCP

Para Claude Desktop, Cursor u otros clientes MCP — esto es opcional, el CLI es la interfaz principal:

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

18 herramientas disponibles. La configuración se lee automáticamente de `~/.config/smartest-tv/config.toml`. Sin variables de entorno.

## Arquitectura

```
Tú (lenguaje natural)
  → IA + Skills (busca el ID del contenido con yt-dlp / Playwright / búsqueda web)
    → stv CLI (formatea y envía)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contribuir

Los **drivers** de Samsung, Android TV y Roku son la contribución de mayor impacto. La [interfaz del driver](src/smartest_tv/drivers/base.py) ya está definida — implementa `TVDriver` para tu plataforma y abre una PR.

Los **skills** para nuevos servicios de streaming (Disney+, Hulu, Prime Video) también son bienvenidos.

## Licencia

MIT
