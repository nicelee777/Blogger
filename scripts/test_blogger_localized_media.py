"""Checks for authorized image overrides and preservation of ordinary links."""
import json
import tempfile
import unittest
from pathlib import Path

from blogger_localized_media import apply_localized_media
from blogger_translate import assert_structure


class LocalizedMediaTests(unittest.TestCase):
    def test_overrides_are_scoped_idempotent_and_structure_checked(self):
        source = '<a href="https://example.com/original"><img src="https://example.com/image" alt="" data-original-width="100" data-original-height="50" /></a><a href="https://example.com/guide">Guide</a>'
        manifest = {"version": 1, "images": [{"source": {"src": "https://example.com/image", "href": "https://example.com/original"}, "locales": {"ja": {"src": "https://example.com/ja.png", "href": "https://example.com/ja.png", "width": 200, "height": 100, "alt": "勤務表"}}}]}
        with tempfile.TemporaryDirectory() as directory:
            item = Path(directory)
            (item / 'media.json').write_text(json.dumps(manifest))
            localized = apply_localized_media(item, source, 'ja')
            self.assertIn('alt="勤務表"', localized)
            self.assertIn('https://example.com/guide', localized)
            self.assertEqual(localized, apply_localized_media(item, localized, 'ja'))
            self.assertEqual(source, apply_localized_media(item, source, 'en'))
            assert_structure(localized, localized)
            with self.assertRaises(ValueError):
                assert_structure(localized, localized.replace('https://example.com/guide', 'https://example.com/changed'))
            manifest['images'][0]['locales']['ja']['src'] = 'http://example.com/ja.png'
            (item / 'media.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                apply_localized_media(item, source, 'ja')


if __name__ == '__main__':
    unittest.main()
