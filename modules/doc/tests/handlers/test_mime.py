import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from pathlib import Path

from src.handlers.mime import MIMETypeRegistry
from src.constants import DEFAULT_MIME_TYPE, MIME_TYPE_REGISTRY


@pytest.fixture
def default_registry():
    return MIMETypeRegistry()


def test_init_default(default_registry):
    assert default_registry.registry == MIME_TYPE_REGISTRY
    assert default_registry.registry is not MIME_TYPE_REGISTRY


def test_init_custom():
    custom_registry = {".custom": "application/x-custom"}
    registry = MIMETypeRegistry(registry=custom_registry)
    assert registry.registry == custom_registry
    assert registry.registry is custom_registry


@pytest.mark.parametrize(
    "filename, expected_mime",
    [
        ("image.png", "image/png"),
        ("document.PDF", "application/pdf"),
        ("script.JS", "application/javascript"),
        ("style.css", "text/css"),
        ("file.unknown", DEFAULT_MIME_TYPE),
        ("file_without_extension", DEFAULT_MIME_TYPE),
        (".hiddenfile", DEFAULT_MIME_TYPE),
        ("archive.tar.gz", DEFAULT_MIME_TYPE), # .gz usually isn't in default, but even if it was, tar.gz suffix is .gz
        ("", DEFAULT_MIME_TYPE), # Empty path
        (".", DEFAULT_MIME_TYPE), # Current directory
        ("..", DEFAULT_MIME_TYPE), # Parent directory
        ("folder/file.png", "image/png"), # File in folder
        ("folder.ext/file", DEFAULT_MIME_TYPE), # Folder has extension but file does not
    ],
)
def test_get_mime_type(default_registry, filename, expected_mime):
    default_registry.registry.update({
        ".png": "image/png",
        ".pdf": "application/pdf",
        ".js": "application/javascript",
        ".css": "text/css"
    })

    file_path = Path(filename)
    assert default_registry.get_mime_type(file_path) == expected_mime
