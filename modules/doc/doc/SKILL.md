# Mono記法 (Mono Markdown Syntax) ガイドライン（AI向け）

このドキュメントは、AIアシスタントがMono専用の拡張Markdown記法（Mono記法）を正しく理解し、ユーザーの要請に応じて適切なMarkdownを出力するためのスキルセットとルールを定義するものです。

## 1. 基本ルールと構文 (Core Rules & Syntax)

Monoは、標準Markdownの親しみやすさと、Mono Space直系のディレクティブ記法（`::`）、およびモノリシック縦スクロールを支えるフェンスブロック記法（`:::`）を統合したハイブリッド構文体系を採用しています。

### A. 基本ドキュメント要素（Markdown標準構文）
標準のMarkdown構文をそのまま使用します。
* **画像:** `![代替テキスト](path/to/image.png)` （自動Base64化・読み込み失敗時エラーバナー自動表示）
* **見出し:** `# 大見出し`, `## セクション`, `### サブセクション` （末尾に `{#id}` でID指定可能）
* **コードブロック:** フェンスコードブロック（```）から自動変換（コピーボタン・ハイライト付き）
* **テキストリンク:** `[表示テキスト](URL)`

### B. セクション修飾・ディレクティブ構文（::ディレクティブ）
見出しの直下に記述し、その見出しやセクション全体のスタイルを宣言します。
```markdown
## 重要なお知らせ {#notice}
::tone warning
::style note
この枠全体が付箋スタイル（note）で表示されます。
```
* **セマンティックトーン (`::tone`):**
  * `neutral`: 標準グレー
  * `primary`: 紫色（AI・主役）
  * `secondary`: ピンク色
  * `accent`: グリーン色
  * `info`: シアン色
  * `success`: グリーン色（成功・完了）
  * `warning`: オレンジ色（警告・注意）
  * `error`: ピンク色（エラー）
* **付箋カード化 (`::style note`):** セクション全体を角丸カード枠・左アクセント線で囲みます。
* **見出し蛍光マーカー (`::marker on` / `::marker off`):** 見出し蛍光帯の表示を明示制御します。

### C. リッチリンクカード（::link）
単独行に記述することで、URLのOGP情報を取得してリッチカードを自動生成します（TTLキャッシュ対応）。
```markdown
::link https://example.com square
::link-title 手動タイトル
::link-description 手動説明文
::link-image custom.png
```
* `::link URL`: 通常の横長カード
* `::link URL square`: 正方形サムネイルカード
* 直下の `::link-title`, `::link-description`, `::link-image` でOGP情報を手動上書き可能。

### D. 要素間接続線（::connect）
要素ID間を結ぶベジェ接続線を描画します。
```markdown
::connect #source -> #target | 連携ラベル (tone: "ai")
```

### E. レイアウト構文（フェンスブロック :::）
Mono Docの縦スクロール・モノリシックレイアウトおよび3×3スペーシング（Spacing Trinity）を制御します。カラム間は単独行の `:::` で区切ります。

#### 1. 水平・垂直レイアウト (`::: hbox`, `::: vbox`)
```markdown
::: hbox gap-group
### 左カラム
左側のコンテンツ。
:::
### 右カラム
右側のコンテンツ。
:::
```

#### 2. 比較レイアウト (`::: compare`)
2要素（1:1対比）または3要素（1:1:1等幅並列対比）の比較カードを構築します。
```markdown
::: compare
### Before
従来の課題や問題点
:::
### Intermediate
過渡期の試作品
:::
### After
新しい解決策と成果
:::
```

#### 3. セクション区切り (`::: section`)
フルブリード背景や視覚的な区切りブロックを定義します。
```markdown
::: section padding-group
### セクション見出し
コンテンツ...
:::
```

### F. テキスト強調・スタイリング
* **蛍光マーカー:** `==デフォルト黄色マーカー==`、`==AIトーン紫マーカー=={primary}`、`==警告マーカー=={warning}`
* **蛍光アンダーライン:** `++シアン下線++{cyan}`、`++緑色下線++{green}`
* **改行禁止:** `{{絶対に改行されない}}`
* **Typography Trinity:**
  * `.text-display`: 看板大見出し
  * `.text-body`: 標準本文
  * `.text-compact`: 凝縮注釈・カラム内テキスト
* **Spacing Trinity:**
  * `.gap-flow`: 112px（大ブロック余白）
  * `.gap-group`: 64px（カラム間余白）
  * `.gap-item`: 23px（要素間微小余白）

---

## 2. コンポーネント一覧

### A. コア・アクティブコンポーネント
| コンポーネント | 種類 | 構文例 |
|---|---|---|
| レイアウト | Fence | `::: hbox gap-group\n左\n:::\n右\n:::` |
| 比較（2/3要素） | Fence | `::: compare\nA\n:::\nB\n:::\nC\n:::` |
| セクション | Fence | `::: section padding-group\n...\n:::` |
| リッチリンク | Directive | `::link https://example.com` |
| 接続線 | Directive | `::connect #a -> #b \| ラベル` |
| ズーム | Auto/Inline | `@[zoom]()` または `-p presentation` |
| コードブロック | Auto | 通常のフェンスコードブロック（```） |
| テーマ切替 | Inline | `@[theme: corporate]()` |

### B. インタラクティブパッケージ（オプトイン）
`@[poll]`, `@[reaction]`, `@[ab-test]`, `@[notebook]`, `@[textfield-input]`, `@[group-assignment]`, `@[session-join]`, `@[account]`

### C. 廃止されたコンポーネント（使用禁止）
`mono-hero`, `mono-drawer`, `mono-mermaid`, `mono-media-grid` は完全に廃止されました。

---

## 3. AI生成時の厳格な禁止・遵守事項

1. **廃止構文および廃止コンポーネントの完全排除:** `@[image]`, `@[hbox]`, `@[vbox]`, `@[compare]`, `@[section]`, `@[mermaid]`, `@[hero]`, `@[drawer]`, `@[media-grid]` は一切出力してはなりません。画像は標準Markdown（`![alt](url)`）、レイアウトはフェンス記法（`::: hbox`, `::: compare`, `::: section`）を使用してください。
2. **等号デリミタ（`=`）の禁止:** コンポーネント引数には必ずコロン記法（`key: "val"`）を使用してください。
3. **3要素比較の等幅並列性:** `::: compare` で3要素を記述する場合、1:1:1の対等な並列対比としてレンダリングされます。
4. **Spacing Trinityの遵守:** 余白には `.gap-flow`, `.gap-group`, `.gap-item` を使用してください。
5. **詳細仕様の参照:** 全体仕様および印刷・HTML要素規約については [doc/SPECIFICATION.md](SPECIFICATION.md) を参照してください。
