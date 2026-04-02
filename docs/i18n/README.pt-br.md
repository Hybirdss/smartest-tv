# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | **Português** | [Français](README.fr.md)

Fale com a sua TV. Ela entende.

CLI e skill para agentes de IA que controla sua smart TV em linguagem natural. Deep links para Netflix, YouTube e Spotify — diga o que quer assistir e começa a tocar.

> "Coloca o episódio 8 da segunda temporada de Frieren"
>
> *A Netflix abre e o episódio começa a reproduzir.*

Compatível com **LG**, **Samsung**, **Android TV**, **Fire TV** e **Roku**.

## Instalação

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # Tudo
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # Estado atual (app, volume, mudo)
tv launch netflix 82656797         # Reproduzir conteúdo específico na Netflix
tv launch youtube dQw4w9WgXcQ     # Reproduzir vídeo do YouTube
tv launch spotify spotify:album:x # Reproduzir no Spotify
tv volume 25                       # Definir volume
tv mute                            # Alternar mudo
tv apps --format json              # Lista de apps instalados
tv notify "Comida tá pronta!"      # Exibir notificação na TV
tv off                             # Desligar a TV
```

Todos os comandos suportam `--format json` — saída estruturada para agentes de IA.

## Skill para agentes de IA

Instale o skill no Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

Depois, fale com o Claude em linguagem natural:

```
Você: Coloca o episódio 8 da 2ª temporada de Frieren na Netflix
Você: Bota YouTube pra criança
Você: Coloca o novo álbum do Ye no Spotify
Você: Desliga a tela e coloca jazz
Você: Boa noite
```

O skill cuida da parte difícil — buscar o ID do episódio na Netflix, pesquisar no YouTube com yt-dlp, resolver URIs do Spotify — e chama o CLI `tv` para controlar a televisão.

## Deep links

Essa é a principal diferença do smartest-tv. Outras ferramentas só *abrem* a Netflix. A gente *reproduz o episódio 36 de Frieren*.

O mesmo ID de conteúdo funciona em todas as plataformas de TV:

```bash
tv launch netflix 82656797       # Funciona igual na LG, Samsung ou Roku
tv launch youtube dQw4w9WgXcQ    # Igual
tv launch spotify spotify:album:x  # Igual
```

## Casos de uso reais

**2 da manhã.** Deitado na cama, você fala pro Claude: "Continua o Frieren." A TV da sala liga, a Netflix abre e o episódio começa. Sem precisar procurar o controle remoto.

**Sábado de manhã.** "Bota Cocomelon pro bebê." Acha no YouTube e toca na TV. Você continua preparando o café da manhã.

**Quando os amigos chegam.** "Modo game, HDMI 2, baixa o volume." Três mudanças em uma frase.

## Licença

MIT
