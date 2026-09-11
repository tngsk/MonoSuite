# Mono Space

Markdown文書を広いキャンバスへ配置し、話題に近づいて説明するプレゼンテーションです。更新日：2026-09-10。

- [記法ガイド](SYNTAX.md)
- [設計仕様](DESIGN.md)
- [開発・検証状況](DEVELOPMENT.md)
- [移行する方はこちら（手順・検証状況・対象ファイル）](docs/MIGRATION.md)
- [移行後の開発計画](docs/planning/DEVELOPMENT-PLAN.md)
- [通常Markdownの例](examples/standard/document.md) / [表示](examples/standard/presentation.html)
- [詳細レイアウトの例](example.md) / [表示](presentation.html)
- [Craft教材](examples/audacity/presentation.html)
- [Decksetサンプル](examples/deckset-basics/presentation.html)

通常・数式サンプルは移行用の最小構成です。詳細例・Craft教材・Deckset例は現在の開発環境の参考資料で、新規リポジトリへの自動移行対象には含めません。表示HTMLは生成物です。

## 生成

Python 3.9以降の標準ライブラリで生成します。このフォルダーで実行してください。

```sh
python3 build.py examples/standard/document.md -o presentation.html --offline
python3 build.py "教材.textbundle" --from craft -o examples/craft/presentation.html --offline
python3 build.py "Deckset basics.md" --from deckset -o examples/deckset/presentation.html --offline
python3 build.py "Mono教材.md" --from mono -o examples/mono/presentation.html --offline
```

生成HTMLにはCSS・JavaScript・画像を埋め込みます。閲覧時のランタイムやサーバーは不要です。PDF出力はありません。

リッチリンクは通常生成時にOGPを取得・キャッシュします。`--offline` は通信なし、`--refresh-links` は再取得です。同時指定時はオフラインが優先します。リンクを開く操作は外部サイトへ移動します。

## 共通の文書ルール

通常のMarkdownでは、`#` が文書タイトル、`##` が章、`###` が話題、`####` 以下が本文内小見出しです。章を横、話題を縦に配置します。空行で段落を分け、連続する画像を最大3列で並べます。

セクション幅は768px、本文の最大読み幅は512pxです。画像・表・コードはセクション幅を使用します。高さだけを内容に応じて測定し、グリッドに沿って配置します。見出しの深さや文章量で文字を縮小しません。

`::layout` は指定した場所の子要素配置だけを変更します。直下の見出しは配置要素となりますが、本文幅・段落・文書全体の見出しルールは変えません。互換モードはありません。

現時点のテーマはStandard相当の一種類です。幅・グリッド・密度は `src/layout.js`、文字・色・余白は `src/styles.css` が管理します。テーマ切り替えUIは追加していません。

## 操作

| 操作 | 動作 |
|---|---|
| 0 | 全体表示 |
| 1〜9 | 説明順の1〜9番目へ移動（導入を含む） |
| ← / → / Space | 前後の話題へ移動 |
| クリック | 話題へフォーカス。画像・表はその幅へフォーカス。コードは上端の言語表示部分からフォーカス |
| ドラッグ・スクロール | キャンバス移動 |
| ＋ / − | ズーム |
| O | 全体表示とフォーカスを往復 |
| H / 右上の⋯ | メニューの展開・収納 |
| S | カーソル位置に一時付箋を作成 |

入力中は移動ショートカットを抑制します。付箋は編集・移動可能で、保存せずページを閉じると消えます。

フォーカスは横幅優先、上端は画面高さの15%です。画像フォーカスは所属見出しを縦位置の基準にします。フォーカス外の内容は25%に薄め、枠や丸のインジケーターは表示しません。近距離・ほぼ同倍率は控えめなパン、それ以外はフェードです。操作ガイドで動きを抑制できます。

メニューはフォーカス時に収納し、明示操作で展開します。目次は文字中心、ミニマップは初期状態で非表示です。

## インポート

インポーターは独立したPythonモジュールです。外部プラグイン実行や自動探索は行いません。CraftとDecksetは通常モードへ、Monoも共通の文書ルールへ接続します。

Craft / Decksetでは変換Markdown、ローカル画像のコピー、変換レポートを出力します。原本は変更しません。CraftはMarkdown形式TextBundleの単独行画像に対応します。Decksetはスライド区切り、画像の左右配置、ノート分離に対応します。元アプリの全機能・テーマの再現ではありません。対応外の動画や表示設定はレポートに残します。


番号付きリストは通常の `1. 本文` で記述します。最上位の番号を薄いグレーの丸付き数字で表示し、開始番号を保持します。入れ子は通常の番号表示です。背景・影・アニメーションは付けません。


## 数式（生成時SVG）

本文中は `$T=1/f$`、独立した数式は `$$式$$` または独立行の `$$` で囲みます。[数式デモ](examples/math/presentation.html) / [入力Markdown](examples/math/document.md)。

数式を初めて生成する環境ではNode.jsと次の初期設定が必要です。数式のない文書には不要です。

```sh
npm ci --ignore-scripts
python3 build.py examples/math/document.md -o examples/math/presentation.html --offline
```

MathJax 3.2.2のbase・AMS機能でSVGを生成し、TeX・表示形式・描画バージョンをキーとして入力フォルダーの `.spatial-cache/math/` に保存します。同一数式は再利用します。`--offline` でもインストール済みのエンジンで数式を生成できます。依存パッケージの取得は初期設定時のみ必要です。

生成HTMLはSVGと元のTeXを含み、閲覧時にNode.js・MathJax・外部フォントは不要です。数式をクリックするとTeXをコピーします。クリップボードが使えない場合は選択可能なTeXを表示します。エラー時は行番号と元の式を報告し、既存の出力HTMLを置き換えません。
