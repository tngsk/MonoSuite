import json
import tempfile
import unittest
from pathlib import Path
from mono_space.deckset_import import import_document, split_slides
from mono_space.build import build


class DecksetTests(unittest.TestCase):
    def test_delimiters_do_not_split_code(self):
        text = '# A\n\n    ---\n\n```md\n---\n```\n\n---\n# B'
        self.assertEqual(len(split_slides(text)), 2)

    def test_import_assets_notes_and_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root/'slides.md'
            (root/'photo.png').write_bytes(b'png')
            text = 'footer: Example\n# Title\n### Subtitle\n\n---\n# Topic\nA paragraph\ncontinued\n\n![right](photo.png)\n^ Secret notes\n\n---\n![autoplay](water.mov)\n'
            source.write_text(text)
            output = root/'result'/'presentation.html'
            md = import_document(source, output)
            data = build(md, output, offline=True)
            self.assertEqual(len(data['nodes']), 3)
            self.assertNotIn('document_mode', data)
            self.assertIn('media-split right', data['nodes'][1]['html'])
            self.assertIn('A paragraph\ncontinued', data['nodes'][1]['html'])
            self.assertNotIn('Secret notes', output.read_text())
            report = json.loads(output.with_suffix('.conversion.json').read_text())
            self.assertEqual(report['slides'], 3)
            self.assertEqual(report['images'], 1)
            self.assertEqual(report['notes'][0]['text'], 'Secret notes')
            self.assertEqual(source.read_text(), text)
            self.assertIn('water.mov', str(report['changes']))
            with self.assertRaises(ValueError):
                import_document(source, source)

    def test_missing_and_outside_images_report_errors(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'in.md'
            for reference in ('../secret.png','https://example.com/a.png'):
                source.write_text('# T\n![]('+reference+')')
                with self.assertRaises(ValueError):
                    import_document(source, root/'out.html')
