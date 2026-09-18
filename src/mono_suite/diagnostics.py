import re
from pathlib import Path


class DiagnosticsError(Exception):
    """共通入力診断で致命的な不備（Failure）が検出された場合の例外"""
    pass


class Diagnostics:
    """Markdown原稿および参照アセットの共通事前診断を行うクラス"""

    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    HEADING_ID_PATTERN = re.compile(r'^(#{1,6})\s+.+?\s+\{#([\w-]+)\}\s*$', re.MULTILINE)

    @classmethod
    def validate_input_file(cls, input_path: Path) -> None:
        if not input_path.exists():
            raise DiagnosticsError(f"原稿ファイルが見つかりません: {input_path}")
        if not input_path.is_file():
            raise DiagnosticsError(f"指定されたパスはファイルではありません: {input_path}")

    @classmethod
    def validate_assets(cls, input_path: Path, content: str) -> list[str]:
        """原稿内の画像リンクが実在するか検証する"""
        missing_assets = []
        base_dir = input_path.parent

        for match in cls.IMAGE_PATTERN.finditer(content):
            src = match.group(2).strip()
            # 外部URLやBase64データURIはローカルアセット検査から除外
            if src.startswith(("http://", "https://", "data:")):
                continue
            asset_path = (base_dir / src).resolve()
            if not asset_path.exists() or not asset_path.is_file():
                missing_assets.append(src)

        if missing_assets:
            raise DiagnosticsError(f"必須画像アセットが見つかりません: {', '.join(missing_assets)}")
        return missing_assets

    @classmethod
    def validate_heading_ids(cls, content: str) -> None:
        """コードブロック外の明示IDの重複を検知する"""
        # 循環参照を避けるため遅延インポート
        from .preprocessor import Preprocessor

        seen_ids = set()
        in_code_fence = False
        active_fence: tuple[str, int] | None = None

        for line in content.splitlines():
            if not in_code_fence:
                fence_info = Preprocessor.match_fence_open(line)
                if fence_info:
                    in_code_fence = True
                    active_fence = fence_info
                    continue
            else:
                if active_fence and Preprocessor.match_fence_close(line, active_fence[0], active_fence[1]):
                    in_code_fence = False
                    active_fence = None
                continue

            match = cls.HEADING_ID_PATTERN.match(line)
            if match:
                h_id = match.group(2)
                if h_id in seen_ids:
                    raise DiagnosticsError(f"見出し明示IDが重複しています: {h_id}")
                seen_ids.add(h_id)

    @classmethod
    def run_all(cls, input_path: Path) -> str:
        """すべての診断を実行し、問題がなければ原稿文字列を返す"""
        cls.validate_input_file(input_path)
        content = input_path.read_text(encoding="utf-8")
        cls.validate_assets(input_path, content)
        cls.validate_heading_ids(content)
        return content
