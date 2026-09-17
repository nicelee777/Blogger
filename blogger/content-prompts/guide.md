# Guide authoring policy

## Role

Create or update an evergreen ShiftMate user guide that teaches a task from start to finish.

## Goal

Make the guide useful as a long-lived reference Page. Prefer one well-structured Page with stable section anchors over many small pages.

## Requirements

- Organize by user task, not by internal app architecture.
- Use stable semantic section IDs so app/help links can deep-link to specific sections.
- Begin each major section with what the user can accomplish.
- Give steps in the order the user performs them.
- Use exact UI terminology from `blogger/glossary.json` where available.
- Add troubleshooting only when it directly relates to the section.
- Use screenshots/images to clarify visual tasks; never invent their URLs.
- Use YouTube embeds only when an exact URL/video ID is provided.
- Keep explanatory text useful even without the video.
- Do not duplicate FAQ answers verbatim; link or summarize when appropriate.
- Do not claim planned features are released.

## Recommended section shape

```html
<section id="shift-input">
  <h2>근무 입력</h2>
  <p>이 섹션에서 할 수 있는 일을 짧게 설명합니다.</p>

  <h3>입력 방법</h3>
  <ol>
    <li>첫 번째 단계</li>
    <li>두 번째 단계</li>
  </ol>

  <!-- Optional exact image/video supplied by the brief -->
</section>
```

## Media

For images:

```html
<figure class="sm-media">
  <img src="EXACT_HTTPS_URL" alt="화면을 설명하는 대체 텍스트" loading="lazy">
  <figcaption>필요한 경우 짧은 설명</figcaption>
</figure>
```

For YouTube:

```html
<div class="sm-video">
  <iframe
    src="https://www.youtube-nocookie.com/embed/VIDEO_ID"
    title="영상 내용을 설명하는 제목"
    loading="lazy"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen>
  </iframe>
</div>
```

Never autoplay media or alter supplied media URLs during localization.
