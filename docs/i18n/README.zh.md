# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | **中文** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**跟你的电视说话。它听得懂。**

| 没有 stv | 有了 stv |
|:-------:|:-------:|
| 手机上打开 Netflix | `stv play netflix "Dark" s1e1` |
| 搜索剧集 | (自动完成) |
| 选择季数 | (自动计算) |
| 选择集数 | (深度链接直达) |
| 点击播放 | |
| **约30秒** | **约3秒** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*点击观看完整视频（含声音）*

## 快速开始

```bash
pip install stv
stv setup          # 自动发现电视、完成配对，搞定
```

## 大家用 stv 做什么

### "把这个链接投到电视上"

朋友发来一个 YouTube 链接。粘贴。电视开始播放。

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "派对歌单排队"

每个人加入自己喜欢的歌。电视按顺序播放。

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # 按顺序开始播放
stv queue skip                     # 下一首
```

### "不知道看什么"

别再刷 30 分钟 Netflix 了。问问什么在热播。获取一个推荐。

```bash
stv whats-on netflix               # 当前热门前 10 名
stv recommend --mood chill         # 基于你的观看记录
stv recommend --mood action        # 换个心情，换批推荐
```

### "电影之夜"

一条命令搞定氛围：音量、通知、内容。

```bash
stv scene movie-night              # 音量20，影院模式
stv scene kids                     # 音量15，播放 Cocomelon
stv scene sleep                    # 环境音效，自动关机
stv scene create date-night        # 创建你自己的场景
```

### "在卧室电视上播"

用一个 CLI 控制家里所有电视。

```bash
stv multi list                     # living-room (LG), bedroom (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### "从上次看到的地方继续"

```bash
stv next                           # 从上次的剧集继续
stv next "Breaking Bad"            # 指定剧集继续看
stv history                        # 查看观看记录
```

## 与 stv 共度的一天

**早上 7 点** -- 闹钟响了。"有什么热播？" `stv whats-on youtube` 显示晨间新闻。电视开始播放。

**早上 8 点** -- 孩子醒了。`stv scene kids` -- 音量 15，Cocomelon 启动。

**中午 12 点** -- 朋友发来一个 Netflix 链接。`stv cast https://netflix.com/watch/...` -- 电视直接播放。

**下午 6 点 30 分** -- 下班回家。`stv scene movie-night` -- 音量降低，影院模式。

**晚上 7 点** -- "看什么好？" `stv recommend --mood chill` -- 推荐《女王的棋局》。

**晚上 9 点** -- 朋友来了。大家各自运行 `stv queue add ...` -- 电视按顺序播放。

**晚上 11 点 30 分** -- "晚安。" `stv scene sleep` -- 环境音效，45 分钟后电视自动关机。

<details>
<summary><b>stv 是怎么只用一次 HTTP 请求就找到 Netflix 剧集的？</b></summary>

Netflix 会在 `<script>` 标签中服务端渲染 `__typename:"Episode"` 元数据。同一季内的剧集 ID 是连续整数。向剧集页面发送一次 `curl` 请求，即可提取所有季的所有剧集 ID。无需 Playwright，无需无头浏览器，无需 API Key，无需登录。

结果以三层缓存存储：
1. **本地缓存** -- `~/.config/smartest-tv/cache.json`，即时返回 (~0.1 秒)
2. **社区缓存** -- 通过 GitHub raw CDN 众包 ID（预置 40 余条），零服务器成本
3. **网络搜索兜底** -- 通过 Brave Search 自动发现未知标题 ID

</details>

<details>
<summary><b>深度链接 -- stv 与电视通信的方式</b></summary>

每个驱动将内容 ID 转换为平台原生的深度链接格式：

| 电视 | 协议 | 深度链接格式 |
|------|------|------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

这些细节你完全不需要关心。驱动会自动处理。

</details>

<details>
<summary><b>支持平台</b></summary>

| 平台 | 驱动 | 状态 |
|------|------|------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **已验证** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | 社区测试中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | 社区测试中 |
| Roku | HTTP ECP | 社区测试中 |

</details>

## 安装

```bash
pip install stv                 # LG（默认）
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # 全部平台
```

## 与一切集成

| 集成 | 效果 |
|------|------|
| **Claude Code** | "播放 Breaking Bad s1e1" -- 电视开始播放 |
| **OpenClaw** | Telegram: "到家了" -- 场景 + 推荐 + 播放 |
| **Home Assistant** | 门打开 -- 电视开机 -- 热播节目列表出现 |
| **Cursor / Codex** | AI 写代码休息时，顺便控制电视 |
| **cron / 脚本** | 早 7 点：卧室电视播新闻。晚 9 点：儿童电视关机 |
| **任意 MCP 客户端** | stdio 或 HTTP，32 个工具随时可用 |

### MCP 服务器

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

作为 HTTP 服务器运行以支持远程访问：

```bash
stv serve --port 8910              # SSE 在 http://localhost:8910/sse
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## 文档

| | |
|---|---|
| [快速上手](../../docs/getting-started/installation.md) | 各品牌电视的首次配置 |
| [播放内容](../../docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [场景](../../docs/guides/scenes.md) | 预设：movie-night, kids, sleep, 自定义 |
| [多电视](../../docs/guides/multi-tv.md) | 用 `--tv` 控制多台电视 |
| [AI 助手](../../docs/guides/ai-agents.md) | Claude, Cursor, OpenClaw 的 MCP 配置 |
| [推荐功能](../../docs/guides/recommendations.md) | AI 驱动的内容推荐 |
| [CLI 参考](../../docs/reference/cli.md) | 所有命令和选项 |
| [MCP 工具](../../docs/reference/mcp-tools.md) | 含参数的全部 32 个 MCP 工具 |
| [OpenClaw](../../docs/integrations/openclaw.md) | ClawHub 技能 + Telegram 场景 |

## 贡献

Samsung、Roku 和 Android TV 驱动需要真实设备测试。如果你有这些电视，你的反馈非常宝贵。

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 个测试，无需电视
```

想把你喜欢的剧集加入社区缓存？请参阅[贡献缓存](../../docs/contributing/cache-contributions.md)。

想为新电视编写驱动？请参阅[驱动开发](../../docs/contributing/driver-development.md)。

## 许可证

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
