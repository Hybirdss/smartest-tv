<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">你的电视一直在等待的 CLI。</h4>

<p align="center">
  <b>按名称播放 Netflix。投屏 URL。多房间音频。AI 管家。全在你的终端里。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="../../tests/"><img src="https://img.shields.io/badge/tests-270%2B%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
  <a href="https://glama.ai/mcp/servers/Hybirdss/smartest-tv"><img src="https://img.shields.io/badge/Glama-A%20A%20A-00d992?style=flat-square" alt="Glama Score"></a>
  <a href="https://github.com/punkpeye/awesome-mcp-servers"><img src="https://img.shields.io/badge/awesome--mcp--servers-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome MCP Servers"></a>
  <a href="https://github.com/vitalets/awesome-smart-tv"><img src="https://img.shields.io/badge/awesome--smart--tv-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome Smart TV"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square" alt="HACS"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <b>中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.pt-br.md">Português</a> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv play "Frieren"</code></p>

<p align="center"><sub>没有电视？在浏览器中打开。有电视？运行 <code>stv setup</code> 连接它。</sub></p>

<p align="center">
  <img src="../assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 没有 stv</th>
<th>😎 有了 stv</th>
</tr>
<tr>
<td>

1. 拿起遥控器
2. 打开 Netflix 应用
3. 搜索节目
4. 选择季数
5. 选择集数
6. 按播放

**约 30 秒**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
```

**约 3 秒**

</td>
</tr>
</table>

<br>

---

## ✨ 它能做什么

<table>
<tr>
<td width="33%" valign="top">

### 🎬 按名称播放
```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
说出名称，stv 找到 ID，打开应用，开始播放。

</td>
<td width="33%" valign="top">

### 🔗 投屏任意 URL
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
朋友发来链接，粘贴，电视开始播放。

</td>
<td width="33%" valign="top">

### 🎵 队列与派对
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
每个人添加自己的选择，电视按顺序播放。

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 场景预设
```bash
stv scene movie-night   # 音量 20，影院模式
stv scene kids          # 音量 15，Cocomelon
stv scene sleep         # 雨声，自动关机
```
一条命令设定氛围。

</td>
<td width="33%" valign="top">

### 🔊 多房间音频
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
屏幕关闭，音乐无处不在。<br>**免费的 Sonos。**

</td>
<td width="33%" valign="top">

### 📺 电视作为显示屏
```bash
stv display message "Dinner!"
stv display clock
stv display dashboard "Temp:22°C"
```
仪表板、时钟、标牌。<br>**每月 $0。**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 观看智能分析
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
你的 Netflix 值 $18/月吗？

</td>
<td width="33%" valign="top">

### 🌐 同步派对
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # 晚安
```
每台电视，同时播放，甚至包括远程朋友。

</td>
<td width="33%" valign="top">

### 🤖 AI 管家
```
"Play something chill"
→ tv_recommend → tv_play
→ Playing The Queen's Gambit
```
21 个 MCP 工具，一句话就够了。

</td>
</tr>
</table>

---

## 🤖 让你的 AI 控制电视

stv 是一个 **MCP 服务器**。Claude、GPT、Cursor 或任何 MCP 客户端都可以用自然语言控制你的电视。

<table>
<tr>
<td width="50%" valign="top">

**配置（一行搞定）：**

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

或通过 [OpenClaw](../../docs/integrations/openclaw.md)：
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**然后直接对话：**

```
You: "I just got home, set up movie night"

Claude: 🎬 Movie night activated.
  Volume → 20, cinema mode on.
  
  Based on your history:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

You: "Play 1, put a clock on kitchen TV"

Claude: ✓ Playing The Queen's Gambit
         ✓ Clock on kitchen TV
