import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
import logging
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.embedders.css import CSSEmbedder
from src.handlers.file import FileHandler
from src.config import FileProcessingError


class TestCSSEmbedder(unittest.TestCase):
    def setUp(self):
        # Setup common objects for testing
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_file_handler = MagicMock(spec=FileHandler)
        self.css_embedder = CSSEmbedder(
            logger=self.mock_logger,
            file_handler=self.mock_file_handler
        )

    @patch('src.embedders.css.Path.exists')
    def test_load_css_files_success(self, mock_exists):
        mock_exists.return_value = True

        path1 = Path("style1.css")
        path2 = Path("style2.css")

        # Setup mock file handler to return specific content based on path
        def read_text_side_effect(path):
            if path.name == "style1.css":
                return "body { color: red; }"
            elif path.name == "style2.css":
                return "div { margin: 10px; }"
            return ""

        self.mock_file_handler.read_text.side_effect = read_text_side_effect

        # Test loading multiple files
        result = self.css_embedder.load_css_files([path1, path2])

        # Verify result and method calls
        expected = "body { color: red; }\ndiv { margin: 10px; }"
        self.assertEqual(result, expected)
        self.assertEqual(self.mock_file_handler.read_text.call_count, 2)

    @patch('src.embedders.css.Path.exists')
    def test_load_css_files_missing_file(self, mock_exists):
        # Setup a mock path that exists and one that doesn't
        path_exists = Path("exists.css")
        path_missing = Path("missing.css")

        mock_exists.side_effect = [True, False]

        self.mock_file_handler.read_text.return_value = "content"

        # Call load_css_files
        result = self.css_embedder.load_css_files([path_exists, path_missing])

        # Verify the missing file was skipped and logged, while the existing one was read
        self.assertEqual(result, "content")
        self.mock_logger.warning.assert_called_once()
        self.assertEqual(self.mock_file_handler.read_text.call_count, 1)

    @patch('src.embedders.css.Path.exists')
    def test_load_css_files_processing_error(self, mock_exists):
        mock_exists.return_value = True

        path1 = Path("error.css")
        path2 = Path("success.css")

        # Raise FileProcessingError on first call, succeed on second
        self.mock_file_handler.read_text.side_effect = [
            FileProcessingError("Error reading file"),
            "success content"
        ]

        # Call load_css_files
        result = self.css_embedder.load_css_files([path1, path2])

        # Verify the error was logged and execution continued
        self.assertEqual(result, "success content")
        self.mock_logger.error.assert_called_once()
        self.assertEqual(self.mock_file_handler.read_text.call_count, 2)

    @patch.object(CSSEmbedder, 'get_base_css')
    def test_embed_css_in_html_empty_css(self, mock_get_base_css):
        mock_get_base_css.return_value = ""
        html = "<html><body>Test</body></html>"
        result = self.css_embedder.embed_css_in_html(html, "")
        self.assertEqual(result, html)

    @patch.object(CSSEmbedder, 'get_base_css')
    def test_embed_css_in_html_with_head_closing(self, mock_get_base_css):
        mock_get_base_css.return_value = ""
        html = "<!DOCTYPE html><html><head><title>Test</title></head><body>Hello</body></html>"
        css = "body { color: black; }"

        result = self.css_embedder.embed_css_in_html(html, css)

        expected_tag = f"    <style>\n{css}\n    </style>\n"
        self.assertIn(expected_tag, result)
        self.assertTrue(result.find(expected_tag) < result.find("</head>"))

    @patch.object(CSSEmbedder, 'get_base_css')
    def test_embed_css_in_html_with_html_opening_only(self, mock_get_base_css):
        mock_get_base_css.return_value = ""
        html = "<html><body>Hello</body></html>"
        css = "body { color: black; }"

        result = self.css_embedder.embed_css_in_html(html, css)

        expected_tag = f"    <style>\n{css}\n    </style>\n"
        self.assertIn(expected_tag, result)
        self.assertTrue(result.find("<html>") < result.find(expected_tag))

    @patch.object(CSSEmbedder, 'get_base_css')
    def test_embed_css_in_html_no_tags(self, mock_get_base_css):
        mock_get_base_css.return_value = ""
        html = "Hello World"
        css = "body { color: black; }"

        result = self.css_embedder.embed_css_in_html(html, css)

        expected_tag = f"    <style>\n{css}\n    </style>\n"
        expected = f"{expected_tag}\n{html}"
        self.assertEqual(result, expected)

    @patch.object(CSSEmbedder, 'get_base_css')
    def test_embed_css_in_html_with_placeholders(self, mock_get_base_css):
        mock_get_base_css.return_value = "<style>base css</style>"
        html = "<html><head>{CODE_BLOCK_CSS}{CSS_BLOCK}</head><body>Hello</body></html>"
        css = "body { color: black; }"

        result = self.css_embedder.embed_css_in_html(html, css)

        self.assertIn("<style>base css</style>", result)
        self.assertIn(f"    <style>\n{css}\n    </style>\n", result)
        self.assertNotIn("{CODE_BLOCK_CSS}", result)
        self.assertNotIn("{CSS_BLOCK}", result)

    def test_get_base_css_includes_design_tokens(self):
        self.mock_file_handler.read_text.return_value = "/* base.css content with minmax(0, var(--content-max-width)) */"
        result = self.css_embedder.get_base_css()
        self.assertIn("--radius-sm:", result)
        self.assertIn("--radius-md:", result)
        self.assertIn("--shadow-sm:", result)
        self.assertIn("--content-max-width:", result)

    def test_base_css_space_marker_system(self):
        base_css_path = Path(__file__).parent.parent.parent / "src" / "templates" / "core" / "base.css"
        content = base_css_path.read_text(encoding="utf-8")
        self.assertIn("--marker-space-normal:", content)
        self.assertIn("--marker-space-ai:", content)
        self.assertIn("--marker-space-warning:", content)
        self.assertIn(".marker,", content)
        self.assertIn(".heading-marker", content)
        self.assertIn(".marker-ai", content)
        self.assertIn(".marker-warning", content)
        self.assertIn("box-decoration-break: clone;", content)


if __name__ == '__main__':
    unittest.main()
