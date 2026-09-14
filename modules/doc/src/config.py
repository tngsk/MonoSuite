"""
Configuration and Exception Classes
===================================
Centralized definitions for conversion configuration and error handling.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

# ============================================================================
# Custom Exceptions
# ============================================================================


class ConversionError(Exception):
    """変換処理中に発生する汎用エラー"""

    pass


class FileProcessingError(ConversionError):
    """ファイル処理エラー"""

    pass


class ImageEmbeddingError(ConversionError):
    """画像埋め込みエラー"""

    pass


class CSSEmbeddingError(ConversionError):
    """CSS埋め込みエラー"""

    pass


class ConfigurationError(ConversionError):
    """設定エラー"""

    pass


# ============================================================================
# Data Classes & Configuration
# ============================================================================


@dataclass
class ConversionConfig:
    """変換処理の設定を保持するデータクラス"""

    input_file: Path
    output_file: Optional[Path] = None
    css_files: Optional[List[Path]] = None
    template_path: Optional[Path] = None
    verbose: bool = False
    excluded_tags: Optional[List[str]] = None
    force: bool = False
    enable_export: bool = False
    pdf_output: Union[Path, bool, None] = None
    theme: Optional[str] = None
    connect_src: str = ""
    csp_additions: dict[str, List[str]] = None
    profile: Optional[str] = None
    profile_components: Optional[List[str]] = None

    def __post_init__(self):
        self.csp_additions = {}
        self.profile_components = []

        # 1. 基底となるシステム設定（Monoプロジェクトルートのconfig.toml）を常時読み込む
        system_config_path = Path(__file__).resolve().parent.parent / "config.toml"
        merged_config = {}
        if system_config_path.is_file():
            try:
                with open(system_config_path, "rb") as f:
                    merged_config = tomllib.load(f)
            except Exception:
                pass

        # 2. ユーザー設定（カレント作業ディレクトリおよび入力Markdownディレクトリ）を順次読み込み、マージ・上書き
        user_config_paths = []
        cwd_cfg = Path.cwd() / "config.toml"
        if cwd_cfg != system_config_path:
            user_config_paths.append(cwd_cfg)

        if self.input_file:
            try:
                input_dir = self.input_file.parent if isinstance(self.input_file, Path) else Path(self.input_file).parent
                md_cfg = input_dir / "config.toml"
                if md_cfg not in user_config_paths and md_cfg != system_config_path:
                    user_config_paths.append(md_cfg)
            except Exception:
                pass

        for p in user_config_paths:
            if p.is_file():
                try:
                    with open(p, "rb") as f:
                        user_data = tomllib.load(f)
                        # security のマージ
                        if "security" in user_data:
                            merged_sec = merged_config.setdefault("security", {})
                            for k, v in user_data["security"].items():
                                if k == "csp-additions" and isinstance(v, dict):
                                    merged_csp = merged_sec.setdefault("csp-additions", {})
                                    for ck, cv in v.items():
                                        if ck not in merged_csp:
                                            merged_csp[ck] = list(cv)
                                        else:
                                            for item in cv:
                                                if item not in merged_csp[ck]:
                                                    merged_csp[ck].append(item)
                                else:
                                    merged_sec[k] = v
                        # profiles のマージ
                        if "profiles" in user_data:
                            merged_profiles = merged_config.setdefault("profiles", {})
                            for pk, pv in user_data["profiles"].items():
                                merged_profiles[pk] = pv
                except Exception:
                    pass

        # 3. マージ済み設定の適用
        security = merged_config.get("security", {})
        self.connect_src = security.get("connect-src", "")
        raw_csp = security.get("csp-additions", {})
        self.csp_additions = dict(raw_csp) if isinstance(raw_csp, dict) else {}

        # security直下のリスト形式ディレクティブ（img-src, connect-src等）もcsp-additionsに自動マージ
        for sec_key, sec_val in security.items():
            if sec_key.endswith("-src") and isinstance(sec_val, list):
                existing = self.csp_additions.setdefault(sec_key, [])
                for item in sec_val:
                    if item not in existing:
                        existing.append(item)

        # Profiles resolving
        profiles = merged_config.get("profiles", {})
        if self.profile:
            if self.profile == "static":
                active_profile_name = "minimal"
            elif self.profile in profiles:
                active_profile_name = self.profile
            else:
                raise ConfigurationError(f"未定義のプロファイルが指定されました: {self.profile}")
        else:
            active_profile_name = profiles.get("default", "standard")

        if active_profile_name in profiles and isinstance(profiles[active_profile_name], dict):
            self.profile_components = profiles[active_profile_name].get("components", [])

    def resolve_output_file(self) -> Path:
        """出力ファイルパスを決定する（未指定時は入力ファイル名から生成）"""
        if self.output_file:
            return self.output_file

        dist_dir = self.input_file.parent / "dist"
        if dist_dir.is_dir():
            return dist_dir / self.input_file.with_suffix(".html").name

        return self.input_file.with_suffix(".html")

    def resolve_pdf_output_file(self) -> Optional[Path]:
        """PDF出力ファイルパスを決定する"""
        if self.pdf_output is None or self.pdf_output is False:
            return None
        pdf_file: Path
        if isinstance(self.pdf_output, bool) and self.pdf_output:
            dist_dir = self.input_file.parent / "dist"
            if dist_dir.is_dir():
                pdf_file = dist_dir / self.input_file.with_suffix(".pdf").name
            else:
                pdf_file = self.input_file.with_suffix(".pdf")
        else:
            pdf_file = Path(self.pdf_output)

        # HTML出力先との衝突を検証
        html_file = self.resolve_output_file()
        try:
            if html_file.resolve() == pdf_file.resolve():
                raise ConfigurationError(
                    f"HTML出力先とPDF出力先に同一のファイルパスが指定されています: {html_file}"
                )
        except ValueError:
            pass

        return pdf_file


@dataclass
class ConversionStats:
    """変換結果の統計情報"""

    images_embedded: int = 0
    css_files_embedded: int = 0
    output_file_size: int = 0
    markdown_file: Optional[str] = None
    output_file: Optional[str] = None
