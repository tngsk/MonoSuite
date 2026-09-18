import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PRACTICAL_DOC = ROOT_DIR / "examples" / "practical" / "document.md"


def run_mono_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "mono"] + args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def test_stage_f_space_html_contains_annotations(tmp_path: Path):
    """Mono Spaceのビルド成果物に空間アノテーションレイヤーと関連JS/CSSが含まれていることを検証"""
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(PRACTICAL_DOC), "-o", str(out_dir)])
    assert res.returncode == 0, f"mono build failed: {res.stderr}"

    space_html = out_dir / "document" / "presentation.html"
    assert space_html.exists()
    content = space_html.read_text(encoding="utf-8")

    # SVGレイヤーおよび関連スクリプト・スタイルの存在
    assert "SpatialAnnotations" in content
    assert "annotations-layer" in content
    assert "annotation-arrow-end" in content
    assert "annotation-arrow-start" in content
    assert ".annotation-draw" in content
    assert ".annotation-arrow" in content

    # ヘルプパネル内のショートカット記述
    assert "自由描画ペン" in content
    assert "双方向矢印" in content


def test_stage_f_mono_brush_deprecated_manifest():
    """Doc側の旧mono-brushコンポーネントが非推奨(deprecated)として記録されていることを検証"""
    brush_manifest_file = ROOT_DIR / "modules" / "doc" / "src" / "components" / "mono-brush" / "manifest.json"
    assert brush_manifest_file.exists()

    manifest = json.loads(brush_manifest_file.read_text(encoding="utf-8"))
    assert manifest["status"] == "deprecated"
    assert "非推奨" in manifest["description"]
