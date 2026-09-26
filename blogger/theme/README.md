# ShiftMate Blogger theme

GitHub is the source of truth for ShiftMate Blogger theme code.

## Canonical theme and runtime

`shiftmate-theme.xml` is the committed complete Blogger theme and the file to upload in Blogger Theme UI.

`shiftmate-menu-runtime-v6.js` is the canonical 10-locale language/menu runtime embedded into that XML. CI verifies that the embedded runtime matches the standalone source exactly.

Managed locales:

- English (`lang`)
- Español (`lang-es`)
- Deutsch (`lang-de`)
- Français (`lang-fr`)
- Português (Brasil) (`lang-pt-br`)
- 简体中文 (`lang-zh-cn`)
- 繁體中文 (`lang-zh-tw`)
- 한국어 (`lang-ko`)
- 日本語 (`lang-ja`)
- Tiếng Việt (`lang-vi`)

FAQ and Guide use Blogger Pages. Notice and Story use label-combination URLs.

FAQ/Guide links must use clean Page paths from `blogger/config.json`, for example:

- `/p/faq-ko.html`
- `/p/guide-ko.html`

Do not append `?sm-lang=...` to FAQ or Guide Page links. Locale state is kept in `localStorage`. The runtime removes legacy `sm-lang` from FAQ/Guide addresses with `history.replaceState` while preserving unrelated Blogger query parameters, and maintains clean canonical/hreflang metadata.

## Build a complete Blogger theme

Do not hand-edit the inline `<script id='shiftmate-menu-runtime'>...</script>` block in Blogger.

Export/download the current Blogger theme XML, then build the complete paste-ready file from the GitHub runtime:

```bash
python scripts/blogger_build_theme.py \
  --input /path/to/blogger-export.xml \
  --output /tmp/shiftmate-blogger-theme.xml \
  --theme-version 1.2.0 \
  --theme-date 2026-09-27
```

The builder:

1. finds exactly one `shiftmate-menu-runtime` script;
2. replaces its body with the GitHub-managed runtime;
3. optionally updates the ShiftMate theme version/date comment;
4. parses the final XML;
5. rejects a runtime that generates `?sm-lang=` Page URLs;
6. requires canonical/hreflang safeguards.

Before changing the theme runtime, run:

```bash
python scripts/blogger_validate_theme_runtime.py
```

The GitHub verification workflows run this regression check automatically.

## Deployment boundary

Blogger API v3 can publish the managed FAQ/Guide Pages and Posts, but it does not update the Blogger theme HTML. Therefore:

- **code changes are managed and reviewed in GitHub**;
- **the complete theme XML is built from GitHub-managed code**;
- the final generated XML still has to be applied in Blogger Theme UI.

For future changes, edit the GitHub source first. Do not patch the live Blogger runtime independently, because that causes the live theme and repository to drift.

## Notice list cards

The runtime applies a dedicated card presentation only on localized Notice label pages such as:

- `/search/label/lang-ko+notice`
- `/search/label/lang+notice`

Notice cards use the existing Blogger Post markup and labels. `notice_type` is automatically added as a Blogger label for managed notices.

Supported type badges:

- `general` — general notice
- `update` — update
- `maintenance` — maintenance
- `incident` — incident/outage
- `feature` — feature announcement
- `service` — service information
- `policy` — policy information

The badge text is localized for all 10 managed locales. A semantic-version label such as `10.0.0` is shown separately as a version badge.

## Managed Post search descriptions

Blogger API does not currently provide a supported way to populate the editor's **Search Description** field for Posts. Managed Notice/Story items therefore use repository-owned SEO metadata:

1. Korean `seo_description_ko` is required in `meta.json`.
2. Localization generates `descriptions.json` for every managed locale.
3. Blogger sync embeds the localized value in the Post as a hidden `.sm-post-seo[data-sm-description]` marker.
4. On a single managed Post page, the runtime applies the managed metadata to:
   - `meta[name="description"]`
   - `og:title`
   - `og:description`
   - `og:url`
   - `og:type=article`
   - `og:site_name`
   - `twitter:title`
   - `twitter:description`
   - `twitter:card`
   - canonical URL
   - `article:published_time` when the rendered Blogger timestamp is available.

This provides automatic rendered-page metadata while keeping the repository as the source of truth. Do not describe this as populating Blogger's editor-side Search Description input.

## Updating the committed theme

When the runtime changes, rebuild `blogger/theme/shiftmate-theme.xml` from the latest exported Blogger theme and canonical runtime, then run:

```bash
python scripts/blogger_validate_theme_runtime.py
python scripts/blogger_validate_theme_xml.py
```

Do not merge a runtime change while the committed XML contains an older embedded runtime.
