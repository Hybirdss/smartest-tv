# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | **日本語** | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**テレビに話しかけてください。ちゃんと聞いています。**

他のツールは Netflix を「開く」だけです。smartest-tv は*The Queen's Gambit 第5話*を再生します。

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## クイックスタート

```bash
pip install stv
stv setup          # テレビを自動検出してペアリング、これだけ
```

以上です。開発者モード不要。API キー不要。環境変数不要。見たいものを言うだけ。

## 何ができるの？

```
あなた: Netflix で Squid Game シーズン2 第3話をかけて
あなた: 子どもに Baby Shark かけて
あなた: Wednesday のサウンドトラックを Spotify で
あなた: Netflix で Glass Onion を探して          (映画も対応してます)
あなた: 画面消して lo-fi ビートかけて
あなた: おやすみ
```

AI がコンテンツ ID（Netflix のエピソード、YouTube の動画、Spotify の URI）を見つけて `stv` を呼び出し、テレビで再生されます。

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## インストール

```bash
pip install stv                 # LG（デフォルト、すぐ使える）
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # すべて
```

## CLI

```bash
# 名前でコンテンツを再生 — stv が ID を自動検索
stv play netflix "Bridgerton" s3e4         # 解決 + ディープリンクを一発
stv play youtube "baby shark"              # 検索 + 再生
stv play spotify "Ye White Lines"          # Spotify で検索 + 再生

# 再生せずに検索
stv search netflix "Money Heist"           # 全シーズン + 話数を表示
stv search youtube "lofi hip hop"          # 上位 3 件を表示
stv resolve netflix "The Witcher" s2e5     # エピソード ID だけ取得

# 続きを再生
stv next                                   # 履歴から次のエピソードを再生
stv next "Breaking Bad"                    # 特定作品の次のエピソード
stv history                                # 最近の再生履歴とタイムスタンプ

# TV 操作
stv status                                 # 現在の状態（アプリ、音量、ミュート）
stv volume 25                              # 音量を設定
stv mute                                   # ミュートの切り替え
stv notify "ご飯できたよ〜"                # テレビ画面に通知を表示
stv off                                    # おやすみ

# 直接ディープリンク（ID がわかっている場合）
stv launch netflix 82656797
```

すべてのコマンドで `--format json` が使えます——スクリプトや AI エージェント向け設計です。

### コンテンツ解決の仕組み

`stv play` と `stv resolve` はストリーミング ID を代わりに見つけてくれます：

```bash
stv resolve netflix "The Witcher" s2e5     # → 80189693
stv resolve youtube "lofi hip hop"         # → dQw4w9WgXcQ（yt-dlp 経由）
stv resolve spotify "Ye White Lines"       # → spotify:track:3bbjDFVu...
```

Netflix の解決はタイトルページへの 1 回の `curl` リクエストのみです。Netflix がサーバーサイドで `<script>` タグ内に `__typename:"Episode"` メタデータをレンダリングしているためです。シーズン内のエピソード ID は連続した整数なので、1 回の HTTP リクエストで作品の全シーズンを解決できます。Playwright もヘッドレスブラウザも、ログインも不要です。

結果は 3 段階でキャッシュされます：
1. **ローカルキャッシュ** — `~/.config/smartest-tv/cache.json`、即時返却（約 0.1 秒）
2. **コミュニティキャッシュ** — GitHub raw CDN 経由のクラウドソーシング ID（Netflix 29 作品、YouTube 11 動画をあらかじめ登録済み）、サーバーコストなし
3. **ウェブ検索フォールバック** — Brave Search で未知のタイトル ID を自動発見

### キャッシュ

```bash
stv cache show                                # キャッシュ済み ID を全件表示
stv cache set netflix "Narcos" -s 1 --first-ep-id 80025173 --count 10
stv cache get netflix "Narcos" -s 1 -e 5      # → 80025177
stv cache contribute                          # コミュニティキャッシュ PR 用にエクスポート
```

## エージェントスキル

smartest-tv には、AI アシスタントにテレビ操作のすべてを教える 1 つのスキルが付属しています。Claude Code にインストールするには：

```bash
cd smartest-tv && ./install-skills.sh
```

`tv` スキルは、すべてのプラットフォーム（Netflix、YouTube、Spotify）、すべてのコマンド（`play`、`search`、`resolve`、`cache`、`volume`、`off`）、および複合ワークフロー（映画モード、子どもモード、スリープタイマー）をカバーします。1 つの Markdown ファイル — どんな AI エージェントにも数分で移植できます。

## 対応エージェント

シェルコマンドを実行できる AI エージェントならなんでも動きます：

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · または素の `bash`

## 実際の使用例

**深夜 2 時。** ベッドで Claude に「Stranger Things の続き、かけて」と言います。リビングのテレビがついて、Netflix が開いて、エピソードが始まります。リモコンには触れていません。目もほとんど開けていません。

**土曜日の朝。** 「Cocomelon かけて」。YouTube で見つけてテレビで再生されます。朝食の準備を続けてください。

