import json
import re
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "integration"
STANDARD_DOC = ROOT_DIR / "examples" / "standard" / "document.md"


def run_mono_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "mono"] + args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def test_pipeline_standard_build_success(tmp_path: Path):
    """標準サンプル原稿の一括ビルドが成功し、3成果物およびマニフェストが生成されることを検証"""
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(STANDARD_DOC), "-o", str(out_dir)])
    assert res.returncode == 0, f"mono build failed: {res.stderr}"

    target_pkg = out_dir / "document"
    assert target_pkg.exists()

    space_html = target_pkg / "presentation.html"
    doc_html = target_pkg / "document.html"
    doc_pdf = target_pkg / "document.pdf"
    manifest_file = target_pkg / "build-manifest.json"

    assert space_html.exists() and space_html.stat().st_size > 0
    assert doc_html.exists() and doc_html.stat().st_size > 0
    assert doc_pdf.exists() and doc_pdf.stat().st_size > 0
    assert manifest_file.exists() and manifest_file.stat().st_size > 0

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["suite_version"] == "1.0.0b1"
    assert "presentation_html" in manifest["artifacts"]
    assert "document_html" in manifest["artifacts"]
    assert "document_pdf" in manifest["artifacts"]
    assert len(manifest["headings"]) > 0


def test_pipeline_no_pdf_option(tmp_path: Path):
    """--no-pdf オプション指定時にPDF生成がスキップされ、高速に完了することを検証"""
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(STANDARD_DOC), "-o", str(out_dir), "--no-pdf"])
    assert res.returncode == 0

    target_pkg = out_dir / "document"
    assert (target_pkg / "presentation.html").exists()
    assert (target_pkg / "document.html").exists()
    assert not (target_pkg / "document.pdf").exists()

    manifest = json.loads((target_pkg / "build-manifest.json").read_text(encoding="utf-8"))
    assert "document_pdf" not in manifest["artifacts"]


def test_pipeline_implicit_heading_id_consistency(tmp_path: Path):
    """明示IDのない原稿において自動補完されたIDがSpaceとDocで1対1完全一致することを検証"""
    doc_path = FIXTURES_DIR / "implicit_heading_id.md"
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(doc_path), "-o", str(out_dir), "--no-pdf"])
    assert res.returncode == 0

    target_pkg = out_dir / "implicit_heading_id"
    space_html = target_pkg / "presentation.html"
    doc_html = target_pkg / "document.html"

    # SpaceのノードIDを抽出
    space_text = space_html.read_text(encoding="utf-8")
    m = re.search(r'<script id="data" type="application/json">\s*(\{.*?\})\s*</script>', space_text, re.DOTALL)
    assert m is not None
    space_ids = [n["id"] for n in json.loads(m.group(1))["nodes"]]

    # Docの見出しIDを抽出
    doc_text = doc_html.read_text(encoding="utf-8")
    doc_ids = re.findall(r'<h[1-6][^>]*\bid="([^"]+)"', doc_text)

    expected = ["sec-1", "sec-2", "sec-3", "sec-4"]
    assert space_ids == expected
    assert doc_ids == expected
    assert space_ids == doc_ids


def test_pipeline_missing_image_aborts_and_protects_existing(tmp_path: Path):
    """画像欠落原稿に対するビルド中断と、既存配布セットの保護を検証"""
    out_dir = tmp_path / "output"
    target_pkg = out_dir / "err_missing_image"
    target_pkg.mkdir(parents=True, exist_ok=True)
    sentinel = target_pkg / "sentinel.txt"
    sentinel.write_text("protected_data", encoding="utf-8")

    err_doc = FIXTURES_DIR / "err_missing_image.md"
    res = run_mono_cli(["build", str(err_doc), "-o", str(out_dir)])
    assert res.returncode == 1
    assert "必須画像アセットが見つかりません" in res.stderr

    # 既存の配布セットが破壊されず維持されていること
    assert sentinel.exists()
    assert sentinel.read_text(encoding="utf-8") == "protected_data"


def test_pipeline_duplicate_id_aborts(tmp_path: Path):
    """見出し明示ID重複原稿に対するビルド中断を検証"""
    out_dir = tmp_path / "output"
    err_doc = FIXTURES_DIR / "err_duplicate_id.md"
    res = run_mono_cli(["build", str(err_doc), "-o", str(out_dir)])
    assert res.returncode == 1
    assert "見出し明示IDが重複しています" in res.stderr


def test_pipeline_preamble_before_first_heading_succeeds(tmp_path: Path):
    """見出しの前にキャッチコピーや情報テキストが存在する原稿でも正常ビルドできることを検証"""
    doc_file = tmp_path / "lecture.md"
    doc_file.write_text(
        "キャッチコピー：次世代Webプログラミング\n"
        "2026年度版 講義ノート\n\n"
        "# 第1回 ガイダンス\n"
        "::layout row\n\n"
        "本日の講義概要です。\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(doc_file), "-o", str(out_dir), "--no-pdf"])
    assert res.returncode == 0

    target_pkg = out_dir / "lecture"
    space_html = target_pkg / "presentation.html"
    doc_html = target_pkg / "document.html"

    assert space_html.exists()
    assert doc_html.exists()

    # Space側にキャッチコピーが含まれていること
    space_text = space_html.read_text(encoding="utf-8")
    assert "キャッチコピー" in space_text
    assert "次世代Webプログラミング" in space_text

    # Doc側にもキャッチコピーが含まれていること
    doc_text = doc_html.read_text(encoding="utf-8")
    assert "キャッチコピー" in doc_text


def test_pipeline_svg_image_support(tmp_path: Path):
    """SVGベクター画像を含む原稿がSpaceおよびDocの双方で正常変換されることを検証"""
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    svg_file = assets_dir / "diagram.svg"
    svg_file.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>',
        encoding="utf-8",
    )

    doc_file = tmp_path / "svg_test.md"
    doc_file.write_text(
        "# SVG検証\n\n![ダイアグラム](assets/diagram.svg)\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(doc_file), "-o", str(out_dir), "--no-pdf"])
    assert res.returncode == 0

    target_pkg = out_dir / "svg_test"
    space_html = target_pkg / "presentation.html"
    doc_html = target_pkg / "document.html"

    assert space_html.exists()
    assert doc_html.exists()

    # Space側にSVGのData URLが埋め込まれていること
    assert "data:image/svg+xml;base64," in space_html.read_text(encoding="utf-8")

    # Doc側にもSVG画像タグまたはインラインSVGが含まれていること
    doc_content = doc_html.read_text(encoding="utf-8")
    assert "<svg" in doc_content or "diagram.svg" in doc_content
