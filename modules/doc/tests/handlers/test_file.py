import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from unittest.mock import patch
from pathlib import Path
import logging

from src.handlers.file import FileHandler
from src.config import FileProcessingError
from src.constants import DEFAULT_TEXT_ENCODING


class TestFileHandler(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_logger")
        self.file_handler = FileHandler(self.logger)
        self.test_path = Path("dummy_path")

    @patch("pathlib.Path.read_text")
    def test_read_text_success(self, mock_read_text):
        expected_content = "Hello, world!"
        mock_read_text.return_value = expected_content

        result = self.file_handler.read_text(self.test_path)

        self.assertEqual(result, expected_content)
        mock_read_text.assert_called_once_with(encoding=DEFAULT_TEXT_ENCODING)

    @patch("pathlib.Path.read_text")
    def test_read_text_custom_encoding(self, mock_read_text):
        expected_content = "Hello, world!"
        mock_read_text.return_value = expected_content
        custom_encoding = "shift_jis"

        result = self.file_handler.read_text(self.test_path, encoding=custom_encoding)

        self.assertEqual(result, expected_content)
        mock_read_text.assert_called_once_with(encoding=custom_encoding)

    @patch("pathlib.Path.read_text")
    def test_read_text_file_not_found(self, mock_read_text):
        mock_read_text.side_effect = FileNotFoundError("Not found")

        with self.assertRaises(FileProcessingError) as context:
            self.file_handler.read_text(self.test_path)

        self.assertIn("ファイルが見つかりません", str(context.exception))

    @patch("pathlib.Path.read_text")
    def test_read_text_generic_exception(self, mock_read_text):
        mock_read_text.side_effect = Exception("Some random error")

        with self.assertRaises(FileProcessingError) as context:
            self.file_handler.read_text(self.test_path)

        self.assertIn("ファイル読み込みエラー", str(context.exception))
        self.assertIn("Some random error", str(context.exception))

    @patch("pathlib.Path.read_bytes")
    def test_read_binary_success(self, mock_read_bytes):
        expected_bytes = b"\x00\x01\x02"
        mock_read_bytes.return_value = expected_bytes

        result = self.file_handler.read_binary(self.test_path)

        self.assertEqual(result, expected_bytes)
        mock_read_bytes.assert_called_once()

    @patch("pathlib.Path.read_bytes")
    def test_read_binary_file_not_found(self, mock_read_bytes):
        mock_read_bytes.side_effect = FileNotFoundError("Not found")

        with self.assertRaises(FileProcessingError) as context:
            self.file_handler.read_binary(self.test_path)

        self.assertIn("ファイルが見つかりません", str(context.exception))

    @patch("pathlib.Path.read_bytes")
    def test_read_binary_generic_exception(self, mock_read_bytes):
        mock_read_bytes.side_effect = Exception("Binary read error")

        with self.assertRaises(FileProcessingError) as context:
            self.file_handler.read_binary(self.test_path)

        self.assertIn("バイナリファイル読み込みエラー", str(context.exception))
        self.assertIn("Binary read error", str(context.exception))

    @patch("pathlib.Path.write_text")
    def test_write_text_success(self, mock_write_text):
        content_to_write = "Test content"

        self.file_handler.write_text(self.test_path, content_to_write)

        mock_write_text.assert_called_once_with(content_to_write, encoding=DEFAULT_TEXT_ENCODING)

    @patch("pathlib.Path.write_text")
    def test_write_text_custom_encoding(self, mock_write_text):
        content_to_write = "Test content"
        custom_encoding = "euc-jp"

        self.file_handler.write_text(self.test_path, content_to_write, encoding=custom_encoding)

        mock_write_text.assert_called_once_with(content_to_write, encoding=custom_encoding)

    @patch("pathlib.Path.write_text")
    def test_write_text_generic_exception(self, mock_write_text):
        mock_write_text.side_effect = Exception("Write error")

        with self.assertRaises(FileProcessingError) as context:
            self.file_handler.write_text(self.test_path, "content")

        self.assertIn("ファイル書き込みエラー", str(context.exception))
        self.assertIn("Write error", str(context.exception))


if __name__ == "__main__":
    unittest.main()
