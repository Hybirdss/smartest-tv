<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">A CLI que a sua TV estava esperando.</h4>

<p align="center">
  <b>Toca Netflix pelo nome. Casteia URLs. Áudio em vários cômodos. Concierge com IA. Tudo do terminal.</b>
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
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <b>Português</b> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>Roda na sua rede local. Sem nuvem. Sem chaves de API. Sem assinaturas.</sub></p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 Sem stv</th>
<th>😎 Com stv</th>
</tr>
<tr>
<td>

1. Pegar o controle
2. Abrir o app da Netflix
3. Buscar a série
4. Escolher a temporada
5. Escolher o episódio
6. Apertar play

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

## ✨ O que faz

<table>
<tr>
<td width="33%" valign="top">

### 🎬 Toca pelo nome
```bash
stv play netflix "Dark" s1e1
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
Fala o nome. stv acha o ID, abre o app, começa a tocar.

</td>
<td width="33%" valign="top">

### 🔗 Casteia qualquer URL
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
Amigo manda um link. Cola. A TV toca.

</td>
<td width="33%" valign="top">

### 🎵 Fila e festa
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
Todo mundo adiciona sua música. A TV toca na ordem.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 Cenas pré-configuradas
```bash
stv scene movie-night   # volume 20, cinema
stv scene kids          # volume 15, Cocomelon
stv scene sleep         # chuva, desligamento automático
```
Um comando cria o clima.

</td>
<td width="33%" valign="top">

### 🔊 Áudio em vários cômodos
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
Telas desligadas. Música em todo lugar.<br>**Sonos de graça.**

</td>
<td width="33%" valign="top">

### 📺 TV como display
```bash
stv display message "Jantar pronto!"
stv display clock
stv display dashboard "Temp:22°C"
```
Dashboards, relógios, painéis.<br>**R$0/mês.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 Inteligência de visualização
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
Sua Netflix vale $18 por mês?

</td>
<td width="33%" valign="top">

### 🌐 Festa sincronizada
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # boa noite
```
Todas as TVs. Ao mesmo tempo. Até amigos remotos.

</td>
<td width="33%" valign="top">

### 🤖 Concierge com IA
```
"Toca algo relaxante"
→ tv_recommend → tv_play
→ Tocando The Queen's Gambit
```
21 ferramentas MCP. Uma frase é suficiente.

</td>
</tr>
</table>

---

## 🤖 Manda sua IA controlar sua TV

stv é um **servidor MCP**. Claude, GPT, Cursor ou qualquer cliente MCP pode controlar sua TV com linguagem natural.

<table>
<tr>
<td width="50%" valign="top">

**Configuração (uma linha):**

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

Ou via [OpenClaw](../../docs/integrations/openclaw.md):
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**Depois é só falar:**

```
Você: "Cheguei em casa, prepara a noite de cinema"

Claude: 🎬 Noite de cinema ativada.
  Volume → 20, modo cinema ligado.
  
  Com base no seu histórico:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

Você: "Toca o 1, e coloca um relógio na TV da cozinha"

Claude: ✓ Tocando The Queen's Gambit
         ✓ Relógio na TV da cozinha
```

</td>
</tr>
</table>

<details>
<summary><b>Todas as 21 ferramentas MCP</b></summary>
<br>

| Categoria | Ferramenta | O que faz |
|----------|------|-------------|
| **Tocar** | `tv_play` | Busca + toca pelo nome |
| | `tv_cast` | Casteia qualquer URL |
| | `tv_next` | Continua assistindo |
| | `tv_launch` | Abre app por ID |
| | `tv_resolve` | Só pega o ID do conteúdo |
| **Descobrir** | `tv_whats_on` | Conteúdo em alta |
| | `tv_recommend` | Recomendações personalizadas |
| **Controlar** | `tv_power` | Liga/desliga |
| | `tv_volume` | Pega/define/ajusta/muda |
| | `tv_screen` | Tela liga/desliga |
| | `tv_notify` | Notificação toast |
| | `tv_status` | Estado atual |
| **Organizar** | `tv_queue` | Fila de reprodução |
| | `tv_scene` | Cenas pré-configuradas |
| | `tv_history` | Histórico de visualização |
| **Inteligência** | `tv_insights` | Estatísticas de visualização |
| | `tv_display` | TV como display |
| | `tv_audio` | Áudio em vários cômodos |
| **Multi-TV** | `tv_sync` | Toca em todas as TVs |
| | `tv_list_tvs` | Lista TVs |
| | `tv_groups` | Grupos de TVs |

