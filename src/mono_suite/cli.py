import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__
from .pipeline import BuildPipeline, PipelineError
from .server import DevServer, SSEBroadcaster
from .watcher import FileWatcher


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mono",
        description="Mono Suite - 単一Markdown原稿から発表用Spaceと配布用Docを一括生成・プレビューする制作環境",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="バージョンを表示します",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="実行するサブコマンド")

    # 1. mono build サブコマンド
    build_parser = subparsers.add_parser("build", help="原稿から配布セット（Space HTML、Doc HTML、Doc PDF）を一括生成します")
    build_parser.add_argument("input_file", type=Path, help="入力Markdownファイルのパス")
    build_parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        help="配布セットの出力先ディレクトリ（デフォルト: dist/{原稿名}）",
    )
    build_parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="PDF出力をスキップし、HTMLのみを高速生成します",
    )
    build_parser.add_argument(
        "--no-offline",
        action="store_true",
        help="Space生成時に外部OGP等の取得を許可します（デフォルトはオフライン安全モード）",
    )

    # 2. mono dev サブコマンド
    dev_parser = subparsers.add_parser("dev", help="原稿の保存を監視し、ブラウザ上でSpaceとDocを相互切り替えプレビューするローカル開発サーバーを起動します")
    dev_parser.add_argument("input_file", type=Path, help="入力Markdownファイルのパス")
    dev_parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="サーバーのポート番号（デフォルト: 8000）",
    )
    dev_parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        help="一時出力先ディレクトリ（デフォルト: dist/{原稿名}）",
    )
    dev_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="サーバー起動時にブラウザを自動オープンしません",
    )

    # 3. mono serve サブコマンド
    serve_parser = subparsers.add_parser("serve", help="完成した配布セット（dist/{原稿名}）を閲覧するための静的プレビューサーバーを起動します")
    serve_parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=Path("dist/document"),
        help="プレビュー対象の配布ディレクトリ（デフォルト: dist/document）",
    )
    serve_parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="サーバーのポート番号（デフォルト: 8080）",
    )
    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="サーバー起動時にブラウザを自動オープンしません",
    )

    return parser


def run_dev(args: argparse.Namespace) -> int:
    input_path = args.input_file.resolve()
    if not input_path.exists():
        print(f"❌ エラー: 原稿ファイルが見つかりません: {input_path}", file=sys.stderr)
        return 1

    # 初期ビルド（高速化のため --no-pdf で起動）
    print("初期プレビューを構築しています...")
    pipeline = BuildPipeline(
        input_path=input_path,
        output_dir=args.output_dir,
        generate_pdf=False,
        offline=True,
    )
    try:
        target_dir = pipeline.run()
    except PipelineError as e:
        print(f"❌ 初期ビルドエラー: {e}", file=sys.stderr)
        return 1

    broadcaster = SSEBroadcaster()
    build_lock = threading.Lock()

    def on_change():
        acquired = build_lock.acquire(blocking=False)
        if not acquired:
            print("⚠️ ビルド実行中のため、原稿保存検知をスキップしました")
            return

        try:
            print(f"\n原稿の変更を検知しました: {input_path.name}")
            pipeline.run()
            broadcaster.broadcast("reload", {"build_id": pipeline.build_id})
            print("✓ プレビューを更新しました")
        except Exception as e:
            print(f"❌ 更新エラー: {e}")
        finally:
            build_lock.release()

    def on_full_build() -> bool:
        acquired = build_lock.acquire(blocking=True)
        try:
            print(f"\n完全配布セット（PDF含む）の生成を開始します: {input_path.name}")
            full_pipeline = BuildPipeline(
                input_path=input_path,
                output_dir=args.output_dir,
                generate_pdf=True,
                offline=True,
            )
            full_pipeline.run()
            broadcaster.broadcast("reload", {"build_id": full_pipeline.build_id})
            print("✅ 完全配布セットの生成が完了しました")
            return True
        except Exception as e:
            print(f"❌ 完全ビルドエラー: {e}")
            return False
        finally:
            build_lock.release()

    watcher = FileWatcher(input_path, on_change)
    watcher.start()

    server = DevServer(
        target_dir=target_dir,
        source_name=input_path.name,
        port=args.port,
        broadcaster=broadcaster,
        on_full_build=on_full_build,
    )

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{server.port}")

    try:
        server.start(block=True)
    finally:
        watcher.stop()

    return 0


def run_serve(args: argparse.Namespace) -> int:
    target_dir = args.target_dir.resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"❌ エラー: 配布ディレクトリが見つかりません: {target_dir}", file=sys.stderr)
        return 1

    server = DevServer(
        target_dir=target_dir,
        source_name=target_dir.name,
        port=args.port,
        broadcaster=None,
        on_full_build=None,
    )

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{server.port}")

    server.start(block=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "build":
        try:
            pipeline = BuildPipeline(
                input_path=args.input_file,
                output_dir=args.output_dir,
                generate_pdf=not args.no_pdf,
                offline=not args.no_offline,
            )
            pipeline.run()
            return 0
        except PipelineError as e:
            print(f"❌ エラー: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ 予期せぬエラー: {e}", file=sys.stderr)
            return 1

    elif args.subcommand == "dev":
        return run_dev(args)

    elif args.subcommand == "serve":
        return run_serve(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
