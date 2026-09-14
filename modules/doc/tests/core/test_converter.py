import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mocking missing dependencies only if they are not installed
import importlib.util

if importlib.util.find_spec("markdown") is None:
    mock_markdown = MagicMock()
    sys.modules['markdown'] = mock_markdown
if importlib.util.find_spec("PIL") is None:
    mock_pil = MagicMock()
    sys.modules['PIL'] = mock_pil
    sys.modules['PIL.Image'] = mock_pil.Image
if importlib.util.find_spec("requests") is None:
    mock_requests = MagicMock()
    sys.modules['requests'] = mock_requests
if importlib.util.find_spec("fastapi") is None:
    mock_fastapi = MagicMock()
    sys.modules['fastapi'] = mock_fastapi
if importlib.util.find_spec("uvicorn") is None:
    mock_uvicorn = MagicMock()
    sys.modules['uvicorn'] = mock_uvicorn

from pathlib import Path
import logging

from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig, ConversionError, FileProcessingError

class TestMarkdownToHTMLConverter(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_logger")
        # Ensure we don't actually read config.toml if it exists
        with patch('tomllib.load', return_value={}):
            self.config = ConversionConfig(
                input_file=Path("test.md"),
                output_file=Path("test.html"),
                css_files=None,
                template_path=None
            )
        self.converter = MarkdownToHTMLConverter(self.config, self.logger)

        # Mock dependencies on the instance
        self.converter.file_handler = MagicMock()
        self.converter.media_embedder = MagicMock()
        self.converter.css_embedder = MagicMock()
        self.converter.markdown_processor = MagicMock()
        self.converter.html_document_builder = MagicMock()
        self.converter.pdf_processor = MagicMock()

    def test_convert_success(self):
        # Setup mocks
        self.converter.file_handler.read_text.return_value = "# Test Markdown"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test HTML</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test HTML</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Test Title"
        self.converter.html_document_builder.build_document.return_value = "<html><body><h1>Test HTML</h1></body></html>"

        result = self.converter.convert()

        self.assertTrue(result)
        self.converter.file_handler.read_text.assert_called_once_with(self.config.input_file)
        self.converter.markdown_processor.convert_markdown_to_html.assert_called_once()
        self.converter.html_document_builder.build_document.assert_called_once()
        self.converter.file_handler.write_text.assert_called_once()

    def test_convert_with_css(self):
        self.config.css_files = [Path("style.css")]
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.css_embedder.load_css_files.return_value = "body { color: red; }"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"
        self.converter.html_document_builder.build_document.return_value = "<html>...</html>"

        result = self.converter.convert()

        self.assertTrue(result)
        self.converter.css_embedder.load_css_files.assert_called_once_with(self.config.css_files)
        self.assertEqual(self.converter.stats.css_files_embedded, 1)

    def test_convert_conversion_error(self):
        self.converter.file_handler.read_text.side_effect = ConversionError("Read error")

        # We need to suppress error logging to keep test output clean or just let it happen
        with self.assertLogs(self.logger, level='ERROR') as cm:
            result = self.converter.convert()

        self.assertFalse(result)
        self.assertIn("変換失敗: Read error", cm.output[0])

    def test_convert_unexpected_error(self):
        self.converter.file_handler.read_text.side_effect = Exception("Unexpected")

        with self.assertLogs(self.logger, level='ERROR') as cm:
            result = self.converter.convert()

        self.assertFalse(result)
        self.assertIn("予期しないエラー: Unexpected", cm.output[0])

    def test_convert_size_limit_error(self):
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"

        # Build a large document > 30MB
        large_content = "A" * (31 * 1024 * 1024)
        self.converter.html_document_builder.build_document.return_value = large_content
        self.converter.css_embedder.embed_css_in_html.return_value = large_content

        with self.assertLogs(self.logger, level='ERROR') as cm:
            result = self.converter.convert()

        self.assertFalse(result)
        self.assertIn("出力サイズが 30MB を超えています", cm.output[0])

    def test_convert_size_limit_force(self):
        self.config.force = True
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"

        large_content = "A" * (31 * 1024 * 1024)
        self.converter.html_document_builder.build_document.return_value = large_content
        self.converter.css_embedder.embed_css_in_html.return_value = large_content

        result = self.converter.convert()

        self.assertTrue(result)
        self.converter.file_handler.write_text.assert_called_once()

    def test_convert_size_warning(self):
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        # Include an asset to trigger detailed size breakdown in warning
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 1, {"img1": "data..."})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"

        # Build a document > 20MB but < 30MB
        content = "A" * (21 * 1024 * 1024)
        self.converter.html_document_builder.build_document.return_value = content
        self.converter.css_embedder.embed_css_in_html.return_value = content

        with self.assertLogs(self.logger, level='WARNING') as cm:
            result = self.converter.convert()

        self.assertTrue(result)
        self.assertTrue(any("出力サイズが 20MB を超えています" in msg for msg in cm.output))

    def test_convert_with_excluded_tags(self):
        self.config.excluded_tags = ['script', 'iframe']
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"
        self.converter.html_document_builder.build_document.return_value = "<html><body><h1>Test</h1></body></html>"

        with self.assertLogs(self.logger, level='INFO') as cm:
            result = self.converter.convert()

        self.assertTrue(result)
        self.assertTrue(any("✓ 除外タグ: script, iframe" in msg for msg in cm.output))

    def test_convert_write_output_file_processing_error(self):
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"

        from src.config import FileProcessingError
        self.converter.file_handler.write_text.side_effect = FileProcessingError("Mock write error")

        with self.assertLogs(self.logger, level='ERROR') as cm:
            result = self.converter.convert()

        self.assertFalse(result)
        self.assertTrue(any("出力ファイル書き込み失敗" in msg for msg in cm.output))

    def test_write_output_file_processing_error(self):
        self.converter.file_handler.write_text.side_effect = FileProcessingError("Write failed")

        with self.assertRaises(ConversionError) as context:
            self.converter._write_output("<html>Test</html>", Path("test.html"))

        self.assertEqual(str(context.exception), "出力ファイル書き込み失敗: Write failed")

    def test_format_size_units(self):
        self.assertEqual(self.converter._format_size(500), "500.0 B")
        self.assertEqual(self.converter._format_size(1024), "1.0 KB")
        self.assertEqual(self.converter._format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(self.converter._format_size(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(self.converter._format_size(1024 * 1024 * 1024 * 1024), "1.0 TB")

        # 1.5 TB
        size_bytes = 1.5 * 1024**4
        self.assertEqual(self.converter._format_size(size_bytes), "1.5 TB")

    def test_convert_pdf_success(self):
        self.config.pdf_output = Path("output.pdf")
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"
        self.converter.html_document_builder.build_document.return_value = "<html>Test</html>"
        self.converter.css_embedder.embed_css_in_html.return_value = "<html>Test</html>"
        self.converter.pdf_processor.export_html_to_pdf.return_value = True

        result = self.converter.convert()
        self.assertTrue(result)
        self.converter.pdf_processor.export_html_to_pdf.assert_called_once()

    def test_convert_pdf_failure_returns_false(self):
        self.config.pdf_output = Path("output.pdf")
        self.converter.file_handler.read_text.return_value = "# Test"
        self.converter.markdown_processor.convert_markdown_to_html.return_value = "<h1>Test</h1>"
        self.converter.media_embedder.embed_media_in_html.return_value = ("<h1>Test</h1>", 0, {})
        self.converter.html_document_builder.extract_title_from_html.return_value = "Title"
        self.converter.html_document_builder.build_document.return_value = "<html>Test</html>"
        self.converter.css_embedder.embed_css_in_html.return_value = "<html>Test</html>"
        self.converter.pdf_processor.export_html_to_pdf.return_value = False

        result = self.converter.convert()
        self.assertFalse(result)
        self.converter.pdf_processor.export_html_to_pdf.assert_called_once()

if __name__ == '__main__':
    unittest.main()
