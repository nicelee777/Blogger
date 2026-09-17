#!/usr/bin/env python3
"""Generate a Korean ShiftMate Notice/Story source from repository editorial policy."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.openai.com/v1/responses"
POLICY_FILES = [
    Path("blogger/product-facts.md"),
    Path("blogger/editorial-policy.md"),
    Path("blogger/seo-policy.md"),
]
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")


def read_text(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"required editorial file is missing: {path}")
    return path.read_text(encoding="utf-8")


def extract_output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(str(content["text"]))
    if not chunks:
        raise RuntimeError("OpenAI response did not contain output_text")
    return "\n".join(chunks).strip()


def parse_json_output(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"content model returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("content model output must be a JSON object")
    return value


def call_openai(api_key: str, model: str, instructions: str, brief: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "instructions": instructions,
        "input": brief,
        "reasoning": {"effort": "low"},
        "store": False,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"OpenAI API error {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc
    return parse_json_output(extract_output_text(data))


def validate_generated(result: dict[str, Any], category: str) -> tuple[str, str, str, list[str]]:
    title = str(result.get("title_ko", "")).strip()
    description = str(result.get("seo_description_ko", "")).strip()
    primary = str(result.get("primary_keyword", "")).strip()
    html = str(result.get("html", "")).strip()
    secondary_raw = result.get("secondary_keywords", [])
    secondary = [str(x).strip() for x in secondary_raw] if isinstance(secondary_raw, list) else []

    if not title:
        raise RuntimeError("generated content has no title_ko")
    if not html:
        raise RuntimeError("generated content has no html")
    if "<h1" in html.lower():
        raise RuntimeError("generated Post body must not contain an h1")
    if not re.search(r'<article\b[^>]*class=["\'][^"\']*\bsm-post\b', html, flags=re.I):
        raise RuntimeError("generated HTML must use <article class=\"sm-post\" ...>")
    if not re.search(r'<article\b[^>]*lang=["\']ko["\']', html, flags=re.I):
        raise RuntimeError("generated Korean HTML root article must use lang=\"ko\"")
    if re.search(r"<(script|style|form|object|embed)\b", html, flags=re.I):
        raise RuntimeError("generated HTML contains a forbidden executable/style tag")
    if category == "story" and len(title) < 4:
        raise RuntimeError("generated Story title is unexpectedly short")
    if len(secondary) > 4:
        raise RuntimeError("secondary_keywords must contain at most four terms")
    return title, description, primary, secondary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", choices=["notice", "story"], required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--labels", default="")
    ap.add_argument("--references", default="")
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--root", type=Path, default=Path("blogger/posts"))
    ap.add_argument("--overwrite-source", action="store_true")
    args = ap.parse_args()

    if not SLUG_RE.fullmatch(args.slug):
        print("slug must contain only lowercase a-z, 0-9, and hyphens (2-80 chars)", file=sys.stderr)
        return 2

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 2

    config = json.loads(args.config.read_text(encoding="utf-8"))
    model = os.environ.get(
        "OPENAI_CONTENT_MODEL",
        str(config.get("content_model", "gpt-5.6-terra")),
    ).strip()
    policy_version = int(config.get("editorial_policy_version", 1))

    item = args.root / args.category / args.slug
    meta_path = item / "meta.json"
    ko_path = item / "ko.html"
    if (meta_path.exists() or ko_path.exists()) and not args.overwrite_source:
        print(f"source item already exists: {item}; use --overwrite-source to replace it", file=sys.stderr)
        return 2

    policies = "\n\n".join(
        f"===== {path} =====\n{read_text(path)}" for path in POLICY_FILES
    )
    type_policy_path = Path("blogger/content-prompts") / f"{args.category}.md"
    type_policy = read_text(type_policy_path)

    instructions = f"""You are the Korean editorial writer for ShiftMate Blogger.
Create ONE new {args.category.upper()} draft from the user's brief.
The repository policies below are mandatory and override stylistic impulses.

{policies}

===== CONTENT-TYPE POLICY =====
{type_policy}

OUTPUT CONTRACT:
Return ONLY one valid JSON object, no Markdown fences and no commentary, with exactly these keys:
{{
  "title_ko": "Korean Blogger post title",
  "seo_description_ko": "one concise Korean search/snippet description",
  "primary_keyword": "one natural Korean search theme or empty string",
  "secondary_keywords": ["0 to 4 closely related terms"],
  "html": "complete Korean Blogger body HTML"
}}

HTML RULES:
- Body root must be <article class="sm-post" lang="ko"> ... </article>.
- Do not put an <h1> in the body; Blogger manages the title separately.
- Use only semantic body tags such as p, h2, h3, ul, ol, li, strong, em, a, figure, img, figcaption, div, iframe, br.
- Never create script/style/form/object/embed tags.
- Never invent an image URL, YouTube URL, external source, statistic, quotation, app feature, or release state.
- Only include media/links whose exact URLs are present in the brief or reference notes.
- If references are supplied, use only what the brief actually establishes; do not invent citations.
- Do not output placeholders such as TODO, EXAMPLE_URL, or VIDEO_ID unless the user explicitly asked for a placeholder.
"""

    brief = f"CATEGORY: {args.category}\nSLUG: {args.slug}\n\nUSER BRIEF:\n{args.brief.strip()}"
    if args.references.strip():
        brief += f"\n\nREFERENCE NOTES / URLS PROVIDED BY USER:\n{args.references.strip()}"

    result = call_openai(api_key, model, instructions, brief)
    title, description, primary, secondary = validate_generated(result, args.category)
    html = str(result["html"]).strip() + "\n"

    labels = [x.strip() for x in args.labels.split(",") if x.strip()]
    meta = {
        "category": args.category,
        "slug": args.slug,
        "title_ko": title,
        "publish": False,
        "labels": labels,
        "seo_description_ko": description,
        "primary_keyword": primary,
        "secondary_keywords": secondary,
        "generation": {
            "model": model,
            "policy_version": policy_version,
        },
    }

    item.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ko_path.write_text(html, encoding="utf-8")
    print(f"Generated draft source: {item}")
    print(f"Title: {title}")
    print("publish=false (forced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
