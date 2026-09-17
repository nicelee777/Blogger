# Notice authoring policy

## Role

Write an official ShiftMate notice about a confirmed product, service, policy, or operational change.

## Goal

Explain what changed, who is affected, and what the user should do next without hype or ambiguity.

## Requirements

- Use only facts explicitly provided in the brief or confirmed in `blogger/product-facts.md`.
- Do not invent a version number, release date, rollout status, platform availability, or completion state.
- If rollout is partial, say so clearly.
- Put the most important change near the top.
- Explain user impact in plain language.
- If no action is required, say so when useful.
- Keep promotional language minimal.
- Do not imply data loss, migration, or compatibility impact unless verified.
- New Notice items must start as Blogger drafts (`publish: false`).

## Recommended structure

```html
<article class="sm-post" lang="ko">
  <p>핵심 변경사항을 1~2문장으로 설명합니다.</p>

  <h2>무엇이 변경되나요?</h2>
  <p>확정된 변경 내용.</p>

  <h2>사용자에게 어떤 영향이 있나요?</h2>
  <p>영향 또는 변경 없음.</p>

  <h2>확인해 주세요</h2>
  <p>필요한 조치나 참고사항.</p>
</article>
```

Omit sections that are unnecessary rather than filling them with generic text.
