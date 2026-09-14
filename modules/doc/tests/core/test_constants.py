import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from pathlib import Path

# Import the module to test
import src.constants as constants

class TestConstants(unittest.TestCase):
    def test_file_paths_and_directories(self):
        """Test File Paths & Directories constants"""
        self.assertIsInstance(constants.TEMPLATES_DIR, Path)
        self.assertEqual(constants.TEMPLATES_DIR.name, "templates")

        self.assertIsInstance(constants.COMPONENTS_DIR, Path)
        self.assertEqual(constants.COMPONENTS_DIR.name, "components")

        self.assertIsInstance(constants.DEFAULT_TEMPLATE_PATH, Path)
        self.assertEqual(constants.DEFAULT_TEMPLATE_PATH.name, "default.html")
        self.assertEqual(constants.DEFAULT_TEMPLATE_PATH.parent, constants.TEMPLATES_DIR)

        self.assertEqual(constants.BASE_CSS_FILE, "base.css")

        self.assertIsInstance(constants.ALLOWED_COMPONENTS, list)
        self.assertIn("mono-badge", constants.ALLOWED_COMPONENTS)
        self.assertIn("mono-layout", constants.ALLOWED_COMPONENTS)



    def test_mime_type_registry(self):
        """Test MIME Type Registry constants"""
        self.assertIsInstance(constants.MIME_TYPE_REGISTRY, dict)
        self.assertIn(".png", constants.MIME_TYPE_REGISTRY)
        self.assertEqual(constants.MIME_TYPE_REGISTRY[".png"], "image/png")
        self.assertIn(".jpg", constants.MIME_TYPE_REGISTRY)
        self.assertIn(".svg", constants.MIME_TYPE_REGISTRY)
        self.assertEqual(constants.MIME_TYPE_REGISTRY[".svg"], "image/svg+xml")

        self.assertEqual(constants.DEFAULT_MIME_TYPE, "application/octet-stream")

    def test_file_io_encoding(self):
        """Test File I/O Encoding constants"""
        self.assertEqual(constants.DEFAULT_TEXT_ENCODING, "utf-8")

    def test_html_processing(self):
        """Test HTML Processing constants"""
        self.assertIsInstance(constants.LOG_FORMAT, str)
        self.assertIsInstance(constants.LOG_DATE_FORMAT, str)
        self.assertIsInstance(constants.HTML_OPENING_TAG, str)
        self.assertIsInstance(constants.HTML_HEAD_CLOSING_TAG, str)
        self.assertIsInstance(constants.HTML_IMG_TAG_PATTERN, str)
        self.assertIsInstance(constants.HTML_SCRIPT_TAG_PATTERN, str)
        self.assertIsInstance(constants.HTML_TABLE_STYLE_PATTERN, str)
        self.assertIsInstance(constants.HTML_TAG_REMOVAL_PATTERN_TEMPLATE, str)
        self.assertIsInstance(constants.HTML_IPYNB_LINK_PATTERN, str)
        self.assertIn("github.com", constants.GITHUB_BASE_URL)
        self.assertIn("github", constants.COLAB_GITHUB_BASE_URL)
        self.assertIn("colab-badge.svg", constants.COLAB_BADGE_URL)
        self.assertIsInstance(constants.HTML_COLAB_BADGE_IMG, str)
        self.assertIsInstance(constants.HTML_COLAB_LINK_TEMPLATE, str)
        self.assertEqual(constants.REGEX_FLAG_IGNORECASE, "IGNORECASE")

    def test_markdown_processing(self):
        """Test Markdown Processing constants"""
        self.assertIsInstance(constants.MARKDOWN_EXTENSIONS, list)
        self.assertIn("fenced_code", constants.MARKDOWN_EXTENSIONS)
        self.assertIn("tables", constants.MARKDOWN_EXTENSIONS)
        self.assertIn("nl2br", constants.MARKDOWN_EXTENSIONS)
        self.assertIn("toc", constants.MARKDOWN_EXTENSIONS)
        self.assertIn("md_in_html", constants.MARKDOWN_EXTENSIONS)

    def test_size_formatting(self):
        """Test Size Formatting constants"""
        self.assertEqual(constants.SIZE_UNITS, ("B", "KB", "MB", "GB", "TB"))
        self.assertEqual(constants.SIZE_UNIT_THRESHOLD, 1024)

    def test_cli_and_output(self):
        """Test CLI & Output constants"""
        self.assertIsInstance(constants.HEADER_TEXT, str)
        self.assertIn("Markdown to Single-File HTML Converter", constants.HEADER_TEXT)

if __name__ == '__main__':
    unittest.main()
