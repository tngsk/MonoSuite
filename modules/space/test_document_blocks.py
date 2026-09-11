import unittest
from build import parse

class DocumentBlocksTests(unittest.TestCase):
    def test_nested_quote_heading_and_list(self):
        result=parse('# T\n> #### 補足\n\n- > **項目**\n\n    >> 説明<script>\n\n- > **次の項目**\n\n    >> 詳細\n')
        html=result['nodes'][0]['html']
        self.assertIn('<h3 class="block-heading">補足</h3>',html)
        self.assertEqual(html.count('<li>'),2)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('####',html)
        self.assertEqual(len(result['nodes']),1)
    def test_ordered_list_keeps_start_and_code_literal(self):
        html=parse('# T\n3. Third\n4. Fourth\n\n```\n> quote\n- item\n```')['nodes'][0]['html']
        self.assertIn('<ol class="markdown-list" start="3">',html)
        self.assertEqual(html.count('<li>'),2)
        self.assertIn('&gt; quote\n- item',html)
