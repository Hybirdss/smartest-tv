# smartest-tv

[English](../../README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | **日本語** | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

テレビに話しかけてください。ちゃんと聞いています。

スマートテレビを自然言語で操作する CLI と AI エージェントスキル。Netflix、YouTube、Spotify の深度リンク対応——見たいものを言えば、すぐに再生されます。

> 「葬送のフリーレン 第2期 第8話をかけて」
>
> *Netflix が開いて、そのエピソードが再生されます。*

**LG**、**Samsung**、**Android TV**、**Fire TV**、**Roku** に対応。

## インストール

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # すべて
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # 現在の状態（アプリ、音量、ミュート）
tv launch netflix 82656797         # Netflix で特定コンテンツを再生
tv launch youtube dQw4w9WgXcQ     # YouTube 動画を再生
tv launch spotify spotify:album:x # Spotify を再生
tv volume 25                       # 音量を設定
tv mute                            # ミュートの切り替え
tv apps --format json              # インストール済みアプリ一覧
tv notify "ご飯できたよ〜"          # テレビ画面に通知を表示
tv off                             # テレビをオフ
```

すべてのコマンドで `--format json` が使えます — AI エージェント向けの構造化出力。

## AI エージェントスキル

Claude Code にスキルをインストール：

```bash
cd smartest-tv && ./install-skills.sh
```

あとは Claude に自然言語で話しかけるだけ：

```
あなた: フリーレン 第2期 第8話を Netflix でかけて
あなた: 子どもに YouTube をつけて
あなた: Ye の新アルバムを Spotify でかけて
あなた: 画面を消してジャズをかけて
あなた: おやすみ
```

スキルが面倒な部分を処理してくれます — Netflix のエピソード ID の検索、yt-dlp による YouTube 検索、Spotify URI の解析 — そして `tv` CLI を呼び出してテレビを操作します。

## 深度リンク

これが smartest-tv の核心的な差別化ポイントです。他のツールは Netflix を*開く*だけです。私たちは*フリーレンの36話を再生*します。

同じコンテンツ ID がすべての TV プラットフォームで動作します：

```bash
tv launch netflix 82656797       # LG でも Samsung でも Roku でも同じ
tv launch youtube dQw4w9WgXcQ    # 同じ
tv launch spotify spotify:album:x  # 同じ
```

## 実際の使用例

**深夜2時。** ベッドで Claude に「フリーレンの続き、かけて」と言います。リビングのテレビがついて、Netflix が開いて、エピソードが始まります。リモコンを探す必要はありません。

**土曜日の朝。** 「子どもにココメロンかけて。」YouTube で見つけてテレビで再生されます。朝の準備を続けてください。

**友達が来たとき。** 「ゲームモード、HDMI 2、音量下げて。」一文で3つの変更。

## ライセンス

MIT
