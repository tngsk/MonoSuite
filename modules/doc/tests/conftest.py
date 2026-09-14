import sys
import os
from pathlib import Path
import pytest
import importlib.util

# プロジェクトルートディレクトリを自動的に sys.path に追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def load_parser():
    """ハイフン付きディレクトリ内のコンポーネントパーサーを動的に読み込むヘルパーフィクスチャ"""
    def _loader(component_name: str):
        parser_path = PROJECT_ROOT / "src" / "components" / component_name / "parser.py"
        if not parser_path.exists():
            raise FileNotFoundError(f"Parser not found at {parser_path}")
        spec = importlib.util.spec_from_file_location(f"{component_name.replace('-', '_')}_parser", str(parser_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Parser()
    return _loader
