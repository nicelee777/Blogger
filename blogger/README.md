# ShiftMate Blogger automation

GitHub is the source of truth for ShiftMate Blogger content. Blogger is the publishing target.

## Branch policy

- `develop`: edit, validate, translate, review
- `main`: publish reviewed content to Blogger
- pull requests touching Blogger content/scripts run validation only and never publish

## FAQ

Korean is the source of truth:

```text
blogger/faq/ko.html
```

Generated locales:

```text
blogger/faq/en.html
blogger/faq/ja.html
blogger/faq/zh-cn.html
blogger/faq/zh-tw.html
blogger/faq/es.html
blogger/faq/vi.html
```

Existing Blogger FAQ pages are resolved by URL path, not by hard-coded page IDs:

- EN `/p/faq.html`
- KO `/p/faq-ko.html`
- JA `/p/faq-ja.html`
- ZH-CN `/p/faq-cn.html`
- ZH-TW `/p/faq-tw.html`
- ES `/p/faq-es.html`
- VI `/p/faq-vi.html`

`blogger/glossary.json` stores app UI terms that must remain consistent with the localized ShiftMate UI. When this glossary changes on `develop`, the translation workflow runs again.

The FAQ validator checks each localized file independently and also compares stable IDs, ID order, and CSS against the Korean source.

## Notice / Story / Guide

Managed post content lives under `blogger/posts/<category>/<slug>/`.
See `blogger/posts/README.md` for the format.

The automation adds a hidden stable marker to each managed Blogger post. This makes publishing idempotent: re-running updates the same localized post instead of creating duplicates.

Managed posts are discovered across Blogger `live`, `draft`, and `scheduled` states. Changing `publish` in `meta.json` reconciles an existing post to the desired live/draft state instead of creating another copy.

## Required GitHub Actions secrets

Repository → **Settings → Secrets and variables → Actions**

- `OPENAI_API_KEY`
- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

Never commit these values.

The translation model defaults to `gpt-5.6-luna`. It can be overridden locally using `OPENAI_TRANSLATION_MODEL`.

## One-time Blogger OAuth setup

1. In Google Cloud Console, enable **Blogger API v3**.
2. Create an OAuth 2.0 **Desktop app** client.
3. Run on your own computer:

```bash
python scripts/blogger_oauth_helper.py \
  --client-id 'YOUR_CLIENT_ID' \
  --client-secret 'YOUR_CLIENT_SECRET'
```

4. Approve access to Blogger.
5. Paste the full redirected localhost URL into the terminal.
6. Save the printed values as the three Blogger GitHub Actions secrets above.

OAuth scope:

```text
https://www.googleapis.com/auth/blogger
```

## First safe test

After the secrets are configured, run the GitHub Actions workflow **Blogger - Publish** manually with `dry_run=true`.

This resolves the target blog/pages and reports what would be changed, but does not update Blogger.

After checking the output, run with `dry_run=false` or merge reviewed Blogger changes to `main`.

## Local validation

```bash
python scripts/blogger_validate.py blogger/faq/*.html
```

## Local FAQ translation

```bash
export OPENAI_API_KEY='...'
python scripts/blogger_translate.py
python scripts/blogger_validate.py blogger/faq/*.html
```

## Local Blogger checks

After exporting the Blogger OAuth variables:

```bash
python scripts/blogger_sync.py discover
python scripts/blogger_sync.py faq --dry-run
python scripts/blogger_sync.py posts --dry-run
```

## Normal future workflow

FAQ:

1. Edit only `blogger/faq/ko.html` on `develop`.
2. Push to `develop`.
3. GitHub Actions translates the other six languages and validates structure.
4. Review generated files.
5. Merge to `main`.
6. GitHub Actions updates all seven Blogger FAQ pages.

Notice / Story / Guide:

1. Add `meta.json` + `ko.html` under the appropriate item folder.
2. Push to `develop`.
3. GitHub Actions translates title/body to all supported locales.
4. Review generated files.
5. Merge to `main`.
6. GitHub Actions creates or updates the localized Blogger posts with the correct category/language labels and desired publish state.
