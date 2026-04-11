<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">あなたのテレビが待ち望んでいた CLI。</h4>

<p align="center">
  <b>名前で Netflix を再生。URL をキャスト。マルチルーム音楽。AI コンシェルジュ。すべてターミナルから。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-270%2B%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
  <a href="https://glama.ai/mcp/servers/Hybirdss/smartest-tv"><img src="https://img.shields.io/badge/Glama-A%20A%20A-00d992?style=flat-square" alt="Glama Score"></a>
  <a href="https://github.com/punkpeye/awesome-mcp-servers"><img src="https://img.shields.io/badge/awesome--mcp--servers-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome MCP Servers"></a>
  <a href="https://github.com/vitalets/awesome-smart-tv"><img src="https://img.shields.io/badge/awesome--smart--tv-listed-fc60a8?style=flat-square&logo=awesome-lists&logoColor=white" alt="Awesome Smart TV"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square" alt="HACS"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh.md">中文</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.pt-br.md">Português</a> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv play "Frieren"</code></p>

<p align="center"><sub>テレビがなくてもブラウザで開きます。テレビをお持ちなら <code>stv setup</code> で接続。</sub></p>

<p align="center">
  <img src="../assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 stv なし</th>
<th>😎 stv あり</th>
</tr>
<tr>
<td>

1. リモコンを手に取る
2. Netflix アプリを開く
3. 作品を検索する
4. シーズンを選ぶ
5. エピソードを選ぶ
6. 再生ボタンを押す

**約30秒**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
```

**約3秒**

</td>
</tr>
</table>

<br>

---

## ✨ 機能一覧

<table>
<tr>
<td width="33%" valign="top">

### 🎬 名前で再生
```bash
stv play netflix "Dark" s1e1
stv play "Frieren"              # auto-detects platform
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
名前を言うだけ。stv が ID を見つけ、アプリを開き、再生を始める。

</td>
<td width="33%" valign="top">

### 🔗 任意の URL をキャスト
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
友達がリンクを送ってきた。貼り付けるだけ。テレビで再生される。

</td>
<td width="33%" valign="top">

### 🎵 キューとパーティー
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
みんなが選曲を追加。テレビが順番に再生する。

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 シーンプリセット
```bash
stv scene movie-night   # 音量20、シネマモード
stv scene kids          # 音量15、Cocomelon
stv scene sleep         # 雨音、自動オフ
```
コマンド一つで雰囲気を設定。

</td>
<td width="33%" valign="top">

### 🔊 マルチルーム音楽
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
画面オフ。音楽はどこでも。<br>**無料の Sonos。**

</td>
<td width="33%" valign="top">

### 📺 ディスプレイとして使う
```bash
stv display message "Dinner!"
stv display clock
stv display dashboard "Temp:22°C"
```
ダッシュボード、時計、サイネージ。<br>**月額 $0。**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 視聴インサイト
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
Netflix は月 $18 の価値がある？

</td>
<td width="33%" valign="top">

