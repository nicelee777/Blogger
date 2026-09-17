# Managed Blogger Posts

Use this directory only for **Notice** and **Story** content.

`FAQ` and `Guide` are long-lived Blogger Pages and are managed separately.

## Item structure

```text
blogger/posts/story/<slug>/
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

`notice` uses the same structure under `blogger/posts/notice/<slug>/`.

## meta.json

Example:

```json
{
  "category": "story",
  "slug": "shift-schedule-tips",
  "title_ko": "교대근무 일정이 자주 바뀔 때 일정 관리 방법",
  "publish": false,
  "labels": [],
  "seo_description_ko": "교대근무 일정이 자주 바뀔 때 놓치지 않고 관리하는 실용적인 방법을 정리합니다.",
  "primary_keyword": "교대근무 일정 관리",
  "secondary_keywords": [
    "간호사 근무표",
    "교대근무 캘린더"
  ]
}
```

Rules:

- `category`: `notice` or `story` only.
- `slug`: lowercase letters/numbers/hyphens, stable after publication.
- `title_ko`: Korean source title.
- New items begin with `publish: false`.
- `publish: true` is a production decision and should only be set after explicit review/approval.
- `labels` are additional Blogger labels; category/language labels are added automatically.
- SEO metadata is stored for review/future tooling even if Blogger sync does not currently expose it as a dedicated field.

## AI source generation

The generator reads repository policy automatically:

```bash
export OPENAI_API_KEY='...'
python scripts/blogger_generate.py \
  --category story \
  --slug shift-schedule-tips \
  --brief '교대근무 일정이 자주 바뀌는 사용자를 위한 실용적인 일정 관리 글. ShiftMate는 과하지 않게 연결.'
```

The generator always writes `publish: false`.

Use exact reference notes/URLs when factual external claims or media are required:

```bash
python scripts/blogger_generate.py \
  --category notice \
  --slug widget-update \
  --brief '홈 위젯 개선 공지 작성' \
  --references '확정된 변경사항: ...'
```

Never put secrets in the brief/reference text.

## Translation

```bash
python scripts/blogger_translate_posts.py \
  --item blogger/posts/story/shift-schedule-tips
```

## Validation

Korean source only:

```bash
python scripts/blogger_validate_post.py \
  blogger/posts/story/shift-schedule-tips \
  --require-draft
```

After localization:

```bash
python scripts/blogger_validate_post.py \
  blogger/posts/story/shift-schedule-tips \
  --all-locales
```

## Blogger draft preview

For a new Post or an existing Blogger draft:

```bash
python scripts/blogger_sync_draft.py \
  --item blogger/posts/story/shift-schedule-tips
```

Draft sync never changes a canonical Post that is already live or scheduled.

## Stable identity

Production sync adds a hidden marker such as:

```html
<!--shiftmate-content-id:story/shift-schedule-tips/en-->
```

This allows repeated syncs to update the same localized Blogger Post instead of creating duplicates.

## Media

Images and YouTube embeds may be included directly in `ko.html` when exact URLs are known. Translation preserves media URLs.

- image URLs should use HTTPS;
- YouTube iframe embeds should use HTTPS and preferably `youtube-nocookie.com`;
- do not invent asset/media URLs;
- use meaningful `alt` text and iframe `title` text.
