# Mono Suite 段階B3 契約検証レポート（Stage B3 Verification Report）

作成日：2026-09-14
判定：合格（Accepted）
対象コミット：feature/stage-b3-verification
検証者：AI Coding Agent

## 1. 検証の目的と背景

段階B3（契約検証）は、同一のMarkdown原稿からMono Space（空間プレゼンテーション）およびMono Doc（配布用ドキュメントHTML・PDF）を安定生成するための共通仕様と診断規準を実証的に確定することを目的とする。先行する段階B1で策定された共通契約案（COMMON-CONTRACT-PROPOSAL.md）と段階B2で独立移行されたDoc実装に基づき、両レンダラーの出力差分、見出し位置の追跡性、数式描画、および異常系エラーハンドリングを網羅的に検証した。この検証を通じて、各モジュールの既存資産を改変することなく、段階C（共通CLIおよび配布セット生成パイプライン）で吸収すべき差分と要件を客観的に同定した。

## 2. 検証環境と実行コマンド

検証はmacOS（darwin 25.3.0）上のPython 3.11仮想環境にて実施した。リポジトリルート直下に配置された統合契約テストスイート（tests/test_stage_b3_contract.py）を実行し、7項目の検証ケースすべてが正常に通過することを確認した。

実行コマンド：
uv run pytest tests/test_stage_b3_contract.py -v

検証結果概要：
- 総合正常系原稿変換（test_shared_contract_document_conversion）：通過
- 明示見出しID一致性（test_heading_id_explicit_consistency）：通過
- 暗黙見出しID連番対応（test_heading_id_implicit_mapping）：通過
- 必須画像欠落ハンドリング（test_missing_image_behavior）：通過
- 見出しID重複ハンドリング（test_duplicate_id_behavior）：通過
- 数式構文異常ハンドリング（test_math_syntax_error_behavior）：通過
- 独自ディレクティブ・コネクタ互換性（test_space_directives_and_connector_in_doc）：通過
総計：7 passed in 3.47s

## 3. 主要な検証結果と実装差分

### 3.1 見出し識別と位置マッピング（Position Mapping）

