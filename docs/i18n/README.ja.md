# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-132%20passed-brightgreen)](tests/)

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | **日本語** | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**テレビに話しかけてください。ちゃんと聞いています。**

| stv なし | stv あり |
|:--------:|:-------:|
| スマホで Netflix アプリを開く | `stv play netflix "Dark" s1e1` |
| 作品を検索する | (自動処理) |
| シーズンを選ぶ | (自動計算) |
| エピソードを選ぶ | (ディープリンク) |
| 再生ボタンをタップ | |
| **約30秒** | **約3秒** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*音声付き全編動画はこちら*

## クイックスタート

```bash
pip install stv
stv setup          # テレビを自動検出してペアリング、これだけ
```

## みんなが stv でやっていること

### 「このリンクをテレビにキャストして」

友達が YouTube リンクを送ってきた。貼り付ける。テレビで再生される。

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### 「パーティー用の曲をキューに追加して」

みんなが自分の曲を追加する。テレビが順番に再生する。

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # 順番に再生開始
stv queue skip                     # 次の曲へ
```

### 「何を見ればいいかわからない」

30 分 Netflix をスクロールするのをやめよう。トレンドを聞いて。おすすめを受け取ろう。

```bash
stv whats-on netflix               # 今のトレンド上位10件
stv recommend --mood chill         # 視聴履歴に基づくおすすめ
stv recommend --mood action        # 気分を変えて別のおすすめ
```

### 「映画を見る雰囲気」

コマンド一つで雰囲気を設定: 音量、通知、コンテンツ。

```bash
stv scene movie-night              # 音量20、シネマモード
stv scene kids                     # 音量15、Cocomelon を再生
stv scene sleep                    # アンビエントサウンド、自動オフ
stv scene create date-night        # 自分だけのシーンを作成
```

### 「寝室のテレビで再生して」

CLI 一つで家中すべてのテレビを操作できる。

```bash
stv multi list                     # living-room (LG), bedroom (Samsung)
stv play netflix "The Crown" --tv bedroom
stv off --tv living-room
```

### 「続きから見たい」

```bash
stv next                           # 最後のエピソードの続きを再生
stv next "Breaking Bad"            # 特定の作品の続きを再生
stv history                        # 視聴履歴を確認
```

## stv と過ごす一日

**午前 7 時** -- 目覚ましが鳴る。「トレンドは？」 `stv whats-on youtube` で朝のニュースを確認。テレビが再生される。

**午前 8 時** -- 子どもたちが起きる。`stv scene kids` -- 音量 15、Cocomelon 開始。

**正午** -- 友達から Netflix リンクが届く。`stv cast https://netflix.com/watch/...` -- テレビで即再生。

**午後 6 時 30 分** -- 仕事から帰宅。`stv scene movie-night` -- 音量を下げて、シネマモード。

**午後 7 時** -- 「何を見ようか？」 `stv recommend --mood chill` -- The Queen's Gambit をおすすめ。

**午後 9 時** -- 友達が来る。みんなが `stv queue add ...` を実行 -- テレビが順番に再生。

**午後 11 時 30 分** -- 「おやすみ。」 `stv scene sleep` -- アンビエントサウンド、45 分後にテレビがオフ。

<details>
<summary><b>stv はどうやって HTTP リクエスト 1 回で Netflix のエピソードを見つけるのか？</b></summary>

Netflix はサーバーサイドで `<script>` タグ内に `__typename:"Episode"` メタデータをレンダリングしています。シーズン内のエピソード ID は連続した整数です。タイトルページへの `curl` リクエスト 1 回で、全シーズンのすべてのエピソード ID を抽出できます。Playwright も、ヘッドレスブラウザも、API キーも、ログインも不要です。

結果は 3 段階でキャッシュされます:
1. **ローカルキャッシュ** -- `~/.config/smartest-tv/cache.json`、即時返却 (~0.1 秒)
2. **コミュニティキャッシュ** -- GitHub raw CDN 経由のクラウドソーシング ID (40 件以上を事前登録)、サーバーコストなし
3. **ウェブ検索フォールバック** -- Brave Search で未知のタイトル ID を自動発見

</details>

<details>
<summary><b>ディープリンク -- stv がテレビと通信する仕組み</b></summary>

各ドライバーがコンテンツ ID をプラットフォーム固有の形式に変換します:

| TV | プロトコル | ディープリンク形式 |
|----|-----------|-----------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

これらを意識する必要はありません。ドライバーが自動で処理します。

</details>

<details>
<summary><b>対応プラットフォーム</b></summary>

| プラットフォーム | ドライバー | ステータス |
|----------------|-----------|----------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **動作確認済み** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | コミュニティ検証中 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | コミュニティ検証中 |
| Roku | HTTP ECP | コミュニティ検証中 |

</details>

## インストール

```bash
pip install stv                 # LG（デフォルト）
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # すべて
```

## あらゆるものと連携

| 連携 | 何が起きるか |
|------|------------|
| **Claude Code** | 「Breaking Bad s1e1 かけて」 -- テレビで再生 |
| **OpenClaw** | Telegram: 「帰ったよ」 -- scene + おすすめ + 再生 |
| **Home Assistant** | ドアが開く -- テレビがオン -- トレンドが表示される |
| **Cursor / Codex** | AI がコードを書く合間に、テレビを操作 |
| **cron / スクリプト** | 午前 7 時: 寝室 TV にニュース。午後 9 時: 子どものテレビをオフ |
| **すべての MCP クライアント** | stdio または HTTP で 32 個のツールを使用 |

### MCP サーバー

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

リモートアクセス用に HTTP サーバーとして実行:

```bash
stv serve --port 8910              # http://localhost:8910/sse で SSE
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## ドキュメント

| | |
|---|---|
| [はじめに](../../docs/getting-started/installation.md) | すべての TV ブランドの初回セットアップ |
| [コンテンツの再生](../../docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [シーン](../../docs/guides/scenes.md) | プリセット: movie-night, kids, sleep, カスタム |
| [マルチ TV](../../docs/guides/multi-tv.md) | `--tv` で複数のテレビを操作 |
| [AI エージェント](../../docs/guides/ai-agents.md) | Claude, Cursor, OpenClaw の MCP 設定 |
| [おすすめ機能](../../docs/guides/recommendations.md) | AI によるコンテンツ推薦 |
| [CLI リファレンス](../../docs/reference/cli.md) | すべてのコマンドとオプション |
| [MCP ツール](../../docs/reference/mcp-tools.md) | パラメーター付き MCP ツール 32 個の全一覧 |
| [OpenClaw](../../docs/integrations/openclaw.md) | ClawHub スキル + Telegram シナリオ |

## コントリビューション

Samsung、Roku、Android TV のドライバーは実機テストが必要です。これらのテレビをお持ちであれば、フィードバックは非常に貴重です。

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 132 テスト、TV 不要
```

お気に入りの作品をコミュニティキャッシュに追加したいですか？[キャッシュへの貢献](../../docs/contributing/cache-contributions.md)をご覧ください。

新しい TV のドライバーを書きたいですか？[ドライバー開発](../../docs/contributing/driver-development.md)をご覧ください。

## ライセンス

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
