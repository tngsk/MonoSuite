import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .preprocessor import HeadingInfo
from . import __version__


class Manifest:
    """ビルドメタデータおよび見出し対応マニフェストを生成・管理するクラス"""

    @staticmethod
    def calculate_file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def create(
        cls,
        build_id: str,
        input_path: Path,
        raw_content: str,
        headings: list[HeadingInfo],
        artifacts: dict[str, Path],
    ) -> dict[str, Any]:
        """マニフェスト辞書を生成する"""
        input_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        created_at = datetime.now(timezone.utc).isoformat()

        artifact_records = {}
        for name, path in artifacts.items():
            if path.exists():
                artifact_records[name] = {
                    "file_name": path.name,
                    "size_bytes": path.stat().st_size,
                    "sha256": cls.calculate_file_hash(path),
                }

        heading_records = [
            {
                "id": h.id,
                "title": h.title,
                "level": h.level,
                "is_explicit": h.is_explicit,
                "space_node_id": h.id,
                "doc_anchor_id": h.id,
            }
            for h in headings
        ]

        return {
            "suite_version": __version__,
            "build_id": build_id,
            "created_at": created_at,
            "input": {
                "source_file": input_path.name,
                "sha256": input_hash,
            },
            "artifacts": artifact_records,
            "headings": heading_records,
        }

    @classmethod
    def write_to_file(cls, manifest_data: dict[str, Any], output_path: Path) -> None:
        output_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
