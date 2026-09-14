import argparse
import sys
from pathlib import Path

from . import __version__
from .pipeline import BuildPipeline, PipelineError


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mono",
        description="Mono Suite - 単一Markdown原稿から発表用Spaceと配布用Docを一括生成する制作環境",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="バージョンを表示します",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="実行するサブコマンド")

    # mono build サブコマンド
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

    return parser


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

    return 0


if __name__ == "__main__":
    sys.exit(main())
