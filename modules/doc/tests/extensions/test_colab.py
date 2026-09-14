import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
import markdown

from src.extensions.colab import ColabExtension

class TestColabExtension(unittest.TestCase):
    def setUp(self):
        self.md = markdown.Markdown(extensions=[ColabExtension()])

    def test_github_colab_link_conversion(self):
        text = "[Open Note](https://github.com/user/repo/blob/main/test.ipynb)"
        html = self.md.convert(text)
        self.assertIn("https://colab.research.google.com/github/user/repo/blob/main/test.ipynb", html)
        self.assertIn('class="colab-link"', html)
        self.assertIn("colab-badge.svg", html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_other_colab_link_conversion(self):
        text = "[Open Note](https://example.com/test.ipynb)"
        html = self.md.convert(text)
        self.assertIn("https://example.com/test.ipynb", html)
        self.assertIn('class="colab-link"', html)
        self.assertIn("colab-badge.svg", html)

    def test_non_ipynb_link_not_converted(self):
        text = "[Google](https://google.com)"
        html = self.md.convert(text)
        self.assertNotIn('colab-link', html)
        self.assertNotIn('colab-badge.svg', html)
        self.assertEqual(html, '<p><a href="https://google.com">Google</a></p>')
