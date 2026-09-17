# ShiftMate Blogger automation

GitHub is the source of truth for managed Blogger content.

## Content model

- FAQ → long-lived Blogger Page
- Guide → long-lived Blogger Page
- Notice → Blogger Post
- Story → Blogger Post

Korean (`ko`) is the editorial source locale. Localized files are generated from the Korean source.

## GitHub Actions policy

**All Blogger workflows are manual-only.**

No Blogger workflow should run automatically on `push` or `pull_request`.
Run an Action only when the operator intentionally requests it from GitHub Actions or asks ChatGPT to run the corresponding workflow.

Available workflows:

- `Blogger - Translate` — manually translate `faq`, `guide`, `posts`, or `all` on `develop`.
- `Blogger - Verify` — manually validate repository content and perform Blogger API dry-run discovery without writing.
- `Blogger - Publish` — manually validate and either dry-run or publish the current `main` content.
- `Blogger - Generate Draft` — manually generate a new Story/Notice draft from an editorial brief, localize it, and create Blogger drafts.

Recommended operating flow:

```text
Edit Korean source on develop
→ manually run Blogger - Translate for the needed scope
→ review localized files
→ merge/reconcile to main
→ manually run Blogger - Verify when desired
→ manually run Blogger - Publish (dry_run=true first when appropriate)
→ manually run Blogger - Publish (dry_run=false) for production
```

## Page sources

FAQ source:

```text
blogger/faq/ko.html
```

Guide source:

```text
blogger/guide/ko.html
```

Localized Page files use the same locale names:

```text
en.html
ja.html
zh-cn.html
zh-tw.html
es.html
vi.html
```

Guide search descriptions are stored in:

```text
blogger/guide/search-descriptions.json
```

Blogger API v3 does not expose the static Page editor's Search description field, so these values are Git-managed and validated but must be entered manually in the Blogger Page editor.

## Managed Posts

Notice and Story items live under:

```text
blogger/posts/notice/<slug>/
blogger/posts/story/<slug>/
```

Each item contains `meta.json`, `ko.html`, localized bodies, and `titles.json` after localization.

## Editorial system

AI-assisted content should follow:

```text
AGENTS.md
blogger/product-facts.md
blogger/editorial-policy.md
blogger/seo-policy.md
blogger/content-prompts/*.md
blogger/glossary.json
```

These files define product-fact boundaries, tone, SEO principles, content-type behavior, and localized UI terminology.

## Safety

- Never commit API keys, OAuth credentials, refresh tokens, passwords, or private/personal data.
- The repository is public, so GitHub workflow inputs are not a place for secrets or sensitive material.
- Production Blogger writes occur only when `Blogger - Publish` is manually run with `dry_run=false`.