**友達が来たとき。** 「ゲームモード、HDMI 2、音量下げて」。一文で 3 つの変更、誰かが気づく前に完了。

**夕飯の支度中。** 「画面消してジャズかけて」。画面が暗くなり、音楽が流れます。

**眠りにつく前。** 「45 分後に消して」。テレビが勝手に消えます。あなたは消えません。

## smartest-tv とは

- **ディープリンクリゾルバー** — Netflix のエピソード ID、YouTube の動画、Spotify の URI を見つける
- **ユニバーサルリモコン** — 4 つの TV プラットフォームを一つの CLI で操作
- **AI ネイティブ** — 人間だけでなく、エージェントが呼び出すことを前提に設計

## smartest-tv ではないもの

- リモコンアプリではありません（チャンネルサーフィン、矢印キー操作は対象外）
- HDMI-CEC コントローラーではありません
- 画面ミラーリングツールではありません

<details>
<summary><strong>ディープリンク</strong> — 実際の仕組み</summary>

同じコンテンツ ID が、すべての TV プラットフォームで動作します：

```bash
stv launch netflix 82656797                           # LG、Samsung、Roku、Android TV すべて同じ
stv launch youtube dQw4w9WgXcQ                        # 同じ
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # 同じ
```

各ドライバーがコンテンツ ID をプラットフォーム固有のディープリンク形式に変換します：

| TV | ディープリンクの送信方法 |
|----|---------------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

これらを意識する必要はありません。ドライバーが自動で処理します。

</details>

<details>
<summary><strong>対応プラットフォーム</strong> — 動作確認済みの TV とドライバー</summary>

| プラットフォーム | ドライバー | 接続方式 | ステータス |
|----------------|-----------|---------|-----------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **動作確認済み** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | コミュニティ検証中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | コミュニティ検証中 |
| Roku | HTTP ECP | REST :8060 | コミュニティ検証中 |

LG がメインの検証プラットフォームです。いずれのプラットフォームも開発者モードは不要です。

</details>

## ゼロ設定ではじめる

```bash
stv setup
```

LG、Samsung、Roku、Android/Fire TV を同時にネットワークスキャンします（SSDP + ADB）。プラットフォームを自動検出し、ペアリング、設定保存、テスト通知まで一括処理します。自動で見つからない場合は IP を直接指定してください:

```bash
stv setup --ip 192.168.1.100
```

設定はすべて `~/.config/smartest-tv/config.toml` に保存されます。何かおかしければ `stv doctor` が原因を教えてくれます。

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 任意、Wake-on-LAN 用
```

初回接続時に TV のペアリング確認が表示されます。一度承認すればキーが保存され、以降は表示されません。

## MCP サーバー

### ローカル (stdio)

Claude Desktop、Cursor などの MCP クライアント向け——ローカルプロセスとして接続：

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

### リモート (HTTP)

ネットワーク経由でアクセス可能な MCP サーバーとして起動。別のマシンの AI エージェントから TV を制御するのに便利です：

```bash
stv serve                          # localhost:8910 (SSE)
stv serve --host 0.0.0.0 --port 8910
stv serve --transport streamable-http
```

MCP クライアントから接続：

```json
{
  "mcpServers": {
    "tv": {
      "url": "http://192.168.1.50:8910/sse"
    }
  }
}
```

## アーキテクチャ

```
あなた（自然言語）
  → AI + stv resolve（HTTP スクレイピング / yt-dlp / キャッシュでコンテンツ ID を取得）
    → stv play（ディープリンクに変換して送信）
      → ドライバー（WebSocket / ADB / HTTP）
        → テレビ
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## ドキュメント

| ガイド | 内容 |
|-------|------|
| [セットアップガイド](docs/setup-guide.md) | TV ブランド別の設定手順（LG ペアリング、Samsung リモートアクセス、ADB、Roku ECP） |
| [MCP 連携](docs/mcp-integration.md) | Claude Code、Cursor などの MCP クライアント設定 |
| [API リファレンス](docs/api-reference.md) | 全 CLI コマンド + 20 の MCP ツールとパラメーター |
| [キャッシュへの貢献](docs/contributing-cache.md) | Netflix ID の見つけ方とコミュニティキャッシュへの PR 提出方法 |

## コントリビューション

| ステータス | 対象 | 必要なこと |
|-----------|------|-----------|
| **動作確認済み** | LG webOS ドライバー | テスト済み、動作中 |
| **テスト募集中** | Samsung、Android TV、Roku ドライバー | 実機での動作報告を歓迎 |
| **募集中** | Disney+、Hulu、Prime Video | ディープリンク ID の解決 |
| **募集中** | コミュニティキャッシュのエントリー | [お気に入り作品を追加する](docs/contributing-cache.md) |

[ドライバーインターフェース](src/smartest_tv/drivers/base.py)は定義済みです——`TVDriver` を実装して PR を送ってください。

### テストの実行

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

コンテンツリゾルバー、キャッシュ、CLI パーサーをカバーする 55 のユニットテスト。TV やネットワーク接続は不要です — すべての外部呼び出しはモック化されています。

## ライセンス

MIT
