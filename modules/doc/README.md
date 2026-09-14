# Mono Doc

Markdownを、ローカル画像やスタイルが埋め込まれた単一の自己完結型HTMLファイル（Single-File HTML）および高精度PDFに変換するCLIツールです。16pxの繊細なドットグリッドによる知的で構造的なキャンバス上に、プロジェクターでのプレゼンテーションから配布用ドキュメントまで、オフライン環境で完全動作する成果物を生成します。

## インストール

```bash
uv sync
```

## 使い方

```bash
# 基本変換（入力ファイル名.html を出力。同階層に dist/ がある場合は dist/ 内に出力）
uv run main.py document.md

# プレゼンテーション用（オートズーム mono-zoom を有効化）
uv run main.py slides.md -o output.html -p presentation

# 静的ドキュメント用（Zero-JS 出力）
uv run main.py doc.md -o output.html -p minimal

# PDF 書き出し（単一縦長PDFを出力）
uv run main.py document.md -o document.html --pdf document.pdf

# データ収集・同期サーバー起動（オプション）
uv run python -m src.server

# バージョン確認
uv run main.py --version
```

## 記法

### 3×3 デザイントークン & 16px ドットグリッド

Mono Docは、16pxのドットグリッドを基盤とした3段階の流体スケール（Typography Trinity / Spacing Trinity）を採用しています。

```markdown
# 看板見出し {.text-display}

標準本文テキスト
{: .text-body}

凝縮注釈テキスト
{: .text-compact}

::: hbox gap-group
左カラム
:::
右カラム
:::
```

- タイポグラフィ: `.text-display`（大見出し）、`.text-body`（本文）、`.text-compact`（注釈・カラム内）
- 余白: `.gap-flow`（均一112px）、`.gap-group`（64px）、`.gap-item`（23px）
- 背景基盤: 16px四方の精緻なドットグリッドがコンテンツ境界（CSS Grid）と数理的に連動します。

### セクション修飾・Mono Spaceディレクティブ（::構文）

見出しの直下にディレクティブを記述することで、見出しマーカー色や付箋カード枠を適用できます。

```markdown
## 重要なお知らせ {#notice}
::tone warning
::style note
このセクション全体が付箋スタイル（note）のカード枠で囲まれます。
```

- `::tone [neutral | primary | secondary | accent | info | success | warning | error]`
- `::style note`: セクション全体を付箋カード枠として装飾
- `::marker on` / `::marker off`: 見出し蛍光帯の表示切替

### テキスト強調（インラインマーカー・アンダーライン）

本文中の蛍光ペン風マーカー強調（`== ==`）およびアンダーライン強調（`++ ++`）が利用できます。波括弧でトーンやカラー（`primary`, `warning`, `yellow`, `pink`, `green`, `cyan`, `orange`）を指定可能です（省略時は黄色）。

```markdown
これは ==デフォルト黄色マーカー== です。
これは ==AIトーン紫マーカー=={primary} です。
これは ==警告オレンジマーカー=={warning} です。
これは ++シアン下線++{cyan} です。
```

### レイアウトシステム（フェンス構文 :::）

Mono Doc本来の縦スクロール・モノリシックレイアウトおよび3×3スペーシングを制御するクリーンなフェンスブロック記法です。

```markdown
::: hbox gap-group
### 左カラム
左側のコンテンツ。
:::
### 右カラム
右側のコンテンツ。
:::
```

```markdown
::: compare
### Before
従来の問題点
:::
### Intermediate
過渡期の試作品
:::
### After
解決策と成果
:::
```
※3要素比較は1:1:1の等幅並列対比レイアウトとなります。

### 主要コンポーネント・特殊要素

| コンポーネント | 構文例 | 備考 |
|---|---|---|
| 画像 | `![代替テキスト](path/to/image.png)` | 標準Markdown画像（自動Base64化・エラーバナー対応） |
| リッチリンクカード | `::link https://example.com [square]` | OGP自動取得キャッシュ対応、手動上書き（`::link-title`等） |
| 要素間接続線 | `::connect #step1 -> #step2 \| 連携` | ベジェ曲線によるID間接続線描画 |
| 水平・垂直レイアウト | `::: hbox gap-group ... :::` | カラム間を `:::` で区切るグリッドレイアウト |
| 比較レイアウト | `::: compare ... :::` | 2要素（1:1）または3要素（1:1:1等幅並列）比較カード |
| セクション | `::: section padding-group ... :::` | 背景付きグループコンテンツブロック |
| ズーム | `@[zoom]()` または `-p presentation` | プレゼンテーション用オートズーム |
| コードブロック | 通常のコードブロック（```）から自動変換 | ワンクリックコピー・シンタックスハイライト |
| テーマ切替 | `@[theme: corporate]()` | ドキュメントカラーテーマの切替 |

詳細な仕様および規約については [doc/SPECIFICATION.md](doc/SPECIFICATION.md) を参照してください。

## プレゼンテーション操作

- `B`: 蛍光ブラシ描画モード切替（画面上への手書きアノテーション、`Esc` で解除）
