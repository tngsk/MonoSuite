# Mono Doc 最新仕様リファレンス (Specification Reference)

本ドキュメントは、Mono DocにおけるMarkdown記法、レイアウト構文、スタイリング体系、HTML構造要素、およびPDF出力仕様を網羅した単一の公式リファレンスマニュアルです。

---

## 1. コアデザイン設計原則 (Design Foundations)

Mono Docは、16pxドットグリッドと連動する3×3スケール（Typography TrinityおよびSpacing Trinity）を基盤としたモノリシック・縦スクロール型ドキュメント生成エンジンです。

### A. Typography Trinity（タイポグラフィ三原則）

ドキュメント内の文字サイズ体系は3段階の流体スケールで統一されています。

| クラス / 用途 | CSS変数 | 基準サイズ | 適用対象・役割 |
|---|---|---|---|
| `.text-display` | `--font-display` | 2.25rem (36px) | 最上位の看板見出し、キーメッセージ |
| `.text-body` | `--font-body` | 1.0rem (16px) | 標準本文段落、リスト、引用文 |
| `.text-compact` | `--font-compact` | 0.875rem (14px) | カラム内詳細、注釈、テーブル、小見出し（h4-h6） |

### B. Spacing Trinity（余白三原則）

レイアウトおよびブロック間の垂直・水平余白は、16pxグリッドと整合する3つの値に集約されます。

| クラス / 用途 | CSS変数 | 基準余白 | 適用対象・役割 |
|---|---|---|---|
| `.gap-flow` | `--spacing-xl` | 112px (7rem) | 大セクション間、主要テーマ間の大分離 |
| `.gap-group` | `--spacing-lg` | 64px (4rem) | カラム間ギャップ、関連ブロック間のグルーピング |
| `.gap-item` | `--spacing-sm` | 23px (1.4375rem) | 見出しと本文、隣接要素間の微細余白 |

### C. Line-Height Trinity（行間三原則）

行間比率はマジックナンバーを排除し、視覚的役割に応じた3つのセマンティックトークンに統一されています。

| トークン名 | CSS変数 | 基準値 | 役割・適用対象 |
|---|---|---|---|
| Loose（読解・呼吸） | `--lh-loose` | 2.0 | 本文段落（`p`）、引用（`blockquote`）。行送りの視線移動負荷を最小化。 |
| Snug（情報・凝縮） | `--lh-snug` | 1.75 | リスト（`ul`, `ol`, `dl`）、テーブル（`table`）、コードブロック（`pre`）。 |
| Tight（構造・塊） | `--lh-tight` | 1.25 | 見出し全般（`h1`〜`h6`）。複数行時に1つの構造ブロックとして引き締める。 |

---

## 2. 標準MarkdownおよびHTML要素仕様 (Standard & Semantic Elements)

Mono Docは標準Markdownを忠実に解釈し、印刷およびWebの双方に最適化されたタイポグラフィを自動適用します。

### A. 画像 (`![alt](src)`)

標準の画像構文を使用します。
- 変換時に自動的にBase64エンコードされ、単一HTML内にインライン埋め込みされます。
- 画像が存在しない、または破損している場合は、インラインエラーバナー（プレースホルダーと対象パス）が自動表示されます。

### B. 見出し (`#` 〜 `######`)

- `# 見出し1` (`h1`): `--font-display` (36px) 適用。
- `## 見出し2` (`h2`): `--font-title` (28px) 適用。
- `### 見出し3` (`h3`): `--font-subtitle` (20px) 適用。
- `####` 〜 `######` (`h4` - `h6`): `--font-compact` (14px) 適用。
- 見出し末尾に `{#custom-id}` を付与することで、任意のアンカーIDを指定可能です。

### C. 本文段落 (`p`)

- 行長制限: 日本語の可読性を最大化するため、最大行長は `min(100%, 42em)`（約38〜42文字）に制御されます。
- 組版処理: 両端揃え（`text-align: justify`）、厳格な禁則処理（`line-break: strict`）、および孤立行防止（`text-wrap: pretty`）が標準適用されます。

### D. リスト (`ul`, `ol`, `li`)

- フォントサイズ: `--font-compact` (14px) および `line-height: 1.75` が適用され、本文段落より少し小さく引き締まった可読性を確保します。
- インデント構造: 最上位のリストに `margin-left: 1.25rem` が適用され、本文段落の左端ラインより一段内側にオフセット配置されます。
- インデント構文: 2スペースインデント（`tab_length=2`）に対応しており、半角スペース2文字および4文字のどちらの記法でも正確な階層（`li > ul`, `li > ol`）としてパースされます。
- リスト項目間マージン: `li + li` に `--spacing-xs` (8px) を適用。
- 番号付きリスト (`ol`): ブラウザ標準マーカーに代わり、CSSカウンターによる丸枠バッジ数字（`tabular-nums`・薄枠・背景透明）が最上位項目に自動適用されます。
- ネストされたリスト (`li > ul`, `li > ol`): 親項目との間に上下マージン `--spacing-xs` (8px) を均等に確保し、詰まり感を解消します。子リストの `ol` は自然な階層番号（decimal）表示にフォールバックします。
- 複合ブロック: `li > p + p`、`li > pre`、`li > blockquote`、`li > table` の上下にも `--spacing-xs` が適用されます。

