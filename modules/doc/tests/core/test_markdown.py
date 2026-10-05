import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
from unittest.mock import MagicMock, patch
import sys
import logging

import importlib.util
if importlib.util.find_spec("markdown") is None:
    # Fallback to mock if the dependency is missing in the test environment
    sys.modules['markdown'] = MagicMock()

from src.processors.markdown import MarkdownProcessor
from src.config import ConversionError
from src.constants import MARKDOWN_EXTENSIONS

class TestMarkdownProcessor(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_logger")
        self.file_handler = MagicMock()
        self.processor = MarkdownProcessor(self.logger, self.file_handler)

    def _get_parser(self, component_name, processor=None):
        p = processor if processor else self.processor
        for parser in p.parsers:
            if parser.__class__.__module__.endswith(f"{component_name}.parser"):
                return parser
        return None

    def test_preprocess_layout(self):
        md_content = (
            "::: hbox center gap-md\n"
            "A\n"
            ":::\n"
            "::: vbox\n"
            "B\n"
            ":::\n"
            ":::"
        )
        expected_html = (
            '<mono-layout type="hbox" class="center gap-md" markdown="1">\n'
            '<div class="column" markdown="1">\n'
            "A\n"
            "</div>\n"
            '<div class="column" markdown="1">\n'
            '<mono-layout type="vbox" markdown="1">\n'
            '<div class="column" markdown="1">\n'
            "B\n"
            "</div>\n"
            "</mono-layout>\n"
            "</div>\n"
            "</mono-layout>"
        )
        result = self._get_parser("mono-layout").process(md_content)
        self.assertEqual(result, expected_html)

    @patch('src.processors.markdown.markdown')
    def test_convert_markdown_to_html_success(self, mock_markdown):
        mock_markdown.markdown.side_effect = None
        mock_markdown.markdown.return_value = "<h1>Processed</h1>"

        md_content = "# Title\n@[poll: Title](options: \"A, B\")"
        result = self.processor.convert_markdown_to_html(md_content)

        self.assertEqual(result, "<h1>Processed</h1>")

        # Verify markdown.markdown was called with the preprocessed content
        expected_preprocessed = '# Title\n<mono-poll id="poll-1" title="Title" options="A, B"></mono-poll>'
        mock_markdown.markdown.assert_any_call(
            expected_preprocessed,
            extensions=MARKDOWN_EXTENSIONS,
            tab_length=2,
        )

    def test_code_blocks_protected(self):
        """コードブロック内のコンポーネント構文が変換されず保護されることをテスト"""
        markdown_content = """
@[icon: outside]

```markdown
@[icon: inside_fenced]
```

Inline `@[icon: inside_inline]` testing.
"""
        html_output = self.processor.convert_markdown_to_html(markdown_content)

        # 外側のアイコンは変換される
        assert '<mono-icon name="outside">' in html_output

        # フェンスコードブロック内のアイコンは変換されない
        assert '<mono-icon name="inside_fenced">' not in html_output
        # We just need to ensure the raw string `@` and `[` are present and the component wasn't parsed
        assert 'inside' in html_output
        assert 'fenced' in html_output
        assert 'icon:' in html_output

        # インラインコードブロック内のアイコンは変換されない
        assert '<mono-icon name="inside_inline">' not in html_output
        assert '@[icon: inside_inline]' in html_output

    def test_unclosed_backtick_does_not_swallow_fenced_blocks(self):
        """閉じられていないバックティックが後続のフェンスコードブロックを巻き込まないことをテスト"""
        markdown_content = """
Item with stray backtick:
`
Another paragraph.

```python
def foo():
    return 42
```
"""
        html_output = self.processor.convert_markdown_to_html(markdown_content)
        assert "@@FENCED_CODE_BLOCK" not in html_output
        assert '<mono-code-block language="python">' in html_output
        assert "def foo():" in html_output

    @patch('src.processors.markdown.markdown')
    def test_convert_markdown_to_html_error(self, mock_markdown):
        mock_markdown.markdown.side_effect = Exception("Markdown parsing failed")

        md_content = "# Title"
        with self.assertRaises(ConversionError) as context:
            self.processor.convert_markdown_to_html(md_content)

        self.assertIn("Markdown変換エラー", str(context.exception))

    def test_new_syntax_pattern_a(self):
        """Test the new Markdown syntax (Pattern A) separating specific args and styles"""
        # testfield with label, id, placeholder in [] and class in ()
        md_content = 'Input: @[textfield: "Name", id: "user-name", placeholder: "Enter name"](class: "gap-md center")'
        expected_html = 'Input: <mono-textfield-input placeholder="Enter name" label="Name" class="gap-md center" id="user-name"></mono-textfield-input>'
        result = self._get_parser("mono-textfield-input").process(md_content)
        self.assertEqual(result, expected_html)

        # icon with size, color in [], display in ()
        md_content2 = '@[icon: search, size: 24px, color: red](display: block)'
        expected_html2 = '<mono-icon name="search" size="24px" color="red" display="block"></mono-icon>'
        result2 = self._get_parser("mono-icon").process(md_content2)
        self.assertEqual(result2, expected_html2)

    def test_typography_trinity_classes(self):
        """Typography Trinity (.text-display, .text-body, .text-compact) がattr_list拡張でHTMLクラスに変換されることをテスト"""
        md_content = """# 看板見出し {.text-display}

標準本文テキスト
{: .text-body}

凝縮注釈テキスト
{: .text-compact}"""
        html_output = self.processor.convert_markdown_to_html(md_content)
        self.assertIn('class="text-display"', html_output)
        self.assertIn('class="text-body"', html_output)
        self.assertIn('class="text-compact"', html_output)

    def test_two_space_nested_list(self):
        """2スペースインデントで記述されたネストリストが正確にli > ulに変換されることをテスト"""
        md_content = """- 親項目
  - 子項目1
  - 子項目2"""
        html_output = self.processor.convert_markdown_to_html(md_content)
        self.assertIn("<li>親項目<ul>", html_output)
        self.assertIn("<li>子項目1</li>", html_output)
        self.assertIn("<li>子項目2</li>", html_output)

    def test_html_comment_removal(self):
        """本文中のHTMLコメントが除去され、コードブロック内のコメントは保持されることをテスト"""
        md_content = """# 見出し
<!-- 単一行コメント -->
本文前 <!-- インラインコメント --> 本文後

<!--
複数行
コメント
-->

```html
<!-- コードブロック内のコメント -->
<div>保留</div>
```

`<!-- インラインコード内のコメント -->`
"""
        html_output = self.processor.convert_markdown_to_html(md_content)
        self.assertNotIn("単一行コメント", html_output)
        self.assertNotIn("インラインコメント", html_output)
        self.assertNotIn("複数行", html_output)
        self.assertNotIn("コメント", html_output.split("<pre>")[0])
        self.assertIn("&lt;!-- コードブロック内のコメント --&gt;", html_output)
        self.assertIn("&lt;!-- インラインコード内のコメント --&gt;", html_output)


