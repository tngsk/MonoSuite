import base64
import json
import re
import tempfile
import unittest
from pathlib import Path
from mono_space.build import parse, build

class ParserTests(unittest.TestCase):
    def test_hierarchy_and_route(self):
        d = parse('# Root {#root}\n## Child {#child}\n::tone ai\n::connect child -> root | back\n::route child root')
        self.assertEqual(d['nodes'][1]['parent'], 'root')
        self.assertEqual(d['route'], ['child', 'root'])
        self.assertEqual(d['edges'][0]['label'], 'back')

    def test_invalid_inputs(self):
        for source in ('', '# A {#a}\n# B {#a}', '# A\n::route missing', '# A\n::connect n1 -> missing', '# A\n::layout compare', '# A\n::tone bad'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse(source)

    def test_focus_scopes(self):
        d = parse('# Root\n::focus subtree\n## Picture\n::focus image')
        self.assertEqual([n['focus'] for n in d['nodes']], ['subtree', 'image'])
        with self.assertRaises(ValueError):
            parse('# Root\n::focus unknown')

    def test_image_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'a.png').write_bytes(b'same bytes')
            (root / 'b.png').write_bytes(b'same bytes')
            d = parse('# Images\n![a](a.png)\n![b](b.png)', root)
            self.assertEqual(len(d['assets']), 1)
            self.assertEqual(d['nodes'][0]['html'].count('data-asset='), 2)
            with self.assertRaises(OSError):
                parse('# Missing\n![missing](missing.png)', root)

    def test_marker(self):
        d = parse('# Title\n## Chapter\n### Emphasis\n::marker on\n### Plain\n::marker off')
        self.assertEqual([n['marker'] for n in d['nodes']], ['auto', 'auto', 'on', 'off'])
        with self.assertRaises(ValueError):
            parse('# Title\n::marker yellow')

    def test_compare_counts(self):
        for count in (2, 3):
            data = parse('# Root\n## Comparison\n::layout compare\n' + '\n'.join('### Item '+str(i) for i in range(count)))
            self.assertEqual(len(data['nodes']), count+2)
        for count in (1, 4):
            with self.assertRaises(ValueError):
                parse('# Root\n## Comparison\n::layout compare\n' + '\n'.join('### Item '+str(i) for i in range(count)))

    def test_semantic_tones_and_legacy(self):
        for tone in ('neutral', 'primary', 'secondary', 'accent', 'info', 'success', 'warning', 'error'):
            n = parse('# Title\n::tone '+tone)['nodes'][0]
            self.assertEqual(n['tone'], tone)
            self.assertEqual(n['style'], 'plain')
        for old, new in (('normal','neutral'), ('ai','primary'), ('note','warning')):
            n = parse('# Title\n::tone '+old)['nodes'][0]
            self.assertEqual(n['tone'], new)
            self.assertEqual(n['style'], 'note' if old=='note' else 'plain')
        n = parse('# Note\n::tone info\n::style note')['nodes'][0]
        self.assertEqual((n['tone'],n['style']), ('info','note'))

    def test_text_is_escaped(self):
        d = parse('# <script> {#safe}\n<script>alert(1)</script> **hello**')
        self.assertNotIn('<script>', d['nodes'][0]['html'])
        self.assertIn('<strong>hello</strong>', d['nodes'][0]['html'])

    def test_self_contained_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'pixel.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6ioAAAAASUVORK5CYII='))
            source = root / 'demo.md'
            source.write_text('# </script> {#root}\n![test](pixel.png)')
            out = root / 'out.html'
            build(source, out)
            result = out.read_text()
            payload = re.search(r'<script id="data" type="application/json">(.*?)</script>', result, re.S)[1]
            self.assertEqual(json.loads(payload)['nodes'][0]['title'], '</script>')
            self.assertIn('data:image/png;base64,', result)
            self.assertNotIn('__SPATIAL_DATA__', result)

if __name__ == '__main__':
    unittest.main()
