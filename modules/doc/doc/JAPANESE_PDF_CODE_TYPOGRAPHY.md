# プログラムコードを含む日本語PDF作成の知見と実装アーキテクチャ

作成日: 2026-09-09 / 対象: WebKit/Blink (Playwright/Chromium) エンジンを用いたHTML経由のPDF生成  
Mono実装コミット: `a37721a` / 分類: 印刷・PDF組版技術知見仕様

## 1. 背景と課題（Gap Identification）

### 印刷エンジンにおけるテキストとコードの処理差異
Webブラウザ（特にWebKitおよびBlinkエンジン）をヘッドレス駆動してHTMLからPDFを出力する際、画面表示と印刷・PDF保存処理との間でレイアウトエンジンの解釈に重大な乖離が発生する。一般的なWebページ閲覧では、CSSグリフ描画が画面解像度に合わせてラスタライズされるため視覚的不整合が露見しにくい。しかし、PDF出力処理ではベクターテキストとしての抽出性、フォントグリフの埋め込み、文字コードマッピング（ToUnicode CMapテーブル）の厳密性が要求される。

### 顕在化した具体的破壊事象
Markdownで記述された講義資料や技術文書をPDF化し、読者がPDF上のPythonコード等をコピー＆ペーストして実行環境（IDEやREPL）に貼り付ける運用において、以下の致命的な構文破壊が確認された。

1. アンダースコアの分裂・重複: `__init__` や `df_sampled` などの識別子において、アンダースコアが2重にコピーされたり、間に不要な空白文字（`_ _`）が挿入されて構文エラーを引き起こす。
2. 不可視レイアウト空白によるインデント破壊: WebKit系の印刷パイプラインが、行頭の連続スペースをレイアウト調整用空白として判断し、テキスト抽出時にストリップ（削除）または不正結合する。Pythonのようにオフサイドルール（インデントによるブロック定義）を採用する言語では、コードが実行不能になる。
3. コードブロック内の不意な自動折り返し: 画面表示用の折り返し設定や固定幅コンテナの影響を受け、複数行に分割された行が改行文字としてPDFテキストに定着し、実行時に不正な構文を生成する。
4. CJKと英数字の混植フォントによる文字化け: macOS環境のChromium等で日本語システムフォント（Hiragino Sans等）のフォールバックが機能した際、グリフマッピングがUnicodeのKangxi部首ブロック（康煕部首、U+2F00〜U+2FD5）へ誤射爆し、日本語テキストが検索不能・文字化けする。
5. インラインコードとコードブロックの一括指定による可読性破綻: `code` セレクタに対する一括のフォントサイズ縮小（例: 13px）が、段落内のインラインコード（`df.info()` 等）にまで波及し、本文（約21.6px）との視覚的調和を著しく損ねる。

---

## 2. コア知見と再設計アーキテクチャ（Redesign as Bridge）

### 印刷メディアクエリ（@media print）の設計原則
画面閲覧（Screen/Presentation）と印刷・PDF出力（Print）では目的が根本から異なる。プレゼンテーション用Monoドキュメントでは大画面プロジェクター投影に対応した動的フルイドタイポグラフィ（`clamp()`）、CSS Gridによる均等リズム、行長42em制限、`text-wrap: pretty` による行末孤立文字防止が有効である。しかし、PDF出力においてはこれらを完全に無効化し、紙面幅成り行きと固定長テキスト保全を最優先するスタイルシートの上書きが必要となる。

### コード保全のためのCSSプロパティスタック
PDF内の等幅テキスト領域を安全に保護するため、以下のCSSルールセットを確定した。

```css
@media print {
    /* ブロックレベル・コードブロックの印刷最適化 */
    pre,
    pre code,
    mono-code-block pre,
    mono-code-block code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
        font-size: var(--font-compact) !important;
        line-height: 1.45 !important;
        white-space: pre !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
    }

    /* インラインコードの印刷最適化: 本文フォントサイズを完全に継承 */
    :not(pre) > code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
        font-size: inherit !important;
    }
}
```

#### 各プロパティの技術的役割
- `white-space: pre !important`: 空白文字（スペース、タブ）および改行文字の物理的保持をエンジンに強制する。`pre-wrap` は行頭空白の圧縮や中間折り返しを許容するため、PDF出力では `pre` に限定する。
- `word-break: normal !important` および `overflow-wrap: normal !important`: 識別子の中間での強制改行を完全に抑止し、`df_sampled` や長い関数名が改行によって分断される事故を防ぐ。
- `font-size: var(--font-compact) !important`: 印刷用トークン `--font-compact`（1.125rem = 18px）に統一し、HTML画面表示と同様に箇条書きやテーブルと等しい対本文比率（約83.3%）を維持する。基準フォントサイズ16pxに対して完全な整数ピクセル（18px）となり、グリフ丸め誤差やアンダースコア分裂を防止しつつ高い可読性を担保する。
- `font-family: ui-monospace, ...`: プラットフォームネイティブの等幅フォントスタックを明示指定する。リガチャ（合字）を無効化し、各文字の進み幅（advance width）を完全に均一化することで、PDF抽出器が空白の有無を誤判定しないグリフ列を生成する。
- `:not(pre) > code { font-size: inherit !important; }`: ブロックレベルコードとインラインコードのセレクタを厳格に分離する。インラインコードは親要素（`p`, `li`, `blockquote`）のフォントサイズを継承させ、等幅フォントファミリのみを適用する。

