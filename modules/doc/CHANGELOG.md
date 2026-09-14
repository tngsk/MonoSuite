# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 自由配置可能なベジェコネクタコンポーネント（`mono-connector`）: 任意要素間（ID指定）および任意座標間（相対パーセント/ピクセル指定）を滑らかに結ぶ3次ベジェ曲線、Space 3-tone連動、ハロー付きラベル、ResizeObserverによる動的追従
- 空間アンカリング用垂直カラーレールコンポーネント（`mono-topic-rail`、`src.extensions.topic_rail`）: `{.topic}` / `{.section}` 見出しに連動した画面左端3pxのDoc 5-toneマルチセグメント表示、ホバーツールチップ、クリックによるスムーズスクロール、印刷時自動非表示
- `mono-section` と `mono-topic-rail` の重なり順制御（フルブリードセクション通過時にカラーラインが背面に潜り込む `z-index: 10` 対 `z-index: 5` のスタッキング階層設計）
- Mono Space直系の見出しマーカー体系（`{.marker}`, `{.heading-marker}`: 72%〜91%帯比率、複数行追従の`box-decoration-break: clone`）
- Space 3トーン（`normal`, `ai`, `warning`）およびDoc 5カラー（`yellow`, `pink`, `green`, `cyan`, `orange`）の相互運用サポート（見出し属性クラスおよびインライン `==強調=={ai}` 双方に対応）
- `mono-compare` における Spacing Trinity（item, group, flow, none）および任意CSS長（16px等）の動的バインドによるカラム間余白（gap）制御
- `mono-link` におけるローカルキャッシュの有効期限管理（TTL: デフォルト7日間、環境変数 `MONO_CACHE_TTL`）およびネットワーク障害時の古いキャッシュへの優雅なフォールバック
- 16px繊細ドットグリッド背景体系（HTML・PDF両対応、CSS Gridコンテンツ領域との幾何学的原点同期）
- `mono-compare` コンポーネント（2要素: 1:1等幅対比、3要素: 1:2:1視線誘導対比の自動判別・明示指定）
- `mono-link` における `MetadataParser`（HTMLParser）による属性順序非依存のOGP抽出、サイズ上限ガード（2MB/8MB）、およびローカルJSONキャッシュ（`.mono-cache`）
- `MediaEmbedder` におけるバイナリのSHA-256コンテンツハッシュによる画像重複排除
- `mono-flow` におけるDOM非依存の幾何計算モジュール（`MonoFlowGeometry`）の抽出
- `minimal` プロファイルによる完全静的ドキュメント出力（Zero-JS、画像直接Data URI埋め込み、コードブロックアンラップ、CSP `script-src 'none'`、未対応コンポーネント検知・中断）
- `BaseComponentParser`、`mono-badge`、`mono-link` における後置属性構文（`{.class #id}`）の共通解釈とマージ機能
- 蛍光マーカー記法（`==テキスト=={color}`）および蛍光アンダーライン記法（`++テキスト++{color}`）の軽量インライン構文（5色対応: yellow, pink, green, cyan, orange）
- 複数行改行に対応したグラデーション強調描画スタイル（`box-decoration-break: clone`）
- プレゼンテーションモード（`-p presentation`）における手書き蛍光ブラシ機能（`mono-brush`）の標準統合

### Changed
- プロジェクト正式名称を Mono から Mono Doc へ刷新
- コンテンツ最大幅を 1800px から 16px の完全な整数倍である 1792px（112グリッド）へアラインメント
- `mono-link` パーサーにおいて明示指定されたラベルをカードタイトルとして最優先し、OGPタイトルをフォールバックとして扱うよう仕様統一
- `mono-export` においてサーバー送信時のHTTPステータスおよびレスポンスJSON内の `status === 'success'` の二重検証を実装
- 手書きブラシのトグル操作を `B` キー（および `Esc` で解除）へと刷新し、マーカー調の蛍光赤ピンク（`rgba(244, 63, 94, 0.75)`）による一定ストローク描画へ変更
- ドキュメント体系（`README.md`, `doc/SKILL.md`, `AGENTS.md`）の実装整合性訂正（PDFコマンド、サーバー起動コマンド、テキストサイズ記法、教育系コンポーネントの仕様等）

### Removed
- スピーカーノート拡張機能（`src.extensions.notes`）およびプレゼンター機能（`mono-presenter`）の完全廃止（Space統合に伴う機能整理）
- 開発保留中（frozen）であった旧フローチャートコンポーネント（`mono-flow`）の完全廃止（自由配置ベジェコネクタ `mono-connector` への統合代替）

### Fixed
- `MediaEmbedder` におけるパス境界検証（`markdown_dir` および `Path.cwd()`）と通常ファイル検証（`is_file()`）を復元し、ディレクトリトラバーサルによる意図しないファイル埋め込みを防止
- `ComponentRegistry` において `ALLOWED_COMPONENTS` リストによる明示的なコンポーネント走査・インポート制限を復元
- PDF出力失敗時の戻り値検証とCLI終了コード（非ゼロ）へのエラー伝播
- HTML出力先とPDF出力先に同一パスが指定された場合の書込み前衝突検出（`ConfigurationError`）および未知プロファイルの検証

## [2.0.0] - 2026-09-03

### Added
- 3×3 ミニマリスト・デザイントークン体系（Typography Trinity: .text-display, .text-body, .text-compact / Spacing Trinity: --space-flow, --space-group, --space-item）
- @interactive オプトイン・パッケージングアーキテクチャ
- Playwright E2E による完全均一余白・流体スケール自動検証
- CLI `--version`（`-V`）フラグ

### Changed
- 全コアWebコンポーネント（mono-layout, mono-section, mono-zoom, mono-theme, mono-link等）のトークン直結リファクタリング
- mono-image の非WebComponentパーサー最適化（アセット探索スキップ）
- フルスクリーン流体CSS Grid（最大1800px、画面占有率92%）

### Deprecated
- mono-brush（将来的な手書き描画機能の非推奨化）

### Removed
- mono-spacer（空ディレクトリ）
- mono-sync（SSE同期用コンポーネント）

### Fixed
- 流体タイポグラフィにおけるvw係数過大によるスケール停止不具合の解消
- 要素間垂直マージンの完全均一化（112px）
