"""
Media Embedder
==============
Converts media references (Images, Audio) to Base64-encoded data URIs in HTML.
"""

import base64
import hashlib
import io
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Tuple

from PIL import Image

from src.config import FileProcessingError, ImageEmbeddingError
from src.constants import HTML_IMG_TAG_PATTERN
from src.handlers.file import FileHandler
from src.handlers.mime import MIMETypeRegistry


class MediaEmbedder:
    """メディアファイル（画像・音声）をBase64エンコードして扱うクラス"""

    def __init__(self, logger: logging.Logger, file_handler: FileHandler):
        self.logger = logger
        self.file_handler = file_handler
        self.mime_registry = MIMETypeRegistry()
        self._base64_cache = {}

    def encode_media_to_base64(self, media_path: Path) -> str:
        """メディアファイルをBase64エンコード"""
        if not media_path.exists():
            raise ImageEmbeddingError(f"メディアファイルが見つかりません: {media_path}")

        mtime = media_path.stat().st_mtime
        cache_key = f"{media_path.resolve()}_{mtime}"
        if cache_key in self._base64_cache:
            return self._base64_cache[cache_key]

        try:
            media_data = self.file_handler.read_binary(media_path)

            ext = media_path.suffix.lower()
            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                try:
                    img = Image.open(io.BytesIO(media_data))
                    buffer = io.BytesIO()
                    img.save(buffer, format="WEBP")
                    media_data = buffer.getvalue()
                except Exception as img_e:
                    self.logger.warning(
                        f"WebP変換失敗 ({media_path}): {img_e}. オリジナルを使用します。"
                    )

            encoded = base64.b64encode(media_data).decode("utf-8")
            self._base64_cache[cache_key] = encoded
            return encoded
        except FileProcessingError:
            raise
        except Exception as e:
            raise ImageEmbeddingError(
                f"Base64エンコード失敗 ({media_path}): {e}"
            ) from e

    def embed_media_in_html(
        self, html_content: str, markdown_dir: Path, lazy_load: bool = True
    ) -> Tuple[str, int, dict]:
        """
        HTMLの<img>タグおよび<mono-ab-test>のメディアをBase64データに置換

        Args:
            html_content: 変換対象のHTML文字列
            markdown_dir: Markdownファイルが存在するディレクトリ
            lazy_load: Trueの場合1x1透過gif+data-lazy-srcで遅延読込、Falseの場合直接Data URI埋め込み

        Returns:
            (変換後のHTML, 埋め込みメディア数, asset_store)
        """
        media_count = 0
        asset_store = {}
        hash_to_asset_id = {}

        def resolve_and_encode(src_value: str) -> str:
            nonlocal media_count
            if src_value.strip().lower().startswith(("http://", "https://", "data:")):
                return src_value

            unquoted_src = urllib.parse.unquote(src_value)
            media_path = (markdown_dir / unquoted_src).resolve()

            # Security fix: prevent path traversal attacks
            try:
                resolved_md = markdown_dir.resolve()
                resolved_cwd = Path.cwd().resolve()
                is_safe = media_path.is_relative_to(resolved_md) or media_path.is_relative_to(resolved_cwd)
            except ValueError:
                is_safe = False

            if not is_safe:
                self.logger.warning(f"不正なメディアパス (ディレクトリトラバーサル): {src_value}")
                return src_value

            if not media_path.exists() or not media_path.is_file():
                self.logger.warning(f"メディアファイルが見つかりません: {src_value}")
                return src_value

            try:
                if media_path.suffix.lower() == ".svg":
                    svg_content = self.file_handler.read_text(media_path)
                    content_hash = hashlib.sha256(svg_content.encode("utf-8")).hexdigest()
                    if content_hash in hash_to_asset_id:
                        return hash_to_asset_id[content_hash]

                    media_count += 1
                    self.logger.debug(
                        f"インライン埋め込み: {media_path.name} (image/svg+xml)"
                    )
                    hash_to_asset_id[content_hash] = svg_content
                    return svg_content

                base64_data = self.encode_media_to_base64(media_path)
                content_hash = hashlib.sha256(base64_data.encode("utf-8")).hexdigest()
                if content_hash in hash_to_asset_id:
                    return hash_to_asset_id[content_hash]

                mime_type = self.mime_registry.get_mime_type(media_path)
                ext = media_path.suffix.lower()
                if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                    mime_type = "image/webp"

                media_count += 1
                self.logger.debug(f"埋め込み: {media_path.name} ({mime_type})")

                asset_id = f"asset-{media_count}"
                asset_store[asset_id] = f"data:{mime_type};base64,{base64_data}"
                hash_to_asset_id[content_hash] = asset_id
                return asset_id
            except ImageEmbeddingError as e:
                self.logger.error(f"メディア埋め込み失敗: {e}")
                return src_value

        # 1. <img> タグの処理
        img_pattern = re.compile(HTML_IMG_TAG_PATTERN, re.IGNORECASE)

        def img_replacer(match: re.Match) -> str:
            before_src = match.group(1)
            src_value = match.group(2)
            after_src = match.group(3)

            new_src = resolve_and_encode(src_value)
            stripped_src = new_src.strip()
            if stripped_src.startswith("<svg") or stripped_src.startswith("<?xml"):
                return new_src

            if new_src.startswith("asset-"):
                if not lazy_load:
                    direct_src = asset_store.get(new_src, "")
                    return f'<img {before_src}src="{direct_src}"{after_src}>'
                # transparent 1x1 gif
                placeholder = (
                    "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                )
                return f'<img {before_src}src="{placeholder}" data-lazy-src="{new_src}"{after_src}>'

            return f'<img {before_src}src="{new_src}"{after_src}>'

        html_content = img_pattern.sub(img_replacer, html_content)

        # 2. <mono-sound> タグの処理
        # format: <mono-sound id="..." label="..." src="..."></mono-sound>
        sound_pattern = re.compile(
            r'(<mono-sound\s+[^>]*?src=")([^"]+)("[^>]*></mono-sound>)',
            re.IGNORECASE,
        )

        def sound_replacer(match: re.Match) -> str:
            part1 = match.group(1)
            src = match.group(2)
            part3 = match.group(3)

            new_src = resolve_and_encode(src)

            # 音声は通常lazy loadingにしないか、audioタグのpreload=none等で対応するため、
            # そのままsrc属性として埋め込む（Base64の場合は直接記述されるか、asset_store経由で解決）
            # ここでは<img>や<mono-ab-test>と異なり、フロントエンド側のJSが読み込みを制御するので、そのまま置換する。
            if new_src.startswith("asset-"):
                # Component script will handle asset- prefix and fetch from mono-asset-store
                pass
            return f"{part1}{new_src}{part3}"

        html_content = sound_pattern.sub(sound_replacer, html_content)

        # 3. <mono-ab-test> タグの処理
        # format: <mono-ab-test title="..." src-a="..." src-b="..."></mono-ab-test>
        ab_test_pattern = re.compile(
            r'(<mono-ab-test\s+[^>]*?src-a=")([^"]+)(".*?src-b=")([^"]+)("[^>]*></mono-ab-test>)',
            re.IGNORECASE,
        )

        def ab_test_replacer(match: re.Match) -> str:
            part1 = match.group(1)
            src_a = match.group(2)
            part3 = match.group(3)
            src_b = match.group(4)
            part5 = match.group(5)

            new_src_a = resolve_and_encode(src_a)
            new_src_b = resolve_and_encode(src_b)

            out_part1 = part1
            if new_src_a.startswith("asset-"):
                out_part1 = part1.replace(
                    'src-a="', 'data-lazy-src-a="' + new_src_a + '" src-a="'
                )

            out_part3 = part3
            if new_src_b.startswith("asset-"):
                out_part3 = part3.replace(
                    'src-b="', 'data-lazy-src-b="' + new_src_b + '" src-b="'
                )

            return f"{out_part1}{new_src_a if not new_src_a.startswith('asset-') else ''}{out_part3}{new_src_b if not new_src_b.startswith('asset-') else ''}{part5}"

        html_content = ab_test_pattern.sub(ab_test_replacer, html_content)

        return html_content, media_count, asset_store
