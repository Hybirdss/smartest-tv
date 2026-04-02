# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | **Português** | [Français](README.fr.md)

**Fale com a sua TV. Ela entende.**

CLI e skills para agentes de IA que controlam sua smart TV em linguagem natural. Deep links para Netflix, YouTube e Spotify — fala o que quer assistir e começa a tocar. Sem modo desenvolvedor. Sem API keys. Um `stv setup` e pronto.

> "Coloca o episódio 8 da segunda temporada de Frieren"
>
> *A Netflix abre e o episódio começa a reproduzir.*

Compatível com **LG** (testado), **Samsung**, **Android TV / Fire TV** e **Roku** (testes da comunidade).

## Instalação

```bash
pip install stv
```

Só isso. Pra LG não precisa de mais nada.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # Tudo
```

## Configuração zero

Roda isso uma vez e esquece:

```bash
stv setup
```

Descobre a TV na rede automaticamente, identifica a plataforma (LG? Samsung? Roku?), faz o pareamento sozinho — sem modo desenvolvedor, sem precisar caçar o IP da TV — e salva tudo em `~/.config/smartest-tv/config.toml`. Depois disso, todo comando `stv` funciona de primeira.

Se der algum problema, `stv doctor` te fala exatamente o que tá errado.

## CLI

```bash
stv status                          # O que tá tocando, volume, mudo
stv launch netflix 82656797         # Deep link pra conteúdo específico
stv launch youtube dQw4w9WgXcQ     # Tocar um vídeo do YouTube
stv launch spotify spotify:album:x  # Tocar no Spotify
stv volume 25                       # Definir volume
stv mute                            # Alternar mudo
stv apps --format json              # Listar apps instalados
stv notify "Comida tá pronta!"      # Notificação na tela da TV
stv off                             # Desligar a TV
```

Todos os comandos suportam `--format json` — saída estruturada para scripts e agentes de IA.

## Skills para agentes de IA

O stv vem com cinco skills que ensinam assistentes de IA a controlar sua TV de forma inteligente. Instala tudo no Claude Code de uma vez:

```bash
cd smartest-tv && ./install-skills.sh
```

Depois é só falar com o Claude normalmente:

```
Você: Coloca o episódio 8 da 2ª temporada de Frieren na Netflix
Você: Bota Cocomelon pra criança
Você: Coloca o novo álbum do Ye no Spotify
Você: Desliga a tela e coloca jazz
Você: Boa noite
```

Os skills cuidam da parte chata — buscar o ID do episódio na Netflix, pesquisar no YouTube com yt-dlp, resolver URIs do Spotify — e chamam o CLI `stv` pra controlar a TV.

### Lista de skills

| Skill | O que faz |
|-------|-----------|
| `tv-shared` | Referência do CLI, autenticação, configuração, padrões comuns |
| `tv-netflix` | Busca de IDs de episódios com Playwright |
| `tv-youtube` | Busca de vídeos com yt-dlp |
| `tv-spotify` | Resolução de URIs de álbuns, músicas e playlists |
| `tv-workflow` | Ações combinadas: modo cinema, modo criança, timer pra dormir |

## Por que os deep links mudam tudo

Outras ferramentas só *abrem* a Netflix. O stv *reproduz o episódio 36 de Frieren*. É essa a diferença.

O mesmo ID de conteúdo funciona em todas as plataformas de TV:

```bash
stv launch netflix 82656797                          # Funciona igual na LG, Samsung ou Roku
stv launch youtube dQw4w9WgXcQ                       # Igual
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # Igual
```

Cada plataforma tem seu formato de deep link, mas o driver traduz tudo por baixo dos panos. Você não precisa pensar nisso.

## Plataformas

| Plataforma | Driver | Conexão | Status |
|------------|--------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Testado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Testes da comunidade |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Testes da comunidade |
| Roku | HTTP ECP | REST :8060 | Testes da comunidade |

LG é a plataforma principal testada. Samsung, Android TV e Roku devem funcionar — nenhuma precisa de modo desenvolvedor — feedback da comunidade é bem-vindo.

## Configuração

A configuração fica em `~/.config/smartest-tv/config.toml`. Depois do `stv setup`, é assim:

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # opcional, pra Wake-on-LAN
```

Na primeira conexão a TV mostra um aviso de pareamento. Aceita uma vez, a chave fica salva e nunca mais pergunta.

## Casos de uso reais

**2 da manhã.** Deitado na cama, você fala pro Claude: "Continua o Frieren." A TV da sala liga, a Netflix abre e o episódio começa. Sem precisar procurar o controle. Com os olhos meio fechados.

**Sábado de manhã.** "Bota Cocomelon pro bebê." Acha no YouTube e toca na TV. Você continua fazendo o café da manhã. O café ainda tá quente.

**Quando os amigos chegam.** "Modo game, HDMI 2, baixa o volume." Três mudanças em uma frase, antes de alguém notar.

**Cozinhando.** "Desliga a tela e coloca jazz." A tela apaga, a música começa. Sem navegar em menu nenhum.

**Antes de dormir.** "Desliga em 45 minutos." A TV se desliga sozinha. Você não.

## Servidor MCP

Para Claude Desktop, Cursor ou outros clientes MCP — isso é opcional, o CLI é a interface principal:

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

18 ferramentas disponíveis. A configuração é lida automaticamente de `~/.config/smartest-tv/config.toml`. Sem variáveis de ambiente.

## Arquitetura

```
Você (linguagem natural)
  → IA + Skills (encontra o ID do conteúdo via yt-dlp / Playwright / busca)
    → stv CLI (formata e envia)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

## Contribuindo

**Drivers** para Samsung, Android TV e Roku são a contribuição de maior impacto. A [interface do driver](src/smartest_tv/drivers/base.py) já está definida — implementa `TVDriver` pra sua plataforma e abre um PR.

**Skills** para novos serviços de streaming (Disney+, Hulu, Prime Video) também são bem-vindas.

## Licença

MIT
