import unittest
from build import parse

class CodeTests(unittest.TestCase):
    def test_literal_code(self):
        d=parse('# Title\n```bash\n# comment\n::tone error\n\n  echo "<hello>"\n```\n## Next')
        self.assertEqual(len(d['nodes']),2)
        output=d['nodes'][0]['html']
        self.assertIn('# comment\n::tone error\n\n  echo &quot;&lt;hello&gt;&quot;\n',output)
        self.assertIn('codeblock',output)
        self.assertEqual(d['nodes'][0]['tone'],'neutral')
    def test_long_fence_and_unclosed(self):
        d=parse('# T\n````\n```\n````\ntext')
        self.assertIn('<code>```\n</code>',d['nodes'][0]['html'])
        d=parse('# T\n~~~python\nx = 1')
        self.assertIn('<code>x = 1</code>',d['nodes'][0]['html'])
    def test_code_then_table(self):
        d=parse('# T\n```\n| x |\n```\n\n| A |\n| --- |\n| b |')
        self.assertIn('<table',d['nodes'][0]['html'])
