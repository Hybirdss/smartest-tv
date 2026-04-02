# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | **中文** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**跟你的电视说话。它听得懂。**

用自然语言控制智能电视的 CLI 与 AI 助手技能。深度链接 Netflix、YouTube、Spotify——说出你想看的，直接播放。不需要开发者模式，不需要 API Key，运行 `stv setup` 就能用。

> "播放《葬送的芙莉莲》第二季第八集"
>
> *Netflix 随即打开，该集开始播放。*

支持 **LG**（已验证）、**Samsung**、**Android TV / Fire TV**、**Roku**（社区测试中）。

## 安装

```bash
pip install stv
```

就这一行。LG 不需要任何额外依赖。

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # 全部平台
```

## 零配置启动

只需运行一次：

```bash
stv setup
```

自动扫描局域网发现电视，自动识别平台（LG？Samsung？Roku？），自动完成配对——不需要开发者模式，不用手动查 IP。配置写入 `~/.config/smartest-tv/config.toml`，之后所有 `stv` 命令开箱即用。

出了问题？`stv doctor` 会告诉你哪里不对。

## CLI

```bash
stv status                          # 当前状态（应用、音量、静音）
stv launch netflix 82656797         # 播放 Netflix 指定内容
stv launch youtube dQw4w9WgXcQ     # 播放 YouTube 视频
stv launch spotify spotify:album:x  # 播放 Spotify
stv volume 25                       # 设置音量
stv mute                            # 切换静音
stv apps --format json              # 查看已安装应用列表
stv notify "开饭了～"               # 在电视屏幕上显示通知
stv off                             # 关闭电视
```

所有命令均支持 `--format json`，方便脚本和 AI 助手调用。

## AI 助手技能

stv 内置五个技能，教 AI 助手如何智能控制电视。一键安装到 Claude Code：

```bash
cd smartest-tv && ./install-skills.sh
```

装好后直接对 Claude 说话：

```
你: 用 Netflix 播放《葬送的芙莉莲》第二季第八集
你: 给孩子放 Cocomelon
你: 用 Spotify 放 Ye 的新专辑
你: 关掉画面，放爵士乐
你: 晚安
```

技能负责处理麻烦的部分——查 Netflix 剧集 ID、用 yt-dlp 搜索 YouTube、解析 Spotify URI——然后调用 `stv` CLI 控制电视。

### 技能列表

| 技能 | 功能 |
|------|------|
| `tv-shared` | CLI 参考、认证、配置、通用模式 |
| `tv-netflix` | 通过 Playwright 抓取剧集 ID |
| `tv-youtube` | 通过 yt-dlp 搜索和解析视频 |
| `tv-spotify` | 解析专辑/曲目/播放列表 URI |
| `tv-workflow` | 组合操作：观影模式、儿童模式、定时关机 |

## 深度链接的核心价值

其他工具只能*打开* Netflix。stv 能*直接播放《芙莉莲》第 36 集*。

同一个内容 ID，在所有电视平台上都能用：

```bash
stv launch netflix 82656797                          # LG、Samsung、Roku 通用
stv launch youtube dQw4w9WgXcQ                       # 同上
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # 同上
```

每个驱动将内容 ID 转换为平台原生的深度链接格式：

| 电视 | 深度链接发送方式 |
|------|---------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

这些你完全不需要关心。驱动会自动处理。

## 平台支持

| 平台 | 驱动 | 连接方式 | 状态 |
|------|------|---------|------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **已验证** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | 社区测试中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | 社区测试中 |
| Roku | HTTP ECP | REST :8060 | 社区测试中 |

LG 是主要测试平台。Samsung、Android TV、Roku 应该也能用——所有平台均无需开发者模式——欢迎反馈实际使用情况。

## 配置文件

配置保存在 `~/.config/smartest-tv/config.toml`。`stv setup` 完成后大概是这样：

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 可选，用于 Wake-on-LAN
```

首次连接时电视会弹出配对提示，确认一次，密钥自动保存，以后不再询问。

## 真实使用场景

**凌晨两点。** 躺在床上对 Claude 说："继续放《芙莉莲》。" 客厅电视自动开机，Netflix 打开，剧集从上次继续播放。遥控器碰都没碰，眼睛都没睁开。

**周六早上。** "给宝宝放 Cocomelon。" 自动找到，电视开始播放。你继续准备早饭，咖啡都还没凉。

**朋友来了。** "游戏模式，HDMI 2，调低音量。" 一句话，三个操作，完成。

**做饭中。** "关掉画面，放爵士乐。" 屏幕熄灭，音乐响起。不用翻菜单、找应用。

**睡前。** "45 分钟后关机。" 电视自动关掉，你不用管了。

## MCP 服务器

供 Claude Desktop、Cursor 等 MCP 客户端使用——这是可选项，CLI 才是主要入口：

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

共 18 个工具：`tv_on`、`tv_off`、`tv_launch`、`tv_close`、`tv_volume`、`tv_set_volume`、`tv_mute`、`tv_play`、`tv_pause`、`tv_stop`、`tv_status`、`tv_info`、`tv_notify`、`tv_apps`、`tv_volume_up`、`tv_volume_down`、`tv_screen_on`、`tv_screen_off`。

配置自动从 `~/.config/smartest-tv/config.toml` 读取——无需环境变量。

## 架构

```
用户（自然语言）
  → AI + 技能（通过 yt-dlp / Playwright / 搜索查找内容 ID）
    → stv CLI（格式化并分发）
      → 驱动（WebSocket / ADB / HTTP）
        → 电视
```

## 贡献

Samsung、Android TV、Roku **驱动**是最有价值的贡献方向。[驱动接口](src/smartest_tv/drivers/base.py)已定义好——实现 `TVDriver` 并提 PR 即可。

Disney+、Hulu、Prime Video 等新平台的**技能**也欢迎贡献。

## 许可证

MIT
