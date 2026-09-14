import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import logging
import sys
import pytest

from src.logger import configure_logging
from src.constants import LOG_DATE_FORMAT, LOG_FORMAT

@pytest.fixture(autouse=True)
def reset_logger():
    # Reset the logger before each test
    logger = logging.getLogger("markdown_converter")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    yield
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)

def test_default_logging():
    logger = configure_logging(verbose=False)

    assert logger.name == "markdown_converter"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1

    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream == sys.stdout
    assert handler.level == logging.INFO

    formatter = handler.formatter
    assert formatter is not None
    assert formatter._fmt == LOG_FORMAT
    assert formatter.datefmt == LOG_DATE_FORMAT

def test_verbose_logging():
    logger = configure_logging(verbose=True)

    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1

    handler = logger.handlers[0]
    assert handler.level == logging.DEBUG

def test_handler_clear():
    # First configuration
    logger1 = configure_logging(verbose=False)
    assert len(logger1.handlers) == 1

    # Second configuration should clear the first handler and add a new one
    logger2 = configure_logging(verbose=True)
    assert len(logger2.handlers) == 1
    assert logger1 is logger2  # Same logger instance
