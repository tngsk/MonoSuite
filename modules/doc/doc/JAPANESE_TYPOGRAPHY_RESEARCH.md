# 日本語タイポグラフィ：知見と設定候補

調査日: 2026-09-09 / 対象: 画面閲覧・プレゼンテーションを中心とした横組み  
Mono確認時点: `a37721a` / 状態: 調査・提案。アプリケーションへの適用は未実施。

## 結論

本文は「自然な文字幅・行頭揃え・適切な行長」を基準にし、見出しの字詰めや均等な改行は別設定にする。禁則、約物の余白、和欧文間隔、全体の字間は役割が違うため、一つの指定で解決しようとしない。

Monoでは、本文へ継承する `palt`、両端揃え、長い見出しの `keep-all` を最初の比較対象にする。既存の3段階文字サイズ体系は活かしつつ、「手元で読む」と「投影して見る」で行長と行高を分けることを推奨する。

以下では、出典にある仕様・ガイドラインと、Mono向けの提案値を区別する。数値候補は最適値を実証したものではなく、比較評価の開始点である。

## 1. 抽出した知見

### 日本語の組版は、等幅の字面だけでは決まらない

JLReqは、漢字・仮名の配置、禁則、約物、和欧文混植、行調整を別々の問題として整理している。伝統的な書籍の両端揃えには文字クラスに応じた調整がある。「全文字の間隔を一律に増減すれば日本語組版になる」とは捉えない。JLReqはW3Cの組版要件をまとめたNoteであり、全てをブラウザが実装済みであることを意味しない。[JLReq](https://www.w3.org/TR/jlreq/)

**Monoへの示唆:** 文字の読みやすさ、行の折返し、段落の見た目を個別に評価する。長文の閲覧用と見出しの演出用の設定を分ける。

### 禁則と単語分割は別の制御

`line-break` は日本語などの改行規則の厳しさを扱う。`word-break: keep-all` はCJKの通常の文字間改行を抑えるため、「日本語らしく改行する」指定ではない。長い日本語見出しへの一律適用は避ける。[CSS Text Level 4](https://www.w3.org/TR/css-text-4/#line-break-property)、[MDN: word-break](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/word-break)

**候補:** 本文は `line-break: strict; word-break: normal`。長いURLなどは `overflow-wrap: anywhere` を局所的に使う。非常時の折返しは禁則より優先する場合があるため、本文全体の見た目を整えるための道具にはしない。

### `palt` は句読点専用の字詰めではない

OpenTypeの `palt` は、全角幅で設計されたグリフの横方向の送り幅を比例的に調整する機能である。フォントによって対象と調整量が異なる。仕様では既定で無効にするUIが提案され、`chws` など他の横幅調整機能との排他的な扱いも記載されている。[Microsoft: OpenType palt](https://learn.microsoft.com/en-us/typography/opentype/spec/features_pt#tag-palt)

**候補:** 本文は `font-feature-settings: normal` で親からの明示的なpalt指定を解除する。短い見出しにだけpaltを試し、同じフォント・同じ文章で比較する。`palt`、`chws`、負のletter-spacingを無条件に重ねない。

### 約物の空きと和欧文間の空きを分離する

`text-spacing-trim` は句読点や括弧の内側の空きを扱い、`text-autospace` は日本語と英字・数字の境界の空きを扱う。両者は全ての字間を変える `letter-spacing` と異なる。[W3C: inline spaces](https://www.w3.org/International/articles/styling/inline-space)

**候補:** `text-autospace: normal` を対応環境で試す。文章データに装飾目的の半角スペースを自動挿入しない。コード、URL、識別子は `text-autospace: no-autospace` の対象候補にする。括弧の詰めはまず `text-spacing-trim: normal`、見出しの行頭を揃える用途に `trim-start` を別途比較する。

### 行長は「px幅」より、文字の大きさとの比で考える

`em` はフォントサイズ、`ch` は基本的に数字0の送り幅、`ic` は「水」の送り幅を基準にする。日本語の行長には `ic` が意図を表しやすい。ただし英数字の混在や字詰めにより、38icが実際の38文字を保証するわけではない。[CSS Values Level 4](https://www.w3.org/TR/css-values-4/#font-relative-lengths)

WCAG 1.4.8（AAA）は、CJKでは40字以内、両端揃えを避けた表示などへ変更できる仕組みを扱う。これは「常に40字が最も読みやすい」という実験結果でも、AAの一律必須値でもない。[WCAG 1.4.8](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html)

**候補:** 手元閲覧は32〜38ic程度、投影本文は22〜30ic程度から比較する。いずれも提案値。狭い画面では親幅に収める。2カラムで読める文字数が不足する場合は、字を縮めるより1カラム化を優先する。

### 両端揃えは用途を選ぶ

伝統的な書籍組版の原則と、可変幅のWeb画面で読みやすいことは同一ではない。Monoの閲覧用本文は `text-align: start` を標準候補とし、両端揃えを必要とする配布資料では選択可能にする。

両端揃えを使う場合、現行CSSの `inter-ideograph` ではなく、現行仕様の `text-justify: auto` または `inter-character` を検討する。これらは異なる処理であり、後者も日本語だけを選択的に調整する保証ではない。[CSS Text: justification](https://www.w3.org/TR/css-text-4/#text-justify-property)

### `balance` と `pretty` は改行の最適化であり、意味理解ではない

見出しの `text-wrap: balance` は行の長さを整える候補となる。`pretty` は実装ごとの最適化があり、全ブラウザで同一の改行を保証しない。WebKitは段落全体を考慮した処理を説明している。[WebKit: text-wrap pretty](https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/)

**候補:** 本文の比較基準は通常の折返し、見出しはbalance。prettyは比較実験として有効化する。日本語の文節で必ず区切られるとは説明しない。`br` や `nowrap` の多用で一つの画面幅へ固定しない。

### フォント名とウェイトは端末間で同じ結果にならない

デジタル庁はNoto Sans JPなどを採用しているが、システムフォントの利用や閲覧者による変更も認める。フォントサイズ変更で機能や情報が失われない設計を求めている。[デジタル庁: タイポグラフィ](https://design.digital.go.jp/dads/foundations/typography/)、[アクセシビリティ](https://design.digital.go.jp/dads/foundations/typography/accessibility/)

**候補:** オフライン配布のMonoはシステムフォントを基本にし、表示差を受け入れる。Noto Sans JPをスタックへ書くだけではインストールや埋め込みは行われない。フォント埋め込みは、字形の統一が必要な場合に容量とライセンスを確認して別途判断する。本文400、見出し700を比較の起点にするが、ウェイト数値だけで可読性を断定しない。

### アクセシビリティの数値をデザインの既定値と混同しない

WCAG 1.4.12（AA）は、行高1.5倍、段落後2倍、字間0.12em、単語間0.16emへ利用者が変更しても情報・機能を失わないことを扱う。これらを全てデザインの初期値に設定する要求ではなく、言語が使わない間隔には例外がある。[WCAG 1.4.12](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)

横書きの閲覧用コンテンツは320 CSS px相当でのリフローも確認する。意味上2次元配置を必要とする図表やプレゼンテーションには例外があるが、その例外を通常本文全体へ広げない。[WCAG 1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)

通常文字のコントラストは4.5:1以上、大きな文字は3:1以上がAAの基準。投影環境では背景光や距離も影響するので、基準値の達成だけで実用上の視認性を保証しない。[WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

## 2. Monoの現状との対応

参照: [base.css](/Users/ngsklab/Code/Mono/src/templates/core/base.css)、[default.html](/Users/ngsklab/Code/Mono/src/templates/default.html)、[constants.py](/Users/ngsklab/Code/Mono/src/constants.py)。以下はソース確認であり、表示不具合の実機再現を済ませた一覧ではない。

| 現行設定 | 判断・比較候補 |
|---|---|
| `html lang="ja"` | 維持。文書言語を明示する。外国語のまとまった引用には個別のlangを検討 |
| body全体の `"palt" 1` | 本文では解除し、見出し限定と比較 |
| p/liの `justify` + `inter-ideograph` | 閲覧ではstartを候補。両端揃えが必要な用途だけ標準のtext-justify値を検討 |
| 段落幅42em | 厳密な42文字ではない。38ic程度と比較。レイアウト全体の1792px上限とは別に管理 |
| 本文行高1.85、compact 1.65 | 妥当性を比較できる起点。本文のゆとりを一律に削らない |
| h1行高1.15、display行高1.05 | 複数行の日本語見出しやルビには詰まりやすい可能性。1.3〜1.4と比較 |
| 見出し字間0.04em、display -0.02em | paltとの合成結果を確認。0を基準に装飾目的で調整 |
| displayの `keep-all` | 長い日本語見出しではnormalを候補。意味のまとまりを保つnowrapは短い範囲のみ |
| p/li/blockquoteのpretty | ブラウザ差があるため、wrapを比較基準にする |
| rootの16px固定 | `100%`との比較候補。テーマUIもrootサイズを変更するため、両者を一緒に検証 |
| Markdownのnl2br | ソース中の改行が表示の強制改行になる。CSS変更だけでは解消しない。執筆ルールと変更互換性を別途確認 |
| `.column`のoverflow:hidden | 拡大時に長い語や見出しが切れないか確認 |

lang指定の意味は [W3C: Declaring language in HTML](https://www.w3.org/International/questions/qa-html-language-declarations) を参照。

## 3. 抽出した設定候補

以下はMono向けの提案値であり、規格が定める最適値ではない。フォントサイズのpx換算はroot=16pxの場合。投影はスクリーン寸法・解像度・最後列の距離を含めて確認する。

| 設定 | 手元閲覧の開始値 | 投影・プレゼンの開始値 |
|---|---|---|
| 本文サイズ | 1.125〜1.375rem（18〜22px） | 現行bodyトークンを起点（24〜38.4pxの範囲） |
| 本文行高 | 1.8 | 1.65〜1.85、初期比較1.75 |
| 段落の行長上限 | 38ic（比較範囲32〜38ic） | 28ic（比較範囲22〜30ic） |
| 本文字間 | normal | normal |
| 本文palt | 無効 | 無効を基準 |
| 本文揃え | start | start。短いメッセージのみ中央揃えを選択 |
| 禁則・分割 | strict / normal | strict / normal |
| 見出し行高 | 1.4 | 1.35 |
| 見出し改行 | balance、非対応時wrap | balance、必要なら著者が意味単位を調整 |
| 段落間隔 | 1emから比較 | 現行の空間トークンを維持して比較 |
| 和欧文間隔 | normalを段階導入 | 同左 |

閲覧用で文字を小さくする案は、現行のプレゼン向けサイズを置換する提案ではない。用途を明示して選べるようにする。

### CSS設定の参照例

次の `.jp-reading` / `.jp-heading` / `.jp-latin-token` は説明用の新しいクラス名であり、現在のMonoには未接続。bodyへ付けるだけで既存のp/liやShadow DOMの明示スタイルを上書きできるとは限らない。実装時には適用対象と詳細度を設計する。

```css
.jp-reading {
  font-feature-settings: normal;
  font-size: 1.25rem;
  line-height: 1.8;
  letter-spacing: normal;
  text-align: start;
  text-align-last: auto;
  line-break: strict;
  word-break: normal;
  overflow-wrap: break-word;
  text-wrap: wrap;
  max-inline-size: min(100%, 38em);
}

@supports (max-inline-size: 38ic) {
  .jp-reading { max-inline-size: min(100%, 38ic); }
}

.jp-heading {
  font-feature-settings: normal;
  line-height: 1.35;
  letter-spacing: normal;
  line-break: strict;
  word-break: normal;
  overflow-wrap: break-word;
}

@supports (text-wrap: balance) {
  .jp-heading { text-wrap: balance; }
}

@supports (text-autospace: normal) {
  .jp-reading { text-autospace: normal; }
  .jp-reading :is(code, pre, .jp-latin-token) {
    text-autospace: no-autospace;
  }
}

@supports (text-spacing-trim: normal) {
  .jp-reading { text-spacing-trim: normal; }
}
```

機械可読の設定候補は [japanese_typography_settings.toml](/Users/ngsklab/Code/Mono/doc/japanese_typography_settings.toml) に分離した。Monoの `config.toml` のスキーマではなく、比較実験・将来設計のための参照データである。

## 4. ブラウザ対応と導入の扱い

2026-09-09に参照したMDNでは `text-autospace` はBaseline 2025（2025年11月以降の最新ブラウザ群）で、値ごとの対応差がある。`text-spacing-trim` はLimited availability・Experimentalとして掲載されている。古い配布先ブラウザも想定し、前者は段階導入、後者は任意の改善として扱う。[MDN: text-autospace](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-autospace)、[MDN: text-spacing-trim](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-spacing-trim)

`@supports` は構文の受理を確認するもので、書体や禁則の実際の見た目を保証しない。Chrome/Safari/Firefoxの対象バージョンとOSを記録して確認する。CSS Text Level 4には作業草案の機能も含まれるため、仕様掲載と実装済みを区別する。

## 5. 検証用の文章と評価項目

次のような文章を、同一フォント・同一幅で設定だけ変えて比較する。

| 観点 | 検証文・操作 |
|---|---|
| 禁則・約物 | `「日本語（横組み）の設定」を確認します。『引用』、句読点、……、――を比較する。` |
| 和欧文混植 | `Python 3.14でAPIを実行し、2026年9月の結果をHTMLとPDFで共有する。` |
| 長い見出し | `日本語タイポグラフィの扱いとプレゼンテーションにおける可読性` |
| 長い識別子 | 長いURL、アンダースコア入りのコード、英数字の製品名 |
| ルビ・強調 | ルビ、太字、マーカーを含む複数行。行の重なり・文字切れを確認 |
| 拡大・狭幅 | 320/375/768/1280/1920 CSS px、文字200%拡大、1280px画面の400%ズーム |
| 利用者の設定 | WCAGの行高・段落間・字間を上書きし、欠落・重なり・操作不能を確認 |
| 投影 | 最後列から読めるか、複雑な漢字が潰れないか、淡色マーカー上の文字が読めるか |

行数、横はみ出し、実フォント、スクリーンショットを記録する。可読性の優劣を判断するには、実際の利用者による読み間違い・読み時間・主観評価も必要である。CSSの構文検証やユニットテストだけで優劣を実証したとはしない。

## 6. 次に行う比較の順序

1. 現行の文字サイズを維持したまま、本文paltの有無とstart/justifyを比較する。
2. 行長38ic/28icと行高を比較し、閲覧・投影の設定を分ける。
3. 長い見出しのkeep-allを外した比較と、複数行行高を検証する。
4. 和欧文間隔と約物調整を段階導入し、未対応環境でのフォールバックを確認する。
5. Markdownの強制改行、カラム、テーマUI、印刷時の上書きを含めて統合検証する。

本調査では文献・仕様・現在のソースを照合した。新しい設定のブラウザ間比較、利用者による可読性実験、印刷の視覚検証は未実施。縦組み・専門的なルビ組版・書籍のページ設計は今回の中心範囲に含めていない。