### 🌐 シンクパーティー
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # おやすみ
```
すべてのテレビ。一斉に。リモートの友達も含めて。

</td>
<td width="33%" valign="top">

### 🤖 AI コンシェルジュ
```
"Play something chill"
→ tv_recommend → tv_play
→ Playing The Queen's Gambit
```
MCP ツール 21 個。一言で十分。

</td>
</tr>
</table>

---

## 🤖 AI にテレビを操作させる

stv は **MCP サーバー**です。Claude、GPT、Cursor、またはあらゆる MCP クライアントが自然言語でテレビを操作できます。

<table>
<tr>
<td width="50%" valign="top">

**セットアップ（1行）:**

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

または [OpenClaw](../../docs/integrations/openclaw.md) 経由:
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**あとは話しかけるだけ:**

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
<summary><b>全 21 MCP ツール</b></summary>
<br>

| カテゴリ | ツール | 機能 |
|----------|------|-------------|
| **再生** | `tv_play` | 名前で検索して再生 |
| | `tv_cast` | 任意の URL をキャスト |
| | `tv_next` | 続きから視聴 |
| | `tv_launch` | ID でアプリを起動 |
| | `tv_resolve` | コンテンツ ID のみ取得 |
| **探す** | `tv_whats_on` | トレンドコンテンツ |
| | `tv_recommend` | パーソナライズされたおすすめ |
| **制御** | `tv_power` | オン/オフ |
| | `tv_volume` | 取得/設定/ステップ/ミュート |
| | `tv_screen` | 画面オン/オフ |
| | `tv_notify` | トースト通知 |
| | `tv_status` | 現在の状態 |
| **整理** | `tv_queue` | 再生キュー |
| | `tv_scene` | シーンプリセット |
| | `tv_history` | 視聴履歴 |
| **インサイト** | `tv_insights` | 視聴統計 |
| | `tv_display` | ディスプレイとして使用 |
| | `tv_audio` | マルチルーム音楽 |
| **マルチ TV** | `tv_sync` | 全テレビで再生 |
| | `tv_list_tvs` | テレビの一覧 |
| | `tv_groups` | TV グループ |

</details>

---

## 📅 stv と過ごす一日

| 時間 | 出来事 |
|------|-------------|
| **午前7時** | キッチン TV に `stv display dashboard "Weather:18°C" "Meeting:10am"` |
| **午前8時** | `stv scene kids --tv kids-room` -- Cocomelon、音量 15 |
| **正午** | 友達が Netflix リンクを送ってくる → `stv cast <url>` |
| **午後5時** | `stv screen-time` → 子どもは今日 2 時間 15 分視聴 |
| **午後6時30分** | `stv scene movie-night` -- 音量 20、シネマモード |
| **午後7時** | `stv recommend --mood chill` → Ozark をおすすめ |
| **午後9時** | `stv audio play "friday vibes" -p spotify` -- 音楽どこでも |
| **午後10時** | `stv --group party play netflix "Wednesday" s1e1` -- シンク |
| **午後11時30分** | `stv scene sleep` → `stv --all off` -- おやすみ |

---

## 🔥 最強コンボ

<table>
<tr>
<td width="33%" valign="top">

**🌙 就寝オートパイロット**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
アンビエントサウンド、画面オフ、自動タイマー、他のテレビもすべてオフ。

</td>
<td width="33%" valign="top">

**🎧 無料の Sonos**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
すべてのテレビがスピーカーに。部屋ごとに音量調整。画面オフ。

</td>
<td width="33%" valign="top">

**💰 サブスク診断**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — consider canceling

stv sub-value youtube --cost 13.99
# → $1.20/hr — good value
```

</td>
</tr>
</table>

> [**レシピをもっと見る（10件）→**](../../docs/guides/recipes.md)

---

## ⚙️ 仕組み

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

名前を言うだけ。stv がコンテンツ ID に変換し、テレビのアプリにディープリンクする。ブラウザ自動化なし、API キーなし、クラウド依存なし。結果はキャッシュされるので、繰り返し再生は即時。

---

## 📦 インストール

```bash
pip install stv                    # LG webOS（デフォルト）
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # すべて
```

```bash
stv setup                          # TV を自動検出してペアリング
```

> 対応機種: **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku**

---

## 🔌 連携

| 連携先 | 方法 |
|------------|-----|
| **Claude Code / Cursor** | MCP 設定を追加 → `"play Dark s1e1"` |
| **OpenClaw** | `clawhub install smartest-tv` → Telegram ボット |
| **Home Assistant** | オートメーションのシェルコマンド |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **シェルスクリプト** | `sleep-mode`、`party-mode` のワンライナー |
| **あらゆる MCP クライアント** | 21 ツール、stdio または HTTP（`stv serve`） |

---

## 📚 ドキュメント

| | |
|---|---|
| [はじめに](../../docs/getting-started/installation.md) | あらゆる TV ブランドのセットアップ |
| [コンテンツの再生](../../docs/guides/playing-content.md) | play、cast、queue、resolve |
| [シーン](../../docs/guides/scenes.md) | movie-night、kids、sleep、カスタム |
| [シンク & パーティー](../../docs/guides/sync-party.md) | マルチ TV、リモート視聴パーティー |
| [レシピ](../../docs/guides/recipes.md) | **強力な機能コンボ 10 選** |
| [AI エージェント](../../docs/guides/ai-agents.md) | Claude、Cursor、OpenClaw の MCP |
| [CLI リファレンス](../../docs/reference/cli.md) | すべてのコマンドとオプション |
| [MCP ツール](../../docs/reference/mcp-tools.md) | パラメーター付き全 21 ツール |

---

## 🤝 コントリビューション

211 テスト。実機の TV は不要。

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Samsung、Roku、Android TV のドライバーは実機テストが必要です。これらの機器をお持ちであれば、[フィードバックをお寄せください](https://github.com/Hybirdss/smartest-tv/issues)。

[キャッシュへの貢献](../../docs/contributing/cache-contributions.md) · [ドライバー開発](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Pythonで構築 · クラウド不要</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
