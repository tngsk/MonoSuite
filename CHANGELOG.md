# Changelog

## Unreleased

### 2026-09-14

- 段階B2（Doc独立移行）完了：移行元 `tngsk/Mono`（コミット `e84c459`）からコア資産（src, tests, doc, pyproject.toml, uv.lock, package.json, package-lock.json, main.py, LICENSE）を `modules/doc` へ独立移行。ルートに `uv` ワークスペースを導入して依存関係を一元管理。modules/doc のテスト全271件通過、PlaywrightによるHTML・PDF生成の完全再現、および modules/space の既存テスト全件通過を確認。
- 統合開発計画文書を `modules/space/docs/planning/` からルート `docs/planning/` へ昇格。共通契約案（`COMMON-CONTRACT-PROPOSAL.md`）および移行受入記録（`STAGE-B2-MIGRATION-REPORT.md`）を策定。
- 開発計画をB1仕様整理・B2 Doc独立移行・B3契約検証へ具体化。各段階の成果物・完了条件・未決事項を明記し、リリース方針とDoc仕様レビューの現在地を統一。

- Spaceの本体を `src/mono_space/`、テストを `tests/`、文書を `docs/`、生成物を `dist/` に整理。CLI入口 `build.py` は維持し、既定出力を `dist/presentation.html`、ビルドキャッシュを出力先配下へ変更。整理後はPython 54件・Node 13件成功。

- ルートの利用案内・版・変更履歴を追加し、移行状態と作例リンクを更新。
- ブラウザ回帰テストを専用原稿から生成するよう変更。旧デモへの依存を除去し、合成キーイベントをDOM要素から送信するよう修正。
- Space：Python 53件・Node 13件成功。Chromiumでブラウザ回帰8項目成功。通常・数式サンプルの俯瞰とフォーカスを目視確認。
- 空のnpmキャッシュから固定依存を取得し、生成キャッシュのないコピー先で通常8ノード・数式7ノードを生成。
- 別リポジトリ `tngsk/Mono` のプログラムをDocと誤認して調査したため、Doc検証済みの扱いを撤回。調査対象と実行内容を訂正記録に保存。作成した `tests/fixtures/integration/` は未採用の検証用原稿であり、Docの対応保証や合意済み契約ではない。

## 0.1.0 — 2026-09-11

- Spaceを `modules/space` に移行し、独立Git履歴を開始。
- 基準コミット：`a7cc6beee2cf80c92772986b8e4dff195d6fc1d4`。
- ローカルタグ：`v0.1.0`。2026-09-14にGitHubのmainが同コミットと確認できたが、リモートタグは存在しなかった。
- この版での目視確認とクリーン依存取得は未完了だった。後日の検証はUnreleased参照。
