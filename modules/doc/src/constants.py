"""
Constants for Markdown to HTML Converter
========================================
Centralized configuration and constant definitions for the converter.
"""

from pathlib import Path
from typing import Dict

# ============================================================================
# File Paths & Directories
# ============================================================================

# バージョン情報
__version__ = "2.0.0"

# テンプレートディレクトリ
TEMPLATES_DIR = Path(__file__).parent / "templates"

# コンポーネントディレクトリ
COMPONENTS_DIR = Path(__file__).parent / "components"

# デフォルトテンプレートパス
DEFAULT_TEMPLATE_PATH = TEMPLATES_DIR / "default.html"

# テンプレートファイル名
BASE_CSS_FILE = "base.css"
THEMES_TOML_FILE = "themes.toml"

# 許可されたコンポーネントのリスト (セキュリティのため、明示的に指定)
ALLOWED_COMPONENTS = [
    "mono-ab-test",
    "mono-account",
    "mono-badge",
    "mono-brush",
    "mono-clock",
    "mono-code-block",
    "mono-compare",
    "mono-connector",
    "mono-countdown",
    "mono-dice",
    "mono-export",
    "mono-flipcard",
    "mono-group-assignment",
    "mono-icon",
    "mono-layout",
    "mono-link",
    "mono-notebook",
    "mono-poll",
    "mono-reaction",
    "mono-score",
    "mono-section",
    "mono-session-join",
    "mono-sound",
    "mono-synth",
    "mono-textfield-input",
    "mono-theme",
    # "mono-topic-rail",  # 開発中
    "mono-zoom",
]

# ============================================================================
# Component Behavior Configuration
# ============================================================================

# エクスポート機能（mono-export）を自動的に有効にするインタラクティブなコンポーネント

# ドキュメントに常に含めるシステム/暗黙的コンポーネント

# アイコン用フォント（Material Symbols）を必要とするコンポーネント

# MathJax (数式レンダリング) を必要とする要素のクラス名
CLASSES_REQUIRING_MATH = [
    "mono-math",
]

# ============================================================================
# MathJax Configuration
# ============================================================================

# MathJax CDN URL
MATHJAX_CDN_JS = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"

# ============================================================================
# MIME Type Registry
# ============================================================================

# ファイル拡張子とMIMEタイプのマッピング
MIME_TYPE_REGISTRY: Dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
}

# デフォルトMIMEタイプ
DEFAULT_MIME_TYPE = "application/octet-stream"

# ============================================================================
# File I/O Encoding
# ============================================================================

# テキストファイルのデフォルトエンコーディング
DEFAULT_TEXT_ENCODING = "utf-8"

# ============================================================================
# HTML Processing
# ============================================================================

# HTMLロギングのフォーマット文字列
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 正規表現パターン
HTML_IMG_TAG_PATTERN = r'<img\s+([^>]*?)src="([^"]+)"([^>]*)/?>'
HTML_SCRIPT_TAG_PATTERN = r'<script\s+([^>]*?)src="([^"]+)"([^>]*)></script>'
HTML_TABLE_STYLE_PATTERN = r'<(td|th)\s+style="[^"]*?"'
HTML_HEAD_CLOSING_TAG = "</head>"
HTML_OPENING_TAG = r"<html[^>]*>"
HTML_TAG_REMOVAL_PATTERN_TEMPLATE = r"<{tag}[^>]*>.*?</{tag}>"
HTML_IPYNB_LINK_PATTERN = r'<a\s+([^>]*?)href="([^"]+\.ipynb)"([^>]*)>(.*?)</a>'

# 外部サービス URL
GITHUB_BASE_URL = "https://github.com/"
MATERIAL_SYMBOLS_URL = "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
COLAB_GITHUB_BASE_URL = "https://colab.research.google.com/github/"
COLAB_BADGE_URL = "https://colab.research.google.com/assets/colab-badge.svg"

# Colabリンク変換用テンプレート
HTML_COLAB_BADGE_IMG = '<img src="{badge_url}" alt="Open In Colab" class="colab-badge">'
HTML_COLAB_LINK_TEMPLATE = '<a {before_href}href="{colab_url}"{after_href} target="_blank" rel="noopener noreferrer" class="colab-link">{badge_img}{link_text}</a>'

# 正規表現フラグ
REGEX_FLAG_IGNORECASE = "IGNORECASE"

# ============================================================================
# Markdown Processing
# ============================================================================

# Markdownの拡張機能リスト
MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "tables",
    "nl2br",
    "toc",
    "md_in_html",
    "attr_list",
    "src.extensions.nowrap",
    "src.extensions.colab",
    "src.extensions.code_block",
    "src.extensions.math",
    "src.extensions.highlight",
    "src.extensions.heading_marker",
    "src.extensions.section_modifier",
]


# ============================================================================
# Size Formatting
# ============================================================================

# バイトサイズのフォーマット単位
SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")
SIZE_UNIT_THRESHOLD = 1024

# ============================================================================
# CLI & Output
# ============================================================================

# Monoコンパイラのバージョン
MONO_VERSION = __version__

# CLIのヘッダー表示
HEADER_TEXT = f"""
╔═══════════════════════════════════════════════════════════════╗
║         Markdown to Single-File HTML Converter                ║
║                    Version {MONO_VERSION}                              ║
╚═══════════════════════════════════════════════════════════════╝
"""
