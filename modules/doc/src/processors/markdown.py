"""
Markdown Processor
==================
Converts Markdown content to intermediate HTML.
"""

import importlib
import logging
import re

import markdown
import markdown.util

from src.config import ConversionError
from src.constants import (
    MARKDOWN_EXTENSIONS,
)
from src.handlers.file import FileHandler
from src import registry


class MarkdownProcessor:
    """Markdownから中間HTMLへの変換処理"""

    def __init__(self, logger: logging.Logger, file_handler: FileHandler):
        self.logger = logger
        self.file_handler = file_handler
        self.parsers = self._load_component_parsers()

    def _load_component_parsers(self):
        """
        レジストリから取得したコンポーネントをインポートしてインスタンス化し、リストで返す
        """
        parsers = []

        from src.constants import COMPONENTS_DIR

        for component_name in registry.get_all_components():
            component_dir = COMPONENTS_DIR / component_name
            parser_file = component_dir / "parser.py"

            if not parser_file.exists():
                # Some system components (e.g. mono-export, mono-brush) don't have a parser
                continue

            module_name = f"src.components.{component_name}.parser"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "Parser"):
                    parser_instance = module.Parser()
                    parsers.append(parser_instance)
                    self.logger.debug(f"パーサーをロードしました: {component_name}")
            except Exception as e:
                self.logger.warning(
                    f"パーサーのロードに失敗しました ({component_name}): {e}"
                )

        return parsers

    def _protect_code_blocks(self, markdown_content: str) -> tuple[str, dict[str, str]]:
        """
        コードブロック（フェンスおよびインライン）を保護するための一時的なプレースホルダーに置換する。
        """
        blocks = {}
        counter = 0
        processed = markdown_content

        if "```" in processed or "~~~" in processed:

            def replace_fenced(match: re.Match) -> str:
                nonlocal counter
                placeholder = f"@@FENCED_CODE_BLOCK_{counter}@@"
                blocks[placeholder] = match.group(0)
                counter += 1
                return placeholder

            # 複数行のコードブロックを保護 (``` または ~~~)
            # 開始フェンスと同じ長さの閉じフェンスを要求し、ネストされたブロックを正しく扱う
            fenced_pattern = re.compile(
                r"(?s)(^[ \t]*(?P<f>`{3,}|~{3,})[^\n]*.*?\n[ \t]*(?P=f)[ \t]*(?=\n|$))",
                re.MULTILINE,
            )
            processed = fenced_pattern.sub(replace_fenced, processed)

        if "`" in processed:

            def replace_inline(match: re.Match) -> str:
                nonlocal counter
                placeholder = f"@@INLINE_CODE_BLOCK_{counter}@@"
                blocks[placeholder] = match.group(0)
                counter += 1
                return placeholder

            # インラインのコードブロックを保護
            # バックティックの数に厳密に一致させ、前後のバックティックとの混同を避ける
            inline_pattern = re.compile(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)", re.DOTALL)
            processed = inline_pattern.sub(replace_inline, processed)

        return processed, blocks

    def _restore_code_blocks(
        self, processed_content: str, blocks: dict[str, str]
    ) -> str:
        """
        保護されたプレースホルダーを元のコードブロックに戻す。

        Note:
            Performance optimization: Uses a single regex pass instead of O(M*N) sequential string replacements,
            significantly improving render times for documents with many code blocks.
        """
        if not blocks:
            return processed_content

        pattern = re.compile(r"@@(?:FENCED|INLINE)_CODE_BLOCK_\d+@@")

        def replacer(match: re.Match) -> str:
            res = blocks.get(match.group(0), match.group(0))
            return res if res is not None else match.group(0)

        return pattern.sub(replacer, processed_content)

    @staticmethod
    def _remove_html_comments(content: str) -> str:
        """HTMLコメント（<!-- ... -->）を削除する"""
        return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    def convert_markdown_to_html(self, markdown_content: str) -> str:
        """
        MarkdownをHTMLに変換

        Args:
            markdown_content: Markdown形式の文字列

        Returns:
            HTML形式の文字列

        Raises:
            ConversionError: 変換に失敗した場合
        """
        try:
            # コンポーネントパース前にコードブロックを保護
            protected_content, blocks = self._protect_code_blocks(markdown_content)

            # HTMLコメント（コードブロック外）を除去
            protected_content = self._remove_html_comments(protected_content)

            # Fast path: If the document doesn't contain any potential component markers,
            # we can safely skip running the 20+ regex component parsers over the entire document.
            if "@[" in protected_content or "::" in protected_content:
                for parser in self.parsers:
                    try:
                        protected_content = parser.process(protected_content)
                    except Exception as e:
                        self.logger.warning(f"コンポーネントパース処理でエラー: {e}")

            # コードブロックを復元
            markdown_content = self._restore_code_blocks(protected_content, blocks)

            # Markdownパーサーにカスタムコンポーネントをブロックレベル要素として認識させる
            tags_to_add = []
            for parser in self.parsers:
                if hasattr(parser, "block_level_tags"):
                    tags_to_add.extend(parser.block_level_tags)

            if tags_to_add:
                block_level = markdown.util.BLOCK_LEVEL_ELEMENTS
                if isinstance(block_level, list):
                    for tag in tags_to_add:
                        if tag not in block_level:
                            block_level.append(tag)
                elif isinstance(block_level, set):
                    for tag in tags_to_add:
                        block_level.add(tag)
                else:
                    add_fn = getattr(block_level, "add", None)
                    if callable(add_fn):
                        for tag in tags_to_add:
                            add_fn(tag)

            html = markdown.markdown(
                markdown_content,
                extensions=MARKDOWN_EXTENSIONS,
                tab_length=2,
            )
            self.logger.debug("Markdown → HTML 変換完了")
            return html
        except Exception as e:
            raise ConversionError(f"Markdown変換エラー: {e}") from e