```

</td>
</tr>
</table>

<details>
<summary><b>全部 21 个 MCP 工具</b></summary>
<br>

| 分类 | 工具 | 功能 |
|------|------|------|
| **播放** | `tv_play` | 按名称搜索并播放 |
| | `tv_cast` | 投屏任意 URL |
| | `tv_next` | 继续观看 |
| | `tv_launch` | 通过 ID 启动应用 |
| | `tv_resolve` | 仅获取内容 ID |
| **发现** | `tv_whats_on` | 热门内容 |
| | `tv_recommend` | 个性化推荐 |
| **控制** | `tv_power` | 开/关机 |
| | `tv_volume` | 获取/设置/调节/静音 |
| | `tv_screen` | 屏幕开/关 |
| | `tv_notify` | 弹出通知 |
| | `tv_status` | 当前状态 |
| **组织** | `tv_queue` | 播放队列 |
| | `tv_scene` | 场景预设 |
| | `tv_history` | 观看记录 |
| **智能** | `tv_insights` | 观看统计 |
| | `tv_display` | 电视作为显示屏 |
| | `tv_audio` | 多房间音频 |
| **多电视** | `tv_sync` | 在所有电视上播放 |
| | `tv_list_tvs` | 列出电视 |
| | `tv_groups` | 电视分组 |

</details>

---

## 📅 与 stv 共度的一天

| 时间 | 发生的事 |
|------|---------|
| **早上 7 点** | 厨房电视上 `stv display dashboard "Weather:18°C" "Meeting:10am"` |
| **早上 8 点** | `stv scene kids --tv kids-room` -- Cocomelon，音量 15 |
| **中午 12 点** | 朋友发来 Netflix 链接 → `stv cast <url>` |
| **下午 5 点** | `stv screen-time` → 孩子今天看了 2 小时 15 分钟 |
| **下午 6:30** | `stv scene movie-night` -- 音量 20，影院模式 |
| **晚上 7 点** | `stv recommend --mood chill` → 推荐《Ozark》 |
| **晚上 9 点** | `stv audio play "friday vibes" -p spotify` -- 音乐无处不在 |
| **晚上 10 点** | `stv --group party play netflix "Wednesday" s1e1` -- 同步播放 |
| **晚上 11:30** | `stv scene sleep` → `stv --all off` -- 晚安 |

---

## 🔥 杀手级组合

<table>
<tr>
<td width="33%" valign="top">

**🌙 就寝自动驾驶**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
环境音效，屏幕关闭，自动定时，关掉所有其他电视。

</td>
<td width="33%" valign="top">

**🎧 免费的 Sonos**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
每台电视都是扬声器，各房间独立音量，屏幕关闭。

</td>
<td width="33%" valign="top">

**💰 订阅审计**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — consider canceling

stv sub-value youtube --cost 13.99
# → $1.20/hr — good value
```

</td>
</tr>
</table>

> [**10 个更多使用方案 →**](../../docs/guides/recipes.md)

---

## ⚙️ 工作原理

```
  "Play Dark S1E1"
        │
        ▼
  ┌─── Resolution ───┐
  │ Cache → API → Web │  content_id
  │  0.1s   1s    3s  │──────────────▶ 📺 TV plays it
  └───────────────────┘       │
                         Deep link via
                    LG / Samsung / Roku / Android
```

说出名称，stv 将其解析为内容 ID，通过深度链接直接在电视上打开应用。无需浏览器自动化，无需 API 密钥，无需云依赖。结果会被缓存，重复播放即时完成。

---

## 📦 安装

```bash
pip install stv                    # LG webOS（默认）
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # 全部平台
```

```bash
stv setup                          # 自动发现并配对你的电视
```

> 支持 **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 集成支持

| 集成 | 方式 |
|------|------|
| **Claude Code / Cursor** | 添加 MCP 配置 → `"play Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → Telegram 机器人 |
| **Home Assistant** | 在自动化中使用 Shell 命令 |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **Shell 脚本** | `sleep-mode`、`party-mode` 一行命令 |
| **任意 MCP 客户端** | 21 个工具，stdio 或 HTTP（`stv serve`） |

---

## 📚 文档

| | |
|---|---|
| [快速上手](../../docs/getting-started/installation.md) | 各品牌电视的配置 |
| [播放内容](../../docs/guides/playing-content.md) | play、cast、queue、resolve |
| [场景](../../docs/guides/scenes.md) | movie-night、kids、sleep、自定义 |
| [同步与派对](../../docs/guides/sync-party.md) | 多电视、远程观影派对 |
| [使用方案](../../docs/guides/recipes.md) | **10 个强力功能组合** |
| [AI 助手](../../docs/guides/ai-agents.md) | Claude、Cursor、OpenClaw 的 MCP 配置 |
| [CLI 参考](../../docs/reference/cli.md) | 所有命令和选项 |
| [MCP 工具](../../docs/reference/mcp-tools.md) | 含参数的全部 21 个工具 |

---

## 🤝 贡献

211 个测试，无需电视即可运行。

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Samsung、Roku 和 Android TV 驱动需要真实设备测试。如果你有这些设备，[你的反馈非常重要](https://github.com/Hybirdss/smartest-tv/issues)。

[贡献缓存](../../docs/contributing/cache-contributions.md) · [驱动开发](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · 使用 Python 构建 · 无需云端</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
