import pytest
import os
import sys
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def load_parser():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/components/mono-zoom/parser.py'))
    spec = importlib.util.spec_from_file_location("mono_zoom_parser", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MonoZoomParser()

@pytest.fixture
def parser():
    return load_parser()

import json
from pathlib import Path

class TestMonoZoomParser:
    def test_process_does_nothing(self, parser):
        # mono-zoom is a system component that just includes assets and handles things on frontend.
        # Its process method should just return the input content unchanged.
        content = "Some markdown @[image: test.png]"
        result = parser.process(content)
        assert result == content

    def test_manifest_config(self):
        manifest_path = Path(__file__).resolve().parent.parent.parent / "src" / "components" / "mono-zoom" / "manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest.get("name") == "mono-zoom"
        assert manifest.get("always_include", False) is False
        assert manifest.get("requires_icons") is True

    def test_component_files_exist(self):
        component_dir = Path(__file__).resolve().parent.parent.parent / "src" / "components" / "mono-zoom"
        assert (component_dir / "template.html").exists()
        assert (component_dir / "style.css").exists()
        assert (component_dir / "script.js").exists()
        assert (component_dir / "parser.py").exists()
