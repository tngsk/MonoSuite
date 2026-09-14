import unittest
from mono_space.mono_import import convert_mono
from mono_space.markdown_parser import parse_document

class MonoImportTests(unittest.TestCase):
    def test_components_and_hierarchy(self):
        source='@[section](bg-color: #FFC13E)\n# Title<br>Lesson\n@[/section]\n## Goal\n@[flow](orientation: "vertical")\nA -> B\n@[/flow]\n## Work\n| Value |\n| --- |\n| @[textfield](size: "8") |'
        text,report=convert_mono(source)
        nodes=parse_document(text)['nodes']
        self.assertEqual(nodes[0]['title'],'Title — Lesson')
        self.assertEqual([n['title'] for n in nodes],['Title — Lesson','Goal','工程','A','B','Work'])
        self.assertIn('［記入欄］',text)
        self.assertTrue(all(r['line']>0 for r in report))
    def test_code_is_literal_and_unknown_is_reported(self):
        source='# Title\n```python\n@[section](x)\n<br>\n```\n`@[textfield](x)`\n@[unknown](x)'
        text,report=convert_mono(source)
        self.assertIn('```python\n@[section](x)\n<br>\n```',text)
        self.assertIn('`@[textfield](x)`',text)
        self.assertIn('@[unknown](x)',text)
        self.assertEqual(len(report),1)
        self.assertEqual(report[0]['kind'],'unsupported')
    def test_label_before_heading_is_preserved(self):
        text,_=convert_mono('@[badge: "課題"]\n# Title')
        self.assertTrue(text.startswith('# Title\n課題'))
    def test_unclosed_flow_fails(self):
        with self.assertRaises(ValueError):convert_mono('# T\n@[flow]\nA -> B')


class UnifiedMonoTests(unittest.TestCase):
    def test_lists_and_breaks_use_common_parser(self):
        from mono_space.markdown_parser import parse_document
        text, _ = convert_mono('# T\n## Chapter\nOne<br>Two\n\n- A\n- B')
        self.assertNotIn('::layout', text)
        blocks = parse_document(text)['nodes'][1]['blocks']
        self.assertEqual([b['kind'] for b in blocks], ['paragraph','paragraph','list'])
