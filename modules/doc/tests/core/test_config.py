import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import tomllib

from src.config import (
    ConversionError,
    FileProcessingError,
    ImageEmbeddingError,
    CSSEmbeddingError,
    ConfigurationError,
    ConversionConfig,
    ConversionStats
)

class TestCustomExceptions(unittest.TestCase):
    def test_exception_inheritance(self):
        """Test that custom exceptions inherit correctly."""
        self.assertTrue(issubclass(ConversionError, Exception))
        self.assertTrue(issubclass(FileProcessingError, ConversionError))
        self.assertTrue(issubclass(ImageEmbeddingError, ConversionError))
        self.assertTrue(issubclass(CSSEmbeddingError, ConversionError))

class TestConversionConfig(unittest.TestCase):
    def test_conversion_config_defaults(self):
        """Test ConversionConfig default values."""
        config = ConversionConfig(
            input_file=Path("test.md"),
            output_file=None,
            css_files=None
        )
        self.assertIsNone(config.template_path)
        self.assertFalse(config.verbose)
        self.assertIsNone(config.excluded_tags)
        self.assertFalse(config.force)
        self.assertFalse(config.enable_export)

    def test_post_init_success(self):
        """Test initialization when config.toml is loaded successfully."""
        mock_toml_data = {
            "security": {
                "connect-src": "wss://example.com"
            }
        }
        with patch('builtins.open', mock_open(read_data=b"dummy")):
            with patch('tomllib.load', return_value=mock_toml_data):
                config = ConversionConfig(
                    input_file=Path("test.md"),
                    output_file=None,
                    css_files=None
                )
                self.assertEqual(config.connect_src, "wss://example.com")

    def test_post_init_no_security_key(self):
        """Test initialization when config.toml doesn't have security key."""
        with patch('builtins.open', mock_open(read_data=b"dummy")):
            with patch('tomllib.load', return_value={}):
                config = ConversionConfig(
                    input_file=Path("test.md"),
                    output_file=None,
                    css_files=None
                )
                self.assertEqual(config.connect_src, "")

    def test_post_init_file_not_found(self):
        """Test exception handling during initialization (e.g. FileNotFoundError)."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConversionConfig(
                input_file=Path("test.md"),
                output_file=None,
                css_files=None
            )
            # Default values should be preserved
            self.assertEqual(config.connect_src, "")

    def test_post_init_toml_decode_error(self):
        """Test exception handling during initialization (TOML decode error)."""
        with patch('builtins.open', mock_open(read_data=b"invalid toml")):
            with patch('tomllib.load', side_effect=tomllib.TOMLDecodeError("Error", "doc", 0)):
                config = ConversionConfig(
                    input_file=Path("test.md"),
                    output_file=None,
                    css_files=None
                )
                # Default values should be preserved
                self.assertEqual(config.connect_src, "")

    def test_resolve_output_file_provided(self):
        """Test resolving output file when explicitly provided."""
        config = ConversionConfig(
            input_file=Path("input.md"),
            output_file=Path("custom.html"),
            css_files=None
        )
        self.assertEqual(config.resolve_output_file(), Path("custom.html"))

    @patch('pathlib.Path.is_dir')
    def test_resolve_output_file_not_provided_no_dist(self, mock_is_dir):
        """Test resolving output file when not provided and no dist folder exists."""
        mock_is_dir.return_value = False
        config = ConversionConfig(
            input_file=Path("input.md"),
            output_file=None,
            css_files=None
        )
        self.assertEqual(config.resolve_output_file(), Path("input.html"))

    @patch('pathlib.Path.is_dir')
    def test_resolve_output_file_not_provided_with_dist(self, mock_is_dir):
        """Test resolving output file when not provided and dist folder exists."""
        mock_is_dir.return_value = True
        config = ConversionConfig(
            input_file=Path("some_dir/input.md"),
            output_file=None,
            css_files=None
        )
        self.assertEqual(config.resolve_output_file(), Path("some_dir/dist/input.html"))

    @patch('pathlib.Path.is_dir')
    def test_resolve_pdf_output_file_not_provided_no_dist(self, mock_is_dir):
        """Test resolving pdf output file when not provided and no dist folder exists."""
        mock_is_dir.return_value = False
        config = ConversionConfig(
            input_file=Path("input.md"),
            output_file=None,
            css_files=None,
            pdf_output=True
        )
        self.assertEqual(config.resolve_pdf_output_file(), Path("input.pdf"))

    @patch('pathlib.Path.is_dir')
    def test_resolve_pdf_output_file_not_provided_with_dist(self, mock_is_dir):
        """Test resolving pdf output file when not provided and dist folder exists."""
        mock_is_dir.return_value = True
        config = ConversionConfig(
            input_file=Path("some_dir/input.md"),
            output_file=None,
            css_files=None,
            pdf_output=True
        )
        self.assertEqual(config.resolve_pdf_output_file(), Path("some_dir/dist/input.pdf"))

    def test_path_collision_raises_configuration_error(self):
        """Test that same HTML and PDF output paths raise ConfigurationError."""
        config = ConversionConfig(
            input_file=Path("doc.md"),
            output_file=Path("doc.pdf"),
            pdf_output=Path("doc.pdf")
        )
        with self.assertRaises(ConfigurationError):
            config.resolve_pdf_output_file()

    def test_unknown_profile_raises_configuration_error(self):
        """Test that unknown profile raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            ConversionConfig(
                input_file=Path("doc.md"),
                profile="nonexistent_profile_xyz"
            )

    def test_markdown_adjacent_config_and_direct_security_directives(self):
        """Test that config.toml located in the input markdown directory is prioritized and direct -src keys are merged."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "sub" / "lecture.md"
            md_file.parent.mkdir(parents=True, exist_ok=True)
            md_file.write_text("# Test", encoding="utf-8")
            
            cfg_file = md_file.parent / "config.toml"
            cfg_file.write_text(
                '[security]\nimg-src = ["https://developer.mozilla.org"]\nconnect-src = "http://localhost:9000"\n',
                encoding="utf-8"
            )

            config = ConversionConfig(input_file=md_file)
            self.assertEqual(config.connect_src, "http://localhost:9000")
            self.assertIn("img-src", config.csp_additions)
            self.assertIn("https://developer.mozilla.org", config.csp_additions["img-src"])

class TestConversionStats(unittest.TestCase):
    def test_default_initialization(self):
        """Test ConversionStats default values."""
        stats = ConversionStats()
        self.assertEqual(stats.images_embedded, 0)
        self.assertEqual(stats.css_files_embedded, 0)
        self.assertEqual(stats.output_file_size, 0)
        self.assertIsNone(stats.markdown_file)
        self.assertIsNone(stats.output_file)

    def test_custom_initialization(self):
        """Test ConversionStats custom values."""
        stats = ConversionStats(
            images_embedded=5,
            css_files_embedded=2,
            output_file_size=1024,
            markdown_file="test.md",
            output_file="out.html"
        )
        self.assertEqual(stats.images_embedded, 5)
        self.assertEqual(stats.css_files_embedded, 2)
        self.assertEqual(stats.output_file_size, 1024)
        self.assertEqual(stats.markdown_file, "test.md")
        self.assertEqual(stats.output_file, "out.html")

if __name__ == '__main__':
    unittest.main()
