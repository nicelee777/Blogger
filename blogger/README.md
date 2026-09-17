# ShiftMate Blogger automation

GitHub is the source of truth for ShiftMate Blogger content. Blogger is the publishing target.

## Content model

```text
FAQ     -> Blogger Page (same page is updated repeatedly)
Guide   -> Blogger Page (same page is updated repeatedly)
Notice  -> Blogger Post (new item per notice)
Story   -> Blogger Post (new item per story)
```

Korean is the editorial source language. Other managed locales are generated from the Korean source.

## AI/editorial policy stack

Any AI writing or editing Blogger content should read these files before creating content:

```text
AGENTS.md
blogger/product-facts.md
blogger/editorial-policy.md
blogger/seo-policy.md
blogger/content-prompts/faq.md
blogger/content-prompts/guide.md
blogger/content-prompts/notice.md
blogger/content-prompts/story.md
blogger/glossary.json
blogger/config.json
```

The policies separate responsibilities:

- `product-facts.md`: factual boundary for ShiftMate capabilities and release-state claims
- `editorial-policy.md`: brand voice, accuracy, accessibility, CTA, high-stakes content rules
- `seo-policy.md`: search intent, title/headings, keywords, links, media SEO, duplicate-content rules
- `content-prompts/*.md`: content-type-specific writing requirements
- `glossary.json`: localized UI/product terminology
- `config.json`: models, locales, Blogger Page paths, category configuration

Changing policy files changes the instructions used by future AI-generated drafts.

## AI models

Defaults are configured in `blogger/config.json`:

```text
content_model     -> gpt-5.6-terra
translation_model -> gpt-5.6-luna
```

The content model focuses on planning/writing quality. The translation model is optimized for repeated localization work.

Environment overrides are available:

```text
OPENAI_CONTENT_MODEL
OPENAI_TRANSLATION_MODEL
```

## Branch policy

- `develop`: edit, generate, translate, validate, verify, and preview new Post drafts
- `main`: production publication branch
- Pull-request validation never publishes.
- Develop-side draft sync never modifies a live/scheduled canonical Post.

## Managed Pages: FAQ and Guide

Korean source files:

```text
blogger/faq/ko.html
blogger/guide/ko.html
```

FAQ Page paths:

- EN `/p/faq.html`
- KO `/p/faq-ko.html`
- JA `/p/faq-ja.html`
- ZH-CN `/p/faq-cn.html`
- ZH-TW `/p/faq-tw.html`
- ES `/p/faq-es.html`
- VI `/p/faq-vi.html`

Guide Page paths:

- EN `/p/guide.html`
- KO `/p/guide-ko.html`
- JA `/p/guide-ja.html`
- ZH-CN `/p/guide-cn.html`
- ZH-TW `/p/guide-tw.html`
- ES `/p/guide-es.html`
- VI `/p/guide-vi.html`

Page targets are resolved by URL path instead of hard-coded Page IDs.

Guide publication remains disabled until `blogger/guide/ko.html` exists, preventing accidental replacement of the current live Guide Pages.

## Managed Posts: Notice and Story

```text
blogger/posts/notice/<slug>/
blogger/posts/story/<slug>/
```

Each managed Post contains:

```text
meta.json
ko.html

titles.json   # generated
en.html        # generated
ja.html        # generated
zh-cn.html     # generated
zh-tw.html     # generated
es.html        # generated
vi.html        # generated
```

New Posts must begin with `publish: false`.

## Two ways to create a new Notice/Story

### 1. Ask ChatGPT to create it

Example request:

```text
Story 글 하나 만들어줘.
주제: 교대근무 일정이 자주 바뀔 때 일정 관리 방법
SEO를 고려하고 ShiftMate는 과하지 않게 연결해줘.
Blogger draft까지 진행해줘.
```

The expected automation path is:

```text
ChatGPT reads repository policies
-> creates meta.json + ko.html on develop
-> Blogger - Translate generates six localized versions
-> validators run
-> Blogger draft sync creates/updates drafts for a new managed Post
-> human review
-> main
-> production publish
```

### 2. Use GitHub Actions directly

Run **Blogger - Generate Draft** and provide:

- category: `story` or `notice`
- slug
- brief
- optional reference notes/URLs
- optional labels

The workflow performs:

```text
repository policy read
-> GPT Korean source generation
-> Korean source validation
-> six-language localization
-> full Post validation
-> commit to develop
-> Blogger draft creation/update
```

It always generates `publish: false`. Production publication still requires review and `main`.

## Draft safety

`scripts/blogger_sync_draft.py` only handles one managed Post item at a time.

- If the canonical Blogger Post does not exist, it creates a draft.
- If the canonical Post is already a draft, it updates the draft.
- If the canonical Post is live or scheduled, develop-side draft sync **skips it** and does not unpublish or edit it.

This makes new-Post preview safe while protecting already published Posts.

## Translation behavior

`Blogger - Translate` runs on `develop` when Korean source content changes.

- FAQ -> translated as FAQ Page content
- Guide -> translated as long-form Guide Page content
- Notice/Story -> translated as Posts
- IDs, CSS, URLs, media source URLs, element order, and protected attributes remain unchanged
- visible text, image alt text, iframe/video titles, and accessibility labels are localized
- only changed content is translated when possible

## Validation

FAQ:

```bash
python scripts/blogger_validate.py blogger/faq/*.html
```

Guide, after the Guide source exists:

```bash
python scripts/blogger_validate_guide.py blogger/guide/*.html
```

Managed Post:

```bash
python scripts/blogger_validate_post.py blogger/posts/story/<slug>
python scripts/blogger_validate_post.py blogger/posts/story/<slug> --all-locales
```

The Post validator checks category/slug consistency, draft metadata, root HTML shape, forbidden executable tags, duplicate IDs, media URL safety, localized titles, and protected HTML structure.

## Read-only Blogger verification

`Blogger - Verify` performs:

```text
repository validation
-> Blogger target discovery
-> managed Page dry-run
-> managed Post dry-run
```

It never writes to Blogger.

## Production publishing

`Blogger - Publish` on `main` updates managed Pages and creates/updates managed Posts according to `publish` in `meta.json`.

Before a manual production publish, use `dry_run=true`.

## Required GitHub Actions secrets

Repository -> **Settings -> Secrets and variables -> Actions**

- `OPENAI_API_KEY`
- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

Never commit these values.
