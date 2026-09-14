# 実装・ドキュメント差分の調査と更新判断

調査日: 2026-09-07 / 対象コミット: `d3a2f82`

結論: 現行実装への一括追従は不適切。安全性と出力契約の不備は実装を修正し、古い利用例・未実装機能の説明は文書を修正する。依存方針と同期アーキテクチャは資料間でも矛盾しているため、設計判断を記録した上で整合させる。

本調査ではアプリケーションコード、既存ドキュメント、設定を変更していない。この報告書のみ追加した。`doc/` はGit管理対象外であり、強制追加は行っていない。

## 判断基準

- 安全性、基本コンテンツの保持、指定した出力の成功・失敗は実装側が守る契約と判断する。
- 最近のCHANGELOG・実装・テストが一致する変更は、古い記述を更新する方向を推奨する。
- 利用ガイドだけに存在する追加機能は、説明の訂正を優先する。記述との整合だけを目的に機能を新設しない。
- `doc/ARCHITECTURE.md` はAGENTS.mdで不変の設計正本とされている。本報告の設計変更案は承認済み仕様ではなく、同ファイルの書換えもしていない。
- テスト成功は記述した仕様の充足と同義ではない。対象を絞った再現結果も判断に用いた。

## 実装を優先して更新する項目

### 1. メディア読込範囲の検証が無効化されている — 優先度: 高

**文書:** [AGENTS.md:76](/Users/ngsklab/Code/Mono/AGENTS.md:76) は、解決済みMarkdownディレクトリまたは作業ディレクトリ配下だけを許可し、`is_file()`を用いるよう要求する。

**実装:** [media.py:92](/Users/ngsklab/Code/Mono/src/embedders/media.py:92) で境界チェックがコメントアウトされ、`exists()`のみで処理を続ける。

**再現:** 一時ディレクトリの `markdown/` と同階層に置いた `dummy.txt` を、`../dummy.txt` と絶対パスの両方で参照した。どちらも埋め込み数1となり、asset storeを復号すると調査用文字列 `AUDIT_DUMMY_ONLY` が得られた。実在する個人ファイルや機密ファイルは使用していない。

**判断:** 実装を修正する。正規化後の範囲チェックと通常ファイル判定を復元する。プロジェクト内の正当な `../assets/` は許可できるため、親参照を一律禁止する必要はない。これは表示機能の仕様変更ではなく、出力HTMLへの意図しないファイル混入を防ぐ制約の回復である。

**必要な検証:** 存在するダミーファイルで範囲外の相対・絶対・シンボリックリンク参照を拒否し、許可範囲内の親参照は成功すること。現在の [test_media_security.py](/Users/ngsklab/Code/Mono/tests/core/test_media_security.py) は実ファイル境界の再現が弱く、テスト成功を防御の証明にできない。

### 2. コンポーネントの許可リストが失われている — 優先度: 高

**文書:** [AGENTS.md:77](/Users/ngsklab/Code/Mono/AGENTS.md:77) は `ALLOWED_COMPONENTS` による明示的なPythonロード制限を要求する。

**実装:** [registry.py:34](/Users/ngsklab/Code/Mono/src/registry.py:34) がディレクトリを走査し、マニフェストがないディレクトリも登録する。[markdown.py:38](/Users/ngsklab/Code/Mono/src/processors/markdown.py:38) はその一覧にある `parser.py` をインポートする。`src/constants.py` に許可リスト本体はない。

**判断:** マニフェストによるメタデータ管理は残し、Pythonロード対象を明示的に制限する実装を追加する。文書から安全要件を削除して実装に合わせるべきではない。マニフェストが存在すること自体は信頼の証明にならない。

**限界:** ソース読解で確認したポリシー違反であり、Markdownだけから任意のコンポーネントファイルを配置できることを示したものではない。

### 3. `minimal` がZero-JSを保証しない — 優先度: 高

**文書:** [README.md:20](/Users/ngsklab/Code/Mono/README.md:20) は `static` をZero-JS出力として紹介し、[config.toml](/Users/ngsklab/Code/Mono/config.toml) は `minimal` を「完全静的ドキュメント（JavaScriptゼロ出力）」と説明する。

**実装:** [config.py:82](/Users/ngsklab/Code/Mono/src/config.py:82) はプロファイルを追加コンポーネント一覧へ変換するだけで、未知名もエラーにしない。[html.py:327](/Users/ngsklab/Code/Mono/src/processors/html.py:327) は全プロファイルで本文タグを自動検出する。画像は [media.py:144](/Users/ngsklab/Code/Mono/src/embedders/media.py:144) で透明画像に置き換え、JavaScriptによる復元を前提とする。

