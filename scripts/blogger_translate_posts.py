#!/usr/bin/env python3
"""Translate Blogger notice/story items from Korean source files."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from blogger_translate import translate_preserving_structure


def strip_single_paragraph(html: str) -> str:
    text = re.sub(r"^\s*<p[^>]*>", "", html.strip(), flags=re.I)
    text = re.sub(r"</p>\s*$", "", text, flags=re.I)
    return re.sub(r"<[^>]+>", "", text).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--root", type=Path, default=Path("blogger/posts"))
    ap.add_argument("--item", type=Path)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 2

    config = json.loads(args.config.read_text(encoding="utf-8"))
    locales = config["locales"]
    source_locale = config.get("source_locale", "ko")
    allowed_categories = set(config.get("post_categories", {}))
    model = os.environ.get(
        "OPENAI_TRANSLATION_MODEL",
        config.get("translation_model", "gpt-5.6-luna"),
    )
    items = (
        [args.item]
        if args.item
        else sorted(p.parent for p in args.root.glob("*/*/meta.json"))
    )

    for item in items:
        if item is None:
            continue
        meta_path = item / "meta.json"
        source_path = item / f"{source_locale}.html"
        if not meta_path.exists() or not source_path.exists():
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        category = str(meta.get("category") or item.parent.name)
        if category not in allowed_categories:
            raise RuntimeError(
                f"Unsupported Blogger post category '{category}' in {meta_path}. "
                "Only notice/story are translated as posts."
            )

        source = source_path.read_text(encoding="utf-8")
        titles = {source_locale: meta["title_ko"]}
        for locale, info in locales.items():
            if locale == source_locale:
                continue
            print(f"{category}/{item.name}: {source_locale} -> {locale}")
            translated = translate_preserving_structure(
                api_key,
                model,
                source,
                locale,
                info["name"],
                info["html_lang"],
                content_type="post",
            )
            (item / f"{locale}.html").write_text(translated, encoding="utf-8")

            # Translate titles through the same structure-preserving segment engine.
            title_html = translate_preserving_structure(
                api_key,
                model,
                f"<p>{meta['title_ko']}</p>",
                locale,
                info["name"],
                info["html_lang"],
                content_type="post-title",
            )
            titles[locale] = strip_single_paragraph(title_html)

        (item / "titles.json").write_text(
            json.dumps(titles, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
