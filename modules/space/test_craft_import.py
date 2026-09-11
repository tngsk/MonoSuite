import json
import tempfile
import unittest
from pathlib import Path
from craft_import import import_bundle
from markdown_parser import parse_document

class CraftTests(unittest.TestCase):
    def test_assets_and_hierarchy_and_literal_code(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);bundle=root/'input.textbundle';bundle.mkdir();(bundle/'assets').mkdir()
            (bundle/'info.json').write_text(json.dumps({'type':'net.daringfireball.markdown','version':2}))
            (bundle/'assets'/'日本 (2).png').write_bytes(b'image')
            source='# Title\n## First\n![image](assets/%E6%97%A5%E6%9C%AC%20(2).png)\n# Second\n### Child\n    - Nested\n> Quote\n```\n# Literal\n![literal](x)\n```\n'
            (bundle/'text.markdown').write_text(source)
            out=root/'out'/'presentation.html';md=import_bundle(bundle,out)
            nodes=parse_document(md.read_text())['nodes']
            self.assertEqual([n['level'] for n in nodes],[1,2,2,3])
            self.assertIn('    - Nested',md.read_text())
            self.assertIn('> Quote',md.read_text())
            self.assertIn('# Literal\n![literal](x)',md.read_text())
            self.assertEqual(len(list((out.parent/'presentation.assets').iterdir())),1)
            self.assertEqual((bundle/'text.markdown').read_text(),source)
            with self.assertRaises(ValueError):import_bundle(bundle,bundle/'output.html')
    def test_image_cannot_escape_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);bundle=root/'input';bundle.mkdir()
            (bundle/'info.json').write_text('{"type":"net.daringfireball.markdown"}')
            (bundle/'text.markdown').write_text('# T\n![x](../secret.png)')
            with self.assertRaises(ValueError):import_bundle(bundle,root/'out.html')
