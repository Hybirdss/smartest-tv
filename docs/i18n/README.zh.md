# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | **中文** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**跟你的电视说话。它听得懂。**

其他工具只能打开 Netflix。smartest-tv 能直接播放*《葬送的芙莉莲》第二季第八集*。

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## 快速开始

```bash
pip install stv
stv setup          # 自动发现电视、完成配对，搞定
```

就这些。不需要开发者模式，不需要 API Key，不需要配环境变量。说你想看什么就行。

## 能做什么？

```
你: 用 Netflix 播放《葬送的芙莉莲》第二季第八集
你: 给孩子放《小鲨鱼》
你: 用 Spotify 放 Ye 的新专辑
你: 关掉画面，放爵士乐
你: 晚安
```

AI 负责找到内容 ID（Netflix 剧集、YouTube 视频、Spotify URI），调用 `stv`，电视随即播放。

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## 安装

```bash
pip install stv                 # LG（默认，开箱即用）
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # 全部平台
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # 搜索 + 一步播放
stv play youtube "baby shark"                          # 搜索 + 播放
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # 仅获取 ID
stv launch netflix 82656797         # 已知 ID 时直接深度链接
stv status                          # 当前状态、音量、静音
stv volume 25                       # 设置音量
stv mute                            # 切换静音
stv apps --format json              # 查看应用列表（结构化输出）
stv notify "开饭了"                 # 在电视屏幕上弹出通知
stv off                             # 晚安
```

所有命令均支持 `--format json`——专为脚本和 AI 助手调用设计。

### 内容解析

`stv resolve` 帮你找到流媒体 ID，省去手动查找的麻烦。`stv play` 在此基础上一步完成播放。

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ（通过 yt-dlp）
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → 直接透传
```

Netflix 解析通过单次 `curl` 请求抓取剧集元数据——无需 Playwright、无需浏览器、无需登录。所有季集一次性解析并本地缓存，第二次查询即时返回（约 0.1 秒）。

### 缓存

ID 一旦找到，会永久缓存到 `~/.config/smartest-tv/cache.json`。也可以手动填充缓存：

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # 查看所有已缓存 ID
```

## AI 助手技能

smartest-tv 内置五个技能，教 AI 助手如何控制你的电视。一键安装到 Claude Code：

```bash
cd smartest-tv && ./install-skills.sh
```

| 技能 | 功能 |
|------|------|
| `tv-shared` | CLI 参考、认证、配置、通用模式 |
| `tv-netflix` | 通过 HTTP 抓取剧集 ID |
| `tv-youtube` | 通过 yt-dlp 搜索视频并解析格式 |
| `tv-spotify` | 解析专辑/曲目/播放列表 URI |
| `tv-workflow` | 组合操作：观影模式、儿童模式、定时关机 |

技能文件全部是普通的 Markdown。移植到其他 AI 助手，几分钟搞定。

## 支持的助手

任何能执行 shell 命令的 AI 助手均可使用：

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · 或者直接用 `bash`

## 真实使用场景

**凌晨两点。** 你躺在床上，跟 Claude 说："继续放《芙莉莲》。" 客厅电视自动开机，Netflix 打开，剧集从上次的地方继续播放。遥控器碰都没碰，眼睛都没睁开。

**周六早上。** "给宝宝放《小鲨鱼》。" YouTube 自动找到，电视开始播放。你继续做早饭。

**朋友来了。** "游戏模式，HDMI 2，调低音量。" 一句话，三个操作，没人注意到你动过什么。

**做晚饭。** "关掉画面，放爵士乐。" 屏幕熄灭，音乐响起。

**快睡着了。** "45 分钟后关机。" 电视自动关掉，你不用管了。

## smartest-tv 是什么

- **深度链接解析器** — 找到 Netflix 剧集 ID、YouTube 视频、Spotify URI
- **通用遥控器** — 一套 CLI 覆盖 4 个电视平台
- **AI 原生** — 为 AI 助手调用而设计，而不只是人工操作

## 不是什么

- 不是遥控器 App（不能换台、不能按方向键）
- 不是 HDMI-CEC 控制器
- 不是投屏工具

<details>
<summary><strong>深度链接</strong> — 实际工作原理</summary>

同一个内容 ID，在所有电视平台上都通用：

```bash
stv launch netflix 82656797                           # LG、Samsung、Roku、Android TV
stv launch youtube dQw4w9WgXcQ                        # 同上
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # 同上
```

每个驱动将内容 ID 转换为平台原生的深度链接格式：

| 电视 | 深度链接发送方式 |
|----|---------------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

这些细节你完全不需要关心。驱动会自动处理。

</details>

<details>
<summary><strong>平台支持</strong> — 已支持的电视和驱动</summary>

| 平台 | 驱动 | 连接方式 | 状态 |
|----------|--------|-----------|--------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **已验证** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | 社区测试中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | 社区测试中 |
| Roku | HTTP ECP | REST :8060 | 社区测试中 |

LG 是主要测试平台。所有平台均无需开发者模式。

</details>

## 零配置启动

```bash
stv setup
```

同时扫描局域网中的 LG、Samsung、Roku 和 Android/Fire TV（SSDP + ADB）。自动识别平台、完成配对、保存配置并发送测试通知——一步搞定。如果自动发现失败，直接指定 IP：

```bash
stv setup --ip 192.168.1.100
```

所有配置写入 `~/.config/smartest-tv/config.toml`。有问题？`stv doctor` 会告诉你哪里不对。

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 可选，用于 Wake-on-LAN
```

首次连接时电视会弹出配对提示，确认一次，密钥自动保存，以后不再询问。

## MCP 服务器

### 本地 (stdio)

供 Claude Desktop、Cursor 等 MCP 客户端使用——作为本地进程连接：

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

### 远程 (HTTP)

作为可通过网络访问的 MCP 服务器运行。适用于在其他设备上运行的 AI 代理远程控制电视：

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

从任意 MCP 客户端连接：

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
    }
  }
}
```

## 架构

```
用户（自然语言）
  → AI + stv resolve（通过 HTTP 抓取 / yt-dlp / 缓存查找内容 ID）
    → stv play（格式化并分发）
      → 驱动（WebSocket / ADB / HTTP）
        → 电视
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## 贡献

| 状态 | 方向 | 需要什么 |
|--------|------|---------------|
| **就绪** | LG webOS 驱动 | 已测试，可用 |
| **需要测试** | Samsung、Android TV、Roku 驱动 | 欢迎提交实机测试报告 |
| **招募中** | Disney+ 技能 | 深度链接 ID 解析 |
| **招募中** | Hulu、Prime Video 技能 | 深度链接 ID 解析 |

[驱动接口](src/smartest_tv/drivers/base.py)已定义好——实现 `TVDriver`，提 PR 即可。

## 许可证

MIT