**再現:** 見出し・フェンスコード・ローカルPNGを含む同じMarkdownを `minimal` / `standard` / `static` / `unknown` で変換した。全て成功し、全て `<script>` が3個、`mono-code-block` とasset storeを含んだ。3個の内訳は実行用2個とJSONデータ用1個である。

**判断:** **実装と文書の両方を修正する。** 正式名称は設定・CLIに合わせて `minimal` とする。実装は通常HTML/CSS・直接埋め込み画像で基本コンテンツを保持し、JS依存コンポーネントは静的代替を持たせるか、未対応として明示的に扱う。単にscriptタグを削除すると画像やUIが失われる。未知プロファイルの黙認も修正する。

**理由:** 静的配布という既存の用途と明記された保証を守る方が、名称だけを直して説明を弱めるより妥当である。対応できない対話機能の静的表現は、実装着手前に具体化が必要。

### 4. PDFの利用例と失敗の扱い — 優先度: 高

**文書:** [README.md:24](/Users/ngsklab/Code/Mono/README.md:24) の例は `uv run main.py document.md --pdf -o document.pdf`。

**実装:** `-o` はHTML出力先、`--pdf [path]` は別のPDF出力先。[config.py:88](/Users/ngsklab/Code/Mono/src/config.py:88) の解決結果では、この例は通常HTMLとPDFの保存先が同じになる。また [converter.py:127](/Users/ngsklab/Code/Mono/src/converter.py:127) はPDF生成の戻り値を無視する。

**再現:** 既存 `dist/` のない一時ディレクトリでREADMEと同じファイル名を使うと、両出力パスが一致した。PDFプロセッサーが `False` を返すようモックすると `convert()` は `True` のままで、`.pdf` 指定先の先頭にはHTMLの `<!doctype html>` が残った。ブラウザによる同一パス変換の最終結果までは検証していない。

**判断:** 文書は `uv run main.py document.md -o document.html --pdf document.pdf` へ訂正する。実装はPDF失敗をCLIの失敗へ伝播し、HTML/PDFの同一パス指定を拒否する。PDF不要時の挙動は維持する。

### 5. インラインコンポーネントの共通属性構文が不統一 — 優先度: 中

**文書:** [doc/SKILL.md:11](/Users/ngsklab/Code/Mono/doc/SKILL.md:11) は `@[...](...){.クラス #ID}` を共通構文として定義する。

**再現:** `@[badge: 重要]{.error}` は `<mono-badge>重要</mono-badge>{.error}` となり、波括弧が本文に残る。`@[link: タイトル](url: "..."){.large-card}` も同様。一方、layoutパーサーは後置波括弧を解釈する。

**判断:** 文書が宣言する共通のclass/id構文に実装を統一することを推奨する。ただし `.error` がバッジの色を意味するわけではないので、色指定の例は項目7の訂正も必要。修正までのガイドには対応範囲と `class: "..."` の代替を記載する。

## ドキュメントを優先して更新する項目

### 6. プレーンテキストのサイズ指定例 — 優先度: 中

[doc/SKILL.md:62](/Users/ngsklab/Code/Mono/doc/SKILL.md:62) とAGENTS.mdの `[テキスト]{.text-body}` 型の例は、現在のMarkdown拡張ではそのまま文字列として残る。リンクでも画像でもない角括弧テキストに `attr_list` は適用されない。

**判断:** READMEにある段落末尾の属性指定へ文書を統一する。短い例のために新たな独自インライン記法を導入する必要はない。

```markdown
標準の本文テキスト
{: .text-body}
```

### 7. 教育系・基本コンポーネントの説明が実装を超えている — 優先度: 中

対象は [doc/SKILL.mdのコンポーネント一覧](/Users/ngsklab/Code/Mono/doc/SKILL.md:81)。下記はいずれも、現状に合わせた文書訂正を推奨する。新機能の追加は別件として判断する。

| 記述 | 確認した実装 | 推奨する訂正 |
|---|---|---|
| badgeの `type: "error"` | parserは `color` を読み、`type` を捨てる | `color: "error"` に訂正 |
| pollはリアルタイム・複数選択 | `selectedValue` 一つを保存し、サーバー集計を取得しない | ローカル保存の単一選択投票と記載 |
| group-assignmentの `groups: "4"` | パラメーターを捨て、JS内のA〜Dの4グループから選ぶ | 4グループ固定と明記し、無効な引数を削除 |
| session-joinの `room: "101"` とQR表示 | roomは出力されず、セッションIDの手入力UIのみ | 手入力・ローカル保存と記載 |
| accountの「ユーザー認証」 | Test Userと `mock-jwt-token` を生成するMock Login | ローカルの模擬ログインと明記。本人確認の保証と混同しない |
| exportのJSONL/CSV書き出し | 単一JSONオブジェクトを `.json` で保存。サーバー側がJSONL追記 | ブラウザはJSON、サーバー保存はJSONLと区別 |
| themeの例が切替UIとして紹介される | `show_ui` の既定値はfalse | テーマ適用とUI表示を分け、UI例に `show_ui: "true"` を付ける |
| Mermaidの「動的描画」 | ビルド時に `npx mmdc` でSVG生成。JSは表示用プロパティを設定 | ビルド時SVG生成と記載 |

