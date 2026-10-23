import json
import tempfile
import unittest
from pathlib import Path
from blogger_publish_scope import resolve_scope, stage_items


class PublicationScopeTests(unittest.TestCase):
    def test_article_with_helpers_and_config_never_selects_pages_or_other_posts(self):
        result = resolve_scope(['blogger/posts/story/duo/meta.json',
                                'scripts/blogger_validate_post.py',
                                '.github/workflows/blogger-publish.yml',
                                'blogger/config.json'])
        self.assertEqual(result, {'full': False, 'pages': False, 'items': ['story/duo']})

    def test_manual_item_is_scoped_and_rejects_traversal(self):
        self.assertEqual(resolve_scope([], manual=True, requested_item='story/duo')['items'], ['story/duo'])
        with self.assertRaises(ValueError):
            resolve_scope([], manual=True, requested_item='story/../faq')

    def test_assets_only_do_not_publish(self):
        self.assertEqual(resolve_scope(['blogger/assets/duo/en.png']),
                         {'full': False, 'pages': False, 'items': []})

    def test_explicit_manual_full_sync_is_preserved(self):
        self.assertTrue(resolve_scope([], manual=True)['full'])

    def test_missing_item_fails_instead_of_zero_target_success(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'does not exist'):
                stage_items(Path(d), ['story/duo'])

    def test_staging_copies_only_selected_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ['duo', 'unrelated']:
                p = root / 'story' / name
                p.mkdir(parents=True)
                (p/'meta.json').write_text(json.dumps({'category':'story','slug':name}))
            target = stage_items(root, ['story/duo'])
            self.addCleanup(__import__('shutil').rmtree, target)
            self.assertEqual([p.parent.name for p in target.glob('*/*/meta.json')], ['duo'])


if __name__ == '__main__':
    unittest.main()
