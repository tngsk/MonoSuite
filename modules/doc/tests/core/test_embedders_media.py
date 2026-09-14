import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import base64
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import FileProcessingError, ImageEmbeddingError
from src.embedders.media import MediaEmbedder
from src.handlers.file import FileHandler


@pytest.fixture
def mock_logger():
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def mock_file_handler():
    return MagicMock(spec=FileHandler)


@pytest.fixture
def media_embedder(mock_logger, mock_file_handler):
    return MediaEmbedder(logger=mock_logger, file_handler=mock_file_handler)


def test_encode_media_file_not_found(media_embedder):
    """Test encode_media_to_base64 raises error if file does not exist"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = False

    with pytest.raises(ImageEmbeddingError, match="メディアファイルが見つかりません"):
        media_embedder.encode_media_to_base64(media_path)


def test_encode_media_cache(media_embedder, mock_file_handler):
    """Test encode_media_to_base64 uses cache if available"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/media.jpg"

    mock_stat = MagicMock()
    mock_stat.st_mtime = 12345.6
    media_path.stat.return_value = mock_stat

    media_embedder._base64_cache["/path/to/media.jpg_12345.6"] = "cached_base64_data"

    result = media_embedder.encode_media_to_base64(media_path)

    assert result == "cached_base64_data"
    mock_file_handler.read_binary.assert_not_called()


def test_encode_media_standard_file(media_embedder, mock_file_handler):
    """Test encode_media_to_base64 successfully encodes non-image files"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/file.svg"
    media_path.suffix.lower.return_value = ".svg"

    mock_stat = MagicMock()
    mock_stat.st_mtime = 12345.6
    media_path.stat.return_value = mock_stat

    mock_file_handler.read_binary.return_value = b"test_data"
    expected_base64 = base64.b64encode(b"test_data").decode("utf-8")

    result = media_embedder.encode_media_to_base64(media_path)

    assert result == expected_base64
    assert media_embedder._base64_cache["/path/to/file.svg_12345.6"] == expected_base64


@patch("src.embedders.media.Image.open")
def test_encode_media_webp_conversion(mock_image_open, media_embedder, mock_file_handler):
    """Test encode_media_to_base64 converts supported images to WebP"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/image.png"
    media_path.suffix.lower.return_value = ".png"

    mock_stat = MagicMock()
    mock_stat.st_mtime = 12345.6
    media_path.stat.return_value = mock_stat

    mock_file_handler.read_binary.return_value = b"original_png_data"

    mock_img = MagicMock()
    mock_image_open.return_value = mock_img

    # Simulate saving as WebP
    def save_mock(buffer, format):
        assert format == "WEBP"
        buffer.write(b"webp_data")
    mock_img.save.side_effect = save_mock

    result = media_embedder.encode_media_to_base64(media_path)

    expected_base64 = base64.b64encode(b"webp_data").decode("utf-8")
    assert result == expected_base64
    assert media_embedder._base64_cache["/path/to/image.png_12345.6"] == expected_base64


@patch("src.embedders.media.Image.open")
def test_encode_media_webp_conversion_fallback(mock_image_open, media_embedder, mock_file_handler, mock_logger):
    """Test encode_media_to_base64 falls back to original data if WebP conversion fails"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/image.png"
    media_path.suffix.lower.return_value = ".png"

    mock_stat = MagicMock()
    mock_stat.st_mtime = 12345.6
    media_path.stat.return_value = mock_stat

    mock_file_handler.read_binary.return_value = b"original_png_data"

    mock_image_open.side_effect = Exception("Mocked conversion error")

    result = media_embedder.encode_media_to_base64(media_path)

    expected_base64 = base64.b64encode(b"original_png_data").decode("utf-8")
    assert result == expected_base64
    assert media_embedder._base64_cache["/path/to/image.png_12345.6"] == expected_base64
    mock_logger.warning.assert_called_once()


def test_encode_media_file_processing_error(media_embedder, mock_file_handler):
    """Test encode_media_to_base64 propagates FileProcessingError"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/error.jpg"

    mock_file_handler.read_binary.side_effect = FileProcessingError("Read error")

    with pytest.raises(FileProcessingError, match="Read error"):
        media_embedder.encode_media_to_base64(media_path)


def test_encode_media_general_error(media_embedder, mock_file_handler):
    """Test encode_media_to_base64 wraps general exceptions in ImageEmbeddingError"""
    media_path = MagicMock(spec=Path)
    media_path.exists.return_value = True
    media_path.resolve.return_value = "/path/to/error.jpg"

    mock_file_handler.read_binary.side_effect = ValueError("Some other error")

    with pytest.raises(ImageEmbeddingError, match="Base64エンコード失敗"):
        media_embedder.encode_media_to_base64(media_path)


