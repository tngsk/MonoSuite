import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from unittest.mock import patch
from pathlib import Path
import logging

from src.processors.html import HTMLDocumentBuilder
from src.config import ConversionError

class TestHTMLDocumentBuilder(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_html_logger")
        self.template_path = Path("test_template.html")
        self.builder = HTMLDocumentBuilder(self.logger, self.template_path)

    @patch('pathlib.Path.read_text')
    def test_build_document_success(self, mock_read_text):
        mock_read_text.return_value = "<html><head>{CSP_META}{HIGHLIGHT_JS_CSS}</head><body>{TITLE}{BODY}{HIGHLIGHT_JS}{COPY_BUTTON_JS}</body></html>"

        with patch.object(self.builder, '_get_used_component_dirs', return_value=[]):

            result = self.builder.build_document(html_body="<p>test</p>", title="Test Title")

            self.assertIn("Test Title", result)
            self.assertIn("<p>test</p>", result)

    def test_build_document_missing_template(self):
        with patch('pathlib.Path.read_text', side_effect=FileNotFoundError):
            with self.assertRaises(ConversionError) as context:
                self.builder.build_document(html_body="<p>test</p>")
            self.assertIn("テンプレートファイルが見つかりません", str(context.exception))

    def test_build_document_generic_exception(self):
        with patch('pathlib.Path.read_text', side_effect=Exception("Read error")):
            with self.assertRaises(ConversionError) as context:
                self.builder.build_document(html_body="<p>test</p>")
            self.assertIn("テンプレート読み込みエラー: Read error", str(context.exception))

    @patch("pathlib.Path.read_text")
    def test_build_document_icon_fonts_injection(self, mock_read_text):
        """<mono-icon>が存在する場合にGoogle Fontsが注入されることをテスト"""
        mock_read_text.return_value = "<!doctype html><html><head>{CSP_META}</head><body>{BODY}</body></html>"
        html_body = "<mono-icon name=search></mono-icon>"

        result = self.builder.build_document(html_body=html_body)

        self.assertIn("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined", result)
        self.assertIn("https://fonts.googleapis.com", result)
        self.assertIn("https://fonts.gstatic.com", result)

    @patch('pathlib.Path.read_text')
    def test_build_document_export_and_interactive(self, mock_read_text):
        mock_read_text.return_value = "{BODY}{COPY_BUTTON_JS}"
        with patch.object(self.builder, '_get_used_component_dirs', return_value=[]), \
             patch.object(self.builder, '_load_component_templates', return_value=""), \
             patch.object(self.builder, '_load_mono_components_script', return_value=""):

            # test enable_export=True
            result1 = self.builder.build_document(html_body="<p>test</p>", enable_export=True)
            self.assertIn("<mono-export></mono-export>", result1)

            # test interactive component triggers export
            result2 = self.builder.build_document(html_body="<mono-poll></mono-poll>")
            self.assertIn("<mono-export></mono-export>", result2)

    @patch('pathlib.Path.read_text')
    def test_build_document_connect_src(self, mock_read_text):
        mock_read_text.return_value = "{CSP_META}{COPY_BUTTON_JS}"
        with patch.object(self.builder, '_get_used_component_dirs', return_value=[]), \
             patch.object(self.builder, '_load_component_templates', return_value=""), \
             patch.object(self.builder, '_load_mono_components_script', return_value=""):

            result = self.builder.build_document(
                html_body="<p>test</p>",
                connect_src="https://api.example.com"
            )
            self.assertIn("connect-src 'self' https://cdn.jsdelivr.net https://api.example.com", result)
            self.assertIn('<meta name="mono-api-url" content="https://api.example.com">', result)

    @patch('pathlib.Path.read_text')
    def test_build_document_csp_additions(self, mock_read_text):
        mock_read_text.return_value = "{CSP_META}"
        with patch.object(self.builder, '_get_used_component_dirs', return_value=[]), \
             patch.object(self.builder, '_load_lazy_load_script', return_value="console.log('lazy');"), \
             patch.object(self.builder, '_load_component_templates', return_value=""), \
             patch.object(self.builder, '_load_mono_components_script', return_value=""):
            csp_additions = {"img-src": ["https://example.com"], "new-src": ["'self'"]}
            result = self.builder.build_document(html_body="<p>test</p>", csp_additions=csp_additions)

            self.assertIn("https://example.com", result)
            self.assertIn("new-src 'self'", result)

    @patch('pathlib.Path.read_text')
    def test_build_document_asset_store(self, mock_read_text):
        mock_read_text.return_value = "{BODY}{COPY_BUTTON_JS}"
        with patch.object(self.builder, '_get_used_component_dirs', return_value=[]), \
             patch.object(self.builder, '_load_lazy_load_script', return_value="console.log('lazy');"), \
             patch.object(self.builder, '_load_component_templates', return_value=""), \
             patch.object(self.builder, '_load_mono_components_script', return_value=""):
            asset_store = {"image1.png": "data:image/png;base64,1234"}
            result = self.builder.build_document(html_body="<p>test</p>", asset_store=asset_store)

            self.assertIn('<script type="application/json" id="mono-asset-store">{"image1.png": "data:image/png;base64,1234"}</script>', result)
            self.assertIn("console.log('lazy');", result)

    def test_extract_title_from_html(self):
        html_with_title = "<html><body><h1>My Title</h1><p>content</p></body></html>"
        self.assertEqual(self.builder.extract_title_from_html(html_with_title), "My Title")

        html_without_title = "<html><body><h2>My Title</h2><p>content</p></body></html>"
        self.assertEqual(self.builder.extract_title_from_html(html_without_title), "Document")

        html_with_nested_tags = "<h1><span>Complex</span> Title</h1>"
        self.assertEqual(self.builder.extract_title_from_html(html_with_nested_tags), "Complex Title")

        html_with_attributes = '<h1 id="main-title" class="title-class">My Styled Title</h1>'
        self.assertEqual(self.builder.extract_title_from_html(html_with_attributes), "My Styled Title")

    def test_escape_html(self):
        self.assertEqual(self.builder._escape_html("AT&T"), "AT&amp;T")
        self.assertEqual(self.builder._escape_html("<script>"), "&lt;script&gt;")
        self.assertEqual(self.builder._escape_html('He said "Hello"'), 'He said &quot;Hello&quot;')
        self.assertEqual(self.builder._escape_html("It's a test"), "It&#39;s a test")

    def test_remove_table_inline_styles(self):
        html_input = '<table><tr><td style="text-align: left;">Data</td><th style="color: red;">Head</th></tr></table>'
        expected = '<table><tr><td>Data</td><th>Head</th></tr></table>'
        self.assertEqual(self.builder._remove_table_inline_styles(html_input), expected)

    def test_remove_excluded_tags(self):
        # Basic paired tag exclusion
        html_input_paired = '<div><p>Text</p></div><p>Outside</p>'
        result1 = self.builder._remove_excluded_tags(html_input_paired, ["div"])
        self.assertEqual(result1, '<p>Outside</p>')

        # Test void (self-closing) tag exclusion
        html_input_void = '<div><p>Text</p><hr /><hr></div>'
        result2 = self.builder._remove_excluded_tags(html_input_void, ["hr"])
        self.assertEqual(result2, '<div><p>Text</p></div>')

        # Test nested tag exclusion (ensures the AST parsing doesn't break)
        html_input_nested = '<div><p>Keep this</p><div class="exclude">Exclude me <hr> and this <div>nested</div> text.</div><p>Also keep this</p><hr /></div>'
        result3 = self.builder._remove_excluded_tags(html_input_nested, ["div"])
        self.assertEqual(result3, '')

        result4 = self.builder._remove_excluded_tags(html_input_nested, ["hr"])
        self.assertEqual(result4, '<div><p>Keep this</p><div class="exclude">Exclude me  and this <div>nested</div> text.</div><p>Also keep this</p></div>')

        # Test no exclusions
        result5 = self.builder._remove_excluded_tags(html_input_paired, None)
        self.assertEqual(result5, html_input_paired)

    def test_load_lazy_load_script(self):
        with patch('pathlib.Path.read_text', return_value="console.log('lazy');"):
            self.assertEqual(self.builder._load_lazy_load_script(), "console.log('lazy');")

        with patch('pathlib.Path.read_text', side_effect=FileNotFoundError):
            self.assertEqual(self.builder._load_lazy_load_script(), "")

        with patch('pathlib.Path.read_text', side_effect=Exception("Read error")):
            self.assertEqual(self.builder._load_lazy_load_script(), "")

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.iterdir')
    def test_get_used_component_dirs(self, mock_iterdir, mock_is_dir, mock_exists):
        # Create mock paths using MagicMock so they are sortable
        from unittest.mock import MagicMock

        mock_zoom = MagicMock()
        mock_zoom.name = 'mono-zoom'
        mock_zoom.is_dir.return_value = True
        mock_zoom.__lt__.side_effect = lambda other: mock_zoom.name < other.name

        mock_brush = MagicMock()
        mock_brush.name = 'mono-brush'
        mock_brush.is_dir.return_value = True
        mock_brush.__lt__.side_effect = lambda other: mock_brush.name < other.name

        mock_export = MagicMock()
        mock_export.name = 'mono-export'
        mock_export.is_dir.return_value = True
        mock_export.__lt__.side_effect = lambda other: mock_export.name < other.name

        mock_poll = MagicMock()
        mock_poll.name = 'mono-poll'
        mock_poll.is_dir.return_value = True
        mock_poll.__lt__.side_effect = lambda other: mock_poll.name < other.name

        mock_unknown = MagicMock()
        mock_unknown.name = 'mono-unknown'
        mock_unknown.is_dir.return_value = True
        mock_unknown.__lt__.side_effect = lambda other: mock_unknown.name < other.name

        mock_not_dir = MagicMock()
        mock_not_dir.name = 'not-a-dir'
        mock_not_dir.is_dir.return_value = False
        mock_not_dir.__lt__.side_effect = lambda other: mock_not_dir.name < other.name

        mock_iterdir.return_value = [mock_zoom, mock_brush, mock_export, mock_poll, mock_unknown, mock_not_dir]

        # Test 1: enable_export=False, html_body has <mono-poll> (On-demand only)
        result1 = self.builder._get_used_component_dirs(found_mono_tags={"mono-poll"}, should_enable_export=False)
        names1 = [p.name for p in result1]
        self.assertIn('mono-poll', names1)  # Found in HTML
        self.assertNotIn('mono-zoom', names1)  # Not in profile or HTML
        self.assertNotIn('mono-brush', names1) # Not in profile or HTML
        self.assertNotIn('mono-export', names1) # Export not enabled
        self.assertNotIn('mono-unknown', names1) # Not found in HTML
        self.assertNotIn('not-a-dir', names1) # Not a directory

        # Test 2: enable_export=True, no components in HTML
        result2 = self.builder._get_used_component_dirs(found_mono_tags=set(), should_enable_export=True)
        names2 = [p.name for p in result2]
        self.assertIn('mono-export', names2) # Export enabled
        self.assertNotIn('mono-poll', names2)
        self.assertNotIn('mono-zoom', names2)

        # Test 3: with profile_components
        result3 = self.builder._get_used_component_dirs(
            found_mono_tags=set(),
            should_enable_export=False,
            profile_components=["mono-zoom", "mono-brush"]
        )
        names3 = [p.name for p in result3]
        self.assertIn('mono-zoom', names3)
        self.assertIn('mono-brush', names3)
        self.assertNotIn('mono-poll', names3)

    @patch('pathlib.Path.exists', return_value=False)
    def test_get_used_component_dirs_missing_dir(self, mock_exists):
        result = self.builder._get_used_component_dirs(found_mono_tags=set(), should_enable_export=False)
        self.assertEqual(result, [])

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.read_text', return_value="console.log('component');")
    def test_load_mono_components_script(self, mock_read_text, mock_exists):
        mock_dir1 = Path("fake_dir1")
        mock_dir2 = Path("fake_dir2")

        result = self.builder._load_mono_components_script([mock_dir1, mock_dir2])
        self.assertIn("<script>", result)
        self.assertIn("console.log('component');", result)
        self.assertIn("</script>", result)

        # Test exception handling
        mock_read_text.side_effect = Exception("Read error")
        result_error = self.builder._load_mono_components_script([mock_dir1])
        self.assertEqual(result_error, "")

    def test_load_mono_components_script_empty(self):
        self.assertEqual(self.builder._load_mono_components_script([]), "")

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.read_text')
    def test_load_component_templates(self, mock_read_text, mock_exists):
        # We can simulate by returning a dictionary-like side_effect based on the file name being accessed.
        # But for simpler mocking, we will just return a string and see what happens.
        # Since read_text is called twice (for template, then css), side_effect as list works.
        mock_read_text.side_effect = ["<template>{COMPONENTS_CSS}</template>", ".css { color: red; }"]

        mock_dir = Path("fake_dir")
        result = self.builder._load_component_templates([mock_dir])
        self.assertEqual(result, "<template>.css { color: red; }</template>")

        # Test CSS error
        mock_read_text.side_effect = ["<template>{COMPONENTS_CSS}</template>", Exception("CSS read error")]
        result_css_error = self.builder._load_component_templates([mock_dir])
        self.assertEqual(result_css_error, "<template></template>")

        # Test template error
        mock_read_text.side_effect = Exception("Template read error")
        result_template_error = self.builder._load_component_templates([mock_dir])
        self.assertEqual(result_template_error, "")

    def test_load_component_templates_empty(self):
        self.assertEqual(self.builder._load_component_templates([]), "")

    @patch('pathlib.Path.read_text')
    def test_build_document_zero_js_for_static_content(self, mock_read_text):
        """静的コンテンツ（コンポーネントなし）の場合、<script>タグが出力されない（Zero-JS）ことをテスト"""
        mock_read_text.return_value = "<!doctype html><html><head>{CSP_META}</head><body>{BODY}{COPY_BUTTON_JS}</body></html>"
        html_body = "<p>Simple static text</p>"

        result = self.builder.build_document(html_body=html_body, profile_components=[])
        self.assertNotIn("<script>", result)
        self.assertNotIn("</script>", result)
        self.assertIn("<p>Simple static text</p>", result)

    def test_get_used_component_dirs_with_profile(self):
        """プロファイルで指定されたコンポーネントが抽出されることをテスト"""
        result = self.builder._get_used_component_dirs(
            found_mono_tags=set(),
            should_enable_export=False,
            profile_components=["mono-zoom", "mono-brush"]
        )
        names = [d.name for d in result]
        self.assertIn("mono-zoom", names)
        self.assertIn("mono-brush", names)
        self.assertNotIn("mono-poll", names)

    def test_get_used_component_dirs_with_category_profile(self):
        """プロファイルで@category（例: @interactive）が指定された場合に対象群が一括抽出されることをテスト"""
        result = self.builder._get_used_component_dirs(
            found_mono_tags=set(),
            should_enable_export=False,
            profile_components=["@interactive"]
        )
        names = [d.name for d in result]
        self.assertIn("mono-poll", names)
        self.assertIn("mono-reaction", names)
        self.assertIn("mono-account", names)
        self.assertIn("mono-export", names)
        self.assertNotIn("mono-zoom", names)
        self.assertNotIn("mono-clock", names)

    @patch('pathlib.Path.read_text')
    def test_build_document_minimal_profile_zero_js(self, mock_read_text):
        """minimalプロファイルでコードブロックと画像が含まれる場合でもZero-JSとなりコードブロックがアンラップされることをテスト"""
        mock_read_text.return_value = "<!doctype html><html><head>{CSP_META}</head><body>{BODY}{COPY_BUTTON_JS}</body></html>"
        html_body = '<p>Hello</p><mono-code-block language="python"><pre><code class="language-python">print("hi")</code></pre></mono-code-block>'
        asset_store = {"asset-1": "data:image/png;base64,xxxx"}

        result = self.builder.build_document(
            html_body=html_body,
            title="Minimal Doc",
            asset_store=asset_store,
            profile="minimal"
        )

        self.assertNotIn("<script", result)
        self.assertNotIn("</script>", result)
        self.assertIn("script-src 'none'", result)
        self.assertNotIn("<mono-code-block", result)
        self.assertIn('<pre><code class="language-python">print("hi")</code></pre>', result)
        self.assertNotIn("mono-asset-store", result)

    @patch('pathlib.Path.read_text')
    def test_build_document_minimal_profile_unsupported_component(self, mock_read_text):
        """minimalプロファイルで未対応のコンポーネントが存在する場合に例外が送出されることをテスト"""
        mock_read_text.return_value = "<!doctype html><html><head>{CSP_META}</head><body>{BODY}{COPY_BUTTON_JS}</body></html>"
        html_body = '<mono-poll id="p1" question="Q?"></mono-poll>'

        with self.assertRaises(ConversionError) as context:
            self.builder.build_document(
                html_body=html_body,
                profile="minimal"
            )

        self.assertIn("minimalプロファイルで未対応のコンポーネントが含まれています: mono-poll", str(context.exception))

    @patch('pathlib.Path.read_text')
    def test_build_document_external_image_lazy_load_injection(self, mock_read_text):
        """外部画像のみが存在する場合でも画像エラーハンドラ用のlazy_load.jsが注入されることをテスト"""
        mock_read_text.return_value = "<!doctype html><html><head>{CSP_META}</head><body>{BODY}{COPY_BUTTON_JS}</body></html>"
        html_body = '<p>Test</p><img src="https://example.com/test.png" alt="test" />'

        with patch.object(self.builder, '_load_lazy_load_script', return_value="console.log('lazy_load_mock');"):
            result = self.builder.build_document(
                html_body=html_body,
                title="External Image Doc",
                asset_store={},
            )

            self.assertIn("lazy_load_mock", result)
            self.assertNotIn("mono-asset-store", result)

if __name__ == '__main__':
    unittest.main()
