"""
Markdown to HTML Converter
==========================
Main orchestrator that coordinates all conversion components.
"""

import logging
from pathlib import Path

from src.config import (
    ConversionConfig,
    ConversionError,
    ConversionStats,
    FileProcessingError,
)
from src.embedders.css import CSSEmbedder
from src.embedders.media import MediaEmbedder
from src.handlers.file import FileHandler
from src.processors.html import HTMLDocumentBuilder
from src.processors.markdown import MarkdownProcessor
from src.processors.pdf import PDFProcessor

class MarkdownToHTMLConverter:
    """Markdown → 単一HTML変換の統合オーケストレータ"""

    def __init__(self, config: ConversionConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.file_handler = FileHandler(logger)
        self.media_embedder = MediaEmbedder(logger, self.file_handler)
        self.css_embedder = CSSEmbedder(logger, self.file_handler)
        self.markdown_processor = MarkdownProcessor(logger, self.file_handler)
        self.html_document_builder = HTMLDocumentBuilder(
            logger, template_path=config.template_path
        )
        self.pdf_processor = PDFProcessor(logger)
        self.stats = ConversionStats()

    def convert(self) -> bool:
        """
        変換処理の実行

        Returns:
            成功時True、失敗時False
        """
        try:
            self.logger.info(f"変換開始: {self.config.input_file}")

            # 除外タグを出力
            if self.config.excluded_tags:
                tags_str = ", ".join(self.config.excluded_tags)
                self.logger.info(f"✓ 除外タグ: {tags_str}")

            # Step 1: Markdown読み込み
            markdown_content = self.file_handler.read_text(self.config.input_file)
            self.logger.info("✓ Markdownファイルを読み込みました")

            # Step 2: Markdown → HTML変換
            html_body = self.markdown_processor.convert_markdown_to_html(
                markdown_content
            )
            self.logger.info("✓ Markdownを中間HTMLに変換しました")

            # Step 3: CSS読み込み
            css_content = ""
            if self.config.css_files:
                css_content = self.css_embedder.load_css_files(self.config.css_files)
                if css_content:
                    self.stats.css_files_embedded = len(self.config.css_files)
                    self.logger.info(
                        f"✓ {len(self.config.css_files)} 個のCSSを読み込みました"
                    )

            # Step 4: メディア埋め込み
            markdown_dir = self.config.input_file.parent
            is_minimal = self.config.profile == "minimal"
            html_body, media_count, asset_store = (
                self.media_embedder.embed_media_in_html(
                    html_body, markdown_dir, lazy_load=(not is_minimal)
                )
            )
            self.stats.images_embedded = media_count
            self.logger.info(f"✓ {media_count} 件のメディアをBase64で埋め込みました")

            # Step 5: HTMLドキュメント生成
            title = self.html_document_builder.extract_title_from_html(html_body)
            html_document = self.html_document_builder.build_document(
                html_body=html_body,
                title=title,
                excluded_tags=self.config.excluded_tags,
                connect_src=self.config.connect_src,
                asset_store=asset_store,
                enable_export=self.config.enable_export,
                csp_additions=self.config.csp_additions,
                profile_components=self.config.profile_components,
                profile=self.config.profile,
            )
            self.logger.info(
                f"✓ HTMLドキュメント構造を生成しました (タイトル: {title})"
            )

            # Step 5.5: CSS埋め込み
            html_document = self.css_embedder.embed_css_in_html(html_document, css_content, markdown_dir=markdown_dir)

            # Validate Size
            total_size = len(html_document.encode("utf-8"))
            if total_size > 20 * 1024 * 1024:
                self.logger.warning(
                    f"⚠️ 出力サイズが 20MB を超えています: {self._format_size(total_size)}"
                )
                for asset_id, asset_data in asset_store.items():
                    asset_size = len(asset_data.encode("utf-8"))
                    percentage = (asset_size / total_size) * 100
                    self.logger.warning(
                        f"   - {asset_id}: {percentage:.1f}% ({self._format_size(asset_size)})"
                    )

            if total_size > 30 * 1024 * 1024 and not self.config.force:
                self.logger.error(
                    f"❌ 出力サイズが 30MB を超えています ({self._format_size(total_size)})。"
                )
                self.logger.error(
                    "   保存を中止します。--force オプションで強制保存できます。"
                )
                return False

            # Step 6: 出力
            output_file = self.config.resolve_output_file()
            self._write_output(html_document, output_file)

            # Step 7: PDF出力 (オプション)
            pdf_file = self.config.resolve_pdf_output_file()
            if pdf_file:
                pdf_success = self.pdf_processor.export_html_to_pdf(output_file, pdf_file)
                if not pdf_success:
                    self.logger.error("PDF生成に失敗しました。")
                    return False

            return True

        except ConversionError as e:
            self.logger.error(f"変換失敗: {e}")
            return False
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}", exc_info=True)
            return False

    def _write_output(self, html_content: str, output_file: Path) -> None:
        """出力ファイルを書き込み"""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self.file_handler.write_text(output_file, html_content)
            self.stats.output_file_size = len(html_content.encode("utf-8"))
            self.logger.info(f"✅ 変換完了: {output_file}")
            self.logger.info(
                f"   ファイルサイズ: {self._format_size(self.stats.output_file_size)}"
            )
        except FileProcessingError as e:
            raise ConversionError(f"出力ファイル書き込み失敗: {e}") from e

    @staticmethod
    def _format_size(size_bytes: float) -> str:
        """バイト数をヒューマンリーダブルなサイズに変換"""
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
