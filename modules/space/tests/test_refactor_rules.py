import tempfile
import unittest
from pathlib import Path
from mono_space.markdown_parser import parse_document
from mono_space.markdown_renderer import render_document
from mono_space.markdown_syntax import fence_open, fence_close
from mono_space.mono_import import convert_mono
from mono_space.deckset_import import split_slides


class RefactorRulesTests(unittest.TestCase):
    def test_local_heading_directives_fail_with_line_number(self):
        for directive in ('tone warning', 'layout compare', 'focus image', 'marker on', 'style note'):
            with self.subTest(directive=directive), self.assertRaisesRegex(ValueError, '4行: 本文内見出し'):
                parse_document('# T\n### Topic\n#### Local\n::'+directive+'\nText')

    def test_recipe_item_directives_remain_valid(self):
        data = parse_document('# T\n### Pair\n::layout compare\n#### A\n::tone warning\nText\n#### B\nOther')
        self.assertEqual(data['nodes'][2]['tone'], 'warning')

    def test_image_alt_is_not_a_layout_and_parentheses_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'photo (1).png').write_bytes(b'image')
            doc=parse_document('# T\n![right](photo (1).png)')
            picture=doc['nodes'][0]['blocks'][0]['images'][0]
            self.assertEqual(picture, {'alt':'right', 'source':'photo (1).png'})
            html=render_document(doc,root)['nodes'][0]['html']
            self.assertIn('alt="right"',html)
            self.assertNotIn('media-split',html)

    def test_fence_rules(self):
        self.assertIsNotNone(fence_open('   ~~~python'))
        self.assertIsNone(fence_open('    ```'))
        self.assertIsNone(fence_open('```a`b'))
        self.assertTrue(fence_close('  `````  ', '```'))
        for line in ('~~','~~~','```python','    ```'):
            self.assertFalse(fence_close(line,'```'))

    def test_importers_keep_fenced_directives_literal(self):
        source='# T\n~~~~\n```\n---\n@[section]\n~~~~\n'
        text,_=convert_mono(source)
        self.assertEqual(text,source)
        self.assertEqual(len(split_slides(source)),1)
        self.assertEqual(parse_document(source)['nodes'][0]['blocks'][0]['text'],'```\n---\n@[section]\n')
