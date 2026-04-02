# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | **Português** | [Français](README.fr.md)

**Fala com a sua TV. Ela obedece.**

Outras ferramentas abrem a Netflix. O smartest-tv reproduz *Frieren temporada 2 episódio 8*.

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## Início rápido

```bash
pip install stv
stv setup          # descobre sua TV automaticamente, faz o pareamento, pronto
```

Só isso. Sem modo desenvolvedor. Sem API keys. Sem variáveis de ambiente. Fala o que quer assistir.

## O que dá pra fazer?

```
Você: Play Frieren season 2 episode 8 on Netflix
Você: Put on Baby Shark for the kids
Você: Ye's new album on Spotify
Você: Screen off, play my jazz playlist
Você: Good night
```

A IA encontra o ID do conteúdo (episódio da Netflix, vídeo do YouTube, URI do Spotify), chama o `stv`, e sua TV começa a reproduzir.

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## Instalação

```bash
pip install stv                 # LG (padrão, já vem tudo)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # Tudo junto
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # Buscar + reproduzir em um passo
stv play youtube "baby shark"                          # Buscar + reproduzir
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # Só pegar o ID
stv launch netflix 82656797         # Deep link direto (se já souber o ID)
stv status                          # O que tá tocando, volume, estado de mudo
stv volume 25                       # Ajustar volume
stv mute                            # Alternar mudo
stv apps --format json              # Listar apps (saída estruturada)
stv notify "Comida tá pronta!"      # Notificação toast na tela
stv off                             # Boa noite
```

Todo comando suporta `--format json` — feito para scripts e agentes de IA.

### Resolução de conteúdo

`stv resolve` encontra os IDs de streaming pra você. `stv play` faz a mesma coisa e já lança na TV em um passo só.

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ (via yt-dlp)
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → passa direto
```

A resolução do Netflix funciona fazendo scraping dos metadados do episódio na página do título com uma única requisição `curl` — sem Playwright, sem navegador, sem login. Todas as temporadas são resolvidas de uma vez e cacheadas localmente. A segunda consulta é instantânea (~0,1 s).

### Cache

Quando um ID é encontrado, fica cacheado para sempre em `~/.config/smartest-tv/cache.json`. Você também pode popular o cache manualmente:

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # Mostrar todos os IDs cacheados
```

## Agent Skills

O smartest-tv vem com cinco skills que ensinam assistentes de IA a controlar sua TV. Instala tudo no Claude Code:

```bash
cd smartest-tv && ./install-skills.sh
```

| Skill | O que faz |
|-------|-----------|
| `tv-shared` | Referência do CLI, autenticação, configuração, padrões comuns |
| `tv-netflix` | Busca de IDs de episódios via scraping HTTP |
| `tv-youtube` | Busca de vídeos via yt-dlp, resolução de formato |
| `tv-spotify` | Resolução de URIs de álbuns, músicas e playlists |
| `tv-workflow` | Ações compostas: noite de cinema, modo criança, timer pra dormir |

Skills são arquivos Markdown simples. Dá pra portar pra qualquer agente em minutos.

## Compatível com

Qualquer agente de IA que consiga rodar comandos shell:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · ou simplesmente `bash`

## Na prática

**2 da manhã.** Deitado na cama, você fala pro Claude: "Continua de onde eu parei em Frieren." A TV da sala liga, a Netflix abre, o episódio começa. Você não tocou no controle. Mal abriu os olhos.

**Sábado de manhã.** "Bota Cocomelon pro bebê." O YouTube acha, a TV toca. Você continua fazendo o café da manhã.

**Galera chegou.** "Modo game, HDMI 2, baixa o volume." Uma frase, três mudanças, feito antes de alguém notar.

**Cozinhando o jantar.** "Desliga a tela e coloca minha playlist de jazz." A tela apaga, a música começa a tocar pelos alto-falantes.

**Caindo no sono.** "Timer de 45 minutos." A TV se desliga sozinha. Você não.

## O que o smartest-tv é

- **Resolvedor de deep links** — encontra o ID do episódio na Netflix, o vídeo no YouTube, a URI do Spotify
- **Controle universal** — uma CLI pra 4 plataformas de TV
- **AI-native** — projetado pra agentes chamarem, não só pra humanos

## O que ele não é

- Não é um app de controle remoto (sem navegar por canais, sem teclas de direção)
- Não é um controlador HDMI-CEC
- Não é uma ferramenta de espelhamento de tela

<details>
<summary><strong>Deep Linking</strong> — como funciona de verdade</summary>

O mesmo ID de conteúdo funciona em todas as plataformas de TV:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # Igual
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # Igual
```

Cada driver traduz o ID pro formato de deep link nativo da plataforma:

| TV | Como envia o deep link |
|----|------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

Você não precisa pensar em nada disso. O driver cuida de tudo.

</details>

<details>
<summary><strong>Plataformas</strong> — TVs e drivers suportados</summary>

| Plataforma | Driver | Conexão | Status |
|------------|--------|---------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **Testado** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | Testes da comunidade |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | Testes da comunidade |
| Roku | HTTP ECP | REST :8060 | Testes da comunidade |

LG é a plataforma principal testada. Nenhuma delas precisa de modo desenvolvedor.

</details>

## Configuração zero

```bash
stv setup
```

Descobre sua TV na rede automaticamente, detecta a plataforma, faz o pareamento sozinho e salva tudo em `~/.config/smartest-tv/config.toml`. Se alguma coisa parecer estranha, `stv doctor` te fala exatamente o que tá acontecendo.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # opcional, para Wake-on-LAN
```

Na primeira conexão, a TV mostra um aviso de pareamento. Aceita uma vez — a chave fica salva e nunca mais pergunta.

## Servidor MCP

Para Claude Desktop, Cursor ou outros clientes MCP — opcional, o CLI é a interface principal:

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

## Arquitetura

```
Você (linguagem natural)
  → IA + stv resolve (encontra o ID do conteúdo via scraping HTTP / yt-dlp / cache)
    → stv play (formata o deep link e despacha)
      → Driver (WebSocket / ADB / HTTP)
        → TV
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## Contribuindo

| Status | Área | O que precisa |
|--------|------|---------------|
| **Pronto** | Driver LG webOS | Testado e funcionando |
| **Precisa de testes** | Drivers Samsung, Android TV, Roku | Relatos com hardware real são bem-vindos |
| **Procurado** | Skill Disney+ | Resolução de ID de deep link |
| **Procurado** | Skills Hulu, Prime Video | Resolução de ID de deep link |

A [interface do driver](src/smartest_tv/drivers/base.py) já está definida — implementa `TVDriver` pra sua plataforma e abre um PR.

## Licença

MIT
