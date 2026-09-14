#!/usr/bin/env python3
"""
Markdown to Single-File HTML Converter - CLI Entry Point
=========================================================
Command-line interface for converting Markdown to self-contained HTML.

Author: Engineering Team
License: MIT
"""

import argparse
import sys
from pathlib import Path

from src.config import ConversionConfig
from src.converter import MarkdownToHTMLConverter
from src.logger import configure_logging
from src.constants import __version__


def create_argument_parser() -> argparse.ArgumentParser:
    """コマンドラインパーサーを構築"""
    parser = argparse.ArgumentParser(
        prog="Mono",
        description="Markdown をBase64埋め込み画像・CSS対応の単一HTMLファイルに変換します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的な変換
  python main.py document.md

  # CSSを埋め込み
  python main.py document.md -c style.css

  # 複数のCSSを埋め込み
  python main.py document.md -c style.css theme.css

  # 出力ファイルを指定
  python main.py document.md -o output.html -c style.css

  # 詳細ログを表示
  python main.py document.md -v

  # カスタムテンプレートを使用
  python main.py document.md -t custom_template.html

  # 除外タグを指定
  python main.py document.md -e hr div

  # 全オプション組み合わせ
  python main.py document.md -o output.html -c style.css -e hr -v
        """,
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="入力Markdownファイルのパス",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="出力HTMLファイルのパス（省略時は {入力ファイル名}.html）",
    )

    parser.add_argument(
        "-c",
        "--css",
        nargs="+",
        type=Path,
        default=None,
        help="埋め込むCSSファイルのパス（複数指定可能）",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="詳細なログを出力する",
    )

    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        default=None,
        help="カスタムHTMLテンプレートファイルのパス",
    )

    parser.add_argument(
        "-e",
        "--excluded-tags",
        nargs="+",
        type=str,
        default=None,
        help="削除対象のHTMLタグ（複数指定可能。例：-e hr div span）",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="30MBの出力サイズ制限をバイパスして強制保存する",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="外部エクスポートモジュール（mono-export）を強制的に有効にする",
    )

    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        default=None,
        help="用途別プロファイルプリセット（minimal, standard, presentation, interactive, all）",
    )

    parser.add_argument(
        "--pdf",
        type=Path,
        nargs='?',
        const=True,
        default=None,
        help="出力されたHTMLからPDFを生成します。ファイルパスを指定しない場合、{入力ファイル名}.pdf になります。",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Monoのバージョンを表示します",
    )

    return parser


def print_header(config: ConversionConfig) -> None:
    """処理開始時のヘッダー情報を表示"""
    print("\n" + "=" * 75)
    print("  Markdown → Single-File HTML Converter")
    print("=" * 75)
    print(f"  入力ファイル: {config.input_file}")
    print(f"  出力ファイル: {config.resolve_output_file()}")
    if config.profile:
        print(f"  プロファイル: {config.profile}")
    if config.css_files:
        print(f"  CSSファイル:  {', '.join(str(f) for f in config.css_files)}")
    if config.excluded_tags:
        print(f"  除外タグ:     {', '.join(config.excluded_tags)}")
    print("=" * 75 + "\n")


def main() -> int:
    """
    メイン処理

    Returns:
        終了コード（0=成功、1=失敗）
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    # ロギング設定
    logger = configure_logging(verbose=args.verbose)

    # 設定の構築
    config = ConversionConfig(
        input_file=args.input_file,
        output_file=args.output,
        css_files=args.css,
        template_path=args.template,
        verbose=args.verbose,
        excluded_tags=args.excluded_tags,
        force=args.force,
        enable_export=args.export,
        pdf_output=args.pdf,
        profile=args.profile,
    )

    # ヘッダー表示
    print_header(config)

    # 変換実行
    converter = MarkdownToHTMLConverter(config, logger)
    success = converter.convert()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
