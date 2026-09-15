# Managed Blogger posts

Use this directory for `notice`, `story`, and `guide` content.

Each content item has one Korean source and generated localized files:

```text
blogger/posts/
  notice/
    2026-09-example/
      meta.json
      ko.html
      titles.json        # generated
      en.html            # generated
      ja.html            # generated
      zh-cn.html         # generated
      zh-tw.html         # generated
      es.html            # generated
      vi.html             # generated
```

`meta.json` example:

```json
{
  "category": "notice",
  "slug": "2026-09-example",
  "title_ko": "ShiftMate 업데이트 안내",
  "publish": false,
  "labels": []
}
```

Rules:

- `category`: `notice`, `story`, or `guide`.
- `title_ko`: Korean source title.
- `publish: false` keeps the managed Blogger post as a draft; `publish: true` makes it live.
- Changing `publish` later updates the existing managed post state (draft ↔ live) rather than creating another post.
- English uses the Blogger language label `lang`; Korean uses `lang-ko`; the other locales use their locale labels from `blogger/config.json`.
- The sync adds a hidden stable marker such as `<!--shiftmate-content-id:notice/2026-09-example/en-->`. Re-running the workflow finds the same post across live/draft/scheduled states and updates it instead of creating duplicates.
- App UI terminology shared with FAQ translation is managed in `blogger/glossary.json`.

Translate locally:

```bash
OPENAI_API_KEY='...' python scripts/blogger_translate_posts.py
```

Dry-run Blogger matching/creation:

```bash
python scripts/blogger_sync.py posts --dry-run
```