### E. テーブル (`table`)

- フォントサイズ: 自動的に `--font-compact` (14px) および `line-height: 1.6` が適用され、情報密度の高い一覧表示を実現します。
- スタイル: 上下境界線およびヘッダー下線によるクリーンな罫線構造。

### F. 定義リスト (`dl`, `dt`, `dd`)

Markdown内で直接記述されたHTML定義リスト要素に対応します。
- フォントサイズ: `--font-compact` (14px) および `line-height: 1.75`。
- 用語 (`dt`): 太字、`margin-top: var(--spacing-xs)`。
- 説明 (`dd`): 左インデント `padding-left: var(--spacing-md)`、文字色 `--font-color-light`、行長42em制御。

### G. 折りたたみ要素 (`details`, `summary`)

- 通常表示: 角丸ボーダー付きカードとしてインタラクティブに開閉可能。
- 印刷・PDF出力時: `@media print` 下で自動的に `display: block !important` が適用され、閉じた状態であっても全コンテンツが強制展開されます（紙面上での情報欠落防止）。

---

## 3. ディレクティブ構文 (Directives: `::`)

見出しやブロックに対する属性付与およびスタンドアロン機能を定義する記法です。

### A. セクション修飾ディレクティブ

見出しの直下に配置し、セクション全体のトーンや外観を制御します。

```markdown
## 重要なお知らせ {#notice}
::tone warning
::style note
::marker on
この枠全体が付箋スタイル（note）のカード枠で囲まれ、見出しに警告マーカーが付与されます。
```

- `::tone [トーン名]`: セクションのキーカラーを決定します。
  - `neutral`: 標準グレー
  - `primary`: 紫色（AI・主役）
  - `secondary`: ピンク色
  - `accent`: グリーン色
  - `info`: シアン色
  - `success`: グリーン色（成功・完了）
  - `warning`: オレンジ色（警告・注意）
  - `error`: ピンク色（エラー）
- `::style note`: セクション全体を角丸カード枠および左アクセント境界線で修飾します。
- `::marker on` / `::marker off`: 見出し背後の蛍光マーカー帯の表示切替。

### B. リッチリンクカード (`::link`)

単独行に記述することで、URLのOGP情報を取得・キャッシュしてリッチカードを生成します。

```markdown
::link https://example.com square
::link-title カスタムタイトル
::link-description カスタム説明文
::link-image custom-thumbnail.png
```

- `::link <URL>`: 標準の横長リッチカード。
- `::link <URL> square`: 正方形サムネイルカード。
- 補助ディレクティブ: 直下に `::link-title`, `::link-description`, `::link-image` を並べることで、OGP取得値を上書き可能です。

### C. 要素間接続線 (`::connect`)

HTML要素のアンカーID間を結ぶベジェ曲線の接続線を描画します。

```markdown
::connect #step1 -> #step2 | 連携処理 (tone: "primary")
```

---

## 4. レイアウトフェンス構文 (Fenced Blocks: `:::`)

モノリシックな縦スクロール構造を整理するためのブロック構文です。ブロック内のカラム区切りには単独行の `:::` を使用します。

### A. 水平・垂直レイアウト (`::: hbox`, `::: vbox`)

```markdown
::: hbox gap-group
### 左カラム
左側のコンテンツ。
:::
### 右カラム
右側のコンテンツ。
:::
```

- オプションクラス: `gap-flow` (112px), `gap-group` (64px), `gap-item` (23px)

### B. 比較レイアウト (`::: compare`)

2要素（1:1）または3要素（1:1:1等幅並列）の比較カードを生成します。

```markdown
::: compare
### Before
従来の手法における課題
:::
### Intermediate
過渡期における検証
:::
### After
本システム導入後の成果
:::
```

### C. セクションブロック (`::: section`)

```markdown
::: section padding-group
### セクション見出し
背景色やパディングを内包する独立したコンテナを構築します。
:::
```

---

## 5. インライン強調構文 (Inline Highlights)

文章中の重要語句を強調するための専用構文です。蛍光マーカー、アンダーライン、およびテキスト選択範囲（`::selection`）は完全に同一のカラーパレット（不透明度75% / ダーク40%）を共有し、角丸は `--radius-sm` (4px) に統一されています。

- 蛍光マーカー (`== ==`):
  - 文字の背後約80%を覆う蛍光ペン塗り（`linear-gradient(transparent 20%, ...)`）。
  - `==標準黄色マーカー==`
  - `==紫マーカー=={primary}`
  - `==警告オレンジ=={warning}`
  - 指定可能トーン/カラー: `primary`, `secondary`, `accent`, `info`, `success`, `warning`, `error`, `yellow`, `pink`, `green`, `cyan`, `orange`
