import shutil
import uuid
from pathlib import Path


class PublisherError(Exception):
    """成果物の検証および公開処理における例外"""
    pass


class Publisher:
    """一時ディレクトリによるアトミック生成と既存配布セットの保護を行うクラス"""

    def __init__(self, target_dir: Path, build_id: str | None = None):
        self.target_dir = target_dir.resolve()
        self.build_id = build_id or uuid.uuid4().hex[:12]
        self.parent_dir = self.target_dir.parent
        self.temp_dir = self.parent_dir / f".tmp-{self.build_id}"

    def set_build_id(self, build_id: str) -> None:
        """ビルド識別子を更新し、一時作業領域パスを同期する"""
        self.build_id = build_id
        self.temp_dir = self.parent_dir / f".tmp-{self.build_id}"

    def prepare_temp_dir(self) -> Path:
        """一時作業領域をクリーンに準備する"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir

    def publish(self, required_artifacts: list[str]) -> None:
        """一時領域の成果物がすべて揃っていることを検証し、完成ディレクトリへアトミックに反映する"""
        # 1. 成果物の検証
        for artifact_name in required_artifacts:
            artifact_file = self.temp_dir / artifact_name
            if not artifact_file.exists() or artifact_file.stat().st_size == 0:
                self.cleanup_temp()
                raise PublisherError(f"成果物が生成されていないか空です: {artifact_name}")

        # 2. ターゲットディレクトリへのアトミックな置き換え
        backup_dir = self.parent_dir / f".backup-{self.build_id}"
        has_existing = self.target_dir.exists()

        try:
            if has_existing:
                # 既存ディレクトリを一時退避
                self.target_dir.rename(backup_dir)

            # 一時ディレクトリを本番ディレクトリへリネーム
            self.temp_dir.rename(self.target_dir)

            # 成功したらバックアップを削除
            if has_existing and backup_dir.exists():
                shutil.rmtree(backup_dir)

        except Exception as e:
            # 失敗時はバックアップから復元
            if has_existing and backup_dir.exists() and not self.target_dir.exists():
                backup_dir.rename(self.target_dir)
            self.cleanup_temp()
            raise PublisherError(f"配布セットの公開置換に失敗しました: {e}") from e

    def cleanup_temp(self) -> None:
        """一時ディレクトリが存在すれば削除する"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