見出しの識別性検証において、明示ID（{#id}）が付与された場合はSpaceとDocで完全同一の文字列が出力されることを実証した。総合原稿（tests/fixtures/integration/document.md）に含まれる11個の見出し明示ID（shared, content, text, image, math, comparison, present, handout, process, input, build）を検証した結果、Spaceの内部データJSON（nodes配列のid属性）とDocのHTML出力（h1〜h3要素のid属性）が1対1で完全に合致した。

一方、明示IDが指定されていない見出し（tests/fixtures/integration/implicit_heading_id.md）については、両モジュールが共に出現順序の連番インデックスに基づいてIDを生成していることが判明した。Space側は n1, n2, n3, n4 という形式でIDを採番し、Doc側（Python-Markdown toc拡張）は _1, _2, _3, _4 というアンダースコア付き連番を生成する。この規則性により、明示IDが存在しない原稿であっても、出現インデックス k に対する n{k} と _{k} の双方向マッピングテーブルを構築することで、段階DにおけるDocとSpaceの相互フォーカス切り替えが確実に実現できる。

### 3.2 必須画像欠落時の診断差分

画像欠落原稿（tests/fixtures/integration/err_missing_image.md）に対する挙動検証により、両モジュールのエラーハンドリング設計に明確な差異が確認された。Spaceは存在しない画像パスに対して直ちにFileNotFoundErrorを発生させ、終了コード1で処理を中断（生成失敗）する。これに対し、現行のDocはWARNINGログ（メディアファイルが見つかりません）を出力したうえで、0件の埋め込みとして処理を継続し、終了コード0でHTMLを生成する。

この結果に基づき、段階Cの一括生成パイプラインでは、Doc実行前に共通バリデーションとしてアセットの存在確認を実施し、必須画像が欠落している場合は配布セットの更新を行わず安全に中断（Failure）する制御を設ける方針を確定した。

### 3.3 見出しID重複時の診断差分

重複した明示IDを指定した原稿（tests/fixtures/integration/err_duplicate_id.md）において、Spaceは構文解析時にID重複例外（ID重複 dup-target）を発生させ終了コード1で停止した。一方、DocはPython-Markdownのattr_list拡張により同一のid属性を複数要素に出力したまま終了コード0で処理を完了した。HTML仕様上および相互参照（::connectやURLアンカー）の観点からID重複は致命的欠陥となるため、段階Cの共通検査規則として原稿解析時に重複IDを検知し、ビルドを安全に遮断する仕様を採用する。

### 3.4 数式描画と構文エラー時の挙動

数式描画の検証において、正常なTeX数式（インラインおよびディスプレイ）はSpace・DocともにMathJaxによる事前SVG変換が適用され、外部フォントやJavaScriptに依存しない自己完結型SVGとして正常に出力された。構文エラーを含む数式原稿（tests/fixtures/integration/err_math_syntax.md）に対しては、SpaceがMathErrorにより終了コード1でビルドを中断するのに対し、DocはMathJaxのエラー表示用SVG（data-mjx-error="Missing close brace"）をインライン埋め込みして終了コード0で完了した。

### 3.5 独自ディレクティブと接続線の互換性

Space独自のレイアウト指定（::layout compare, ::layout flow）は、Doc側において通常の段落テキスト（<p>タグ）として出力され、本文の通読順序や内容を欠落させることなく保持されることを確認した。特筆すべき点として、接続線記法（::connect a -> b | ラベル）はDoc側でも既にmono-connectorパーサーが実装されており、カスタム要素 <mono-connector from="a" to="b" label="ラベル"> として構造化されて出力されることが判明した。Docの標準スタイルシートでは当要素が display: none として制御されており、印刷面を汚すことなく構造情報を内包できている。

### 3.6 発覚した未知の課題と環境制約

契約検証の過程において、単独モジュール運用時には潜在化していた以下の4つの技術的課題を客観的に同定した。

1. 英数見出しにおけるID生成ロジックの乖離：
   日本語見出しではSpace（n1, n2, ...）とDoc（_1, _2, ...）が共に出現順連番を生成したが、英数字を含む見出し（例: ## Section A）ではDocのPython-Markdown toc拡張が文字列スラッグ（id="section-a"）を自動生成するため、連番による暗黙マッピングが成立しない。
2. ディレクティブ接頭辞の衝突によるSpaceのクラッシュ：
   Spaceのパーサーは行頭の :: で始まる行をディレクティブ判定するため、Doc固有のブロック構文（::: note や ::: compare 等）が混入した際に 不明なディレクティブ 例外を送出してビルドが停止する。
3. Doc内部テストのカレントディレクトリ依存性：
   modules/doc/tests/components/ 配下の5つのテストファイルが相対パス（src/components/...）を直接importlibで読み込んでいるため、リポジトリルートからのpytest実行時にファイル未検出エラーが発生する。
4. distディレクトリ存在によるPDF出力テストの干渉：
   カレントディレクトリ直下に dist ディレクトリが存在すると、ConversionConfig の resolve_pdf_output_file() が dist/test.pdf を返し、modules/doc の単体テスト（test_pdf.py）が1件失敗する。

## 4. 段階C（共通CLI・配布セット生成）への引継ぎ要件

契約検証の結果を踏まえ、段階Cの実装において以下の共通仕様を確定する。

1. 前処理レイヤーによる明示ID（{#sec-k}）の自動補完：
   見出しIDの言語・文字種による乖離（英数スラッグとSpace連番）を根本解決するため、共通パイプラインの前処理層で明示IDのない見出しへ一意な決定論的IDを自動注入してから両レンダラーへ渡す。
2. 共通入力バリデーション（ビルド前診断）：
   Markdown原稿の解析前に、参照画像の存在確認および見出し明示IDの重複チェックを共通層で実行し、不備がある場合はSpaceおよびDocの個別処理を起動することなく終了コード1で中断する。
3. 構文サニタイズおよび相互変換：
   Doc固有ブロック記法（:::）のSpace混入によるクラッシュ、およびSpaceディレクティブ（::）のDoc本文露出を防ぐため、共通パイプラインで各レンダラーの入力前に安全な構文調整を行う。
4. 位置マッピングテーブルの生成：
   一括ビルド時に、見出しごとの明示ID、階層レベル、および出現順インデックスを対応づけた build-manifest.json を出力し、段階DのUI連携データとする。
5. テスト実行環境の整流化（段階C着手前）：
   Docコンポーネントテストのimportパスを __file__ 基準の絶対解決へ改訂し、リポジトリルートからの全スイート一括テスト実行を保証する。
6. PDF出力の標準化：
   現行Docが提供する長尺1ページ（Webスクロール追従）PDFをSuiteの標準配布物として位置づけ、A4定型改ページ組版は追加オプションとして整理する。

## 5. 結論と合意

段階B3における検証実験により、SpaceおよびDocの両モジュールが同一のMarkdown原稿から互いの主要機能を損なうことなくHTMLおよびPDFを生成できる実効性が証明された。同定された振る舞いの差異および未知の課題はすべて共通パイプライン層（段階C）で吸収・解消可能な範囲に収まっており、段階Bの全責務を完了し段階Cの設計へ移行する。