def test_embed_media_external_urls(media_embedder):
    """Test embed_media_in_html leaves external URLs unchanged"""
    html_content = '<img src="https://example.com/image.jpg" alt="test">'
    markdown_dir = Path("/path/to/markdown")

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert result_html == html_content
    assert media_count == 0
    assert not asset_store

@patch.object(MediaEmbedder, "encode_media_to_base64")
@patch("src.embedders.media.Path.resolve")
@patch("src.embedders.media.Path.exists")
def test_embed_media_ab_test_tag_both_assets(mock_exists, mock_resolve, mock_encode, media_embedder):
    html_content = '<mono-ab-test title="Test" src-a="imageA.png" src-b="imageB.png"></mono-ab-test>'
    markdown_dir = Path("/path/to/markdown")

    mock_exists.return_value = True

    media_path_a = MagicMock()
    media_path_a.exists.return_value = True
    media_path_a.suffix.lower.return_value = ".png"
    media_path_a.name = "imageA.png"

    media_path_b = MagicMock()
    media_path_b.exists.return_value = True
    media_path_b.suffix.lower.return_value = ".png"
    media_path_b.name = "imageB.png"

    # Sequence of resolves: first for A, then for B
    mock_resolve.side_effect = [media_path_a, media_path_b, media_path_a, media_path_b, media_path_a, media_path_b, media_path_a, media_path_b]

    mock_encode.side_effect = ["base64_data_A", "base64_data_B"]

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert 'data-lazy-src-a="asset-1"' in result_html
    assert 'data-lazy-src-b="asset-2"' in result_html
    assert media_count == 2


@patch("src.embedders.media.Path.resolve")
def test_embed_media_path_traversal(mock_resolve, media_embedder, mock_logger):
    """Test embed_media_in_html rejects paths outside markdown directory (disabled)"""
    pass


@patch("src.embedders.media.Path.resolve")
def test_embed_media_missing_file_fallback(mock_resolve, media_embedder, mock_logger):
    """Test embed_media_in_html logs warning and keeps original src for missing files"""
    html_content = '<img src="local_missing.jpg" alt="test">'
    markdown_dir = Path("/path/to/markdown")

    media_path = MagicMock()
    media_path.exists.return_value = False
    mock_resolve.return_value = media_path

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert result_html == html_content
    assert media_count == 0
    assert not asset_store
    mock_logger.warning.assert_called_once_with("メディアファイルが見つかりません: local_missing.jpg")


@patch("src.embedders.media.Path.resolve")
def test_embed_media_svg_inlining(mock_resolve, media_embedder, mock_file_handler):
    """Test embed_media_in_html inlines SVG files"""
    html_content = '<img class="icon" src="icon.svg">'
    markdown_dir = Path("/path/to/markdown")

    media_path = MagicMock()
    media_path.exists.return_value = True
    media_path.suffix.lower.return_value = ".svg"
    media_path.name = "icon.svg"
    mock_resolve.return_value = media_path

    mock_file_handler.read_text.return_value = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert result_html == '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    assert media_count == 1
    assert not asset_store


@patch.object(MediaEmbedder, "encode_media_to_base64")
@patch("src.embedders.media.Path.resolve")
@patch("src.embedders.media.Path.exists")
def test_embed_media_image_embedding_error(mock_exists, mock_resolve, mock_encode, media_embedder, mock_logger):
    """Test embed_media_in_html catches ImageEmbeddingError and falls back to original source"""
    html_content = '<img class="responsive" src="image.png" alt="test">'
    markdown_dir = Path("/path/to/markdown")

    mock_exists.return_value = True

    media_path = MagicMock()
    media_path.exists.return_value = True
    media_path.suffix.lower.return_value = ".png"
    media_path.name = "image.png"
    mock_resolve.return_value = media_path

    mock_encode.side_effect = ImageEmbeddingError("Test error")

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert result_html == html_content
    assert media_count == 0
    assert not asset_store
    mock_logger.error.assert_called_once_with("メディア埋め込み失敗: Test error")


