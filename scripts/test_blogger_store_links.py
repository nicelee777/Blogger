"""Regression checks for the URLs rendered during Blogger publication."""
import json
import unittest
from pathlib import Path
from blogger_store_links import localize_store_links

class StoreLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path('blogger/config.json').read_text(encoding='utf-8'))

    def test_each_managed_locale_uses_configured_storefront_and_language(self):
        source = '<a href="https://apps.apple.com/app/id6474254415">Apple</a><a href="https://play.google.com/store/apps/details?id=juho.interrobang.yjdiary2">Play</a>'
        for locale, targets in self.config['store_links'].items():
            with self.subTest(locale=locale):
                actual = localize_store_links(source, locale, self.config)
                self.assertIn(targets['app_store_url'], actual)
                self.assertIn(targets['google_play_url'].replace('&', '&amp;'), actual)

    def test_quote_styles_case_and_spacing_do_not_block_rewrite(self):
        source = "<A class='button' HREF = 'https://apps.apple.com/us/app/id6474254415?l=en-US'>Get</A>"
        actual = localize_store_links(source, 'ja', self.config)
        self.assertIn("HREF = 'https://apps.apple.com/jp/app/id6474254415'", actual)
        self.assertIn("class='button'", actual)

    def test_unrelated_links_and_text_remain_unchanged(self):
        source = '<p>https://apps.apple.com/app/id6474254415</p><a href="https://example.com/guide?x=1&amp;y=2">Guide</a><a href="https://play.google.com/store/apps/details?id=another.app">Other</a>'
        self.assertEqual(localize_store_links(source, 'ko', self.config), source)

    def test_repeated_publication_is_idempotent(self):
        source = '<a href="https://play.google.com/store/apps/details?id=juho.interrobang.yjdiary2&amp;hl=en">Play</a>'
        first = localize_store_links(source, 'fr', self.config)
        self.assertEqual(localize_store_links(first, 'fr', self.config), first)

if __name__ == '__main__':
    unittest.main()
