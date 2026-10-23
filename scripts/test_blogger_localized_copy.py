import json
import tempfile
import unittest
from pathlib import Path

from blogger_localized_copy import apply_localized_copy


class LocalizedCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.item = Path(self.tmp.name)
        (self.item / 'ko.html').write_text('<p>한국어 브랜드 안내</p><p>나머지</p>')
        (self.item / 'copy.json').write_text(json.dumps({'version': 1, 'blocks': [
            {'tag': 'p', 'index': 0, 'source_text': '한국어 브랜드 안내',
             'locales': {'en': 'Start with ShiftMate & iPhone Duo'}}]}))

    def test_only_reviewed_locale_block_changes_and_markup_is_preserved(self):
        body = '<p>Old brand claim</p><p>Keep this</p>'
        self.assertEqual(apply_localized_copy(self.item, body, 'en'),
                         '<p>Start with ShiftMate &amp; iPhone Duo</p><p>Keep this</p>')

    def test_korean_is_unchanged(self):
        body = (self.item / 'ko.html').read_text()
        self.assertEqual(apply_localized_copy(self.item, body, 'ko'), body)

    def test_source_drift_fails_instead_of_replacing_wrong_paragraph(self):
        (self.item / 'ko.html').write_text('<p>다른 내용</p>')
        with self.assertRaisesRegex(ValueError, 'Korean copy changed'):
            apply_localized_copy(self.item, '<p>Translated text</p>', 'en')

    def test_nested_markup_cannot_be_removed(self):
        with self.assertRaisesRegex(ValueError, 'text-only'):
            apply_localized_copy(self.item, '<p><a href="https://example.com">Link</a></p>', 'en')


if __name__ == '__main__':
    unittest.main()
