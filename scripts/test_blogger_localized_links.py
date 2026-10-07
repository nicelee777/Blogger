"""Regression checks for same-language Post links and protected URLs."""
import json
import tempfile
import unittest
from pathlib import Path

from blogger_localized_links import apply_localized_post_links
from blogger_translate import assert_structure


class LocalizedPostLinkTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.registry = Path(self.directory.name) / "post-links.json"
        self.urls = {"ko": "https://blog.example/2026/10/source.html", "en": "https://blog.example/2026/10/english.html", "ja": "https://blog.example/2026/10/japanese.html"}
        self.data = {"version": 1, "blog_url": "https://blog.example/", "posts": {"story/source": self.urls}}
        self.save()

    def save(self):
        self.registry.write_text(json.dumps(self.data), encoding="utf-8")

    def test_same_language_from_any_alias_and_idempotence(self):
        source = '<a href="' + self.urls["ko"] + '">Read</a><a href="' + self.urls["en"] + '">More</a>'
        result = apply_localized_post_links(source, "ja", self.registry)
        self.assertEqual(result.count(self.urls["ja"]), 2)
        self.assertEqual(result, apply_localized_post_links(result, "ja", self.registry))
        korean = '<a href="' + self.urls["ko"] + '">한국어</a>'
        self.assertEqual(korean, apply_localized_post_links(korean, "ko", self.registry))

    def test_query_fragment_and_single_quote_attributes(self):
        source = "<A title='Read > next href=\"" + self.urls["ko"] + "\"' data-href='keep' href='" + self.urls["ko"] + "?m=1&amp;x=2#details' target='_blank'>Read</A>"
        expected = source.replace(" href='" + self.urls["ko"], " href='" + self.urls["en"])
        self.assertEqual(expected, apply_localized_post_links(source, "en", self.registry))

    def test_unrelated_urls_images_and_attributes_remain_protected(self):
        source = '<a href="' + self.urls["ko"] + '" class="related">Read</a><a href="https://store.example/app">Store</a><a href="https://images.example/banner.png"><img src="' + self.urls["ko"] + '" alt="Image" /></a>'
        expected = source.replace('href="' + self.urls["ko"] + '"', 'href="' + self.urls["en"] + '"')
        result = apply_localized_post_links(source, "en", self.registry)
        self.assertEqual(expected, result)
        assert_structure(expected, result)
        with self.assertRaises(ValueError):
            assert_structure(expected, result.replace("https://store.example/app", "https://store.example/other"))

    def test_missing_locale_and_invalid_registry_fail(self):
        source = '<a href="' + self.urls["ko"] + '">Read</a>'
        with self.assertRaisesRegex(ValueError, "Missing fr target"):
            apply_localized_post_links(source, "fr", self.registry)
        self.data["posts"]["story/source"]["en"] = "https://another.example/post.html"
        self.save()
        with self.assertRaisesRegex(ValueError, "Invalid canonical"):
            apply_localized_post_links(source, "en", self.registry)

    def test_ambiguous_targets_fail_before_rewriting(self):
        self.data["posts"]["story/other"] = dict(self.urls)
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate registered"):
            apply_localized_post_links("<p>Text</p>", "en", self.registry)


if __name__ == "__main__":
    unittest.main()
