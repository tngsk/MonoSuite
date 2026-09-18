# Mono Suite 開発・検証環境セットアップガイド

更新日：2026-09-14
対象：Mono Suite開発者・検証担当者

## 1. 前提環境

- OS：macOS（推奨）またはLinux
- Python：3.11以上（3.11, 3.12, 3.14 で動作検証済み）
- Node.js：v20以上（v26系で検証済み）
- パッケージマネージャー：uv（Python）、npm（Node.js）

## 2. 初回セットアップ手順

リポジトリルートで以下のコマンドを実行します。

```sh
# 1. Python仮想環境と全モジュール依存関係の同期（uv ワークスペース）
uv sync --all-packages

# 2. Node.js依存パッケージのインストール（npm ワークスペース）
npm install

# 3. Playwright用ブラウザ（Chromium）の配備（DocのPDF出力・E2E用）
uv run playwright install chromium
```

## 3. テスト実行手順

### 3.1 Mono Space テストスイート

```sh
# Python単体テスト（全57件）
uv run --project modules/space pytest modules/space/tests/

# Node幾何計算・アノテーションテスト（全14件）
node --test modules/space/tests/core.test.cjs
```

### 3.2 Mono Doc テストスイート

```sh
# ユニットおよびE2Eテスト（全276件中 271件通過、5件スキップ）
uv run --directory modules/doc pytest
```

注記：`tests/components/test_mono_topic_rail.py` の5件は、トピックライン機能が開発中のため意図的にスキップされています。

### 3.3 Suite 統合テストスイート

```sh
# Suite統合テスト一括実行（全30件通過）
uv run pytest tests/
```

## 4. CLI変換およびプレビューサーバーの確認

リポジトリルートから以下の統一コマンドで実行できます。

### 4.1 Mono Suite 一括ビルド（標準実行）

単一原稿から配布セット（Space HTML、Doc HTML、Doc PDF、マニフェスト）をアトミック生成します。

```sh
# 3形式＋マニフェストの一括生成
uv run mono build examples/standard/document.md

# 高速プレビュー生成（PDF出力をスキップ）
uv run mono build examples/standard/document.md --no-pdf
```

### 4.2 Mono Suite リアルタイム制作プレビュー

外部エディター保存監視、0.4秒台自動リビルド、Space/Doc位置同期UIを起動します。

```sh
# 開発サーバー起動（ブラウザ自動表示）
uv run mono dev examples/standard/document.md
```

### 4.3 配布セット静的プレビュー

完成した配布セットを静的配信します。

```sh
uv run mono serve dist/document/
```

### 4.4 Space 個別プレゼンテーション生成

```sh
uv run mono-space modules/space/examples/standard/document.md -o dist/presentation.html --offline
```

### 4.5 Doc 個別HTMLおよびPDF生成

```sh
uv run mono-doc modules/doc/doc/SPECIFICATION.md -o dist/spec.html --pdf dist/spec.pdf
```

## 5. VS Code タスク連携（エディター統合仕様）

Mono Suite は、Visual Studio Code を用いた執筆・開発を円滑化するため、`.vscode/tasks.json` を標準の開発仕様として配備しています。エディター上でコマンドラインを手動入力することなく、ショートカットやコマンドパレットから各処理を直接呼び出すことができます。

### 5.1 登録タスク一覧

| タスク名 | コマンド | 種別 | 役割・用途 |
|---|---|---|---|
| MonoSuite: Build (Active File) | `uv run mono build "${file}"` | build (既定) | 開いているMarkdown原稿を一括ビルド（PDF含む完全配布セット生成） |
| MonoSuite: Build Standard Example | `uv run mono build examples/standard/document.md` | build | 公式標準サンプル原稿の一括ビルド |
| MonoSuite: Build Standard Example (No PDF) | `uv run mono build examples/standard/document.md --no-pdf` | build | PDF生成を省略した標準サンプルの高速プレビュービルド |
| MonoSuite: Dev Server (Active File) | `uv run mono dev "${file}"` | バックグラウンド | 開いている原稿を対象に保存監視・リアルタイム開発サーバーを起動 |
| MonoSuite: Dev Server Standard Example | `uv run mono dev examples/standard/document.md` | バックグラウンド | 標準サンプル原稿を対象に開発サーバーを起動 |
| MonoSuite: Serve Output | `uv run mono serve dist/document/` | バックグラウンド | 生成された配布セットディレクトリの静的配信サーバーを起動 |
| MonoSuite: Run Tests | `uv run pytest` | test | テストスイート（pytest）の一括実行 |

### 5.2 操作方法

1. 既定のビルド実行：
   対象の原稿ファイルを開いた状態で、キーボードショートカット `Cmd+Shift+B`（macOS）または `Ctrl+Shift+B`（Windows/Linux）を押下すると、`MonoSuite: Build (Active File)` が直ちに実行されます。
2. その他のタスク実行：
   `Cmd+Shift+P`（macOS）または `Ctrl+Shift+P` から `Tasks: Run Task`（タスクの実行）を選択し、一覧から目的のタスク名を選択して実行します。
3. npm / package.json 連携：
   ルートの `package.json` にも同等のスクリプト（`npm run mono:build`、`npm run mono:dev` 等）が登録されており、VS Code のタスク検出機能や外部スクリプトランナーからも同一の操作系を利用できます。

## 6. トラブルシューティング

- `MODULE_NOT_FOUND`（MathJax関連）：ルートで `npm install` が完了しているか確認してください。
- `NameError: name 'Dict' is not defined`：Python 3.11/3.12 環境下では `typing.Dict` の明示的インポートが必要です（適用済み）。
