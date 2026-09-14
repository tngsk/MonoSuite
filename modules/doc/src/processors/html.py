"""
HTML Document Builder
=====================
Generates complete HTML documents from markdown with template support.
"""

import html
import json
import logging
import re
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Optional

from src.config import ConversionError
from src.constants import (
    CLASSES_REQUIRING_MATH,
    COMPONENTS_DIR,
    DEFAULT_TEMPLATE_PATH,
    HTML_TABLE_STYLE_PATTERN,
    MATERIAL_SYMBOLS_URL,
    MONO_VERSION,
    TEMPLATES_DIR,
)
from src import registry


class HTMLDocumentBuilder:
    """テンプレートベースのHTMLドキュメント生成クラス"""

    def __init__(self, logger: logging.Logger, template_path: Optional[Path] = None):
        self.logger = logger
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH

    def build_document(
        self,
        html_body: str,
        title: str = "Document",
        excluded_tags: Optional[List[str]] = None,
        connect_src: str = "",
        asset_store: Optional[Dict[str, str]] = None,
        enable_export: bool = False,
        csp_additions: Optional[dict[str, List[str]]] = None,
        profile_components: Optional[List[str]] = None,
        profile: Optional[str] = None,
    ) -> str:
        """
        テンプレートとHTML断片からドキュメントを生成

        Args:
            html_body: <body>に挿入するHTML
            title: ドキュメントのタイトル
            profile_components: プロファイルで指定された追加コンポーネント名リスト
            profile: 有効なプロファイル名（minimal, standard, presentation など）

        Returns:
            完全なHTMLドキュメント
        """
        try:
            # テンプレートを読み込む
            template_content = self.template_path.read_text(encoding="utf-8")
            self.logger.debug(f"テンプレート読み込み: {self.template_path}")
        except FileNotFoundError as e:
            raise ConversionError(
                f"テンプレートファイルが見つかりません: {self.template_path}"
            ) from e
        except Exception as e:
            raise ConversionError(f"テンプレート読み込みエラー: {e}") from e

        is_minimal = profile == "minimal"

        # テーブルインラインスタイル削除
        html_body = self._remove_table_inline_styles(html_body)

        # 除外タグ削除
        html_body = self._remove_excluded_tags(html_body, excluded_tags)

        if is_minimal:
            # mono-code-block を純粋な <pre><code> にアンラップ
            html_body = re.sub(
                r"<mono-code-block[^>]*>\s*(<pre(?:\s+[^>]+)?><code(?:\s+[^>]+)?>(?:.*?)</code></pre>)\s*</mono-code-block>",
                r"\1",
                html_body,
                flags=re.DOTALL,
            )

        # プレースホルダーを置換
        safe_title = self._escape_html(title)

        # 最適化: HTMLボディからコンポーネントタグを1回のパスで抽出する
        found_mono_tags = set(re.findall(r"<(mono-[a-z0-9-]+)", html_body))

        if is_minimal:
            unsupported = found_mono_tags - {"mono-code-block"}
            if unsupported:
                tag_list = ", ".join(sorted(unsupported))
                raise ConversionError(
                    f"minimalプロファイルで未対応のコンポーネントが含まれています: {tag_list}"
                )
            should_enable_export = False
            used_component_dirs = []
            mathjax = ""
            mono_components_js = ""
            component_templates = ""
        else:
            # エクスポート機能の自動判定
            has_interactive_components = any(
                tag in found_mono_tags
                for tag in registry.get_interactive_components()
            )
            should_enable_export = enable_export or has_interactive_components

            if should_enable_export:
                html_body += "\n<mono-export></mono-export>"

            # 使用されているコンポーネントを特定
            used_component_dirs = self._get_used_component_dirs(
                found_mono_tags, should_enable_export, profile_components
            )

            mathjax = ""
            if any(f'class="{cls}' in html_body for cls in CLASSES_REQUIRING_MATH):
                mathjax = self._build_mathjax_script()

            mono_components_js = self._load_mono_components_script(used_component_dirs)
            component_templates = self._load_component_templates(used_component_dirs)

        # Base CSP Directives
        csp_directives = {
            "default-src": ["'self'", "'unsafe-inline'", "data:", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com", "https://fonts.gstatic.com"],
            "worker-src": ["'self'", "blob:"],
            "img-src": ["'self'", "data:", "https://colab.research.google.com"],
            "connect-src": ["'self'", "https://cdn.jsdelivr.net"],
            "object-src": ["'none'"],
            "font-src": ["'self'", "data:", "https://fonts.gstatic.com"],
            "media-src": ["'self'", "data:", "https://actions.google.com"],
        }

        if connect_src:
            csp_directives["connect-src"].append(connect_src)

        # Merge additional CSP directives from config
        if csp_additions:
            for directive, values in csp_additions.items():
                if directive not in csp_directives:
                    csp_directives[directive] = []
                for val in values:
                    if val not in csp_directives[directive]:
                        csp_directives[directive].append(val)

        if is_minimal:
            csp_directives["script-src"] = ["'none'"]

        csp_parts = []
        for directive, values in csp_directives.items():
            if values:
                csp_parts.append(f"{directive} {' '.join(values)}")

        csp_content = "; ".join(csp_parts) + ";"
        csp_meta = f"<meta http-equiv=\"Content-Security-Policy\" content=\"{csp_content}\">"

        meta_tags = []
        meta_tags.append(
            f'<meta name="mono-version" data-mono-version="{MONO_VERSION}">'
        )
        if connect_src:
            meta_tags.append(f'<meta name="mono-api-url" content="{connect_src}">')

        meta_tags_html = "\n".join(meta_tags)
        if meta_tags_html:
            csp_meta += f"\n        {meta_tags_html}"

        # アイコンが使われている場合はGoogle Fontsのリンクを追加
        fonts_link = ""
        if any(tag in found_mono_tags for tag in registry.get_components_requiring_icons()):
            fonts_link = (
                f'\n        <link rel="stylesheet" href="{MATERIAL_SYMBOLS_URL}" />'
            )

        content_css = self._load_component_content_css(used_component_dirs)

        doc = template_content.replace("{TITLE}", safe_title)
        doc = doc.replace("{CSP_META}", csp_meta + fonts_link)
        # Note: {HIGHLIGHT_JS_CSS} and {HIGHLIGHT_JS} are safely replaced with empty strings for backwards compatibility if still in template
        doc = doc.replace("{HIGHLIGHT_JS_CSS}", "")
        doc = doc.replace("{HIGHLIGHT_JS}", "")
        doc = doc.replace("{MATHJAX}", mathjax)

        if content_css:
            content_css_tag = f'{{CSS_BLOCK}}\n<style id="mono-components-content-css">\n{content_css}\n</style>'
            doc = doc.replace("{CSS_BLOCK}", content_css_tag)

        has_images = bool(re.search(r"<img\b", html_body)) or bool(asset_store)
        if (has_images or asset_store) and not is_minimal:
            asset_template = ""
            if asset_store:
                safe_json = (
                    json.dumps(asset_store)
                    .replace("<", "\\u003c")
                    .replace(">", "\\u003e")
                    .replace("&", "\\u0026")
                )
                asset_template = f'<script type="application/json" id="mono-asset-store">{safe_json}</script>\n'
            lazy_load_js = self._load_lazy_load_script()
            lazy_load_script = (
                f"<script>\n{lazy_load_js}\n</script>\n" if lazy_load_js else ""
            )
            html_body += f"\n{asset_template}{lazy_load_script}"

        # 既存の {COPY_BUTTON_JS} プレースホルダーにまとめて追記する
        combined_js = f"{component_templates}\n{mono_components_js}" if not is_minimal else ""
        doc = doc.replace("{COPY_BUTTON_JS}", combined_js)
        doc = doc.replace(
            "{BODY}", html_body
        )  # Ensure BODY is replaced after appending asset store

        return doc

    def extract_title_from_html(self, html_content: str) -> str:
        """
        HTMLから最初の<h1>をタイトルとして抽出

        Args:
            html_content: HTML文字列

        Returns:
            抽出されたタイトル（デフォルト: "Document"）
        """
        match = re.search(r"<h1[^>]*>(.+?)</h1>", html_content)
        if match:
            # HTMLタグを削除
            title = re.sub(r"<[^>]+>", "", match.group(1))
            return title[:60]  # 最大60文字
        return "Document"

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML特殊文字をエスケープ"""
        # 最適化: C実装の高速な `html.escape` を使用
        # `&#x27;` と `&#39;` の違いはあるが、どちらも有効なアポストロフィのエスケープ
        return html.escape(text, quote=True).replace("&#x27;", "&#39;")

    def _remove_table_inline_styles(self, html_content: str) -> str:
        """
        テーブルタグから不要なインラインスタイルを削除

        Markdownライブラリが付与する text-align: left; などを除去
        """
        # <td style="..."> → <td>
        # <th style="..."> → <th>
        pattern = re.compile(HTML_TABLE_STYLE_PATTERN, re.IGNORECASE)
        result = pattern.sub(r"<\1", html_content)
        return result

    def _remove_excluded_tags(
        self, html_content: str, excluded_tags: Optional[List[str]]
    ) -> str:
        """
        指定されたタグをHTMLから削除（タグとその中身も一緒に削除）

        Args:
            html_content: HTML文字列
            excluded_tags: 削除対象のタグ名リスト（例：["hr", "div"]）

        Returns:
            タグ削除後のHTML
        """
        if not excluded_tags:
            return html_content

        class SafeTagRemovalParser(HTMLParser):
            VOID_ELEMENTS = {
                "area", "base", "br", "col", "embed", "hr", "img", "input",
                "link", "meta", "param", "source", "track", "wbr"
            }

            def __init__(self, excluded_tags):
                super().__init__(convert_charrefs=False)
                self.excluded_tags = set(tag.lower() for tag in excluded_tags)
                self.exclude_stack = []
                self.output = []

            def handle_starttag(self, tag, attrs):
                is_excluded = tag in self.excluded_tags
                is_void = tag in self.VOID_ELEMENTS

                if is_excluded and not is_void:
                    self.exclude_stack.append(tag)

                if not self.exclude_stack and not (is_excluded and is_void):
                    attr_str = "".join([f' {k}="{v}"' if v is not None else f' {k}' for k, v in attrs])
                    self.output.append(f"<{tag}{attr_str}>")

            def handle_endtag(self, tag):
                if self.exclude_stack and tag == self.exclude_stack[-1]:
                    self.exclude_stack.pop()
                elif not self.exclude_stack:
                    self.output.append(f"</{tag}>")

            def handle_startendtag(self, tag, attrs):
                if tag in self.excluded_tags:
                    return

                if not self.exclude_stack:
                    attr_str = "".join([f' {k}="{v}"' if v is not None else f' {k}' for k, v in attrs])
                    self.output.append(f"<{tag}{attr_str} />")

            def handle_data(self, data):
                if not self.exclude_stack:
                    self.output.append(data)

            def handle_entityref(self, name):
                if not self.exclude_stack:
                    self.output.append(f"&{name};")

            def handle_charref(self, name):
                if not self.exclude_stack:
                    self.output.append(f"&#{name};")

            def handle_comment(self, data):
                if not self.exclude_stack:
                    self.output.append(f"<!--{data}-->")

            def handle_decl(self, decl):
                if not self.exclude_stack:
                    self.output.append(f"<!{decl}>")

            def handle_pi(self, data):
                if not self.exclude_stack:
                    self.output.append(f"<?{data}>")

            def get_output(self):
                return "".join(self.output)

        parser = SafeTagRemovalParser(excluded_tags)
        parser.feed(html_content)
        result = parser.get_output()

        self.logger.debug(f"除外タグの一括削除処理を実行 (ASTベース): {excluded_tags}")

        return result

    def _load_lazy_load_script(self) -> str:
        """lazy_load.js ファイルを読み込んで返す"""
        js_file = TEMPLATES_DIR / "core" / "lazy_load.js"
        try:
            return js_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.logger.warning(f"lazy_load.js が見つかりません: {js_file}")
            return ""
        except Exception as e:
            self.logger.warning(f"lazy_load.js の読み込みエラー: {e}")
            return ""

    def _build_mathjax_script(self) -> str:
        """MathJax は事前レンダリングされるため空文字を返す"""
        return ""

    def _get_used_component_dirs(
        self,
        found_mono_tags: set,
        should_enable_export: bool,
        profile_components: Optional[List[str]] = None,
    ) -> List[Path]:
        """使用されているコンポーネントのディレクトリ一覧を取得する"""
        components_dir = COMPONENTS_DIR
        if not components_dir.exists() or not components_dir.is_dir():
            return []

        profile_components = profile_components or []
        include_all = "*" in profile_components

        # カテゴリ指定（例: @interactive）のオプトイン展開
        expanded_profiles = set()
        for comp in profile_components:
            if comp.startswith("@"):
                cat_name = comp[1:]
                expanded_profiles.update(registry.get_components_by_category(cat_name))
            else:
                expanded_profiles.add(comp)

        used_dirs = []
        for component_dir in sorted(components_dir.iterdir()):
            if not component_dir.is_dir():
                continue

            name = component_dir.name

            # Web Component非保持（パーサー専用モジュール等）はアセット探索から除外
            if not registry.is_web_component(name):
                continue

            # プロファイルによる指定
            if include_all or name in expanded_profiles:
                used_dirs.append(component_dir)
                continue

            # 常に含めるコンポーネント（後方互換性）
            if name in registry.get_always_include_components():
                used_dirs.append(component_dir)
                continue

            # エクスポートコンポーネント
            if name == "mono-export":
                if should_enable_export:
                    used_dirs.append(component_dir)
                continue

            # HTML内で使用されているかチェック
            if name in found_mono_tags:
                used_dirs.append(component_dir)

        return used_dirs

    def _load_mono_components_script(self, used_component_dirs: List[Path]) -> str:
        """指定されたコンポーネントの script.js を読み込んで <script> タグで返す"""
        if not used_component_dirs:
            return ""

        js_contents = []

        # Base element script
        base_element_script_file = TEMPLATES_DIR / "core" / "mono-base-element.js"
        if base_element_script_file.exists():
            try:
                js_contents.append(base_element_script_file.read_text(encoding="utf-8"))
            except Exception as e:
                self.logger.warning(
                    f"JS読み込みエラー ({base_element_script_file}): {e}"
                )

        # Base interactive element script (インタラクティブコンポーネントが含まれる場合のみ注入)
        has_interactive = any(
            d.name in registry.get_interactive_components()
            for d in used_component_dirs
        )
        if has_interactive:
            base_script_file = TEMPLATES_DIR / "core" / "mono-interactive-element.js"
            if base_script_file.exists():
                try:
                    js_contents.append(base_script_file.read_text(encoding="utf-8"))
                except Exception as e:
                    self.logger.warning(f"JS読み込みエラー ({base_script_file}): {e}")

        for component_dir in used_component_dirs:
            js_file = component_dir / "script.js"
            if js_file.exists():
                try:
                    js_contents.append(js_file.read_text(encoding="utf-8"))
                except Exception as e:
                    self.logger.warning(f"JS読み込みエラー ({js_file}): {e}")

        if not js_contents:
            return ""

        combined_js = "\n\n".join(js_contents)
        return f"<script>\n{combined_js}\n</script>"

    def _load_component_content_css(self, used_component_dirs: List[Path]) -> str:
        """指定されたコンポーネントの content.css を読み込み、結合して返す"""
        if not used_component_dirs:
            return ""

        css_contents = []
        for component_dir in used_component_dirs:
            css_file = component_dir / "content.css"
            if css_file.exists():
                try:
                    css_contents.append(css_file.read_text(encoding="utf-8"))
                except Exception as e:
                    self.logger.warning(f"content.css読み込みエラー ({css_file}): {e}")

        if not css_contents:
            return ""

        combined_css = "\n\n".join(css_contents)
        return combined_css

    def _load_component_templates(self, used_component_dirs: List[Path]) -> str:
        """指定されたコンポーネントの template.html を読み込み、対応する style.css を注入して結合する"""
        if not used_component_dirs:
            return ""

        templates_html = []
        for component_dir in used_component_dirs:
            template_file = component_dir / "template.html"
            css_file = component_dir / "style.css"

            if template_file.exists():
                try:
                    template_content = template_file.read_text(encoding="utf-8")
                    css_content = ""
                    if css_file.exists():
                        try:
                            css_content = css_file.read_text(encoding="utf-8")
                        except Exception as e:
                            self.logger.warning(f"CSS読み込みエラー ({css_file}): {e}")

                    template_content = template_content.replace(
                        "{COMPONENTS_CSS}", css_content
                    )
                    templates_html.append(template_content)
                except Exception as e:
                    self.logger.warning(
                        f"テンプレート読み込みエラー ({template_file}): {e}"
                    )

        return "\n\n".join(templates_html)
