import json
import re
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import pypdf
import pytest

from mono_suite.pipeline import BuildPipeline
from mono_suite.server import DevServer, SSEBroadcaster
from mono_suite.watcher import FileWatcher

ROOT_DIR = Path(__file__).resolve().parent.parent
PRACTICAL_DOC = ROOT_DIR / "examples" / "practical" / "document.md"


def run_mono_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "mono"] + args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )


def test_stage_e_practical_document_full_build(tmp_path: Path):
    """実践的技術原稿（数式・表・図版・工程・コード）の一括ビルドと3成果物の完全性を検証"""
    out_dir = tmp_path / "output"
    res = run_mono_cli(["build", str(PRACTICAL_DOC), "-o", str(out_dir)])
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
    assert manifest["suite_version"] == "0.1.0"
    assert "presentation_html" in manifest["artifacts"]
    assert "document_html" in manifest["artifacts"]
    assert "document_pdf" in manifest["artifacts"]

    # 見出し階層が正しく抽出され、コードブロック内のコメントや記号が誤抽出されていないこと
    heading_ids = [h["id"] for h in manifest["headings"]]
    assert "practical-doc" in heading_ids
    assert "overview" in heading_ids
    assert "principles" in heading_ids
    assert "technical-spec" in heading_ids
    assert "formatting" in heading_ids
    assert "comparison-table" in heading_ids
    assert "code-example" in heading_ids
    assert "math-equations" in heading_ids
    assert "system-architecture" in heading_ids
    assert "diagram" in heading_ids
    assert "pipeline-compare" in heading_ids
    assert "space-pipeline" in heading_ids
    assert "doc-pipeline" in heading_ids
    assert "workflow" in heading_ids
    assert "diag-step" in heading_ids
    assert "build-step" in heading_ids
    assert "verify-step" in heading_ids

    # コードブロック内のPythonコメント（# 単一原稿...）が見出しとして抽出されていないことを検証
    for h in manifest["headings"]:
        assert "単一原稿から配布セット" not in h["title"]


def test_stage_e_pdf_copy_and_font_quality(tmp_path: Path):
    """生成されたDoc PDFから日本語テキスト、数式周辺文、表組、コードが正確に抽出・コピー可能であることを検証"""
    out_dir = tmp_path / "output"
    pipeline = BuildPipeline(PRACTICAL_DOC, out_dir, generate_pdf=True, offline=True)
    target_dir = pipeline.run()

    pdf_file = target_dir / "document.pdf"
    assert pdf_file.exists()

    reader = pypdf.PdfReader(str(pdf_file))
    assert len(reader.pages) >= 1
    page_text = reader.pages[0].extract_text()

    # 日本語文字および各種要素の抽出確認
    assert "実践的技術ドキュメント原稿" in page_text
    assert "概要と背景" in page_text
    assert "mono build" in page_text
    assert "config.toml" in page_text
    assert "評価軸" in page_text
    assert "カンファレンス発表" in page_text
    assert "報告書" in page_text
    assert "BuildPipeline" in page_text
    assert "published_dir" in page_text
    assert "数式記述" in page_text
    assert "アーキテクチャ概要" in page_text or "システムアーキテクチャ" in page_text
    assert "原稿診断" in page_text


def test_stage_e_watcher_stress_rapid_saves_and_queue(tmp_path: Path):
    """高速連続保存時にビルドロックと再実行予約キューが協調し、最新版への最終収束を保証することを検証"""
    test_doc = tmp_path / "stress_doc.md"
    test_doc.write_text("# 初期版 {#v1}\n\n初期内容です。\n", encoding="utf-8")

    out_dir = tmp_path / "out"
    pipeline = BuildPipeline(test_doc, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    build_lock = threading.Lock()
    rebuild_pending = threading.Event()
    build_count = 0
    executed_versions = []

    def handle_change():
        nonlocal build_count
        acquired = build_lock.acquire(blocking=False)
        if not acquired:
            rebuild_pending.set()
            return

        try:
            while True:
                rebuild_pending.clear()
                content = test_doc.read_text(encoding="utf-8")
                version_match = re.search(r'# (.+)', content)
                version_title = version_match.group(1) if version_match else "unknown"
                time.sleep(0.04)  # ビルド処理の擬似的な負荷
                p = BuildPipeline(test_doc, out_dir, generate_pdf=False, offline=True)
                p.run()
                build_count += 1
                executed_versions.append(version_title)

                if not rebuild_pending.is_set():
                    break
        finally:
            build_lock.release()

    watcher = FileWatcher(test_doc, on_change=handle_change, interval_sec=0.05)
    watcher.start()

    try:
        # 1. 第1回更新
        test_doc.write_text("# 第1更新版 {#v2}\n\n更新内容2\n", encoding="utf-8")
        time.sleep(0.15)

        # 2. ロック競合を発生させるため、短い間隔で連続更新
        for i in range(3, 7):
            test_doc.write_text(f"# 第{i}更新版 {{#v{i}}}\n\n更新内容{i}\n", encoding="utf-8")
            time.sleep(0.02)

        # 全更新が完了し、キューされた最新版ビルドが終了するまで待機
        time.sleep(0.4)
    finally:
        watcher.stop()

    # 最終的にマニフェストが最後の更新版（第6更新版）に収束していることを検証
    manifest_path = target_dir / "build-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["headings"][0]["title"] == "第6更新版"
    assert manifest["headings"][0]["id"] == "v6"


def test_stage_e_dev_server_error_recovery(tmp_path: Path):
    """構文エラー・未解決参照の混入時にも既存正常成果物が保護され、修正保存で即座に復帰することを検証"""
    asset_img = tmp_path / "valid.png"
    asset_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    test_doc = tmp_path / "doc.md"
    test_doc.write_text(f"# 正常原稿 {{#ok}}\n\n![画像](valid.png)\n", encoding="utf-8")

    out_dir = tmp_path / "out"
    pipeline = BuildPipeline(test_doc, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    # 正常ビルド時のハッシュ
    manifest_init = json.loads((target_dir / "build-manifest.json").read_text(encoding="utf-8"))
    init_html_hash = manifest_init["artifacts"]["presentation_html"]["sha256"]

    # 1. 構文エラー（存在しない画像アセット）の投入
    test_doc.write_text("# 破損原稿 {#broken}\n\n![欠損](non_existent.png)\n", encoding="utf-8")
    with pytest.raises(Exception):
        err_pipeline = BuildPipeline(test_doc, out_dir, generate_pdf=False, offline=True)
        err_pipeline.run()

    # 既存のターゲットディレクトリが破壊されず、直前の正常成果物が保持されていること
    manifest_after_err = json.loads((target_dir / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest_after_err["artifacts"]["presentation_html"]["sha256"] == init_html_hash
    assert manifest_after_err["headings"][0]["id"] == "ok"

    # 2. 修正保存の投入
    test_doc.write_text("# 復帰原稿 {#recovered}\n\n![画像](valid.png)\n", encoding="utf-8")
    rec_pipeline = BuildPipeline(test_doc, out_dir, generate_pdf=False, offline=True)
    rec_target = rec_pipeline.run()

    manifest_rec = json.loads((rec_target / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest_rec["headings"][0]["id"] == "recovered"
    assert manifest_rec["headings"][0]["title"] == "復帰原稿"
