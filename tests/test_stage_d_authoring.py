import json
import time
import urllib.request
from pathlib import Path

from mono_suite.pipeline import BuildPipeline
from mono_suite.server import DevServer, SSEBroadcaster
from mono_suite.watcher import FileWatcher

ROOT_DIR = Path(__file__).resolve().parent.parent
STANDARD_DOC = ROOT_DIR / "examples" / "standard" / "document.md"


def test_server_endpoints_and_shell_ui(tmp_path: Path):
    """DevServerが起動し、シェルUI、各レンダラービュー、マニフェストを正常配信することを検証"""
    out_dir = tmp_path / "output"
    pipeline = BuildPipeline(STANDARD_DOC, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    broadcaster = SSEBroadcaster()
    port = 8991
    server = DevServer(target_dir, "document.md", port=port, broadcaster=broadcaster)
    server.start(block=False)

    try:
        base_url = f"http://127.0.0.1:{port}"

        # 1. ルート（シェルUI）
        with urllib.request.urlopen(f"{base_url}/") as res:
            assert res.status == 200
            html = res.read().decode("utf-8")
            assert "Mono Suite" in html
            assert "btn-space" in html
            assert "btn-doc" in html
            assert "sync.js" in html

        # 2. 静的CSSおよびJS
        with urllib.request.urlopen(f"{base_url}/shell/style.css") as res:
            assert res.status == 200
            assert "header-height" in res.read().decode("utf-8")

        with urllib.request.urlopen(f"{base_url}/shell/sync.js") as res:
            assert res.status == 200
            js = res.read().decode("utf-8")
            assert "switchView" in js
            assert "getSpaceActiveId" in js

        # 3. Spaceビュー
        with urllib.request.urlopen(f"{base_url}/space") as res:
            assert res.status == 200
            space_html = res.read().decode("utf-8")
            assert 'id="viewport"' in space_html or 'SpatialCore' in space_html

        # 4. Docビュー
        with urllib.request.urlopen(f"{base_url}/doc") as res:
            assert res.status == 200
            doc_html = res.read().decode("utf-8")
            assert "<h1" in doc_html

        # 5. マニフェスト
        with urllib.request.urlopen(f"{base_url}/manifest") as res:
            assert res.status == 200
            manifest = json.loads(res.read().decode("utf-8"))
            assert manifest["suite_version"] == "0.1.0"
            assert len(manifest["headings"]) > 0

    finally:
        server.stop()


def test_server_api_full_build_trigger(tmp_path: Path):
    """POST /api/build によって完全配布セットの生成がトリガーされることを検証"""
    out_dir = tmp_path / "output"
    pipeline = BuildPipeline(STANDARD_DOC, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    called = False

    def mock_on_full_build() -> bool:
        nonlocal called
        called = True
        return True

    port = 8992
    server = DevServer(
        target_dir, "document.md", port=port, on_full_build=mock_on_full_build
    )
    server.start(block=False)

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/build",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            data = json.loads(res.read().decode("utf-8"))
            assert data["success"] is True
            assert called is True
    finally:
        server.stop()


def test_file_watcher_detects_modification(tmp_path: Path):
    """FileWatcherが原稿ファイルの書き換えを検知してコールバックを実行することを検証"""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Initial", encoding="utf-8")

    change_detected = False

    def on_change():
        nonlocal change_detected
        change_detected = True

    watcher = FileWatcher(test_file, on_change, interval_sec=0.1)
    watcher.start()

    try:
        time.sleep(0.15)
        # ファイル内容を変更
        test_file.write_text("# Updated Title", encoding="utf-8")
        time.sleep(0.3)
        assert change_detected is True
    finally:
        watcher.stop()


def test_sse_broadcaster():
    """SSEBroadcasterがイベントを登録キューへブロードキャストすることを検証"""
    broadcaster = SSEBroadcaster()
    q = broadcaster.subscribe()

    broadcaster.broadcast("reload", {"build_id": "test1234"})
    msg = q.get_nowait()
    assert 'event": "reload"' in msg
    assert 'test1234' in msg

    broadcaster.unsubscribe(q)
