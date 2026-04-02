# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | **Español** | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

Habla con tu tele. Te escucha.

CLI y skill para agentes de IA que controla tu smart TV en lenguaje natural. Deep links para Netflix, YouTube y Spotify — di lo que quieres ver y empieza a reproducirse.

> "Pon el episodio 8 de la temporada 2 de Frieren"
>
> *Netflix se abre y el episodio empieza a reproducirse.*

Compatible con **LG**, **Samsung**, **Android TV**, **Fire TV** y **Roku**.

## Instalación

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # Todo
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # Estado actual (app, volumen, silencio)
tv launch netflix 82656797         # Reproducir contenido específico en Netflix
tv launch youtube dQw4w9WgXcQ     # Reproducir vídeo de YouTube
tv launch spotify spotify:album:x # Reproducir en Spotify
tv volume 25                       # Ajustar volumen
tv mute                            # Activar/desactivar silencio
tv apps --format json              # Lista de apps instaladas
tv notify "¡A comer!"              # Mostrar notificación en pantalla
tv off                             # Apagar la tele
```

Todos los comandos admiten `--format json` — salida estructurada para agentes de IA.

## Skill para agentes de IA

Instala el skill en Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

Luego habla con Claude en lenguaje natural:

```
Tú: Pon el episodio 8 de la temporada 2 de Frieren en Netflix
Tú: Pon YouTube para el niño
Tú: Pon el nuevo álbum de Ye en Spotify
Tú: Apaga la pantalla y pon jazz
Tú: Buenas noches
```

El skill se encarga de lo complicado — buscar el ID del episodio en Netflix, buscar en YouTube con yt-dlp, interpretar URIs de Spotify — y llama al CLI `tv` para controlar la televisión.

## Deep links

Aquí está la diferencia clave de smartest-tv. Otras herramientas solo *abren* Netflix. Nosotros *reproducimos el episodio 36 de Frieren*.

El mismo ID de contenido funciona en todas las plataformas de TV:

```bash
tv launch netflix 82656797       # Igual en LG, Samsung o Roku
tv launch youtube dQw4w9WgXcQ    # Igual
tv launch spotify spotify:album:x  # Igual
```

## Casos de uso reales

**Las 2 de la mañana.** Desde la cama le dices a Claude: "Sigue con Frieren." El televisor del salón se enciende, Netflix se abre y el episodio empieza. Sin buscar el mando.

**Sábado por la mañana.** "Pon Cocomelon para el bebé." Lo encuentra en YouTube y lo reproduce en la tele. Tú sigues preparando el desayuno.

**Cuando vienen amigos.** "Modo juego, HDMI 2, baja el volumen." Tres cambios en una sola frase.

## Licencia

MIT
