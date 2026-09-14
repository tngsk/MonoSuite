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
# Python単体テスト（全54件）
PYTHONPATH=modules/space/src python3 -m unittest discover -s modules/space/tests

# Node幾何計算テスト（全13件）
node --test modules/space/tests/core.test.cjs

# ブラウザテスト用HTML生成
python3 modules/space/tests/build_browser_test.py
```

### 3.2 Mono Doc テストスイート

```sh
# ユニットおよびE2Eテスト（全276件中 271件通過、5件スキップ）
uv run --directory modules/doc pytest
```

注記：`tests/components/test_mono_topic_rail.py` の5件は、トピックライン機能が開発中のため意図的にスキップされています。

### 3.3 Suite 統合契約検証テストスイート

```sh
# 段階B3 統合契約検証テスト（全7件通過）
uv run pytest tests/test_stage_b3_contract.py -v
```

## 4. 単独CLI変換の確認

リポジトリルートから以下の統一コマンドで実行できます。

### 4.1 Space プレゼンテーション生成

```sh
uv run mono-space modules/space/examples/standard/document.md -o dist/presentation.html --offline
```

### 4.2 Doc HTMLおよびPDF生成

```sh
uv run mono-doc modules/doc/doc/SPECIFICATION.md -o dist/spec.html --pdf dist/spec.pdf
```

## 5. トラブルシューティング

- `MODULE_NOT_FOUND`（MathJax関連）：ルートで `npm install` が完了しているか確認してください。
- `NameError: name 'Dict' is not defined`：Python 3.11/3.12 環境下では `typing.Dict` の明示的インポートが必要です（適用済み）。
