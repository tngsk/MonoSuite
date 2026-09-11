# Mono Suite v0.1 移行ガイド

移行時に読む文書はこのファイルだけです。更新：2026-09-11。移行・Git初期化・タグ・公開は未実施。

## 1. 今回行うこと

普段の開発ディレクトリに新しい`mono-suite`を作り、現在のSpaceを`modules/space`にコピーして、新しいGit履歴を開始します。旧フォルダーと履歴は残します。Doc統合や新機能は移行後の作業です。

現在のSpaceは上位のホームディレクトリのGit管理下にあります。旧環境でGitの初期化・履歴整理を行わず、コピー先で独立リポジトリを作ってください。Codex専用フォルダーに置く必要はありません。

## 2. 現在の確認結果

- Python 3.9.6、Node.js v26.7.0、npm 11.19.0で確認。
- Python53件・Node13件が成功。選別コピー先でも成功。
- 通常サンプル8ノード・数式サンプル7ノードを生成できました。
- 通常サンプルは自作の幾何学PNGのみを使用。実教材画像への依存を除去済み。
- **未確認**：CSS復旧後の実ブラウザ目視・操作、新規環境での依存取得。数式の検証には既存node_modulesをコピーして使用しました。
- **公開前に必要**：ライセンスの決定、文書内の個人パスの一般化。v0.1は開発基準点であり、一般公開品質の宣言ではありません。

## 3. コピーするファイル

| コピー元（Space直下） | 新規リポジトリ内の保存先 |
|---|---|
| `*.py`（テストを含む）、`engine.html` | `modules/space/` |
| `src/`、`tools/` | `modules/space/`内の同名フォルダー |
| `tests/`（生成済みbrowser.htmlを除く） | `modules/space/tests/` |
| `package.json`、`package-lock.json` | `modules/space/` |
| README、SYNTAX、DESIGN、DEVELOPMENT | `modules/space/` |
| `examples/standard/`、`examples/math/` | `modules/space/examples/`（生成物・キャッシュを除く） |
| `docs/MIGRATION.md`、`docs/planning/` | `modules/space/docs/`（相対リンクを維持） |

**コピーしないもの**：`docs/archive/`、node_modules、キャッシュ、生成HTML・旧PDF、元の`assets/`、実教材のexamples、変換レポート、Codex設定、既存Git履歴。

細かなファイル一覧は別管理しません。この表を移行対象の正本とします。`engine.html`は必要なソースなので、HTMLを一律除外しないでください。

## 4. コピーと確認

以下はSpaceフォルダーを作業ディレクトリとして実行します。保存先は例です。既存の場所なら停止します。

```sh
python3 - <<'PY'
from pathlib import Path
import shutil

source = Path.cwd()
assert (source / 'build.py').is_file(), 'Spaceフォルダーで実行してください'
destination = Path.home() / 'Code' / 'mono-suite'
if destination.exists():
    raise SystemExit('保存先が存在するため停止しました')
module = destination / 'modules' / 'space'
module.mkdir(parents=True)
for path in source.glob('*.py'):
    shutil.copy2(path, module / path.name)
for name in ('engine.html', 'package.json', 'package-lock.json',
             'README.md', 'SYNTAX.md', 'DESIGN.md', 'DEVELOPMENT.md'):
    shutil.copy2(source / name, module / name)
ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store',
                               '.spatial-cache', 'presentation*.html', 'browser.html')
for name in ('src', 'tools', 'tests', 'examples/standard', 'examples/math', 'docs/planning'):
    shutil.copytree(source / name, module / name, ignore=ignore)
shutil.copy2(source / 'docs/MIGRATION.md', module / 'docs/MIGRATION.md')
print(destination)
PY
```

コピー先の`modules/space`で実行：

```sh
npm ci --ignore-scripts
python3 -m unittest discover -p 'test_*.py'
node --test tests/core.test.cjs
python3 build.py examples/standard/document.md -o examples/standard/presentation.html --offline
python3 build.py examples/math/document.md -o examples/math/presentation.html --offline
```

HTMLをブラウザで開き、文字・背景・メニュー・数式、0/1〜9と前後移動、画像フォーカス、ドラッグ・ズーム、コード／TeXコピー、一時付箋を確認します。未確認や問題が残る場合は、v0.1の既知の問題として記録します。

## 5. 新しいGit履歴を開始する

新規ルート`mono-suite`に、短いREADME（SpaceのREADMEへのリンク）、`VERSION`（`0.1.0`）、`CHANGELOG.md`（上記の結果と未確認項目）を作ります。ライセンスは決定後に追加します。

ルート`.gitignore`：

```gitignore
.DS_Store
node_modules/
__pycache__/
*.pyc
.spatial-cache/
.venv/
dist/
exports/
modules/space/presentation*.html
modules/space/presentation.pdf
modules/space/examples/**/presentation*.html
modules/space/tests/browser.html
```

コピー先のREADMEから、コピーしていない私用デモへのリンクを外します。DEVELOPMENTの過去の記録は履歴として扱います。公開予定なら個人パスや権利を確認します。

新規ルートでのみ実行：

```sh
git init -b main
git rev-parse --show-toplevel
```

表示が新しい`mono-suite`自身であることを確認してから続けます。

```sh
git add README.md VERSION CHANGELOG.md .gitignore modules
git diff --cached --stat
git diff --cached --check
git diff --cached
```

内容を確認し、必要なLICENSE等も追加してコミット：

```sh
git commit -m "chore: establish Mono Suite v0.1 baseline"
git tag -a v0.1.0 -m "Mono Suite v0.1 development baseline"
```

リモートの作成・push・公開は別途行います。旧リポジトリへの操作やforce pushは不要です。移行後は新規フォルダーをCodexのローカルプロジェクトとして開き、そこで開発します。

## 6. 移行後に読むもの

- [開発計画](planning/DEVELOPMENT-PLAN.md)：同じ原稿からSpace／Docへ出力する実装順序。
- [製品・リリース方針](planning/RELEASE-STRATEGY.md)：モジュールの責務と配布形態。
- [Doc統合レビュー](planning/MONO-DOC-INTEGRATION.md)：Doc側の確認事項。

過去の移行手順・状態記録・ファイル一覧は旧環境の`docs/archive/`へ退避しました。移行の際に読む・コピーする必要はありません。
