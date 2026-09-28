import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from mono_space.markdown_parser import parse_document
from mono_space.markdown_renderer import render_document

class BlockTests(unittest.TestCase):
    def test_mixed_blocks_and_literal_code(self):
        source = '# Demo\nparagraph\n\n| A |\n| --- |\n| B |\n\n```sh\n# literal\n::tone error\n```\n::link https://example.com\n::link-title Example'
        document = parse_document(source)
        blocks = document['nodes'][0]['blocks']
        self.assertEqual([b['kind'] for b in blocks], ['paragraph', 'table', 'code', 'link'])
        self.assertEqual(blocks[2]['text'], '# literal\n::tone error\n')
        original = copy.deepcopy(document)
        first = render_document(document, Path('.'))
        self.assertEqual(first, render_document(document, Path('.')))
        self.assertEqual(document, original)

    def test_parsing_does_not_load_images(self):
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected IO')):
            document = parse_document('# Picture\n![alt](missing.png)')
        self.assertEqual(document['nodes'][0]['blocks'][0]['kind'], 'images')
        with self.assertRaises(OSError):
            render_document(document, Path('.'))

    def test_html_comment_removal(self):
        source = """# Section
<!-- 単一行コメント -->
段落本文 <!-- インラインコメント --> つづき

<!--
複数行
コメント
-->

```html
<!-- コードブロック内コメント -->
<div>保留</div>
```
`<!-- インラインコード内コメント -->`
"""
        document = parse_document(source)
        rendered = render_document(document, Path('.'))
        html_str = rendered['nodes'][0]['html']
        self.assertNotIn("単一行コメント", html_str)
        self.assertNotIn("インラインコメント", html_str)
        self.assertNotIn("複数行", html_str)
        self.assertIn("&lt;!-- コードブロック内コメント --&gt;", html_str)
        self.assertIn("&lt;!-- インラインコード内コメント --&gt;", html_str)