</details>

---

## 📅 Um dia com stv

| Hora | O que acontece |
|------|-------------|
| **7h** | `stv display dashboard "Clima:18°C" "Reunião:10h"` na TV da cozinha |
| **8h** | `stv scene kids --tv kids-room` — Cocomelon, volume 15 |
| **12h** | Amigo manda link da Netflix → `stv cast <url>` |
| **17h** | `stv screen-time` → crianças assistiram 2h 15m hoje |
| **18h30** | `stv scene movie-night` — volume 20, modo cinema |
| **19h** | `stv recommend --mood chill` → sugere Ozark |
| **21h** | `stv audio play "friday vibes" -p spotify` — música em todo lugar |
| **22h** | `stv --group party play netflix "Wednesday" s1e1` — sincronizado |
| **23h30** | `stv scene sleep` → `stv --all off` — boa noite |

---

## 🔥 Combos matadores

<table>
<tr>
<td width="33%" valign="top">

**🌙 Piloto automático na hora de dormir**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
Som ambiente, tela desligada, timer automático, todas as outras TVs desligadas.

</td>
<td width="33%" valign="top">

**🎧 Sonos de graça**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
Cada TV é uma caixa de som. Volume por cômodo. Telas desligadas.

</td>
<td width="33%" valign="top">

**💰 Auditoria de assinaturas**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — considere cancelar

stv sub-value youtube --cost 13.99
# → $1.20/hr — bom custo-benefício
```

</td>
</tr>
</table>

> [**10 receitas a mais →**](../../docs/guides/recipes.md)

---

## ⚙️ Como funciona

```
  "Toca Dark S1E1"
        │
        ▼
  ┌─── Resolução ───┐
  │ Cache → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 TV toca
  └───────────────────┘       │
                         Deep link via
                    LG / Samsung / Roku / Android
```

Fala um nome. stv resolve para um ID de conteúdo e faz deep-link no app da sua TV. Sem automação de navegador, sem chaves de API, sem dependência de nuvem. Resultados são cacheados, então reproduções repetidas são instantâneas.

---

## 📦 Instalação

```bash
pip install stv                    # LG webOS (padrão)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # Tudo
```

```bash
stv setup                          # descobre e faz o pareamento da sua TV
```

> Suporta **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 Funciona com

| Integração | Como |
|------------|-----|
| **Claude Code / Cursor** | Adiciona config MCP → `"toca Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → bot do Telegram |
| **Home Assistant** | Comandos shell em automações |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Scripts de shell** | One-liners de `sleep-mode`, `party-mode` |
| **Qualquer cliente MCP** | 21 ferramentas, stdio ou HTTP (`stv serve`) |

---

## 📚 Documentação

| | |
|---|---|
| [Primeiros passos](../../docs/getting-started/installation.md) | Configuração para qualquer marca de TV |
| [Reproduzir conteúdo](../../docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Cenas](../../docs/guides/scenes.md) | movie-night, kids, sleep, personalizadas |
| [Sync e festa](../../docs/guides/sync-party.md) | Multi-TV, festa de assistir remota |
| [Receitas](../../docs/guides/recipes.md) | **10 combos de funcionalidades poderosas** |
| [Agentes IA](../../docs/guides/ai-agents.md) | MCP para Claude, Cursor, OpenClaw |
| [Referência CLI](../../docs/reference/cli.md) | Todos os comandos e opções |
| [Ferramentas MCP](../../docs/reference/mcp-tools.md) | Todas as 21 ferramentas com parâmetros |

---

## 🤝 Contribuindo

211 testes. Sem necessidade de TV para rodá-los.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Os drivers de Samsung, Roku e Android TV precisam de testes no mundo real. Se você tem uma dessas TVs, [seu feedback importa](https://github.com/Hybirdss/smartest-tv/issues).

[Contribuindo com o cache](../../docs/contributing/cache-contributions.md) · [Desenvolvimento de drivers](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Feito com Python · Sem necessidade de nuvem</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
