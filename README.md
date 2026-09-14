# Mono Suite

同じMarkdown原稿から、Spaceで発表し、Docで配布資料を生成する制作環境を開発しています。

現在利用できるのは **Mono Space** です。Doc統合・PDF配布セット・制作UIは未実装です。

- [Spaceの使い方](modules/space/README.md)
- [検証状況と既知の問題](modules/space/docs/MIGRATION.md)
- [開発計画](modules/space/docs/planning/DEVELOPMENT-PLAN.md)
- [調査対象の訂正記録](modules/space/docs/planning/INVESTIGATION-CORRECTION.md)

## 試す

Python 3.9以降で実行します。

```sh
cd modules/space
python3 build.py examples/standard/document.md -o dist/presentation.html --offline
```

生成した `dist/presentation.html` をブラウザで開きます。数式の初期設定はSpaceの使い方を参照してください。

v0.1.0は開発基準点です。ライセンスと一般公開の条件は未確定です。
