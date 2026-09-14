"""
CSS Embedder
============
Embeds CSS content into HTML documents.
"""

import logging
import re
from pathlib import Path
from typing import List

from src.config import FileProcessingError
import tomllib
from typing import Optional

from src.constants import (
    BASE_CSS_FILE,
    HTML_HEAD_CLOSING_TAG,
    HTML_OPENING_TAG,
    TEMPLATES_DIR,
    THEMES_TOML_FILE,
)
from src.handlers.file import FileHandler


class CSSEmbedder:
    """CSSファイルを<style>タグで埋め込むクラス"""

    def __init__(self, logger: logging.Logger, file_handler: FileHandler):
        self.logger = logger
        self.file_handler = file_handler

    def get_base_css(self, html_content: str = "", markdown_dir: Optional[Path] = None) -> str:
        """base.css および themes.toml ファイルを読み込んで <style> タグで返す"""
        css_blocks = []

        # テーマ設定の決定
        themes_toml_path = TEMPLATES_DIR / "core" / THEMES_TOML_FILE

        # html_content からカスタム設定ファイル指定を探す
        if html_content and markdown_dir:
            match = re.search(r'<mono-theme[^>]*config=[\'"]([^\'"]+)[\'"]', html_content)
            if match:
                custom_config = match.group(1).strip()
                if custom_config:
                    custom_path = markdown_dir / custom_config
                    if custom_path.exists() and custom_path.is_file():
                        self.logger.info(f"カスタムテーマ設定ファイルを読み込みます: {custom_path}")
                        themes_toml_path = custom_path
                    else:
                        self.logger.warning(f"指定されたカスタムテーマ設定ファイルが見つかりません: {custom_path}")

        # TOMLファイルの読み込みとCSS変換
        try:
            if themes_toml_path.exists():
                with open(themes_toml_path, "rb") as f:
                    themes_data = tomllib.load(f)

                for theme_name, theme_vars in themes_data.items():
                    is_default = theme_vars.pop("is_default", False)
                    selector = ":root" if is_default else f'[data-theme="{theme_name}"]'

                    css_rule = f"{selector} {{\n"
                    for var_name, var_value in theme_vars.items():
                        css_rule += f"  --{var_name}: {var_value};\n"
                    css_rule += "}"

                    css_blocks.append(css_rule)
        except Exception as e:
            self.logger.warning(f"テーマ設定({themes_toml_path})の読み込みエラー: {e}")

        # base.css の読み込み
        css_file = TEMPLATES_DIR / "core" / BASE_CSS_FILE
        try:
            if css_file.exists():
                css_content = self.file_handler.read_text(css_file)
                css_blocks.append(css_content)
            else:
                self.logger.warning(f"base.css が見つかりません: {css_file}")
        except Exception as e:
            self.logger.warning(f"base.css の読み込みエラー: {e}")

        if not css_blocks:
            return ""

        combined_css = "\n\n".join(css_blocks)
        return f"<style>\n{combined_css}\n</style>"

    def load_css_files(self, css_file_paths: List[Path]) -> str:
        """
        複数のCSSファイルを読み込む

        Args:
            css_file_paths: CSSファイルパスのリスト

        Returns:
            結合されたCSS文字列
        """
        css_contents = []

        for css_path in css_file_paths:
            css_path = Path(css_path)
            if not css_path.exists():
                self.logger.warning(f"CSSファイルが見つかりません: {css_path}")
                continue

            try:
                content = self.file_handler.read_text(css_path)
                css_contents.append(content)
                self.logger.debug(f"CSS読み込み完了: {css_path.name}")
            except FileProcessingError as e:
                self.logger.error(f"CSS読み込み失敗: {e}")

        return "\n".join(css_contents)

    def embed_css_in_html(self, html_content: str, css_content: str, markdown_dir: Optional[Path] = None) -> str:
        """
        CSSコンテンツを埋め込む
        テンプレートプレースホルダーが存在すれば置換し、なければタグベースで挿入する

        Args:
            html_content: 対象のHTML
            css_content: 埋め込むカスタムCSS
            markdown_dir: Markdownファイルのあるディレクトリ（カスタムテーマ設定の検索用）

        Returns:
            CSS埋め込み後のHTML
        """
        base_css = self.get_base_css(html_content=html_content, markdown_dir=markdown_dir)
        css_block = f"    <style>\n{css_content}\n    </style>\n" if css_content else ""

        # プレースホルダーの置換を試みる
        has_replaced_base = False
        has_replaced_custom = False

        if "{CODE_BLOCK_CSS}" in html_content:
            html_content = html_content.replace("{CODE_BLOCK_CSS}", base_css)
            has_replaced_base = True

        if "{CSS_BLOCK}" in html_content:
            html_content = html_content.replace("{CSS_BLOCK}", css_block)
            has_replaced_custom = True

        # 両方のプレースホルダーが置換された場合は終了
        if has_replaced_base and has_replaced_custom:
            return html_content

        # 置換されなかったCSSがあればまとめて挿入
        css_to_insert = []
        if not has_replaced_base and base_css:
            css_to_insert.append(base_css)
        if not has_replaced_custom and css_block:
            css_to_insert.append(css_block)

        if not css_to_insert:
            return html_content

        combined_css = "\n".join(css_to_insert)

        # </head> の直前に挿入
        head_match = re.search(HTML_HEAD_CLOSING_TAG, html_content, re.IGNORECASE)
        if head_match:
            insert_pos = head_match.start()
            return (
                html_content[:insert_pos] + combined_css + "\n" + html_content[insert_pos:]
            )

        # <html> タグを探す
        html_match = re.search(HTML_OPENING_TAG, html_content, re.IGNORECASE)
        if html_match:
            insert_pos = html_match.end()
            return (
                html_content[:insert_pos]
                + "\n"
                + combined_css
                + "\n"
                + html_content[insert_pos:]
            )

        # どちらもない場合は最初に挿入
        return combined_css + "\n" + html_content
