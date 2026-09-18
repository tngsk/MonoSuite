# Mono Suite 実践的技術ドキュメント作例

1つのMarkdown原稿（`document.md`）から、発表用Space HTML、閲覧用Doc HTML、および完全自己完結型Doc PDFを一括生成する実務向け作例です。

## 構成

- `document.md`：多段見出し、日本語長文段落、インライン強調・下線、比較分析表、シンタックスハイライトコード、事前レンダリングSVG数式（インラインおよびディスプレイ）、システム構成SVG図版、工程フローディレクティブ、接続線を含む実践原稿。
- `assets/architecture.svg`：統合パイプラインのアーキテクチャ概要ベクター図。
- `assets/benchmark.png`：参照画像アセット。

## 生成コマンド

リポジトリルートから以下のコマンドで配布セット（HTML 2種、PDF、マニフェスト）を生成します。

```sh
uv run mono build examples/practical/document.md -o dist/practical
```

## 制作環境プレビュー

保存監視およびリアルタイム再生成サーバーを起動します。

```sh
uv run mono dev examples/practical/document.md
```
