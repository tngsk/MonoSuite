# Mono Suite v0.1 状態と整理後の運用

更新：2026-09-14。Spaceの独立リポジトリへの移行と、Suite内でのファイル整理を実施済み。

## 保存済みの基準点

- 2026-09-11のコミット `a7cc6be` とローカルタグ `v0.1.0` が移行直後の基準点。
- 今回のディレクトリ整理は基準点の後の変更。タグを書き換えていない。
- 9月14日の確認ではリモートmainは同コミット、リモートタグは未作成。
- 旧プロジェクトのコードや履歴は変更していない。Docの独立移行は今後の計画。

## ディレクトリ整理

| 移行直後 | 整理後 |
|---|---|
| ルートのPython生成器・インポーター | `src/mono_space/` |
| ルートの `build.py` | CLI入口として維持。本体は `src/mono_space/build.py` |
| `src/*.js`、`src/styles.css`、`engine.html` | `src/mono_space/web/` |
| `tools/math-svg.cjs` | `src/mono_space/math-svg.cjs` |
| ルートの `test_*.py` | `tests/` |
| DESIGN・DEVELOPMENT・SYNTAX | `docs/` |
| 作例原稿・元画像 | `examples/` を維持 |
| 生成HTML・ブラウザテストHTML | `dist/` |

Pythonの内部モジュールは `mono_space` パッケージから参照する。旧フラット形式のPython importは変更が必要。CLIの `python3 build.py` は継続利用できる。

## 再現手順

`modules/space` で実行する。

```sh
npm ci --ignore-scripts
PYTHONPATH=src python3 -m unittest discover -s tests
node --test tests/core.test.cjs
python3 build.py examples/standard/document.md --offline
python3 build.py examples/math/document.md -o dist/examples/math/presentation.html --offline
python3 tests/build_browser_test.py
```

通常の出力は `dist/presentation.html`、ブラウザ回帰は `dist/tests/browser.html`。
出力先は `-o` で変更できる。ビルド時の数式・OGPキャッシュは出力フォルダーの `.spatial-cache/` に置く。原稿の相対画像参照は原稿フォルダーを基準に維持する。低水準の `parse()` を直接利用する場合は、従来の入力側キャッシュが既定で、`cache_root` により変更できる。

整理前にあった生成HTMLは `dist/` の対応する場所へ移動した。既存の作例キャッシュは `dist/cache-archive/` に保管し、新しい生成処理では再生成する。`dist/` と依存・キャッシュはGit管理対象外。

## 検証と残件

9月14日にPython 53件・Node 13件、Chromiumブラウザ回帰8項目、通常・数式生成と俯瞰／フォーカスの目視確認を実施した。空のnpmキャッシュから依存を取得したコピー先でも生成に成功した。整理後の検証結果は[開発記録](DEVELOPMENT.md)を参照。

実機タッチ、各ブラウザでの全画面、実サイトのOGP取得、公開ライセンスの決定は残件。v0.1は一般公開品質の宣言ではない。

関連：[開発計画](planning/DEVELOPMENT-PLAN.md)、[リリース方針](planning/RELEASE-STRATEGY.md)、[Doc統合](planning/MONO-DOC-INTEGRATION.md)。
