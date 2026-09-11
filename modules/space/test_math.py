import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from build import parse, build
from markdown_parser import parse_document


class MathTests(unittest.TestCase):
    def test_inline_display_cache_and_copy_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source='# Math\n周期は $T=1/f$。再び $T=1/f$。\n\n$$\nx(t)=A\\sin(2\\pi f t+\\phi)\n$$'
            result=parse(source,root)['nodes'][0]['html']
            self.assertEqual(result.count('<svg'),3)
            self.assertEqual(result.count('class="math-block"'),1)
            self.assertIn('data-tex="T=1/f"',result)
            self.assertIn('vertical-align:',result)
            self.assertNotIn('<script',result)
            self.assertEqual(len(list((root/'.spatial-cache/math').glob('*.json'))),2)
            with patch('math_render.subprocess.run', side_effect=AssertionError('Cache missed')):
                self.assertEqual(parse(source,root)['nodes'][0]['html'],result)

    def test_code_and_escaped_currency_do_not_typeset(self):
        with tempfile.TemporaryDirectory() as folder, patch('math_render.subprocess.run', side_effect=AssertionError('Unexpected rendering')):
            root=Path(folder)
            source='# Code\n`$x$` and \\$5\n\n```sh\n$$\n$HOME\n$$\n```'
            result=parse(source,root)['nodes'][0]['html']
            self.assertNotIn('<svg',result)
            self.assertIn('<code>$x$</code>',result)
            self.assertIn('$HOME',result)
            self.assertFalse((root/'.spatial-cache').exists())

    def test_error_includes_source_and_line(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,r'3行:.*notacommand'):
                parse('# T\n\n$\\notacommand{x}$',Path(folder))
        with self.assertRaisesRegex(ValueError,'2行:.*閉じ'):
            parse_document('# T\n$$\nx+1')

    def test_broken_math_does_not_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'in.md';output=root/'out.html'
            output.write_text('previous')
            source.write_text('# T\n$$\\frac{1}{$$')
            with self.assertRaises(ValueError):build(source,output,offline=True)
            self.assertEqual(output.read_text(),'previous')

    def test_embedded_svg_has_no_external_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'in.md';output=root/'out.html'
            source.write_text('# T\n$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$')
            data=build(source,output,offline=True)
            markup=data['nodes'][0]['html']
            self.assertIn('<path',markup)
            self.assertNotRegex(markup,r'(?:href|src)="https?://')
            self.assertNotIn('mathjax-full',output.read_text())
            self.assertEqual(data['assets'],{})

    def test_display_contents_do_not_become_headings(self):
        blocks=parse_document('# T\n$$\n# literal\n::layout row\n$$')['nodes'][0]['blocks']
        self.assertEqual(len(blocks),1)
        self.assertEqual(blocks[0]['kind'],'math')

    def test_error_line_ignores_code_example(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, '4行:'):
                parse('# T\n`$\\notacommand{x}$`\n\n$\\notacommand{x}$',Path(folder))
            with self.assertRaisesRegex(ValueError, '2行:'):
                parse('# T\n$$$$',Path(folder))
