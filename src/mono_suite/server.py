import json
import mimetypes
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

SHELL_DIR = Path(__file__).resolve().parent / "shell"


class SSEBroadcaster:
    """Server-Sent Events (SSE) を購読クライアントへ配信するクラス"""

    def __init__(self):
        self._subscribers: list[queue.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q = queue.Queue(maxsize=10)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, event_name: str, payload: dict) -> None:
        message = f"data: {json.dumps({'event': event_name, **payload})}\n\n"
        with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(message)
                except queue.Full:
                    pass


def create_handler(
    target_dir: Path,
    source_name: str,
    broadcaster: SSEBroadcaster | None = None,
    on_full_build: Callable[[], bool] | None = None,
):
    class DevServerHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # デバッグログの過剰出力を抑止
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/":
                # 配布ディレクトリ直接プレビュー（serve）かつ presentation.html のみ存在する場合はリダイレクト
                if not broadcaster and (target_dir / "presentation.html").exists():
                    self.send_response(302)
                    self.send_header("Location", "/presentation.html")
                    self.end_headers()
                    return

                html = (SHELL_DIR / "index.html").read_text(encoding="utf-8")
                html = html.replace("document.md", source_name)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return

            if path == "/shell/style.css":
                css = (SHELL_DIR / "style.css").read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.end_headers()
                self.wfile.write(css.encode("utf-8"))
                return

            if path == "/shell/sync.js":
                js = (SHELL_DIR / "sync.js").read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.end_headers()
                self.wfile.write(js.encode("utf-8"))
                return

            if path == "/space":
                file_path = target_dir / "presentation.html"
                self._serve_file(file_path, "text/html; charset=utf-8")
                return

            if path == "/doc":
                file_path = target_dir / "document.html"
                self._serve_file(file_path, "text/html; charset=utf-8")
                return

            if path == "/manifest":
                file_path = target_dir / "build-manifest.json"
                self._serve_file(file_path, "application/json; charset=utf-8")
                return

            if path == "/events" and broadcaster:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                q = broadcaster.subscribe()
                try:
                    self.wfile.write(b"data: {\"event\": \"connected\"}\n\n")
                    self.wfile.flush()
                    while True:
                        try:
                            msg = q.get(timeout=20)
                            self.wfile.write(msg.encode("utf-8"))
                            self.wfile.flush()
                        except queue.Empty:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    broadcaster.unsubscribe(q)
                return

            # 静的アセット（画像等）のフォールバック配信
            relative_path = path.lstrip("/")
            file_path = target_dir / relative_path
            if file_path.exists() and file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                self._serve_file(file_path, mime or "application/octet-stream")
                return

            self.send_error(404, "File Not Found")

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/build" and on_full_build:
                success = on_full_build()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": success}).encode("utf-8"))
                return

            self.send_error(404)

        def _serve_file(self, file_path: Path, content_type: str):
            if not file_path.exists():
                self.send_error(404, f"File not found: {file_path.name}")
                return
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return DevServerHandler


class DevServer:
    """ローカル開発・制作UIを提供するHTTPサーバー（空きポート自動探索対応）"""

    def __init__(
        self,
        target_dir: Path,
        source_name: str,
        port: int = 8000,
        broadcaster: SSEBroadcaster | None = None,
        on_full_build: Callable[[], bool] | None = None,
        max_port_attempts: int = 50,
    ):
        self.target_dir = target_dir
        self.source_name = source_name
        self.requested_port = port
        self.broadcaster = broadcaster
        self.on_full_build = on_full_build

        handler_cls = create_handler(target_dir, source_name, broadcaster, on_full_build)

        current_port = port
        server = None
        for _ in range(max_port_attempts):
            try:
                class CustomHTTPServer(HTTPServer):
                    allow_reuse_address = True

                server = CustomHTTPServer(("127.0.0.1", current_port), handler_cls)
                break
            except OSError as e:
                # Address already in use
                if e.errno in (48, 98):
                    current_port += 1
                    continue
                raise

        if server is None:
            raise RuntimeError(
                f"ポート {port} から {current_port - 1} までの空きポートが見つかりませんでした"
            )

        self.server = server
        self.port = current_port
        self._thread: threading.Thread | None = None

    def start(self, block: bool = True) -> None:
        if self.port != self.requested_port:
            print(f"ポート {self.requested_port} は使用中のため、空きポート {self.port} を使用します")
        print(f"Mono Suite 制作サーバー起動: http://localhost:{self.port}")

        if block:
            try:
                self.server.serve_forever()
            except KeyboardInterrupt:
                print("\nサーバーを停止しました")
            finally:
                self.stop()
        else:
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        if self.server:
            try:
                self.server.shutdown()
            except Exception:
                pass
            try:
                self.server.server_close()
            except Exception:
                pass
