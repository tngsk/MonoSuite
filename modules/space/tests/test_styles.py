import re
import unittest
import tempfile
from pathlib import Path
from mono_space.build import build, validate_styles


class StylesTests(unittest.TestCase):
    def test_styles_are_styles_not_application_code(self):
        root=Path(__file__).resolve().parent.parent
        css=(root/'src/mono_space/web/styles.css').read_text()
        validate_styles(css)
        for selector in ('.markdown-list', '.list-number', '.live-sticky', '.math-copy', '.math-block', '.image-gallery', '.markdown-table', '.codeblock'):
            self.assertIn(selector,css)
        # This is the exact regression: app.js was written into styles.css.
        with self.assertRaises(ValueError):
            validate_styles((root/'src/mono_space/web/app.js').read_text())
        with self.assertRaises(ValueError):
            validate_styles('')

    def test_generated_styles_match_the_source(self):
        root=Path(__file__).resolve().parent.parent
        css=(root/'src/mono_space/web/styles.css').read_text().strip()
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory)/'presentation.html'
            build(root/'examples/standard/document.md', page, offline=True)
            with self.subTest(page='fresh standard build'):
                style=re.search(r'<style>(.*?)</style>',page.read_text(),re.S)[1].strip()
                self.assertEqual(style,css)
                validate_styles(style)
