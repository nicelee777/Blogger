# ShiftMate Blogger SEO policy

SEO should improve discoverability without reducing clarity, accuracy, or trust.

## Search intent first

Before drafting, identify one primary search intent. Typical ShiftMate intents include:

- how to manage nurse/shift schedules
- how to use a specific ShiftMate feature
- troubleshooting an app workflow
- understanding a shift-work problem
- reading product/update news

Do not combine unrelated intents simply to target more keywords.

## Titles

- Make the topic and benefit/problem clear.
- Include the primary keyword naturally when useful.
- Avoid clickbait and repeated brand terms.
- Prefer a specific title over a vague promotional headline.

## Headings

- One logical hierarchy: title in Blogger metadata, then `h2` and `h3` in the body.
- Do not add an extra body `h1` unless a specific Page template requires it.
- Headings should describe the section, not just contain keywords.

## Keywords

- Use one primary keyword/theme and a small number of semantically related terms.
- Prefer natural variations such as “간호사 근무표,” “교대근무 일정,” and “근무 달력” only when they fit the topic.
- Never keyword-stuff titles, headings, alt text, or repeated paragraphs.

## Snippet-friendly writing

- Answer the main question early.
- When appropriate, use a short definition, concise steps, or a direct answer near the top.
- Keep important UI paths explicit, for example `설정 → 알람 → 알람음`.

## Internal links

Add internal links only when they help the reader continue the task. Prefer links to:

- the relevant Guide section
- FAQ section
- a directly related Notice or Story
- the official ShiftMate brand/product page when appropriate

Do not create excessive cross-links solely for SEO.

## Media SEO

- Use descriptive file names when assets are under our control.
- Write alt text for accessibility first; do not stuff keywords into alt text.
- Add a short caption when the image needs context.
- For YouTube, use a descriptive embed title and surrounding explanatory text.

## Duplicate content

- FAQ and Guide may overlap, but their intent should differ: FAQ answers quickly; Guide teaches the task.
- Story should not merely restate Guide sections.
- Notice should document a specific change rather than duplicate evergreen documentation.

## Freshness

Do not add dates or “latest” claims unless the date/release state is verified. Update evergreen content in place rather than creating near-duplicate posts for minor wording changes.

## Search descriptions for managed Posts

Every managed Notice and Story must have a search description.

- `meta.json` must contain a non-empty Korean `seo_description_ko`.
- Search descriptions should be one concise line, normally 20–220 characters, written for humans rather than keyword stuffing.
- Localization must create `descriptions.json` with one search description for every managed locale.
- Missing Korean or localized search descriptions are validation failures.
- Blogger API does not currently expose a supported field for the Blogger editor's Search Description input. Production sync therefore embeds the managed description with the Post, and the ShiftMate theme runtime applies it to the rendered post page's `meta[name="description"]`, Open Graph description, and Twitter description.
- Do not claim that the Blogger editor's Search Description field itself was populated by the API.

## Metadata stored with managed Posts

Managed Notice/Story `meta.json` includes editorial metadata such as:

- `seo_description_ko` (required)
- `primary_keyword`
- `secondary_keywords`

Localized search descriptions are stored separately in `descriptions.json`.

## Quality gate

A draft should be rejected or revised if it:

- makes unsupported factual claims;
- repeats the same keyword unnaturally;
- has headings that do not match the content;
- exists mainly to rank rather than help a reader;
- duplicates an existing managed item without a clear reason.
