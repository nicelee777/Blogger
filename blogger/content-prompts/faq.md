# FAQ authoring policy

## Role

Write or revise a concise answer to a real ShiftMate support question.

## Goal

Help the user solve the issue with the fewest necessary steps while preserving stable FAQ IDs and page structure.

## Requirements

- Start with the direct answer.
- Use exact app/UI terminology from `blogger/glossary.json` when available.
- Prefer explicit navigation paths such as `설정 → 화면 설정 → 근무 크기`.
- Keep one FAQ item focused on one user question.
- Do not add marketing copy, feature promises, or unrelated tips.
- Do not say manual refresh is required when current product facts say the app already fetches the latest data on screen entry/month change.
- If platform behavior differs, state the platform clearly.
- Preserve existing stable `id` values unless the user explicitly requests a new FAQ item.
- For a new FAQ item, use a short semantic ID beginning with `faq-`.

## Recommended answer shape

```html
<details id="faq-example">
  <summary><strong>Q. 사용자 질문</strong></summary>
  <div class="sm-faq-answer">
    <p>직접적인 답변.</p>
    <p>필요한 경우 경로 또는 추가 설명.</p>
  </div>
</details>
```

Keep the answer as short as the task allows.
