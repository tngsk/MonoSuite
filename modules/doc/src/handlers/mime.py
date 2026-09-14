"""
MIME Type Registry
==================
Manages file extension to MIME type mappings.
"""

from pathlib import Path
from typing import Dict, Optional

from src.constants import DEFAULT_MIME_TYPE, MIME_TYPE_REGISTRY


class MIMETypeRegistry:
    """ファイル拡張子とMIMEタイプのマッピング管理"""

    DEFAULT_REGISTRY = MIME_TYPE_REGISTRY

    def __init__(self, registry: Optional[Dict[str, str]] = None):
        self.registry = registry or self.DEFAULT_REGISTRY.copy()

    def get_mime_type(self, file_path: Path) -> str:
        """ファイルパスからMIMEタイプを取得"""
        ext = file_path.suffix.lower()
        return self.registry.get(ext, DEFAULT_MIME_TYPE)
