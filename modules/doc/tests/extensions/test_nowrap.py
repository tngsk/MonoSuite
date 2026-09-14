import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import unittest
import markdown

from src.extensions.nowrap import NowrapExtension

class TestNowrapExtension(unittest.TestCase):
    def setUp(self):
        self.md = markdown.Markdown(extensions=[NowrapExtension()])

    def test_nowrap_conversion(self):
        text = "This is {{custom syntax}} text."
        html = self.md.convert(text)
        expected = '<p>This is <span class="nowrap">custom syntax</span> text.</p>'
        self.assertEqual(html, expected)

    def test_multiple_nowraps(self):
        text = "Test {{first}} and {{second}}."
        html = self.md.convert(text)
        expected = '<p>Test <span class="nowrap">first</span> and <span class="nowrap">second</span>.</p>'
        self.assertEqual(html, expected)
