# Mono Suite 標準共通原稿サンプル

1つのMarkdown原稿（`document.md`）から、発表用Spaceと配布用Docの双方を生成する公式作例です。

## 構成

- `document.md`：見出し、本文、表、コードブロック、引用、画像、数式SVG、比較、工程、接続線を含む標準原稿。
- `assets/overview.png`：参照アセット。

## 生成コマンド

リポジトリルートから以下のコマンドで生成します。

### 1. 発表用プレゼンテーション（Mono Space）

```sh
uv run mono-space examples/standard/document.md -o dist/examples/standard/presentation.html --offline
```

### 2. 配布用ドキュメントおよびPDF（Mono Doc）

```sh
uv run mono-doc examples/standard/document.md -o dist/examples/standard/document.html --pdf dist/examples/standard/document.pdf
```
