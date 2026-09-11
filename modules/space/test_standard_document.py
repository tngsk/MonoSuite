import unittest
from pathlib import Path
from markdown_parser import parse_document
from markdown_renderer import render_document


class StandardDocumentTests(unittest.TestCase):
    def test_fixed_heading_roles_and_route(self):
        data = parse_document('# Title\n## Chapter\n### Topic\nText\n#### Detail\nMore\n##### Small\nEnd\n## Intro\nExplanation\n### Next\nBody')
        self.assertNotIn('document_mode', data)
        self.assertEqual([n['level'] for n in data['nodes']], [1, 2, 3, 2, 3])
        self.assertEqual([n['layout'] for n in data['nodes']], ['row','stack','stack','stack','stack'])
        topic = data['nodes'][2]
        self.assertEqual([b['kind'] for b in topic['blocks']], ['paragraph','local_heading','paragraph','local_heading','paragraph'])
        self.assertNotIn(data['nodes'][1]['id'], data['route'])
        self.assertIn(data['nodes'][3]['id'], data['route'])

    def test_layout_does_not_change_unrelated_heading_rules(self):
        data = parse_document('# Title\n## Chapter\n::layout stack\n### Topic\n#### Nested\nBody')
        self.assertNotIn('document_mode', data)
        self.assertEqual(len(data['nodes']), 3)

    def test_paragraphs_and_images_are_distinct(self):
        blocks = parse_document('# T\nFirst\ncontinued\n\nSecond\n\n![a](a.png)\n\n![b](b.png)\n\nAfter')['nodes'][0]['blocks']
        self.assertEqual([b['kind'] for b in blocks], ['paragraph','paragraph','images','paragraph'])
        self.assertEqual(blocks[0]['text'], 'First\ncontinued')
        self.assertEqual(len(blocks[2]['images']), 2)

    def test_code_heading_and_separators_are_literal(self):
        data = parse_document('# T\n```md\n#### Text\n::layout stack\n---\n```')
        self.assertNotIn('document_mode', data)
        self.assertEqual(data['nodes'][0]['blocks'][0]['text'], '#### Text\n::layout stack\n---\n')

    def test_emphasis_and_inline_code(self):
        data = render_document(parse_document('# T\n**_both_** __bold__ *italic* `**literal**` snake_case'), Path('.'))
        text = data['nodes'][0]['html']
        self.assertIn('<strong><em>both</em></strong>', text)
        self.assertIn('<code>**literal**</code>', text)
        self.assertIn('snake_case', text)

    def test_layout_items_are_local_and_paragraph_rules_are_shared(self):
        data = parse_document('# T\n## C\n### Comparison\n::layout compare\n#### A\nOne\ntwo\n#### B\nOther\n### Text\n#### Local\nBody')
        self.assertEqual([n['title'] for n in data['nodes']], ['T','C','Comparison','A','B','Text'])
        self.assertEqual(data['nodes'][3]['blocks'][0]['text'], 'One\ntwo')
        self.assertEqual(data['nodes'][-1]['blocks'][0]['kind'], 'local_heading')