根拠: 各コンポーネントの `parser.py` / `script.js`、特に [group-assignment/script.js](/Users/ngsklab/Code/Mono/src/components/mono-group-assignment/script.js)、[session-join/script.js](/Users/ngsklab/Code/Mono/src/components/mono-session-join/script.js)、[account/script.js](/Users/ngsklab/Code/Mono/src/components/mono-account/script.js)、[export/script.js](/Users/ngsklab/Code/Mono/src/components/mono-export/script.js)。exportのマニフェスト説明もJSONL/CSVなので、文言訂正対象に含める。

### 8. ブロック表示と終了タグ必須の構文が混同されている — 優先度: 中

[doc/SKILL.md:21](/Users/ngsklab/Code/Mono/doc/SKILL.md:21) はブロック要素に終了タグ必須と書くが、表でBlockとされるpoll等は単独ディレクティブで生成される。`@[poll: 質問](options: "A, B")` に `@[/poll]` を追加すると、後者が本文に残ることを確認した。

**判断:** 文書に「表示形式」と「構文形式」を別項目として記載する。終了タグ必須なのは内部コンテンツを受け取るコンテナ構文である。既存の単独コンポーネントに終了タグを新設する必要はない。

### 9. 古いCSS値・注入条件・ライフサイクル — 優先度: 低〜中

- AGENTS.mdの800px/`minmax(auto, ...)` は過去のGrid設定。現行 [base.css](/Users/ngsklab/Code/Mono/src/templates/core/base.css) は `min(92vw, 1800px)` と `minmax(0, ...)` を使用する。古い問題を現状の欠陥として扱わない。
- `.text-small/.text-large/.text-xlarge` は固定rem値でなく3×3流体トークンへの互換エイリアス。READMEの余白112px/64px/23pxも全画面共通の固定値ではなく、`clamp()`で変化する。
- doc/SKILL.mdのlayout既定gapはgroupとあるが、[style.css](/Users/ngsklab/Code/Mono/src/components/mono-layout/style.css) は `--spacing-xl`、つまりflow。既存デモの多くはgapを明示している。既定値の説明を訂正し、見た目を一括変更しない。
- AGENTS.mdのsync・brush・interactive基底クラスの無条件注入は現状と異なる。syncは削除済み、brushはpresentation等の選択時、interactive基底クラスは対象コンポーネントがあるときだけ注入される。
- code-blockとbrushは現在のmanifestでactive、presenterはwip。AGENTS.mdの一括非推奨記述は最新README/manifestに合わせて対象別に整理する。過去のCHANGELOGは当時の履歴として残し、必要ならUnreleasedに方針変更を明記する。
- READMEのJ/K移動は、現行 [mono-zoom/script.js:85](/Users/ngsklab/Code/Mono/src/components/mono-zoom/script.js:85) に合わせて「水平線があれば水平線区切り、なければH1/H2区切りのスライド間移動」と補足する。

### 10. サーバー起動コマンドと出力先の説明 — 優先度: 中

AGENTS.mdと設計資料の `uv run server.py` に対応するルートファイルは存在せず、実体は [src/server.py](/Users/ngsklab/Code/Mono/src/server.py)。`uv run python -m src.server` を推奨コマンドとする。起動するためだけにルートのラッパーを新設する必要はない。

また、READMEのデフォルト出力先説明は、入力ディレクトリに既存 `dist/` がある場合にはその中へ出す [config.py:88](/Users/ngsklab/Code/Mono/src/config.py:88) の挙動を省略している。この条件を追記する。

### 11. JSONエスケープの開発指示が無効なPython例になっている — 優先度: 高

[AGENTS.md:51](/Users/ngsklab/Code/Mono/AGENTS.md:51) の `.replace('<', '\u003c')` は、Python文字列として評価すると置換先も `<` になり、無変更であることを確認した。

**判断:** 文書のPython例を `.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')` に修正する。[html.py:165](/Users/ngsklab/Code/Mono/src/processors/html.py:165) は既にこちらの形式であり、文書に合わせて実装を戻してはいけない。

## 設計判断を記録した上で整合させる項目

### 12. Pythonのみという指示とNodeのビルド時利用

