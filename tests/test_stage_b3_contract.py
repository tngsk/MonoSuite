import json
import re
import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "integration"
ROOT_DIR = Path(__file__).resolve().parent.parent


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def test_shared_contract_document_conversion(tmp_path: Path):
    """総合正常系原稿がSpaceおよびDocの両方で正常終了し出力を生成することを検証"""
    doc_path = FIXTURES_DIR / "document.md"
    assert doc_path.exists(), f"Fixture not found: {doc_path}"

    space_out = tmp_path / "presentation.html"
    res_space = run_command([
        "uv", "run", "mono-space", str(doc_path),
        "-o", str(space_out), "--offline"
    ])
    assert res_space.returncode == 0, f"mono-space failed: {res_space.stderr}"
    assert space_out.exists()
    assert space_out.stat().st_size > 0

    doc_html = tmp_path / "document.html"
    doc_pdf = tmp_path / "document.pdf"
    res_doc = run_command([
        "uv", "run", "mono-doc", str(doc_path),
        "-o", str(doc_html), "--pdf", str(doc_pdf)
    ])
    assert res_doc.returncode == 0, f"mono-doc failed: {res_doc.stderr}"
    assert doc_html.exists()
    assert doc_html.stat().st_size > 0
    assert doc_pdf.exists()
    assert doc_pdf.stat().st_size > 0


def test_heading_id_explicit_consistency(tmp_path: Path):
    """明示IDが付与された見出しについてSpaceとDocでID文字列が完全一致することを検証"""
    doc_path = FIXTURES_DIR / "document.md"
    space_out = tmp_path / "presentation.html"
    doc_html = tmp_path / "document.html"

    run_command(["uv", "run", "mono-space", str(doc_path), "-o", str(space_out), "--offline"])
    run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])

    # Space側のノードIDを抽出
    space_text = space_out.read_text(encoding="utf-8")
    m = re.search(r'<script id="data" type="application/json">\s*(\{.*?\})\s*</script>', space_text, re.DOTALL)
    assert m is not None, "Space data JSON not found"
    space_data = json.loads(m.group(1))
    space_ids = [node["id"] for node in space_data["nodes"]]

    # Doc側の見出しタグのID属性を抽出
    doc_text = doc_html.read_text(encoding="utf-8")
    doc_ids = re.findall(r'<h[1-6][^>]*\bid="([^"]+)"', doc_text)

    # 期待される明示IDセット
    expected_ids = [
        "shared", "content", "text", "image", "math",
        "comparison", "present", "handout", "process", "input", "build"
    ]

    assert space_ids == expected_ids, f"Space IDs mismatch: {space_ids}"
    assert doc_ids == expected_ids, f"Doc IDs mismatch: {doc_ids}"
    assert space_ids == doc_ids, "Space and Doc IDs must match identically for explicit IDs"


def test_heading_id_implicit_mapping(tmp_path: Path):
    """明示IDのない原稿においてSpaceの連番ID(n{k})とDocのtocスラッグ(_(k))が1対1に対応することを検証"""
    doc_path = FIXTURES_DIR / "implicit_heading_id.md"
    space_out = tmp_path / "implicit_space.html"
    doc_html = tmp_path / "implicit_doc.html"

    res_space = run_command(["uv", "run", "mono-space", str(doc_path), "-o", str(space_out), "--offline"])
    res_doc = run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])
    assert res_space.returncode == 0
    assert res_doc.returncode == 0

    space_text = space_out.read_text(encoding="utf-8")
    m = re.search(r'<script id="data" type="application/json">\s*(\{.*?\})\s*</script>', space_text, re.DOTALL)
    space_ids = [node["id"] for node in json.loads(m.group(1))["nodes"]]

    doc_text = doc_html.read_text(encoding="utf-8")
    doc_ids = re.findall(r'<h[1-6][^>]*\bid="([^"]+)"', doc_text)

    assert space_ids == ["n1", "n2", "n3", "n4"]
    assert doc_ids == ["_1", "_2", "_3", "_4"]
    assert len(space_ids) == len(doc_ids), "Heading counts must be equal"


def test_missing_image_behavior(tmp_path: Path):
    """画像欠落原稿に対する両モジュールの振る舞い（Spaceは生成中断、Docは警告ログ継続）を記録・検証"""
    doc_path = FIXTURES_DIR / "err_missing_image.md"
    space_out = tmp_path / "missing_space.html"
    doc_html = tmp_path / "missing_doc.html"

    # Spaceは画像欠落時にリターンコード1で停止すること
    res_space = run_command(["uv", "run", "mono-space", str(doc_path), "-o", str(space_out), "--offline"])
    assert res_space.returncode == 1
    assert "No such file or directory" in res_space.stdout or "No such file or directory" in res_space.stderr

    # Docは現行仕様としてWARNINGを出力しつつリターンコード0でHTMLを生成すること（段階Cでの統一対象）
    res_doc = run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])
    assert res_doc.returncode == 0
    assert "WARNING" in res_doc.stdout or "WARNING" in res_doc.stderr
    assert "メディアファイルが見つかりません" in res_doc.stdout or "メディアファイルが見つかりません" in res_doc.stderr


