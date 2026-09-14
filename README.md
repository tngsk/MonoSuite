# Mono Suite

同じMarkdown原稿から、Spaceで発表し、Docで配布資料を生成する制作環境を開発しています。

現在、個別のモジュールとして Mono Space（空間プレゼンテーション）および Mono Doc（ドキュメント・PDF組版）が実行可能です。同一原稿からの共通出力処理（段階C）およびSuite制作UI（段階D）は順次開発中です。

## ドキュメント体系

### Suite統合・設計（正本）
- [Suite開発計画](docs/planning/DEVELOPMENT-PLAN.md)：段階B〜Fのロードマップと完了条件
- [共通契約仕様書（段階B3確定）](docs/planning/COMMON-CONTRACT-PROPOSAL.md)：本文・素材・数式・比較等の確定対応表と診断規則
- [段階B3契約検証レポート](docs/planning/STAGE-B3-VERIFICATION-REPORT.md)：位置マッピング、診断差分、互換性の実証結果と合格判定
- [Doc独立移行受入記録（段階B2）](docs/planning/STAGE-B2-MIGRATION-REPORT.md)：移行元コミット、検証結果、受入判定
- [開発・リリース方針](docs/planning/RELEASE-STRATEGY.md)：製品位置づけ、モジュール責務、受入判定基準
- [Doc仕様レビュー](docs/planning/MONO-DOC-INTEGRATION.md)：Doc統合前の照合候補と未決事項
- [環境セットアップガイド](docs/guides/ENVIRONMENT-SETUP.md)：Python・Node依存同期とテスト実行手順
- [調査対象の訂正記録](docs/planning/INVESTIGATION-CORRECTION.md)：以前の調査誤認に関する経緯記録

### 共通サンプル
- [標準サンプル原稿](examples/standard/document.md)：Space発表とDoc配布の両立を実証する公式サンプル（[解説](examples/standard/README.md)）

### モジュール
- [Mono Space（空間プレゼンテーション）](modules/space/README.md)
  - [記法ガイド](modules/space/docs/SYNTAX.md)
  - [設計仕様](modules/space/docs/DESIGN.md)
  - [開発・検証状況](modules/space/docs/DEVELOPMENT.md)
  - [Space移行記録](modules/space/docs/MIGRATION.md)
- [Mono Doc（ドキュメント・PDF組版）](modules/doc/README.md)
  - [Doc仕様書](modules/doc/doc/SPECIFICATION.md)
  - [日本語PDFコード組版仕様](modules/doc/doc/JAPANESE_PDF_CODE_TYPOGRAPHY.md)


## 試す

初回環境セットアップは [環境セットアップガイド](docs/guides/ENVIRONMENT-SETUP.md) を参照してください。

### Suite共通サンプル（Space・Doc両対応）

同じMarkdown原稿 [examples/standard/document.md](examples/standard/document.md) から、プレゼンテーション用HTML、閲覧用HTML、配布用PDFを生成できます。

```sh
# Mono Space（空間プレゼンテーションHTML生成）
uv run mono-space examples/standard/document.md -o dist/examples/standard/presentation.html --offline

# Mono Doc（ドキュメントHTMLおよびPDF生成）
uv run mono-doc examples/standard/document.md -o dist/examples/standard/document.html --pdf dist/examples/standard/document.pdf
```

### モジュール個別実行（内部仕様・フィクスチャ）

各モジュール内部の独自フィクスチャや仕様書も独立して処理できます。

```sh
# Mono Space 開発用フィクスチャ
uv run mono-space modules/space/examples/standard/document.md -o dist/space-fixture.html --offline

# Mono Doc 内部仕様書
uv run mono-doc modules/doc/doc/SPECIFICATION.md -o dist/doc-spec.html --pdf dist/doc-spec.pdf
```

生成されたHTMLやPDFはブラウザやPDFビューアで直接開いて確認できます。

## テスト・契約検証

```sh
# 段階B3 統合契約検証テストスイート（全7件）
uv run pytest tests/test_stage_b3_contract.py -v

# モジュール個別テストの実行手順は 環境セットアップガイド を参照してください。
```
