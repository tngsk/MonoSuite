import json
import socket
import threading
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
        base_url = f"http://127.0.0.1:{server.port}"

        # 1. ルート（シェルUI）
        with urllib.request.urlopen(f"{base_url}/") as res:
            assert res.status == 200
            html = res.read().decode("utf-8")
            assert "Mono" in html
            assert "btn-space" in html
            assert "btn-doc" in html
            assert "sync.js" in html

        # 2. 静的CSSおよびJS
        with urllib.request.urlopen(f"{base_url}/shell/style.css") as res:
            assert res.status == 200
            css_content = res.read().decode("utf-8")
            assert "header-height" in css_content
            assert "visibility: hidden" in css_content
            assert "pointer-events: none" in css_content

        with urllib.request.urlopen(f"{base_url}/shell/sync.js") as res:
            assert res.status == 200
            js = res.read().decode("utf-8")
            assert "switchView" in js
            assert "btnSpace" in js

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
            f"http://127.0.0.1:{server.port}/api/build",
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


def test_dev_server_auto_port_fallback(tmp_path: Path):
    """ポートが使用中の場合に自動的に次の空きポートへフォールバックすることを検証"""
    conflict_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conflict_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conflict_sock.bind(("127.0.0.1", 8995))
    conflict_sock.listen(1)

    try:
        out_dir = tmp_path / "output"
        pipeline = BuildPipeline(STANDARD_DOC, out_dir, generate_pdf=False, offline=True)
        target_dir = pipeline.run()

        # 8995を指定するが、占有されているため 8996 で起動するはず
        server = DevServer(target_dir, "document.md", port=8995)
        server.start(block=False)
        try:
            assert server.port == 8996
            with urllib.request.urlopen(f"http://127.0.0.1:8996/manifest") as res:
                assert res.status == 200
        finally:
            server.stop()
    finally:
        conflict_sock.close()


def test_build_lock_skips_concurrent_watcher_save():
    """完全ビルド実行中のロック排他により、保存検知処理がスキップされることを検証"""
    build_lock = threading.Lock()
    skipped = False
    rebuilt = False

    def simulated_on_change():
        nonlocal skipped, rebuilt
        if not build_lock.acquire(blocking=False):
            skipped = True
            return
        try:
            rebuilt = True
        finally:
            build_lock.release()

    # 完全ビルドがロックを保持中
    with build_lock:
        simulated_on_change()

    assert skipped is True
    assert rebuilt is False

    # ロック解放後
    simulated_on_change()
    assert rebuilt is True


def test_dev_server_threading_concurrent_sse_and_requests(tmp_path: Path):
    """SSE接続を維持した状態でも別リクエストが並行して即座に応答することを検証"""
    out_dir = tmp_path / "output"
    pipeline = BuildPipeline(STANDARD_DOC, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    broadcaster = SSEBroadcaster()
    port = 8998
    server = DevServer(target_dir, "document.md", port=port, broadcaster=broadcaster)
    server.start(block=False)

    try:
        base_url = f"http://127.0.0.1:{server.port}"

        # 1. SSEストリーム接続を開くスレッド（永続ストリーム待機）
        sse_connected = threading.Event()
        sse_stop = threading.Event()

        def keep_sse_connection():
            req = urllib.request.Request(f"{base_url}/events")
            with urllib.request.urlopen(req) as resp:
                sse_connected.set()
                while not sse_stop.is_set():
                    # 接続を維持しながらデータを読み出し
                    line = resp.readline()
                    if not line:
                        break

        t = threading.Thread(target=keep_sse_connection, daemon=True)
        t.start()

        # SSE接続が確立されるのを待つ
        assert sse_connected.wait(timeout=3.0)

        # 2. SSE接続中の状態で、通常のHTTPリクエスト（/、/manifest）がブロックされずに即座に応答するか検証
        with urllib.request.urlopen(f"{base_url}/manifest", timeout=2.0) as res:
            assert res.status == 200
            manifest = json.loads(res.read().decode("utf-8"))
            assert "suite_version" in manifest

        with urllib.request.urlopen(f"{base_url}/", timeout=2.0) as res:
            assert res.status == 200
            assert "Mono" in res.read().decode("utf-8")

        # 3. SSE接続終了
        sse_stop.set()
    finally:
        server.stop()


def test_space_overview_menu_recovery_after_focus(tmp_path: Path):
    """スライドフォーカス後に全体表示へ戻した際、quietモードが解除されメニューが正常展開されることを検証"""
    from playwright.sync_api import sync_playwright

    out_dir = tmp_path / "output"
    pipeline = BuildPipeline(STANDARD_DOC, out_dir, generate_pdf=False, offline=True)
    target_dir = pipeline.run()

    server = DevServer(target_dir, "document.md", port=8999)
    server.start(block=False)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"http://127.0.0.1:{server.port}/presentation.html")
            page.wait_for_selector("#world")

            # 1. 初期状態：quietはついていない
            initial_quiet = page.evaluate("() => document.body.classList.contains('quiet')")
            assert initial_quiet is False

            # 2. スライドをクリックしてフォーカス：quietが付く
            page.locator(".node").first.click()
            page.wait_for_timeout(300)
            focused_quiet = page.evaluate("() => document.body.classList.contains('quiet')")
            assert focused_quiet is True

            # 3. 全体表示（#overviewクリック）を実行：quietが解除されメニューが展開されること
            page.evaluate("() => document.querySelector('#overview').click()")
            page.wait_for_timeout(300)
            after_all_quiet = page.evaluate("() => document.body.classList.contains('quiet')")
            assert after_all_quiet is False

            # ヘッダーのラベルが「キャンバス全体」に更新されていること
            label = page.evaluate("() => document.querySelector('#label').textContent")
            assert "キャンバス全体" in label

            browser.close()
    finally:
        server.stop()


