"""
Logging Configuration
=====================
Centralized logging setup for the Markdown to HTML converter.
"""

import logging
import sys

from src.constants import LOG_DATE_FORMAT, LOG_FORMAT


def configure_logging(verbose: bool = False) -> logging.Logger:
    """
    標準的なロギング設定を初期化する。

    Args:
        verbose: True の場合、DEBUG レベルのログを出力

    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger("markdown_converter")
    logger.handlers.clear()  # 既存ハンドラをリセット

    # ログレベルの決定
    level = logging.DEBUG if verbose else logging.INFO

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # ログフォーマッタ
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.setLevel(level)

    return logger
