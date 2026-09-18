# Mono Suite

同じMarkdown原稿から、Spaceで発表し、Docで配布資料を生成する制作環境を開発しています。

現在、Mono Suite 統合CLI（mono）により、単一原稿から発表用Space HTML、閲覧用Doc HTML、配布用Doc PDF、および build-manifest.json をアトミックに一括生成できるほか、保存監視・超高速自動リビルド・直接ビュー切り替え（位置同期は保留）を備えたローカル制作サーバー（mono dev）や静的プレビューサーバー（mono serve）を利用できます。個別のモジュール（mono-space, mono-doc）としての単独実行も可能です。

## ドキュメント体系

### Suite統合・設計（正本）

- [Suite開発計画](docs/planning/DEVELOPMENT-PLAN.md)：段階B〜Fのロードマップと完了条件
- [段階Dリリース受入記録](docs/planning/STAGE-D-RELEASE-REPORT.md)：制作環境UI、保存監視、直接切り替えとフローティングナビ、静的配信の実証結果
- [段階Cリリース受入記録](docs/planning/STAGE-C-RELEASE-REPORT.md)：共通CLI、アトミック配布セット、マニフェストの実証結果
- [段階B3契約検証レポート](docs/planning/STAGE-B3-VERIFICATION-REPORT.md)：位置マッピング、診断差分、互換性の実証結果と合格判定
- [共通契約仕様書（段階B3確定）](docs/planning/COMMON-CONTRACT-PROPOSAL.md)：本文・素材・数式・比較等の確定対応表と診断規則
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

### Mono Suite 一括ビルド（標準実行）

同じMarkdown原稿 [examples/standard/document.md](examples/standard/document.md) から、配布セット（Space HTML、Doc HTML、Doc PDF、および build-manifest.json）をアトミックに一括生成します。

```sh
# 3形式＋マニフェストの一括生成（dist/document/ 配下に集約）
uv run mono build examples/standard/document.md

# 高速プレビュー生成（PDF出力をスキップして即座に完了）
uv run mono build examples/standard/document.md --no-pdf
```

### Mono Suite リアルタイム制作プレビュー（mono dev）

外部エディターでのMarkdown原稿保存を監視し、0.4秒台で自動リビルドしてブラウザプレビューを即座に更新します。Monoコンセプトに基づいた繊細でフラットなフローティング操作バーにより、Space（発表スライド）とDoc（配布文書）を直接瞬時に切り替えられ（位置同期は保留、ページ再読み込み更新）、空きポートの自動探索や保存更新の予約再実行機構を備えます。画面上のボタンからいつでも完全な配布PDFを出力できます。

```sh
# 原稿の変更を監視し、リアルタイムプレビューサーバーを起動（ブラウザが自動起動します）
uv run mono dev examples/standard/document.md
```

### 配布セットの静的プレビュー（mono serve）

完成した配布セットディレクトリをブラウザで閲覧・確認するための静的配信サーバーを起動します。

```sh
# 生成済み配布セットの静的プレビューサーバーを起動
uv run mono serve dist/document/
```

### モジュール単独実行

各モジュールを個別CLIとして直接呼び出すことも可能です。

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

### Visual Studio Code での利用

リポジトリ直下の `.vscode/tasks.json` により、エディターから直接ビルドやプレビューを起動できます。

- 既定のビルド：原稿ファイルを開いた状態で `Cmd+Shift+B`（macOS）または `Ctrl+Shift+B`（Windows/Linux）を押下すると、アクティブ原稿の完全配布セットが一括生成されます。
- プレビュー起動：`Cmd+Shift+P` > `Tasks: Run Task` から `MonoSuite: Dev Server (Active File)` を選択すると、リアルタイム制作サーバーがバックグラウンドで起動します。

## テスト・契約検証

```sh
# 段階D 制作環境統合テストスイート（全8件）
uv run pytest tests/test_stage_d_authoring.py -v

# 段階C 配布パイプライン回帰テストスイート（全7件）
uv run pytest tests/test_stage_c_pipeline.py -v

# 段階B3 統合契約検証テストスイート（全8件）
uv run pytest tests/test_stage_b3_contract.py -v

# モジュール個別テストの実行手順は 環境セットアップガイド を参照してください。
```
