"""
File Handler
============
Manages file I/O operations (read/write text and binary files).
"""

import logging
from pathlib import Path

from src.config import FileProcessingError
from src.constants import DEFAULT_TEXT_ENCODING


class FileHandler:
    """ファイルI/O操作を管理するクラス"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def read_text(self, file_path: Path, encoding: str = DEFAULT_TEXT_ENCODING) -> str:
        """テキストファイルを読み込む"""
        try:
            self.logger.debug(f"読み込み中: {file_path}")
            return file_path.read_text(encoding=encoding)
        except FileNotFoundError as e:
            raise FileProcessingError(f"ファイルが見つかりません: {file_path}") from e
        except Exception as e:
            raise FileProcessingError(
                f"ファイル読み込みエラー ({file_path}): {e}"
            ) from e

    def read_binary(self, file_path: Path) -> bytes:
        """バイナリファイルを読み込む"""
        try:
            self.logger.debug(f"読み込み中 (バイナリ): {file_path}")
            return file_path.read_bytes()
        except FileNotFoundError as e:
            raise FileProcessingError(f"ファイルが見つかりません: {file_path}") from e
        except Exception as e:
            raise FileProcessingError(
                f"バイナリファイル読み込みエラー ({file_path}): {e}"
            ) from e

    def write_text(
        self, file_path: Path, content: str, encoding: str = DEFAULT_TEXT_ENCODING
    ) -> None:
        """テキストファイルを書き込む"""
        try:
            self.logger.debug(f"書き込み中: {file_path}")
            file_path.write_text(content, encoding=encoding)
        except Exception as e:
            raise FileProcessingError(
                f"ファイル書き込みエラー ({file_path}): {e}"
            ) from e
