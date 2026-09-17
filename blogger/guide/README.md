# ShiftMate Guide Page

`guide` is a long-lived Blogger **Page**, not a Post.

## Source of truth

Edit only the Korean body source:

```text
blogger/guide/ko.html
```

When the Korean source exists, GitHub Actions translates it to:

```text
blogger/guide/en.html
blogger/guide/ja.html
blogger/guide/zh-cn.html
blogger/guide/zh-tw.html
blogger/guide/es.html
blogger/guide/vi.html
```

The publish workflow updates the existing Blogger Guide Pages by URL path. It does not create new Guide posts.

## Guide-specific localization

The Guide contains its own in-page search and media controls. Translation therefore localizes not only visible text but also these values:

- `placeholder`
- `aria-label`
- `alt`
- `title`
- `data-search`
- `data-title`

IDs, classes, `data-video-id`, media URLs, CSS, section order, and structural HTML remain fixed.

Links from the Guide to FAQ are rewritten deterministically to the matching locale. For example, the English Guide links to `/p/faq.html`, Japanese to `/p/faq-ja.html`, and Korean to `/p/faq-ko.html`.

## Search descriptions

Localized Guide search-description copy is tracked in:

```text
blogger/guide/search-descriptions.json
```

Validate or print the values with:

```bash
python scripts/blogger_validate_page_metadata.py guide --show
```

Important: Blogger API v3 Page resources expose `title` and `content`, but do not expose the Blogger editor's **Search description** field. Therefore the HTML body can be deployed automatically, while the Search description must be entered in Blogger's Page editor using the Git-managed values above. Do not insert a `<meta name="description">` tag into the Page body as a substitute.

When a Guide search description changes, update the locale values in `search-descriptions.json` at the same time as the content change.

## Stable sections

Use stable section IDs because the app and blog can deep-link directly to a section such as:

```text
/p/guide-ko.html#guide-widget
```

Images and YouTube embeds may be included in the HTML. URLs, IDs, CSS, media source URLs, and element order are preserved during translation; visible text, accessibility text, and in-page search terms are localized.

Until `blogger/guide/ko.html` is added, Guide synchronization is intentionally skipped so the existing Blogger Guide Pages cannot be overwritten accidentally.
