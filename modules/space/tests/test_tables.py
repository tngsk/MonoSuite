import unittest
from mono_space.build import parse

class Tables(unittest.TestCase):
    def render(self, text):
        return parse('# Test\n'+text)['nodes'][0]['html']

    def test_alignment_and_inline(self):
        result=self.render('| A | B | C |\n| :--- | :---: | ---: |\n| **bold** | `code` | [link](https://example.com) |')
        self.assertIn('<table',result)
        for alignment in ('left','center','right'):
            self.assertIn(f'class="align-{alignment}" scope="col"',result)
        self.assertIn('<strong>bold</strong>',result)
        self.assertIn('<code>code</code>',result)
        self.assertIn('target="_blank"',result)

    def test_optional_pipes_and_blank_end(self):
        result=self.render('A | B\n--- | ---\nx | y\n\na | paragraph')
        self.assertEqual(result.count('<tbody>'),1)
        self.assertIn('</table><p>a | paragraph</p>',result)

    def test_escaped_pipe_ragged_and_html(self):
        result=self.render('| A | B |\n| --- | --- |\n| a\\|b | <script> |\n| one |\n| 1 | 2 | extra |')
        self.assertIn('a|b',result)
        self.assertIn('&lt;script&gt;',result)
        self.assertIn('<td class="align-left"></td>',result)
        self.assertNotIn('extra',result)

    def test_invalid_separator_is_text(self):
        result=self.render('| A | B |\n| --- |\n| x | y |')
        self.assertNotIn('<table',result)