def test_duplicate_id_behavior(tmp_path: Path):
    """重複見出しID原稿に対する両モジュールの振る舞い（SpaceはID重複例外、Docは重複属性許容）を記録・検証"""
    doc_path = FIXTURES_DIR / "err_duplicate_id.md"
    space_out = tmp_path / "dup_space.html"
    doc_html = tmp_path / "dup_doc.html"

    # SpaceはID重複時にリターンコード1で停止すること
    res_space = run_command(["uv", "run", "mono-space", str(doc_path), "-o", str(space_out), "--offline"])
    assert res_space.returncode == 1
    assert "ID重複" in res_space.stdout or "ID重複" in res_space.stderr

    # Docは現行仕様として同一IDを許容して変換完了すること（段階Cでの統一バリデーション対象）
    res_doc = run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])
    assert res_doc.returncode == 0
    doc_text = doc_html.read_text(encoding="utf-8")
    assert doc_text.count('id="dup-target"') == 2


def test_math_syntax_error_behavior(tmp_path: Path):
    """数式構文異常に対する両モジュールの振る舞い（SpaceはMathError中断、DocはエラーSVG埋め込み継続）を検証"""
    doc_path = FIXTURES_DIR / "err_math_syntax.md"
    space_out = tmp_path / "math_space.html"
    doc_html = tmp_path / "math_doc.html"

    # Spaceは数式エラーでリターンコード1となり停止すること
    res_space = run_command(["uv", "run", "mono-space", str(doc_path), "-o", str(space_out), "--offline"])
    assert res_space.returncode == 1
    assert "Missing close brace" in res_space.stdout or "Missing close brace" in res_space.stderr

    # DocはMathJaxのエラー表示SVGを埋め込んでリターンコード0で終了すること
    res_doc = run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])
    assert res_doc.returncode == 0
    doc_text = doc_html.read_text(encoding="utf-8")
    assert "data-mjx-error" in doc_text


def test_space_directives_and_connector_in_doc(tmp_path: Path):
    """SpaceディレクティブがDocで段落保持され、::connectがDocのmono-connectorコンポーネントとして認識されることを検証"""
    doc_path = FIXTURES_DIR / "document.md"
    doc_html = tmp_path / "document.html"

    res_doc = run_command(["uv", "run", "mono-doc", str(doc_path), "-o", str(doc_html)])
    assert res_doc.returncode == 0
    doc_text = doc_html.read_text(encoding="utf-8")

    # Spaceディレクティブが生テキストとして保持されていること
    assert "::layout compare" in doc_text
    assert "::layout flow" in doc_text

    # ::connect が mono-connector 要素として変換されていること
    assert '<mono-connector from="input" to="build"' in doc_text
    assert 'label="同じ入力版"' in doc_text


def test_shared_contract_highlight_and_underline_markup(tmp_path: Path):
    """SpaceおよびDocの両方でマーカー（==）とアンダーライン（++）が互換タグへ変換されることを検証"""
    test_md = tmp_path / "highlight_test.md"
    test_md.write_text(
        "# テスト見出し\n\n"
        "これは ==黄色マーカー== と ==ピンクマーカー=={pink} です。\n"
        "そして ++通常下線++ と ++シアン下線++{cyan} です。\n",
        encoding="utf-8"
    )

    space_out = tmp_path / "space.html"
    doc_out = tmp_path / "doc.html"

    res_space = run_command(["uv", "run", "mono-space", str(test_md), "-o", str(space_out), "--offline"])
    assert res_space.returncode == 0
    space_text = space_out.read_text(encoding="utf-8")

    res_doc = run_command(["uv", "run", "mono-doc", str(test_md), "-o", str(doc_out)])
    assert res_doc.returncode == 0
    doc_text = doc_out.read_text(encoding="utf-8")

    # Spaceの出力検証（JSONエスケープ内またはHTML内）
    assert "mono-marker mono-marker-yellow" in space_text
    assert "mono-marker mono-marker-pink" in space_text
    assert "mono-underline mono-underline-yellow" in space_text
    assert "mono-underline mono-underline-cyan" in space_text

    # Docの出力検証
    assert '<mark class="mono-marker mono-marker-yellow">黄色マーカー</mark>' in doc_text
    assert '<mark class="mono-marker mono-marker-pink">ピンクマーカー</mark>' in doc_text
    assert '<span class="mono-underline mono-underline-yellow">通常下線</span>' in doc_text
    assert '<span class="mono-underline mono-underline-cyan">シアン下線</span>' in doc_text

