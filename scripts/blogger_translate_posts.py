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
from blogger_localized_media import apply_localized_media
from blogger_sync import access_token, get_blog, list_all_posts, post_url_matches


def strip_single_paragraph(html: str) -> str:
    text = re.sub(r"^\s*<p[^>]*>", "", html.strip(), flags=re.I)
    text = re.sub(r"</p>\s*$", "", text, flags=re.I)
    return re.sub(r"<[^>]+>", "", text).strip()


def load_json_object(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return {str(k): str(v) for k, v in data.items()}


def normalize_imported_source_html(content: str) -> str:
    content = re.sub(
        r"^\s*<!--shiftmate-content-id:[^>]+-->\s*",
        "",
        content.strip(),
        count=1,
        flags=re.I,
    )
    content = re.sub(
        r'^\s*<span\b[^>]*class=["\'][^"\']*\bsm-post-seo\b[^"\']*["\'][^>]*>.*?</span>\s*',
        "",
        content,
        count=1,
        flags=re.I | re.S,
    )
    # Blogger authors sometimes put a visual title in the body. Managed Posts
    # reserve h1 for the Blogger post title, so preserve the heading as h2.
    content = re.sub(r"<h1(\b[^>]*)>", r"<h2\1>", content, flags=re.I)
    content = re.sub(r"</h1\s*>", "</h2>", content, flags=re.I)
    if re.search(
        r'<article\b[^>]*class=["\'][^"\']*\bsm-post\b',
        content,
        flags=re.I,
    ):
        return content.strip() + "\n"
    return '<article class="sm-post" lang="ko">\n' + content.strip() + "\n</article>\n"


def import_source_if_needed(
    item: Path,
    meta: dict,
    source_path: Path,
    config: dict,
) -> None:
    if source_path.exists():
        return
    source_url = str(meta.get("source_url", "")).strip()
    if not source_url:
        return

    token = access_token()
    blog = get_blog(token, str(config["blog_url"]))
    posts = list_all_posts(token, str(blog["id"]), fetch_bodies=True)
    matches = [
        post
        for post in posts
        if post_url_matches(str(post.get("url", "")), source_url)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one Blogger post for source_url {source_url}, "
            f"found {len(matches)}"
        )

    post = matches[0]
    content = str(post.get("content", "")).strip()
    if not content:
        raise RuntimeError(f"Blogger source post has no content: {source_url}")

    item.mkdir(parents=True, exist_ok=True)
    source_path.write_text(normalize_imported_source_html(content), encoding="utf-8")
    print(
        f"Imported Korean source from Blogger: {source_url} "
        f"(post {post.get('id', '?')})"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--root", type=Path, default=Path("blogger/posts"))
    ap.add_argument("--item", type=Path)
    ap.add_argument(
        "--metadata-only",
        action="store_true",
        help="Preserve localized Post bodies and update only changed title/description metadata.",
    )
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
        if not meta_path.exists():
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        import_source_if_needed(item, meta, source_path, config)
        if not source_path.exists():
            continue

        category = str(meta.get("category") or item.parent.name)
        if category not in allowed_categories:
            raise RuntimeError(
                f"Unsupported Blogger post category '{category}' in {meta_path}. "
                "Only notice/story are translated as posts."
            )

        source = source_path.read_text(encoding="utf-8")
        source_title = str(meta.get("title_ko", "")).strip()
        source_description = str(meta.get("seo_description_ko", "")).strip()
        if not source_title:
            raise RuntimeError(f"title_ko is required: {meta_path}")
        if not source_description:
            raise RuntimeError(f"seo_description_ko is required: {meta_path}")

        titles_path = item / "titles.json"
        descriptions_path = item / "descriptions.json"
        titles = load_json_object(titles_path)
        descriptions = load_json_object(descriptions_path)

        title_changed = (
            titles.get(source_locale) != source_title
            or any(not titles.get(locale) for locale in locales)
        )
        description_changed = (
            descriptions.get(source_locale) != source_description
            or any(not descriptions.get(locale) for locale in locales)
        )
        titles[source_locale] = source_title
        descriptions[source_locale] = source_description

        for locale, info in locales.items():
            if locale == source_locale:
                continue

            if not args.metadata_only:
                print(f"{category}/{item.name}: body {source_locale} -> {locale}")
                translated = translate_preserving_structure(
                    api_key,
                    model,
                    source,
                    locale,
                    info["name"],
                    info["html_lang"],
                    content_type="post",
                )
                translated = apply_localized_media(item, translated, locale)
                (item / f"{locale}.html").write_text(translated, encoding="utf-8")

            if title_changed:
                print(f"{category}/{item.name}: title {source_locale} -> {locale}")
                title_html = translate_preserving_structure(
                    api_key,
                    model,
                    f"<p>{source_title}</p>",
                    locale,
                    info["name"],
                    info["html_lang"],
                    content_type="post-title",
                )
                titles[locale] = strip_single_paragraph(title_html)

            if description_changed:
                print(
                    f"{category}/{item.name}: search description "
                    f"{source_locale} -> {locale}"
                )
                description_html = translate_preserving_structure(
                    api_key,
                    model,
                    f"<p>{source_description}</p>",
                    locale,
                    info["name"],
                    info["html_lang"],
                    content_type="post-search-description",
                )
                descriptions[locale] = strip_single_paragraph(description_html)

        titles_path.write_text(
            json.dumps(titles, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        descriptions_path.write_text(
            json.dumps(descriptions, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
