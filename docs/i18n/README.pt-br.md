# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | **Português** | [Français](README.fr.md)

**Fala com a sua TV. Ela obedece.**

| Sem stv | Com stv |
|:-------:|:-------:|
| Abrir o app da Netflix no celular | `stv play netflix "Dark" s1e1` |
| Buscar a série | (resolvido automaticamente) |
| Escolher a temporada | (calculado) |
| Escolher o episódio | (deep-linked) |
| Apertar play | |
| **~30 segundos** | **~3 segundos** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Clique para o vídeo completo com som*

## Início rápido

```bash
pip install stv
stv setup          # encontra sua TV, faz o pareamento, pronto
```

## O que as pessoas fazem com stv

### "Manda esse link pra minha TV"

Um amigo manda um link do YouTube. Você cola. A TV toca.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "Enfileira músicas pra festa"

Todo mundo adiciona a sua. A TV toca na ordem.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # começa a tocar na ordem
stv queue skip                     # próxima música
```

### "O que a gente assiste?"

Para de rolar na Netflix por 30 minutos. Pergunta o que está em alta. Recebe uma recomendação.

```bash
stv whats-on netflix               # top 10 em alta agora
stv recommend --mood chill         # baseado no seu histórico
stv recommend --mood action        # outra vibe, outras sugestões
```

### "Noite de cinema"

Um comando cria o clima: volume, notificações, conteúdo.

```bash
stv scene movie-night              # volume 20, modo cinema
stv scene kids                     # volume 15, toca Cocomelon
stv scene sleep                    # sons ambiente, desligamento automático
stv scene create date-night        # cria o seu
```

### "Toca na TV do quarto"

Controla cada TV da casa de uma CLI só.

```bash
stv multi list                     # sala (LG), quarto (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### "Continua de onde eu parei"

```bash
stv next                           # continua do seu último episódio
stv next "Breaking Bad"            # série específica
stv history                        # veja o que você assistiu
```

## Um dia com stv

**7h00** -- o alarme toca. "O que está em alta?" `stv whats-on youtube` mostra as notícias da manhã. A TV toca.

**8h00** -- as crianças acordam. `stv scene kids` -- volume 15, Cocomelon começa.

**12h00** -- um amigo manda um link da Netflix. `stv cast https://netflix.com/watch/...` -- a TV toca.

**18h30** -- chegou do trabalho. `stv scene movie-night` -- volume baixo, modo cinema.

**19h00** -- "o que a gente assiste?" `stv recommend --mood chill` -- sugere The Queen's Gambit.

**21h00** -- os amigos chegam. Todo mundo roda `stv queue add ...` -- a TV toca na ordem.

**23h30** -- "boa noite." `stv scene sleep` -- sons ambiente, a TV desliga em 45 minutos.

<details>
<summary><b>Como o stv encontra um episódio da Netflix com uma única requisição HTTP?</b></summary>

A Netflix renderiza no servidor os metadados `__typename:"Episode"` em tags `<script>`. Os IDs de episódio dentro de uma temporada são inteiros consecutivos. Uma única requisição `curl` para a página do título extrai cada ID de episódio de cada temporada. Sem Playwright, sem navegador headless, sem chave de API, sem login.

Os resultados são cacheados em três níveis:
1. **Cache local** -- `~/.config/smartest-tv/cache.json`, instantâneo (~0,1 s)
2. **Cache comunitário** -- IDs colaborativos via GitHub raw CDN (mais de 40 entradas pré-carregadas), sem custo de servidor
3. **Busca web como fallback** -- Brave Search descobre automaticamente IDs de títulos desconhecidos

</details>

<details>
<summary><b>Deep linking -- como o stv fala com a sua TV</b></summary>

Cada driver traduz um ID de conteúdo para o formato nativo da plataforma:

| TV | Protocolo | Formato do deep link |
|----|----------|---------------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

Você não precisa pensar em nada disso. O driver cuida de tudo.

</details>

<details>
<summary><b>Plataformas suportadas</b></summary>

| Plataforma | Driver | Status |
|------------|--------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **Testado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | Testes da comunidade |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | Testes da comunidade |
| Roku | HTTP ECP | Testes da comunidade |

</details>

## Instalação

```bash
pip install stv                 # LG (padrão)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Tudo
```

## Funciona com tudo

| Integração | O que acontece |
|------------|---------------|
| **Claude Code** | "Toca Breaking Bad s1e1" -- a TV toca |
| **OpenClaw** | Telegram: "Cheguei em casa" -- scene + recommend + play |
| **Home Assistant** | Porta abre -- TV liga -- séries em alta aparecem |
| **Cursor / Codex** | IA escreve código, controla sua TV no intervalo |
| **cron / scripts** | 7h: notícias na TV do quarto. 21h: TV das crianças desliga |
| **Qualquer cliente MCP** | 32 ferramentas via stdio ou HTTP |

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

Ou rode como servidor HTTP para acesso remoto:

```bash
stv serve --port 8910              # SSE em http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## Documentação

| | |
|---|---|
| [Primeiros passos](docs/getting-started/installation.md) | Configuração inicial para qualquer marca de TV |
| [Reproduzir conteúdo](docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Scenes](docs/guides/scenes.md) | Presets: movie-night, kids, sleep, custom |
| [Multi-TV](docs/guides/multi-tv.md) | Controla várias TVs com `--tv` |
| [Agentes IA](docs/guides/ai-agents.md) | Configuração MCP para Claude, Cursor, OpenClaw |
| [Recomendações](docs/guides/recommendations.md) | Sugestões de conteúdo por IA |
| [Referência CLI](docs/reference/cli.md) | Todos os comandos e opções |
| [Ferramentas MCP](docs/reference/mcp-tools.md) | As 32 ferramentas MCP com parâmetros |
| [OpenClaw](docs/integrations/openclaw.md) | ClawHub skill + cenários do Telegram |

## Contribuindo

Os drivers de Samsung, Roku e Android TV precisam de testes no mundo real. Se você tem uma dessas TVs, seu feedback é muito valioso.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 testes, sem necessidade de TV
```

Quer adicionar suas séries favoritas ao cache comunitário? Veja [Contribuindo com o cache](docs/contributing/cache-contributions.md).

Quer escrever um driver para uma nova TV? Veja [Desenvolvimento de drivers](docs/contributing/driver-development.md).

## Licença

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
