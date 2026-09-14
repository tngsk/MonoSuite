# 2026-09-14 調査対象の訂正

ユーザーの指摘により、今回実行した別リポジトリのMonoを、Suiteへ取り込むMono Docとして扱った判断を撤回する。MonoSuiteには `modules/space` のみ存在し、Docの実装は存在しない。Docの所在・版・実装検証は未確認。

## 実際に調査・実行した対象

- ローカルの別リポジトリ `Mono`（MonoSuiteと同じ親ディレクトリ）。
- 設定済みorigin：`https://github.com/tngsk/Mono.git`。
- HEAD：`e84c459a33ba3a0438e520c831a253f0a055d29c`。
- `pyproject.toml` のプロジェクト名：`Mono`、版：`2.0.0`。
- CLI：ルート `main.py` → `src.main.main()` → `src/converter.py`。
- 読み取った主要実装：`src/processors/markdown.py`、`src/processors/pdf.py`、`src/config.py`、`src/extensions/math.py`、layout／connectorのパーサー、定数。
- 同リポジトリの既存Python仮想環境を利用し、core／components／extensions／handlersのテストで264件成功・5件スキップ、e2eで7件成功。
- 今回作成したSpace記法の原稿を同CLIへ渡した。minimalはconnectorを未対応として拒否。standardではHTMLとPDFを一時領域に生成。
- PDFが長尺1ページだったこと、日本語の抽出文字が一部異なること、Space配置指定が本文に残ること等は、この別プログラムと入力の組合せの観測結果。Mono Docの仕様・不具合・統合上の課題と断定できない。

## 誤認の原因

既存のSuite計画文書が別リポジトリの `doc/SPECIFICATION.md` を参照していた。同リポジトリのREADMEと仕様書にも「Mono Doc」と書かれていたが、取り込み対象としての同一性を確認せず、そのソースとCLIが今回のDocだと判断してしまった。名称や近接した保存場所は対象確定の根拠にならない。

## 変更の範囲と扱い

- 別リポジトリのアプリケーションコードは編集していない。調査後のGit作業ツリーもクリーン。
- MonoSuiteへDocコードをコピーしていない。コミット・pushも行っていない。
- Suiteの今回の文書追加から、Doc検証済み・契約案作成済みの誤った状態と未作成レポートへのリンクを除去した。
- `tests/fixtures/integration/` は未採用の検証用原稿。Doc対応を保証するfixtureや受け入れ契約として扱わない。
- Spaceのテスト・生成・ブラウザ検証は、MonoSuite内のSpaceを対象に実施した独立の結果。

追記：Docを別プロジェクトから独立移行し、既存CLI・Playwright PDFを維持する方針はユーザーにより確認済み。今回の別プログラムの検証結果を移行対象Docへ適用しない。現在の作業順序は[開発計画](DEVELOPMENT-PLAN.md)を参照し、まず現リポジトリ内のB1仕様整理を進める。