- 蛍光アンダーライン (`++ ++`):
  - 文字ベースライン下部約30%を引く下線（`linear-gradient(transparent 70%, ...)`）。マーカーと完全同一のカラートークンを参照。
  - `++シアン下線++{cyan}`
  - `++グリーン下線++{green}`
- テキスト選択範囲 (`::selection`):
  - ユーザーがブラウザ上で選択したテキストの背景色も、デフォルトの蛍光黄色マーカー（`--mono-highlight-yellow`）と完全に連動します。
- 改行禁止 (`{{ }}`):
  - `{{絶対に途中で改行させない専門用語}}`

---

## 6. アクティブコンポーネント一覧 (Active Components)

現在システムで有効化されているコンポーネントの一覧です。

### A. コアコンポーネント

| コンポーネント | 呼出構文 | 機能概要 |
|---|---|---|
| レイアウト (`mono-layout`) | `::: hbox` / `::: vbox` | 2〜4カラムの水平・垂直グリッド配置 |
| 比較 (`mono-compare`) | `::: compare` | 2要素または3要素等幅並列の比較カード |
| セクション (`mono-section`) | `::: section` | フルブリード背景・独立コンテナブロック |
| リッチリンク (`mono-link`) | `::link <URL>` | OGPメタデータ取得・カード化表示 |
| 接続線 (`mono-connector`) | `::connect #a -> #b` | 要素ID間の動的SVGベジェ曲線描画 |
| ズーム (`mono-zoom`) | CLI `-p presentation` | プレゼンテーション時のオートズーム実行 |
| コードブロック (`mono-code-block`) | ` ```lang ` | シンタックスハイライトおよびワンクリックコピー |
| テーマ設定 (`mono-theme`) | `@[theme: corporate]()` | ドキュメント全体のカラーパレット切替 |

### B. インタラクティブコンポーネント（オプトイン）

講義・ワークショップ向けの対話型Webコンポーネントです。

- 投票: `@[poll: label](options: "A,B,C")`
- リアクション: `@[reaction]()`
- A/Bテスト: `@[ab-test]()`
- ノート入力: `@[notebook]()`
- テキスト入力: `@[textfield-input]()`
- グループ分け: `@[group-assignment]()`
- セッション参加: `@[session-join]()`
- アカウント認証: `@[account]()`

### C. 廃止されたコンポーネント（使用禁止）

以下のコンポーネントは完全に削除されており、呼び出してはなりません。
- `mono-hero`（廃止）
- `mono-drawer`（廃止）
- `mono-mermaid`（廃止）
- `mono-media-grid`（廃止）
- `@[image]`（廃止: 標準Markdown画像構文 `![]()` を使用）
- `@[hbox]`, `@[vbox]`, `@[compare]`, `@[section]`（廃止: フェンス構文 `:::` を使用）

---

## 7. 印刷およびPDF出力仕様 (Print & PDF Optimization)

Mono Docは、CLI引数 `--pdf output.pdf` によりPlaywrightを用いた高精度モノリシックPDF出力に対応しています。

### A. 日本語フォントスタックの優先順位

PDF出力時（`@media print`）において、Chromium系ブラウザ特有の康煕部首（Kangxi Radicals）文字化けを防止するため、以下のフォントスタックが強制適用されます。

```css
font-family: "PlemolJP", "PlemolJP Console", "PlemolJP Console NF", "PlemolJP35", "BIZ UDGothic", "Meiryo", "Arial Unicode MS", "Yu Gothic", "Noto Sans JP", sans-serif !important;
```

コードブロックおよびインラインコードに対しても、等幅フォント `PlemolJP Console` が最優先で適用されます。

### B. 印刷時の自動展開と改行制御

- `details` タグの常時展開: 折りたたまれているコンテンツも強制的に表示状態となり、印刷時の情報欠落を防止します。
- 行長制限の解除: 本文の42em制限および `text-wrap: pretty` が解除され、紙面幅に応じた自然な折り返しが適用されます。
- アノテーション非表示: 画面上のプレゼンター補助要素やインタラクティブ操作部は、印刷用CSSにより自動的に非表示化されます。

---

## 8. CLIコマンド仕様 (CLI Operations)

```bash
# 基本変換（入力ファイル名と同名のHTMLを出力）
uv run main.py document.md

# プレゼンテーションモード（mono-zoom 有効化）
uv run main.py slides.md -o output.html -p presentation

# 静的ドキュメントモード（Zero-JS）
uv run main.py doc.md -o output.html -p minimal

# 単一モノリシックPDF出力
uv run main.py document.md -o document.html --pdf document.pdf

# データ収集・同期サーバー起動
uv run python -m src.server
```
