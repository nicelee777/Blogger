# ShiftMate Blogger AI operating rules

This repository is the source of truth for ShiftMate Blogger content. Any AI agent editing content or automation in this repository must follow these rules.

## Read before writing content

Before creating or materially editing Blogger content, read:

1. `blogger/product-facts.md`
2. `blogger/editorial-policy.md`
3. `blogger/seo-policy.md`
4. `blogger/content-prompts/<content-type>.md`
5. `blogger/glossary.json`
6. `blogger/config.json`

For existing content, also read the current Korean source before editing it.

## Source-of-truth rules

- Korean (`ko`) is the editorial source language.
- FAQ and Guide are long-lived Blogger Pages.
- Notice and Story are Blogger Posts.
- Localized HTML is generated from Korean source and must preserve protected HTML structure and URLs.
- Never invent a ShiftMate feature, release state, statistic, user quote, award, medical claim, policy requirement, or external source.
- If a requested fact is not in `product-facts.md`, the current source, or the user's brief, omit it or mark it for confirmation.
- Do not claim planned functionality is already released.

## Publication safety

- New Notice/Story items must start with `"publish": false`.
- `develop` is for editing, generation, localization, validation, and draft preview.
- `main` is the publication branch.
- Never change `publish` to `true` unless the user explicitly approves publication.
- Never publish a Page or Post merely because content generation succeeded.

## Content quality

- Write for humans first; SEO is secondary to clarity and usefulness.
- Keep ShiftMate mentions relevant and restrained. Do not turn educational Story content into an advertisement.
- Use scannable headings, short paragraphs, descriptive links, and meaningful image alt text.
- Do not keyword-stuff or create repetitive near-duplicate sections for search engines.
- For health, safety, legal, financial, or other high-stakes claims, use only facts/references provided in the brief or authoritative sources explicitly supplied for the task. Otherwise keep the content general and avoid unsupported advice.

## HTML and media

- Do not invent image or YouTube URLs.
- Preserve exact `href`, `src`, `id`, `class`, `data-*`, and media URLs during localization.
- Prefer `https://www.youtube-nocookie.com/embed/<VIDEO_ID>` for YouTube embeds when creating new embeds.
- Never add executable scripts, forms, trackers, or third-party embeds unrelated to the requested content.

## Normal workflow

```text
brief/request
-> Korean source on develop
-> AI localization
-> validators
-> Blogger draft for a new Notice/Story when applicable
-> review
-> merge to main
-> production Blogger sync
```
