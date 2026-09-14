# Mono Suite

同じMarkdown原稿から、Spaceで発表し、Docで配布資料を生成する制作環境を開発しています。

現在、個別のモジュールとして Mono Space（空間プレゼンテーション）および Mono Doc（ドキュメント・PDF組版）が実行可能です。同一原稿からの共通出力処理（段階C）およびSuite制作UI（段階D）は順次開発中です。

## ドキュメント体系

### Suite統合・設計（正本）
- [Suite開発計画](docs/planning/DEVELOPMENT-PLAN.md)：段階B〜Fのロードマップと完了条件
- [共通契約案（段階B1）](docs/planning/COMMON-CONTRACT-PROPOSAL.md)：本文・素材・数式・比較等の対応表案と診断規則
- [開発・リリース方針](docs/planning/RELEASE-STRATEGY.md)：製品位置づけ、モジュール責務、受入判定基準
- [Doc仕様レビュー](docs/planning/MONO-DOC-INTEGRATION.md)：Doc統合前の照合候補と未決事項
- [Doc独立移行受入記録（段階B2）](docs/planning/STAGE-B2-MIGRATION-REPORT.md)：移行元コミット、検証結果、受入判定
- [環境セットアップガイド](docs/guides/ENVIRONMENT-SETUP.md)：Python・Node依存同期とテスト実行手順
- [調査対象の訂正記録](docs/planning/INVESTIGATION-CORRECTION.md)：以前の調査誤認に関する経緯記録

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

### Mono Space（プレゼンテーションHTML生成）

```sh
cd modules/space
python3 build.py examples/standard/document.md -o dist/presentation.html --offline
```

### Mono Doc（ドキュメントHTMLおよびPDF生成）

```sh
uv run --directory modules/doc main.py doc/SPECIFICATION.md -o dist/spec.html --pdf dist/spec.pdf
```

生成されたHTMLやPDFはブラウザやPDFビューアで直接開いて確認できます。

