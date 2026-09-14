import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mono_space.build import parse
from mono_space.links import Previews

class LinkTests(unittest.TestCase):
    def test_text_link_and_unsafe_scheme(self):
        result=parse('# Title\n[hello](https://example.com/?a=1&b=2)')['nodes'][0]['html']
        self.assertIn('target="_blank"',result)
        self.assertIn('&amp;',result)
        with self.assertRaises(ValueError):parse('# Title\n[x](javascript:alert)')

    def test_cards_and_overrides(self):
        d=parse('# Title\n::link https://example.com square\n::link-title <Sample>\n::link-description Description')
        self.assertIn('rich-link square',d['nodes'][0]['html'])
        self.assertIn('&lt;Sample&gt;',d['nodes'][0]['html'])
        with self.assertRaises(ValueError):parse('# Title\n::link-title orphan')

    def test_fetch_cache_refresh_failure_and_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            page=b'<title>Fallback</title><meta property="og:title" content="OG title"><meta property="og:image" content="/image.png">'
            def fetch(url,limit):
                if url.endswith('.png'):return b'image', 'image/png', 'utf-8',url
                return page,'text/html','utf-8',url
            with patch('mono_space.links.download',side_effect=fetch) as mock:
                first=Previews(folder).get('https://example.com')
                self.assertEqual(first['title'],'OG title')
                self.assertIn('base64',first['image'])
                self.assertEqual(mock.call_count,2)
                Previews(folder).get('https://example.com')
                self.assertEqual(mock.call_count,2)
                Previews(folder,refresh=True).get('https://example.com')
                self.assertEqual(mock.call_count,4)
            with patch('mono_space.links.download',side_effect=OSError('offline')):
                self.assertEqual(Previews(folder,refresh=True).get('https://example.com'),first)
                self.assertEqual(Previews(folder).get('https://missing.example'),{})
            with patch('mono_space.links.download') as mock:
                self.assertEqual(Previews(folder,offline=True).get('https://new.example'),{})
                mock.assert_not_called()

if __name__=='__main__':unittest.main()
