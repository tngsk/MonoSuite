# Mono Suite 段階F リリース受入記録

更新日：2026-09-18
状態：段階F（空間連動アノテーション：ドロー自由描画およびアロー矢印描画の実装、Doc旧mono-brushの整理）完了。本報告書をもって正式受入とする。

## 1. 段階Fの目的と達成状況

プレゼンテーションおよび講義発表時における思考の共有・強調を支援するため、Mono Space（modules/space）の無限キャンバス（ワールド座標系）と完全連動する空間アノテーションレイヤーを新設した。また、静的ドキュメント主体のMono Docに存在していた旧mono-brushコンポーネントを非推奨化し、発表時の一時的アノテーション基盤をMono Spaceへ集約・再設計した。

| 検証項目 | 計画仕様 | 実装・検証結果 | 判定 |
|---|---|---|---|
| 空間連動SVGレイヤー | #world 内でパン・ズームに完全追従するSVGオーバーレイ | #annotations-layer を配備し、ワールド座標系で描画されるため視点移動・倍率変更に完全追従することを実証 | 合格 |
| ドロー機能（自由曲線） | マウスドラッグによる自由な軌跡描画 | Dキーによるトグル起動、ポインター追従パス生成、半透明蛍光ピンク描画を実装 | 合格 |
| アロー機能（片側・双方向） | 始点から終点へ要素を繋ぐ矢印描画 | Aキー（片側矢印）、Shift+A（双方向矢印）によるSVGマーカー付き直線描画を実装 | 合格 |
| 操作モードと入力排他 | キャンバスのパン（ドラッグ）との干渉抑止 | アノテーションモード中はポインターキャプチャによりSpatialInputのパン移動を排他制御 | 合格 |
| セッション限定非永続性 | 原稿Markdownや配布PDFへの非侵襲性 | DOM/SVGセッション内のみに保持され、原稿やPDFへ影響を与えない揮発性を担保。Cキーでの即時全消去をサポート | 合格 |
| 旧mono-brushの整理 | Doc側コンポーネントのステータス更新 | modules/doc/src/components/mono-brush/manifest.json のステータスを deprecated に更新し移行先を明記 | 合格 |

## 2. 実施した実装と改善

1. 空間アノテーションモジュールの新設（modules/space/src/mono_space/web/annotations.js）：
   ビューポート座標からキャンバスのワールド座標への逆変換ロジックを実装し、SVGのdefs（始点・終点マーカー）と連動したベクター描画エンジンを構築した。自由曲線（formatPath）と矢印（formatArrow）の2つの幾何生成ルーチンを備え、キーボードショートカット（Dでドロー、Aでアロー、Escでモード解除、Cで全消去）により直感的に切り替え可能とした。

2. スタイリングと視認性の確保（modules/space/src/mono_space/web/styles.css）：
   #annotations-layer を z-index: 4（接続線の上、付箋・HUDの下）に配置し、視認性を維持しつつ操作要素を妨げない構造とした。ドロー線には高視認性の蛍光カラー、矢印線にはAI/アクセントカラー（--ai）を適用し、描画モード中にはカーソルを crosshair に切り替える視覚フィードバックを実装した。

3. ビルドパイプラインおよびHTMLテンプレートの連携（build.py, engine.html, app.js）：
   Mono Spaceの単一HTML生成時に annotations.js を自動バンドルする構成へ更新した。app.js においてカメラ状態と連動して初期化を行い、engine.html の操作ガイドパネル（ヘルプ）へ新設ショートカットの案内を追記した。

4. Doc側旧mono-brushの非推奨化（modules/doc/src/components/mono-brush/manifest.json）：
   画面固定描画であった従来の mono-brush について、ステータスを deprecated に改定し、Mono Spaceの空間アノテーションへの移行を推奨する注記を明記した。

## 3. 検証実績

以下の自動テストおよび結合テストがすべて合格した。

1. Node環境における空間アノテーション単体テスト（modules/space/tests/core.test.cjs）：
   自由描画パスの始点・中間点・終点生成、および矢印のベクター座標フォーマット（M sx sy L ex ey）が誤差なく生成されることを確認（全14テスト合格）。
2. Space Python単体テスト（modules/space/tests/）：
   全57テストが合格し、スタイル検証や既存構文解析・インポーターとの整合性を確認。
3. 段階F結合テスト（tests/test_stage_f_annotations.py）：
   実践原稿の一括ビルドにおいて、生成された presentation.html に SpatialAnnotations モジュール、SVGマーカー定義、スタイルクラス、ヘルプ表記がすべて正確に埋め込まれていることを実証。また、Doc側の mono-brush manifest.json が deprecated であることを確認。
4. 全体リグレッション検証：
   MonoSuite ルートの pytest（段階B3〜F全30件）、Space Python 57件、Space Node 14件のすべてが一切のエラーなく合格。