AGENTS.mdはpure Python toolchainを要求する一方、[ARCHITECTURE.md:31](/Users/ngsklab/Code/Mono/doc/ARCHITECTURE.md:31) はNodeの任意利用と欠落時の縮退を認めている。現行 [math.py](/Users/ngsklab/Code/Mono/src/extensions/math.py) はNode/MathJax、[mono-mermaid/parser.py](/Users/ngsklab/Code/Mono/src/components/mono-mermaid/parser.py) はnpx/mmdcで事前描画する。[package.json](/Users/ngsklab/Code/Mono/package.json) と [CI](/Users/ngsklab/Code/Mono/.github/workflows/ci.yml) にもNode依存があり、直近履歴にはMathJax依存の復元がある。

**推奨:** 設計正本の「基本変換はPython、図・数式の事前描画は任意のNode、配布HTMLにNodeは不要」に統一し、AGENTS.mdとREADMEの導入説明を更新する。Mermaidのビルド依存も明記する。純Python限定へ全面的に戻す変更は影響が大きく、文書差分修正としては推奨しない。

### 13. 削除済みmono-syncを中核にした設計記述

[ARCHITECTURE.md:63](/Users/ngsklab/Code/Mono/doc/ARCHITECTURE.md:63) はmono-syncによる参加者同期と入力イベント転送を定義するが、[CHANGELOG.md](/Users/ngsklab/Code/Mono/CHANGELOG.md) とdoc/SKILL.mdは削除済みと明記し、実装ディレクトリもない。SSEのサーバーAPIは残るが、現行コンポーネント群に対応するEventSourceクライアントは見当たらない。入力送信はmono-exportの手動操作である。presenterの別ウィンドウ連携はこの参加者向けSSE同期とは別機能。

**推奨:** 削除履歴を尊重し、mono-syncを文書整合のためだけに復活させない。「SSE APIは残存、標準の参加者同期クライアントは未提供、データ送信は手動」と現在の状態を記録する。設計正本の同期責務を廃止するのか、将来の別コンポーネントへ移すのかはアーキテクチャ判断として確定する必要がある。

### 14. オフラインで「完全動作」の範囲

[README.md:3](/Users/ngsklab/Code/Mono/README.md:3) の無条件の完全動作は実装より広い。通常の外部HTTP画像は [media.py:85](/Users/ngsklab/Code/Mono/src/embedders/media.py:85) でURLのまま残る。アイコンはGoogle Fonts、scoreはVexFlow CDN、synthはTone.js CDNを利用する。数式・Mermaidの事前描画とは依存発生のタイミングが異なる。

**推奨:** READMEでは「ローカルに埋め込んだ基本コンテンツのオフライン閲覧」と「オンライン依存の追加機能」を明確に分ける。設計正本の基本本文・説明画像の保持は維持し、必要な説明画像を外部URLのまま残す場合は検出・明示する実装を検討する。全機能完全オフラインが必要ならCDN依存除去や静的代替の実装が必要であり、文言修正だけでは達成しない。

## 関連して見つかった実装上の不整合

中心の文書差分とは別に、次の2点も修正候補とする。

- **リンクラベルが反映されない:** READMEの `@[link: タイトル](url: "...")` に対し、[mono-link/parser.py](/Users/ngsklab/Code/Mono/src/components/mono-link/parser.py) は解決したラベルを捨て、OGPタイトルだけを採用する。OGPレスポンスを固定した再現で、指定タイトルでなく `OG title` になった。明示ラベル優先・OGPフォールバックへの実装修正を推奨する。
- **サーバー同期の失敗表示:** `/api/data` はエラーも通常のHTTP 200で返し、mono-exportは `response.ok` だけで成功判定する。キュー投入失敗時などに成功表示になり得る。送信側でJSONのstatusを確認するか、APIが適切なエラーHTTPステータスを返すように、両者の契約を揃える。ソース読解で確認した組合せで、ブラウザの失敗UI再現は未実施。

## 検証と次の更新順

既存テストは `uv run pytest -q --tb=short` で **312 passed, 12 subtests passed（9.40秒）**。ブラウザ起動を許可された環境で実行した。加えて一時ディレクトリでプロファイル別変換、Markdown構文、PDF出力パス、PDF失敗伝播、範囲外ダミーファイルの埋め込み、JSONエスケープ例を再現した。OGPとPDF失敗はモックで対象を限定し、外部サービスには問い合わせていない。

安全性と出力契約を優先し、更新順は以下を推奨する。

1. メディアの読込境界とコンポーネントのロード制限を修正する。
2. PDFコマンド例と失敗伝播、minimalの契約と未知プロファイル検証を修正する。
3. 共通属性構文とリンクラベルを修正し、利用ガイドを実際に変換できる例へ更新する。
4. 教育系機能の説明、CSS値、注入条件、JSONエスケープ例を訂正する。
5. Node利用とmono-sync廃止後の責務を設計判断として記録し、文書体系を整合させる。

次の実装時には既存テストに加え、今回再現した境界条件と公開サンプルの期待結果を検証する。コードや既存資料を変更する作業は、今回の調査依頼には含めていない。