### 日本語テキストの紙面幅成り行き化
画面用の `max-width: 42em` や `text-wrap: pretty` は、PDF出力時に紙面右側に不自然な巨大空白（デッドスペース）を生じさせ、意図しない行分割を引き起こす。印刷メディアクエリ下では以下を強制適用する。

```css
@media print {
    p,
    li,
    blockquote {
        max-width: 100% !important;
        text-wrap: wrap !important;
    }
}
```

これにより、A4紙面幅（全幅約1177px）一杯を使った自然なテキストフローが形成され、用紙効率と読みやすさが両立される。

### 日本語フォントスタックとKangxi部首化の防止
ChromiumエンジンのPDFテキストレイヤ生成において、macOS標準の特定日本語フォントがCMapマッピング不全を起こす事象に対し、確実なUnicodeマッピングを持つフォントを優先配置する。

```css
@media print {
    body {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        background-image: none !important;
        font-family: "BIZ UDGothic", "Meiryo", "Arial Unicode MS", "Yu Gothic", "Noto Sans JP", sans-serif !important;
    }
}
```

ユニバーサルデザインフォントである `BIZ UDGothic` を最前列に指定することで、漢字の部首置換バグを回避し、PDFテキスト検索およびテキストコピーの完全な文字コード整合性を保証する。

---

## 3. PlaywrightによるモノリシックPDF生成パイプライン

### 単一ページ・モノリシックPDF出力戦略
Monoプロジェクトでは、ページ番号による分断やヘッダー・フッターによるコードの寸断を排除するため、ドキュメント全体を改ページなしの1枚のシームレスなPDFとして出力する戦略を採用している。

```python
# src/processors/pdf.py より抜粋
dimensions = page.evaluate('''() => {
    return {
        width: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, 1024),
        height: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1024)
    }
}''')

page.pdf(
    path=pdf_path,
    print_background=True,
    width=f"{dimensions['width']}px",
    height=f"{dimensions['height']}px",
    page_ranges="1",
)
```

### レンダリング待機とShadow DOMの考慮
Web Componentsを採用したドキュメントでは、HTMLパース完了直後（`DOMContentLoaded` や `networkidle`）であっても、Shadow DOM内部のスタイル解決やテンプレート展開が非同期で完了していない場合がある。`page.wait_for_timeout(1000)` 等の明示的な待機時間を設け、全コンポーネントがDOM上に確定した後にスクロールサイズ計測およびPDFラスタライズを実行することが不可欠である。

---

## 4. 実行性と拡張性（Feasibility & Scalability）

### 検証マトリクスと品質保証プロトコル
本知見に基づく実装の品質を恒常的に保証するため、CI/CDパイプラインおよびテストスイートにおいて以下の検証ステップを標準化する。

1. スタイルシート回帰テスト（Pytest）:
   `tests/core/test_pdf.py` において、`base.css` 内に `font-size: 14px !important`、`white-space: pre !important`、`ui-monospace`、`:not(pre) > code`、`font-size: inherit !important`、`max-width: 100% !important` が常に存在することを静的検証する。
2. ヘッドレスブラウザによる計算済みスタイル実測（Playwright）:
   テスト実行時に `page.emulate_media(media="print")` を設定し、`window.getComputedStyle()` を用いて段落テキストフォントサイズとインラインコードフォントサイズの一致、およびコードブロックの14px確定を動的検証する。
3. PDFテキスト抽出とPython構文解析（AST Parse）:
   生成されたPDFから抽出したテキストブロックに対し、`ast.parse(code_text)` を実行し、インデント破損やアンダースコア分裂のない実行可能な構文が維持されていることを自動検証する。

### 今後の拡張ロードマップ
- ページ分割（Paginated Print）の要求に対するヘッダー・フッター制御とコードブロック分断防止（`page-break-inside: avoid` / `break-inside: avoid`）の高度な調停。
- 印刷時のダークモード・ライトモード切り替え（CSS変数 `--mono-code-text` の自動反転）によるインク消費の最小化。
- Syntax Highlightingトークンの印刷用コントラスト最適化（WCAG 2.2 AA基準 4.5:1 の充足）。
