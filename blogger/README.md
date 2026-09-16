# ShiftMate Blogger automation

GitHub is the source of truth for ShiftMate Blogger content. Blogger is the publishing target.

## Content model

ShiftMate Blogger uses two content models:

```text
FAQ     -> Blogger Page (same page is updated repeatedly)
Guide   -> Blogger Page (same page is updated repeatedly)
Notice  -> Blogger Post (new item per notice)
Story   -> Blogger Post (new item per story)
```

This keeps long-lived help content stable while allowing news/editorial content to accumulate as individual posts.

## Branch policy

- `develop`: edit, validate, translate, and verify Blogger mappings
- `main`: publish reviewed content to Blogger
- `Blogger - Verify` on `develop` is read-only and never writes to Blogger
- pull-request validation never publishes

## Managed Pages: FAQ and Guide

Korean is the source of truth.

FAQ:

```text
blogger/faq/ko.html
```

Guide:

```text
blogger/guide/ko.html
```

Other locale files are generated from the Korean source.

### FAQ Page paths

- EN `/p/faq.html`
- KO `/p/faq-ko.html`
- JA `/p/faq-ja.html`
- ZH-CN `/p/faq-cn.html`
- ZH-TW `/p/faq-tw.html`
- ES `/p/faq-es.html`
- VI `/p/faq-vi.html`

### Guide Page paths

- EN `/p/guide.html`
- KO `/p/guide-ko.html`
- JA `/p/guide-ja.html`
- ZH-CN `/p/guide-cn.html`
- ZH-TW `/p/guide-tw.html`
- ES `/p/guide-es.html`
- VI `/p/guide-vi.html`

Page targets are resolved by URL path instead of hard-coded Blogger Page IDs.

Guide publishing is intentionally disabled until `blogger/guide/ko.html` exists. This prevents the existing live Guide Pages from being overwritten before their GitHub source has been prepared.

`blogger/glossary.json` stores app UI terminology that must remain consistent across localized content.

## Managed Posts: Notice and Story

Managed Posts live under:

```text
blogger/posts/notice/<slug>/
blogger/posts/story/<slug>/
```

Each item contains `meta.json`, Korean `ko.html`, generated locale HTML files, and generated `titles.json`.

The automation adds a hidden stable marker to each managed Post so re-running updates the same localized Post instead of creating duplicates. Existing managed Posts are discovered across live, draft, and scheduled states.

See `blogger/posts/README.md` for the item format.

## Translation behavior

`Blogger - Translate` runs on `develop` when Korean source content changes.

- FAQ -> translated as an FAQ Page
- Guide -> translated as a long-form Guide Page
- Notice/Story -> translated as Posts
- IDs, CSS, URLs, media source URLs, element order, and protected attributes remain unchanged
- visible text, image alt text, iframe/video titles, and accessibility labels are localized

## Validation

FAQ validation checks stable IDs, internal links, CSS, language markers, and FAQ structure.

Guide validation checks duplicate IDs, internal links, aria references, CSS consistency, media URL/order consistency, and locale root language markers.

Run locally:

```bash
python scripts/blogger_validate.py blogger/faq/*.html

# after Guide source/locales exist
python scripts/blogger_validate_guide.py blogger/guide/*.html
```

## Read-only Blogger verification

`Blogger - Verify` runs on `develop` and performs:

```text
repository validation
-> Blogger target discovery
-> managed Page dry-run
-> managed Post dry-run
```

It never writes to Blogger.

Local equivalent:

```bash
python scripts/blogger_sync.py discover
python scripts/blogger_sync.py pages --dry-run
python scripts/blogger_sync.py posts --dry-run
```

## Publishing

`Blogger - Publish` on `main` updates managed Pages and creates/updates managed Posts.

Before a manual production publish, use:

```text
dry_run = true
```

Then use `dry_run = false` only after mappings are correct.

## Required GitHub Actions secrets

Repository -> **Settings -> Secrets and variables -> Actions**

- `OPENAI_API_KEY`
- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

Never commit these values.

## Normal workflow

FAQ or Guide:

1. Edit the Korean source on `develop`.
2. Push to `develop`.
3. GitHub Actions translates the other six locales.
4. Validation and read-only Blogger verification run.
5. Review generated files.
6. Merge to `main`.
7. The existing seven Blogger Pages are updated.

Notice or Story:

1. Create a new item folder with `meta.json` + `ko.html`.
2. Push to `develop`.
3. GitHub Actions translates title/body to the six other locales.
4. Review generated content.
5. Set the desired `publish` state in `meta.json`.
6. Merge to `main`.
7. Blogger creates or updates the seven localized Posts with category/language labels.
