# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | **日本語** | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**テレビに話しかけてください。ちゃんと聞いています。**

他のツールは Netflix を「開く」だけです。smartest-tv は*葬送のフリーレン 第2期 第8話*を再生します。

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
あなた: Netflix でフリーレン 第2期 第8話をかけて
あなた: 子どもに Baby Shark かけて
あなた: Ye の新アルバムを Spotify で
あなた: 画面消してジャズかけて
あなた: おやすみ
```

AI がコンテンツ ID（Netflix のエピソード、YouTube の動画、Spotify の URI）を見つけて `stv` を呼び出し、テレビで再生されます。

### See it in action

<p align="center">
  <video src="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4" controls width="720">
  </video>
</p>

## インストール

```bash
pip install stv                 # LG（デフォルト、すぐ使える）
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # すべて
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # 検索 + 一発再生
stv play youtube "baby shark"                          # 検索 + 再生
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # ID だけ取得
stv launch netflix 82656797         # 直接ディープリンク（ID がわかっている場合）
stv status                          # 現在の状態（アプリ、音量、ミュート）
stv volume 25                       # 音量を設定
stv mute                            # ミュートの切り替え
stv apps --format json              # アプリ一覧（構造化出力）
stv notify "ご飯できたよ〜"         # テレビ画面に通知を表示
stv off                             # おやすみ
```

すべてのコマンドで `--format json` が使えます——スクリプトや AI エージェント向け設計です。

### コンテンツ解決

`stv resolve` はストリーミング ID を代わりに見つけてくれます。`stv play` は同じ処理をして、そのまま一ステップで TV でも再生します。

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ（yt-dlp 経由）
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → そのまま渡す
```

Netflix の解決はタイトルページから 1 回の `curl` リクエストでエピソードのメタデータを取得します——Playwright もブラウザも、ログインも不要です。全シーズンを一度に解決してローカルにキャッシュします。2 回目以降の検索は即時（約 0.1 秒）です。

### キャッシュ

ID が一度見つかると、`~/.config/smartest-tv/cache.json` に永久にキャッシュされます。手動でキャッシュに追加することもできます：

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # キャッシュ済み ID を全件表示
```

## エージェントスキル

smartest-tv には、AI アシスタントにテレビの賢い操作方法を教える 5 つのスキルが付属しています。Claude Code にインストールするには：

```bash
cd smartest-tv && ./install-skills.sh
```

| スキル | 役割 |
|--------|------|
| `tv-shared` | CLI リファレンス、認証、設定、共通パターン |
| `tv-netflix` | HTTP スクレイピングでエピソード ID を取得 |
| `tv-youtube` | yt-dlp で動画検索・解決 |
| `tv-spotify` | アルバム/トラック/プレイリスト URI の解決 |
| `tv-workflow` | 複合アクション：映画モード、子どもモード、スリープタイマー |

スキルはシンプルな Markdown ファイルです。どんなエージェントにも数分で移植できます。

## 対応エージェント

シェルコマンドを実行できる AI エージェントならなんでも動きます：

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · または素の `bash`

## 実際の使用例

**深夜 2 時。** ベッドで Claude に「フリーレンの続き、かけて」と言います。リビングのテレビがついて、Netflix が開いて、エピソードが始まります。リモコンには触れていません。目もほとんど開けていません。

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

ネットワーク上のテレビを自動検出し、プラットフォームを識別して自動ペアリング、設定を `~/.config/smartest-tv/config.toml` に書き込みます。何かおかしければ `stv doctor` が原因を教えてくれます。

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 任意、Wake-on-LAN 用
```

初回接続時に TV のペアリング確認が表示されます。一度承認すればキーが保存され、以降は表示されません。

## MCP サーバー

Claude Desktop、Cursor などの MCP クライアント向け——オプションで、CLI がメインのインターフェースです：

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

## コントリビューション

| ステータス | 対象 | 必要なこと |
|-----------|------|-----------|
| **動作確認済み** | LG webOS ドライバー | テスト済み、動作中 |
| **テスト募集中** | Samsung、Android TV、Roku ドライバー | 実機での動作報告を歓迎 |
| **募集中** | Disney+ スキル | ディープリンク ID の解決 |
| **募集中** | Hulu、Prime Video スキル | ディープリンク ID の解決 |

[ドライバーインターフェース](src/smartest_tv/drivers/base.py)は定義済みです——`TVDriver` を実装して PR を送ってください。

## ライセンス

MIT
