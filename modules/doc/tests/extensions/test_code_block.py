import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest

import markdown

from src.extensions.code_block import CodeBlockExtension


class TestCodeBlockExtension(unittest.TestCase):
    def setUp(self):
        self.md = markdown.Markdown(extensions=["fenced_code", CodeBlockExtension()])

    def test_enhance_code_blocks(self):
        text = '```python\nprint("hello")\n```'
        html = self.md.convert(text)
        self.assertIn('<mono-code-block language="python">', html)
        self.assertIn('<pre><code class="language-python">', html)
        self.assertIn('print(&quot;hello&quot;)', html)

    def test_enhance_code_blocks_no_lang(self):
        text = '```\nprint("hello")\n```'
        html = self.md.convert(text)
        self.assertIn('<mono-code-block language="">', html)
        self.assertIn('<pre><code class="language-">', html)
        self.assertIn('print(&quot;hello&quot;)', html)

    def test_complex_code_block(self):
        text = """```python
def complex_fn(x: int) -> str:
    # Test symbols and placeholders
    s = "@@FENCED_CODE_BLOCK_0@@"
    val = f"Value: {x}"
    return val + "\\1"
```"""
        html = self.md.convert(text)
        self.assertIn('<mono-code-block language="python">', html)
        self.assertIn("@@FENCED_CODE_BLOCK_0@@", html)
        self.assertIn("\\1", html)
        self.assertIn('def complex_fn(x: int) -&gt; str:', html)

    def test_code_block_with_pre_attributes(self):
        # Simulating attributes that might be added by attr_list or manual HTML
        text = '<pre id="custom-id" class="custom-class"><code class="language-python">print("hello")</code></pre>'
        html = self.md.convert(text)
        self.assertIn(
            '<mono-code-block language="python" id="custom-id" class="custom-class">',
            html,
        )
        self.assertIn('<pre><code class="language-python">', html)
