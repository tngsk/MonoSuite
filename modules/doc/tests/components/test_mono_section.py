import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
import importlib.util

class TestMonoSectionParser(unittest.TestCase):
    def setUp(self):
        parser_path = os.path.join(
            os.path.dirname(__file__),
            "../../src/components/mono-section/parser.py"
        )
        spec = importlib.util.spec_from_file_location("mono_section_parser", parser_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.parser = module.Parser()

    def test_basic_parsing(self):
        markdown = "::: section [My Section] (bg-color: red, height: 300px)\nContent\n:::"
        html = self.parser.process(markdown)

        self.assertIn('<mono-section markdown="1" bg-color="red" height="300px">', html)
        self.assertIn("<h2>My Section</h2>", html)
        self.assertIn("Content", html)
        self.assertIn("</mono-section>", html)

    def test_no_title(self):
        markdown = "::: section (bg-color: blue)\nContent\n:::"
        html = self.parser.process(markdown)

        self.assertIn('<mono-section markdown="1" bg-color="blue">', html)
        self.assertNotIn("<h2>", html)
        self.assertIn("Content", html)
        self.assertIn("</mono-section>", html)

    def test_all_attributes(self):
        markdown = "::: section [Full] (image: img.png, mode: contain, bg-color: #000, text-color: #fff, height: 50vh)\nContent\n:::"
        html = self.parser.process(markdown)

        self.assertIn('<mono-section markdown="1" image="img.png" mode="contain" bg-color="#000" text-color="#fff" height="50vh">', html)
        self.assertIn("<h2>Full</h2>", html)
        self.assertIn("Content", html)
        self.assertIn("</mono-section>", html)

    def test_width_attribute(self):
        markdown = "::: section [Fit Width] (width: fit, bg-color: yellow)\nContent\n:::"
        html = self.parser.process(markdown)

        self.assertIn('<mono-section markdown="1" bg-color="yellow" width="fit">', html)
        self.assertIn("<h2>Fit Width</h2>", html)
        self.assertIn("Content", html)
        self.assertIn("</mono-section>", html)

    def test_mono_section_no_options(self):
        markdown = "::: section\nContent\n:::"
        html = self.parser.process(markdown)
        self.assertIn('<mono-section markdown="1">', html)
        self.assertIn("Content", html)

if __name__ == '__main__':
    unittest.main()
