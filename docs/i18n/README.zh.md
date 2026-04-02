# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | **中文** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

跟你的电视说话。它听得懂。

用自然语言控制智能电视的 CLI 与 AI 助手技能。Netflix、YouTube、Spotify 深度链接——说出你想看的，直接播放。

> "播放《葬送的芙莉莲》第二季第八集"
>
> *Netflix 随即打开并开始播放该集。*

支持 **LG**、**Samsung**、**Android TV**、**Fire TV**、**Roku**。

## 安装

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # 全部平台
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # 当前状态（应用、音量、静音）
tv launch netflix 82656797         # 播放 Netflix 特定内容
tv launch youtube dQw4w9WgXcQ     # 播放 YouTube 视频
tv launch spotify spotify:album:x # 播放 Spotify
tv volume 25                       # 设置音量
tv mute                            # 切换静音
tv apps --format json              # 已安装应用列表
tv notify "吃饭啦~"                 # 在电视屏幕上显示通知
tv off                             # 关闭电视
```

所有命令均支持 `--format json` — 为 AI 助手提供结构化输出。

## AI 助手技能

在 Claude Code 中安装技能：

```bash
cd smartest-tv && ./install-skills.sh
```

然后，用自然语言跟 Claude 说：

```
你: 用 Netflix 播放《葬送的芙莉莲》第二季第八集
你: 给孩子放 YouTube
你: 用 Spotify 播放 Ye 的新专辑
你: 关掉画面，放爵士乐
你: 晚安
```

技能会处理所有复杂的部分——查找 Netflix 剧集 ID、用 yt-dlp 搜索 YouTube、解析 Spotify URI——然后调用 `tv` CLI 控制电视。

## 深度链接

这是 smartest-tv 的核心优势。其他工具只能*打开* Netflix。我们能*播放《芙莉莲》第 36 集*。

相同的内容 ID 在所有电视平台上都有效：

```bash
tv launch netflix 82656797       # 无论 LG、Samsung 还是 Roku，效果相同
tv launch youtube dQw4w9WgXcQ    # 同上
tv launch spotify spotify:album:x  # 同上
```

## 真实使用场景

**凌晨两点。** 躺在床上对 Claude 说："继续播《芙莉莲》。" 客厅的电视自动开启，Netflix 打开，剧集开始播放。不需要找遥控器。

**周六早上。** "给宝宝放 Cocomelon。" 自动在 YouTube 找到并在电视上播放。你可以继续准备早餐。

**朋友来访时。** "游戏模式，HDMI 2，调低音量。" 一句话完成三项操作。

## 许可证

MIT
