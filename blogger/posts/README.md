# Managed Blogger Posts

Use this directory only for **Notice** and **Story** content.

`FAQ` and `Guide` are long-lived Blogger Pages and are managed separately under `blogger/faq/` and `blogger/guide/`.

Each Post item has one Korean source and generated localized files:

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
      vi.html            # generated
```

`story` uses the same structure under `blogger/posts/story/<slug>/`.

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

- `category`: `notice` or `story` only.
- `title_ko`: Korean source title.
- `publish: false` keeps the managed Blogger Post as a draft.
- `publish: true` makes the managed Blogger Post live.
- Changing `publish` updates the existing managed Post state instead of creating a duplicate.
- English uses language label `lang`; Korean uses `lang-ko`; other locales use the labels in `blogger/config.json`.
- The sync adds a hidden stable marker such as `<!--shiftmate-content-id:notice/2026-09-example/en-->` so repeated publishing updates the same localized Post.
- Images and YouTube embeds may be included directly in the HTML. URLs and media source attributes are preserved during translation.

Translate locally:

```bash
OPENAI_API_KEY='...' python scripts/blogger_translate_posts.py
```

Dry-run Blogger matching/creation:

```bash
python scripts/blogger_sync.py posts --dry-run
```
