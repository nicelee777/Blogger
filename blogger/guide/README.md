# ShiftMate Guide Page

`guide` is a long-lived Blogger **Page**, not a Post.

## Source of truth

Edit only:

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

Recommended structure:

```html
<div class="shiftmate-guide" lang="ko">
  <h1>ShiftMate 사용 가이드</h1>

  <nav aria-labelledby="guide-toc">
    <h2 id="guide-toc">목차</h2>
    <a href="#shift-input">근무 입력</a>
    <a href="#alarm">출근 알람</a>
    <a href="#widget">홈 위젯</a>
  </nav>

  <section id="shift-input">
    <h2>근무 입력</h2>
    <p>...</p>
  </section>
</div>
```

Use stable section IDs because the app and blog can deep-link directly to a section such as:

```text
/p/guide-ko.html#widget
```

Images and YouTube embeds may be included in the HTML. URLs, IDs, CSS, media source URLs, and element order are preserved during translation; visible text and accessibility text are localized.

Until `blogger/guide/ko.html` is added, Guide synchronization is intentionally skipped so the existing Blogger Guide Pages cannot be overwritten accidentally.
