# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | **日本語** | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**テレビに話しかけてください。ちゃんと聞いています。**

スマートテレビを自然言語で操作する CLI と AI エージェントスキル。Netflix、YouTube、Spotify のディープリンク対応——見たいものを言えばすぐ再生されます。開発者モード不要。API キー不要。`stv setup` を一度実行するだけ。

> 「葬送のフリーレン 第2期 第8話をかけて」
>
> *Netflix が開いて、そのエピソードが再生されます。*

**LG**（動作確認済み）、**Samsung**、**Android TV / Fire TV**、**Roku**（コミュニティ検証中）に対応。

## インストール

```bash
pip install stv
```

以上です。LG なら追加パッケージは不要です。

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # すべて
```

## ゼロ設定ではじめる

一度だけこれを実行してください：

```bash
stv setup
```

ネットワーク上のテレビを自動検出、プラットフォームを自動識別（LG？Samsung？Roku？）、自動ペアリング——開発者モードも不要、IP アドレスを調べる必要もありません。設定は `~/.config/smartest-tv/config.toml` に保存されます。あとはそのまま使えます。

何かおかしければ、`stv doctor` が原因を教えてくれます。

## CLI

```bash
stv status                          # 現在の状態（アプリ、音量、ミュート）
stv launch netflix 82656797         # Netflix で特定コンテンツを再生
stv launch youtube dQw4w9WgXcQ     # YouTube 動画を再生
stv launch spotify spotify:album:x  # Spotify を再生
stv volume 25                       # 音量を設定
stv mute                            # ミュートの切り替え
stv apps --format json              # インストール済みアプリ一覧
stv notify "ご飯できたよ〜"         # テレビ画面に通知を表示
stv off                             # テレビをオフ
```

すべてのコマンドで `--format json` が使えます——スクリプトや AI エージェント向けの構造化出力。

## AI エージェントスキル

stv には、AI アシスタントにテレビの賢い操作方法を教える 5 つのスキルが付属しています。Claude Code に一括インストール：

```bash
cd smartest-tv && ./install-skills.sh
```

あとは Claude に自然言語で話しかけるだけ：

```
あなた: フリーレン 第2期 第8話を Netflix でかけて
あなた: 子どもに Cocomelon をつけて
あなた: Ye の新アルバムを Spotify でかけて
あなた: 画面を消してジャズをかけて
あなた: おやすみ
```

スキルが面倒な部分をすべて担当します——Netflix のエピソード ID の検索、yt-dlp による YouTube 検索、Spotify URI の解決——そして `stv` CLI を呼び出してテレビを操作します。

### スキル一覧

| スキル | 役割 |
|--------|------|
| `tv-shared` | CLI リファレンス、認証、設定、共通パターン |
| `tv-netflix` | Playwright でエピソード ID を取得 |
| `tv-youtube` | yt-dlp で動画検索・解決 |
| `tv-spotify` | アルバム/トラック/プレイリスト URI の解決 |
| `tv-workflow` | 複合アクション：映画モード、子どもモード、スリープタイマー |

## ディープリンクの本質的な違い

他のツールは Netflix を「開く」だけです。stv は「フリーレンの 36 話を再生」します。ここが核心です。

同じコンテンツ ID が、すべての TV プラットフォームで動作します：

```bash
stv launch netflix 82656797                          # LG でも Samsung でも Roku でも同じ
stv launch youtube dQw4w9WgXcQ                       # 同じ
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # 同じ
```

プラットフォームごとにディープリンクの形式は異なりますが、ドライバーが自動で変換します。意識する必要はありません。

## 対応プラットフォーム

| プラットフォーム | ドライバー | 接続方式 | ステータス |
|----------------|-----------|---------|-----------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **動作確認済み** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | コミュニティ検証中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | コミュニティ検証中 |
| Roku | HTTP ECP | REST :8060 | コミュニティ検証中 |

LG がメインの検証プラットフォームです。Samsung、Android TV、Roku も動作するはずです——いずれのプラットフォームも開発者モードは不要です——実際の使用感をぜひフィードバックしてください。

## 設定ファイル

設定は `~/.config/smartest-tv/config.toml` に保存されます。`stv setup` 後はこんな感じになります：

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 任意、Wake-on-LAN 用
```

初回接続時に TV のペアリング確認が表示されます。一度承認すればキーが保存され、以降は表示されません。

## 実際の使用例

**深夜 2 時。** ベッドで Claude に「フリーレンの続き、かけて」と言います。リビングのテレビがついて、Netflix が開いて、エピソードが始まります。リモコンには触れていません。目もほとんど開けていません。

**土曜日の朝。** 「子どもに Cocomelon かけて」。YouTube で見つけてテレビで再生されます。朝食の準備を続けてください。コーヒーが冷める前に。

**友達が来たとき。** 「ゲームモード、HDMI 2、音量下げて」。一文で 3 つの変更。誰かが気づく前に完了。

**夕飯の支度中。** 「画面消してジャズかけて」。画面が暗くなり、音楽が流れます。メニューを掘り返す必要なし。

**眠りにつく前。** 「45 分後に消して」。テレビが勝手に消えます。あなたは消えません。

## MCP サーバー

Claude Desktop、Cursor など MCP クライアント向け——これはオプションで、CLI がメインのインターフェースです：

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

18 個のツールを提供。設定は `~/.config/smartest-tv/config.toml` から自動で読み込みます。環境変数は不要です。

## アーキテクチャ

```
あなた（自然言語）
  → AI + スキル（yt-dlp / Playwright / 検索でコンテンツ ID を取得）
    → stv CLI（フォーマット変換と送信）
      → ドライバー（WebSocket / ADB / HTTP）
        → テレビ
```

## コントリビューション

Samsung、Android TV、Roku の**ドライバー**が最もインパクトの大きい貢献ポイントです。[ドライバーインターフェース](src/smartest_tv/drivers/base.py)は定義済みです——`TVDriver` を実装して PR を送ってください。

Disney+、Hulu、Prime Video などの新しいストリーミングサービス向け**スキル**も歓迎します。

## ライセンス

MIT