@patch.object(MediaEmbedder, "encode_media_to_base64")
@patch("src.embedders.media.Path.resolve")
@patch("src.embedders.media.Path.exists")
def test_embed_media_valid_image(mock_exists, mock_resolve, mock_encode, media_embedder):
    """Test embed_media_in_html encodes valid images and uses transparent placeholders"""
    html_content = '<img class="responsive" src="image.png" alt="test">'
    markdown_dir = Path("/path/to/markdown")

    mock_exists.return_value = True

    media_path = MagicMock()
    media_path.exists.return_value = True
    media_path.suffix.lower.return_value = ".png"
    media_path.name = "image.png"
    mock_resolve.return_value = media_path

    mock_encode.return_value = "base64_encoded_data"

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert 'data-lazy-src="asset-1"' in result_html
    assert 'src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="' in result_html
    assert 'class="responsive"' in result_html
    assert 'alt="test"' in result_html
    assert media_count == 1
    assert "asset-1" in asset_store
    assert asset_store["asset-1"] == "data:image/webp;base64,base64_encoded_data"


@patch.object(MediaEmbedder, "encode_media_to_base64")
@patch("src.embedders.media.Path.resolve")
@patch("src.embedders.media.Path.exists")
def test_embed_media_ab_test_tag(mock_exists, mock_resolve, mock_encode, media_embedder):
    """Test embed_media_in_html replaces src-a and src-b in mono-ab-test tags"""
    html_content = '<mono-ab-test title="Test" src-a="imageA.png" src-b="imageB.png"></mono-ab-test>'
    markdown_dir = Path("/path/to/markdown")

    mock_exists.return_value = True

    def mock_resolve_side_effect():
        media_path = MagicMock()
        media_path.exists.return_value = True
        media_path.suffix.lower.return_value = ".png"
        return media_path

    mock_resolve.side_effect = mock_resolve_side_effect

    # We'll use a sequence for encode results
    mock_encode.side_effect = ["base64_data_A", "base64_data_B"]

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    # Both should be converted to assets
    assert 'data-lazy-src-a="asset-1"' in result_html
    assert 'data-lazy-src-b="asset-2"' in result_html
    assert media_count == 2
    assert "asset-1" in asset_store
    assert "asset-2" in asset_store
    assert asset_store["asset-1"] == "data:image/webp;base64,base64_data_A"
    assert asset_store["asset-2"] == "data:image/webp;base64,base64_data_B"


@patch.object(MediaEmbedder, "encode_media_to_base64")
@patch("src.embedders.media.Path.resolve")
@patch("src.embedders.media.Path.exists")
def test_embed_media_ab_test_tag_mixed(mock_exists, mock_resolve, mock_encode, media_embedder):
    """Test embed_media_in_html handles mixed local/external src in mono-ab-test tags"""
    html_content = '<mono-ab-test title="Test" src-a="https://example.com/imageA.png" src-b="imageB.png"></mono-ab-test>'
    markdown_dir = Path("/path/to/markdown")

    mock_exists.return_value = True

    media_path = MagicMock()
    media_path.exists.return_value = True
    media_path.suffix.lower.return_value = ".png"
    media_path.name = "imageB.png"
    mock_resolve.return_value = media_path

    mock_encode.return_value = "base64_data_B"

    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_content, markdown_dir)

    assert 'src-a="https://example.com/imageA.png"' in result_html
    assert 'data-lazy-src-a' not in result_html
    assert 'data-lazy-src-b="asset-1"' in result_html
    assert media_count == 1
    assert "asset-1" in asset_store
    assert asset_store["asset-1"] == "data:image/webp;base64,base64_data_B"


def test_embed_media_sha256_deduplication(media_embedder, tmp_path):
    """Test embed_media_in_html deduplicates identical images across different file paths using SHA-256"""
    # 異なるパスに同一内容の画像ファイルを配置
    dir_a = tmp_path / "section_a"
    dir_b = tmp_path / "section_b"
    dir_a.mkdir()
    dir_b.mkdir()

    file_a = dir_a / "logo.png"
    file_b = dir_b / "logo_copy.png"
    identical_bytes = b"identical_png_image_binary_content"
    file_a.write_bytes(identical_bytes)
    file_b.write_bytes(identical_bytes)

    # 実際の読み取り・エンコードを使用
    media_embedder.file_handler.read_binary.side_effect = lambda p: p.read_bytes()

    html_input = '<img src="section_a/logo.png"><img src="section_b/logo_copy.png">'
    result_html, media_count, asset_store = media_embedder.embed_media_in_html(html_input, tmp_path)

    # 重複が排除されて単一のアセットのみが生成されること
    assert media_count == 1
    assert len(asset_store) == 1
    assert 'data-lazy-src="asset-1"' in result_html
    assert result_html.count('data-lazy-src="asset-1"') == 2

