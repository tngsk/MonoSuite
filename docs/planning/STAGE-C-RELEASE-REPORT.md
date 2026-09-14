# Mono Suite 段階C（共通CLIおよび配布セット生成）リリース受入記録

作成日：2026-09-14
判定：合格（Accepted）
対象コミット：feature/stage-c-common-build
検証者：AI Coding Agent

## 1. 段階Cの目的と背景

段階C（最初の統合成果）は、同一のMarkdown原稿から発表用Space HTML、閲覧用Doc HTML、および配布用Doc PDFの3形式を一括生成し、完全性が担保された配布セットとしてアトミックに公開する制作パイプラインを確立することを目的とする。先行する段階B3の契約検証において同定された、見出しIDの言語種による乖離、独自構文の接頭辞衝突、およびアセット欠落時の振る舞い差分を根本的に解消し、原稿の二重管理や生成中断によるファイル破損を排除する堅牢な統合CLI（mono build）を設計・実装した。

## 2. 実装アーキテクチャと主要コンポーネント

段階Cの実装は、単一責任の原則（SRP）および疎結合なパイプライン設計に基づき、src/mono_suite/ 配下に以下のモジュールとして集約した。

1. コマンドライン・インターフェース（src/mono_suite/cli.py）：
   mono build input.md [-o output_dir] [--no-pdf] [--no-offline] の形式で実行可能なルートエントリーポイント。サブコマンド構造を採用し、将来の制作UI（段階D）やプレビュー機能への拡張性を確保した。
2. 共通入力診断（src/mono_suite/diagnostics.py）：
   原稿のパース前に、指定パスのファイル妥当性、参照画像アセットの実在性、および見出し明示IDの重複を検査し、不備がある場合は個別モジュールを起動することなく直ちにビルドを安全遮断（Failure）する。
3. 原稿前処理レイヤー（src/mono_suite/preprocessor.py）：
   明示IDを持たない見出しに対し、出現順に決定論的な一意ID（sec-1, sec-2, ...）を自動注入することで、英数字見出しにおけるDocのスラッグ化とSpaceの連番採番の乖離を根本解消した。また、レンダラーごとの構文安全化（Space向け:::ブロックサニタイズ、Doc向け::ディレクティブ注記化）を行い、構文衝突による異常停止を防止した。
4. ビルドマニフェスト生成（src/mono_suite/manifest.py）：
   ビルド識別子（Build ID）、元原稿のSHA256ハッシュ、生成日時、成果物メタデータ（ファイル名、サイズ、ハッシュ）、および見出し位置対応テーブル（SpaceノードIDとDocアンカーIDの1対1対応）を記録した build-manifest.json を出力する。
5. アトミック公開管理（src/mono_suite/publisher.py）：
   一時作業ディレクトリ（.tmp-{build_id}）内で全成果物を生成・検証したうえで、完成先ディレクトリ（dist/{stem}/）へアトミックに置き換える。万が一生成が失敗または中断した場合でも、既存の正常な配布セットを保護するロールバック機構を実装した。
6. パイプライン統括（src/mono_suite/pipeline.py）：
   上記の診断、前処理、レンダラー呼び出し（Space API直接実行およびDoc CLI実行）、マニフェスト作成、公開を一括制御する。

## 3. 検証結果と客観的エビデンス

整備したパイプライン統合テストスイート（tests/test_stage_c_pipeline.py）および既存の全テストスイートを実行し、以下の完全通過を確認した。

1. 標準サンプル一括ビルド検証（test_pipeline_standard_build_success）：
   examples/standard/document.md から presentation.html（88.2 KB）、document.html（75.5 KB）、document.pdf（79.2 KB）、および build-manifest.json が dist/document/ 配下に正常生成されることを確認。
2. 高速ビルド検証（test_pipeline_no_pdf_option）：
   --no-pdf フラグ指定により、Playwright Chromiumの起動をスキップし、0.3秒未満でHTML2種およびマニフェストが生成されることを確認。
3. 暗黙見出しIDの完全一致検証（test_pipeline_implicit_heading_id_consistency）：
   明示IDを持たない原稿（implicit_heading_id.md）に対し、自動補完されたID（sec-1, sec-2, sec-3, sec-4）がSpaceノードIDおよびDoc見出しタグid属性で100パーセント一致することを確認。
4. 異常系アトミック保護検証（test_pipeline_missing_image_aborts_and_protects_existing）：
   画像欠落原稿をビルドした際、事前診断で直ちにエラー終了（終了コード1）し、既存の配布セットが一切改変されず保護されることを確認。
5. 見出しID重複診断検証（test_pipeline_duplicate_id_aborts）：
   ID重複原稿に対し、事前診断で安全に中断することを確認。
6. リグレッション検証：
   Space単体テスト全67件（Python 54件、Node 13件）、Docテスト全271件（5件スキップ）、段階B3契約テスト全7件がすべて合格。

## 4. 段階Dへの引継ぎ事項

段階Cの完了により、同一原稿から3形式の配布セットを無損失かつアトミックに生成するコアエンジンが確立された。後続の段階D（制作環境の試用版）へ以下の資産を引き継ぐ。

1. 見出し位置対応テーブルの提供：
   build-manifest.json に記録された見出し対応マッピング（headings配列）を活用し、SpaceビューとDocビュー間の相互フォーカス移動を実装する。
2. 高速保存時プレビューの実現：
   --no-pdf モードを利用し、GUIエディターの保存イベント時にミリ秒オーダーでHTML画面プレビューを更新する。
3. エクスポート操作の連動：
   GUI上の配布書き出し操作時にPDFを含む完全配布セット生成をトリガーする。
