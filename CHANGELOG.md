# Changelog

## 1.0.0b1 — 2026-09-18

### 統合機能（Mono Suite）
- 単一Markdown原稿からの3形式アトミック一括生成（mono build）：
  - 発表用Mono Space HTML（presentation.html）
  - 閲覧用Mono Doc HTML（document.html）
  - 配布・印刷用Mono Doc PDF（document.pdf）
  - ビルドマニフェスト（build-manifest.json）
- 保存監視・高速リビルド開発サーバー（mono dev）：
  - 外部エディター保存を検知し0.4秒台で自動再ビルド
  - SpaceとDocを即座に切り替えるフローティング操作バー（/space, /doc の直接ルーティング）
  - ビルドロック排他制御および更新予約キュー
  - 空きポート自動探索（既定8000〜8010）
  - ワンクリック配布PDF出力API
- 配布セット静的プレビューサーバー（mono serve）：
  - 完成した配布パッケージをローカルHTTP配信
- 共通診断規則（Diagnostics Contract）：
  - 必須画像欠落、数式構文破損、見出しID重複の厳格検知と直前成果物ロールバック保護
  - 見出しID自動補完（明示指定なき場合は出現順連番で1対1マッピング）

### 空間プレゼンテーション（Mono Space）
- 無限キャンバス連動の空間アノテーション（SpatialAnnotations）：
  - カメラのパン・ズーム・回転に完全追従するSVGオーバーレイレイヤー
  - 自由曲線描画モード（Dキー：半透明蛍光ピンク線、カメラ倍率に応じた線幅補正）
  - 矢印描画モード（Aキー：片側矢印、Shift+A：双方向矢印）
  - 描画全消去（Cキー）および通常モード復帰（Escapeキー）
  - アノテーション描画中のキャンバスパン操作排他制御
- 空間付箋（SpatialStickies）：
  - Sキーによるカーソル位置への一時付箋配置とドラッグ移動

### ドキュメント・PDF組版（Mono Doc）
- 独立モジュール化（modules/doc）：
  - uvワークスペース管理による依存関係統一
  - 日本語フォント埋め込みおよびテキスト抽出・コピー性の完全保証
  - 静的ドキュメント内の旧mono-brushコンポーネントを非推奨化（Spaceアノテーションへ移行）

### 検証・作例
- 実務向け技術作例（examples/practical/）：
  - 数式・表・図版・工程・コード・比較を網羅した実践的原稿
- 全自動回帰テストスイート：
  - Suite統合テスト全30件
  - Space単体テスト全71件（Python 57件、Node 14件）
  - Doc単体テスト全271件

## 0.1.0 — 2026-09-11

- Spaceを modules/space に移行し、独立Git履歴を開始。
- 基準コミット：a7cc6beee2cf80c92772986b8e4dff195d6fc1d4。
