import threading
import time
from pathlib import Path
from typing import Callable


class FileWatcher:
    """Markdown原稿およびアセットの更新を監視し、変更検知コールバックを発火するクラス"""

    def __init__(
        self,
        input_file: Path,
        on_change: Callable[[], None],
        interval_sec: float = 0.5,
    ):
        self.input_file = input_file.resolve()
        self.base_dir = self.input_file.parent
        self.on_change = on_change
        self.interval_sec = interval_sec

        self._running = False
        self._thread: threading.Thread | None = None
        self._last_mtimes: dict[Path, float] = {}
        self._record_mtimes()

    def _get_watched_files(self) -> list[Path]:
        files = [self.input_file]
        # 親ディレクトリのアセット（画像等）も監視対象に追加
        assets_dir = self.base_dir / "assets"
        if assets_dir.exists() and assets_dir.is_dir():
            files.extend(p for p in assets_dir.rglob("*") if p.is_file())
        return files

    def _record_mtimes(self) -> None:
        self._last_mtimes = {}
        for p in self._get_watched_files():
            try:
                self._last_mtimes[p] = p.stat().st_mtime
            except OSError:
                pass

    def _poll(self) -> bool:
        """更新があった場合に True を返す"""
        current_files = self._get_watched_files()
        if len(current_files) != len(self._last_mtimes):
            self._record_mtimes()
            return True

        for p in current_files:
            try:
                mtime = p.stat().st_mtime
                if p not in self._last_mtimes or mtime > self._last_mtimes[p]:
                    self._record_mtimes()
                    return True
            except OSError:
                continue
        return False

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        while self._running:
            time.sleep(self.interval_sec)
            if self._poll():
                try:
                    self.on_change()
                except Exception as e:
                    print(f"自動リビルド中にエラーが発生しました: {e}")

    def stop(self) -> None:
        self._running = False
