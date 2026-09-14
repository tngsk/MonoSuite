# Mono Doc 独立移行受入記録（段階B2）

実施日：2026-09-14
状態：段階B2完了。受入基準達成。

## 1. 移行元情報

- 移行元パス：`/Users/ngsklab/Code/Mono`
- 設定済みorigin：`https://github.com/tngsk/Mono.git`
- 参照コミットハッシュ：`e84c459a33ba3a0438e520c831a253f0a055d29c`
- バージョン：2.0.0
- ライセンス：MIT License（`modules/doc/LICENSE` として保全）

## 2. 取り込み先とファイル構成

MonoSuiteの `modules/doc/` 配下へ以下のコア資産を取り込み、不要なキャッシュ・仮想環境（`.git`, `.venv`, `.pytest_cache`, `.mono-cache`, `.coverage`, `.vscode`, `.zed`, `.jules`, `.agents`）を除外した。

- ソースコード：`modules/doc/src/`
- テストスイート：`modules/doc/tests/`
- ドキュメント・仕様：`modules/doc/doc/`
- CLI入口：`modules/doc/main.py`
- パッケージ設定：`modules/doc/pyproject.toml`, `modules/doc/uv.lock`, `modules/doc/package.json`, `modules/doc/package-lock.json`, `modules/doc/config.toml`

## 3. パッケージ・実行環境の統合管理

リポジトリルートに `uv` ワークスペース（ルート `pyproject.toml`）を導入し、`modules/space` および `modules/doc` を統合管理する構成を確立した。

```toml
[project]
name = "monosuite"
version = "0.1.0"
description = "Mono Suite - Integrated authoring environment for presentation and handout"
readme = "README.md"
requires-python = ">=3.14"
dependencies = []

[tool.uv.workspace]
members = ["modules/*"]
```

## 4. 受入検証結果

### 4.1 modules/doc ユニット・E2Eテスト

Node依存関係（MathJaxを含む379パッケージ）の復元およびPlaywright Chromiumの配備を行い、テストスイートを実行した。

- 実行コマンド：`uv run --directory modules/doc pytest`
- 結果：271 passed, 5 skipped (6.08s)
- 移行前と同等の全件合格を確認。

### 4.2 modules/doc CLIおよびPlaywright PDF生成

代表Markdown（見出し、本文、数式、コードブロック、表）を用いた出力検証を実施した。

- 実行コマンド：`uv run --directory modules/doc main.py sample.md -o sample.html --pdf sample.pdf`
- 結果：
  - `sample.html`（Single-File HTML、48.6 KB）正常生成
  - `sample.pdf`（Playwright Chromium経由、46 KB）正常生成

### 4.3 modules/space 既存機能の回帰検証

Doc移行後もSpace側の既存機能およびテストスイートに影響がないことを確認した。

- Python単体テスト：全54件合格（`PYTHONPATH=src python3 -m unittest discover -s tests`）
- Node幾何計算テスト：全13件合格（`node --test tests/core.test.cjs`）
- ブラウザテストHTML動的生成：正常終了（`python3 tests/build_browser_test.py`）

## 5. 次の段階（段階B3）

段階B2が完了したため、今後は段階B3（契約検証）へ移行する。
ルートの `docs/planning/COMMON-CONTRACT-PROPOSAL.md` に規定された要素対応表および診断規則に基づき、共通検証原稿を用いたSpaceとDocのクロスバリデーションを実施する。
