#!/usr/bin/env python3
"""Validate ShiftMate managed Notice/Story source and localized Post files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from blogger_translate import assert_structure
from blogger_localized_media import apply_localized_media
from blogger_localized_links import apply_localized_post_links

FORBIDDEN_TAGS = {"script", "form", "object", "embed"}
NOTICE_TYPES = {"general", "update", "maintenance", "incident", "feature", "service", "policy"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")


class PostParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.ids: list[str] = []
        self.tags: list[str] = []
        self.images: list[str] = []
        self.iframes: list[str] = []
        self.has_h1 = False
        self.article_class = ""
        self.article_lang = ""
        self.forbidden: list[str] = []

    def _consume(self, tag: str, attrs) -> None:
        tag = tag.lower()
        self.tags.append(tag)
        values = {k.lower(): (v or "") for k, v in attrs}
        if tag in FORBIDDEN_TAGS:
            self.forbidden.append(tag)
        if tag == "h1":
            self.has_h1 = True
        if tag == "article" and not self.article_class:
            self.article_class = values.get("class", "")
            self.article_lang = values.get("lang", "")
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "img":
            self.images.append(values.get("src", ""))
        if tag == "iframe":
            self.iframes.append(values.get("src", ""))

    def handle_starttag(self, tag: str, attrs):
        self._consume(tag, attrs)

    def handle_startendtag(self, tag: str, attrs):
        self._consume(tag, attrs)


def validate_media(parser: PostParser, path: Path) -> list[str]:
    errors: list[str] = []
    for src in parser.images:
        if not src:
            errors.append(f"{path}: img is missing src")
            continue
        parsed = urlparse(src)
        if parsed.scheme != "https":
            errors.append(f"{path}: image src must use https: {src}")
    for src in parser.iframes:
        if not src:
            errors.append(f"{path}: iframe is missing src")
            continue
        parsed = urlparse(src)
        host = parsed.netloc.lower()
        if parsed.scheme != "https" or host not in {"www.youtube.com", "youtube.com", "www.youtube-nocookie.com"}:
            errors.append(f"{path}: only HTTPS YouTube iframe embeds are allowed: {src}")
    return errors


def validate_html(path: Path, *, source: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    parser = PostParser()
    parser.feed(text)
    errors: list[str] = []
    if parser.has_h1:
        errors.append(f"{path}: managed Post body must not contain h1")
    if parser.forbidden:
        errors.append(f"{path}: forbidden tag(s): {', '.join(sorted(set(parser.forbidden)))}")
    duplicates = sorted({x for x in parser.ids if parser.ids.count(x) > 1})
    if duplicates:
        errors.append(f"{path}: duplicate id(s): {', '.join(duplicates)}")
    if "sm-post" not in parser.article_class.split():
        errors.append(f"{path}: first article must include class sm-post")
    if source and parser.article_lang != "ko":
        errors.append(f"{path}: Korean source article must use lang=\"ko\"")
    errors.extend(validate_media(parser, path))
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("item", type=Path)
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--all-locales", action="store_true")
    ap.add_argument("--require-draft", action="store_true")
    args = ap.parse_args()

    item = args.item
    meta_path = item / "meta.json"
    source_path = item / "ko.html"
    errors: list[str] = []

    if not meta_path.exists():
        errors.append(f"missing {meta_path}")
    if not source_path.exists():
        errors.append(f"missing {source_path}")
    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors), file=sys.stderr)
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    category = str(meta.get("category", ""))
    slug = str(meta.get("slug", ""))
    if category not in {"notice", "story"}:
        errors.append(f"unsupported category: {category}")
    if item.parent.name != category:
        errors.append(f"item parent/category mismatch: {item.parent.name} != {category}")
    if item.name != slug:
        errors.append(f"item slug/path mismatch: {item.name} != {slug}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", slug):
        errors.append(f"invalid slug: {slug}")
    if not str(meta.get("title_ko", "")).strip():
        errors.append("title_ko is required")
    seo_description = str(meta.get("seo_description_ko", "")).strip()
    if not seo_description:
        errors.append("seo_description_ko is required")
    elif "\n" in seo_description or "\r" in seo_description:
        errors.append("seo_description_ko must be one line")
    elif len(seo_description) < 20:
        errors.append("seo_description_ko is too short")
    elif len(seo_description) > 220:
        errors.append("seo_description_ko is too long")
    if not isinstance(meta.get("publish"), bool):
        errors.append("publish must be boolean")
    source_url = str(meta.get("source_url", "")).strip()
    if source_url:
        parsed_source_url = urlparse(source_url)
        if parsed_source_url.scheme != "https" or not parsed_source_url.netloc:
            errors.append("source_url must be an absolute https URL")
        if meta.get("publish") is not True:
            errors.append("source_url binding requires publish=true for an existing live post")
    if args.require_draft and meta.get("publish") is not False:
        errors.append("develop/Draft workflow requires publish=false")
    if not isinstance(meta.get("labels", []), list):
        errors.append("labels must be a list")

    locale_names = set(config.get("locales", {}))
    permalink_slugs = meta.get("permalink_slugs", {})
    if permalink_slugs in (None, ""):
        permalink_slugs = {}
    if not isinstance(permalink_slugs, dict):
        errors.append("permalink_slugs must be an object keyed by locale")
        permalink_slugs = {}
    else:
        for locale, value in permalink_slugs.items():
            slug_value = str(value).strip()
            if locale not in locale_names:
                errors.append(f"permalink_slugs contains unknown locale: {locale}")
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", slug_value):
                errors.append(
                    f"invalid permalink slug for {locale}: {slug_value!r}"
                )

    recreate_permalink_locales = meta.get("recreate_permalink_locales", [])
    if not isinstance(recreate_permalink_locales, list):
        errors.append("recreate_permalink_locales must be a list")
    else:
        for locale in recreate_permalink_locales:
            if locale not in locale_names:
                errors.append(
                    f"recreate_permalink_locales contains unknown locale: {locale}"
                )
            if locale not in permalink_slugs:
                errors.append(
                    f"recreate_permalink_locales requires permalink_slugs entry: {locale}"
                )

    if category == "notice":
        notice_type = str(meta.get("notice_type", "")).strip()
        if notice_type not in NOTICE_TYPES:
            errors.append(
                "notice_type must be one of: " + ", ".join(sorted(NOTICE_TYPES))
            )
        release_version = str(meta.get("release_version", "")).strip()
        if release_version and not VERSION_RE.fullmatch(release_version):
            errors.append("release_version must use semantic version format, e.g. 10.0.0")

    errors.extend(validate_html(source_path, source=True))

    if args.all_locales:
        titles_path = item / "titles.json"
        descriptions_path = item / "descriptions.json"
        if not titles_path.exists():
            errors.append(f"missing {titles_path}")
        if not descriptions_path.exists():
            errors.append(f"missing {descriptions_path}")
        if titles_path.exists() and descriptions_path.exists():
            titles = json.loads(titles_path.read_text(encoding="utf-8"))
            descriptions = json.loads(descriptions_path.read_text(encoding="utf-8"))
            source = source_path.read_text(encoding="utf-8")
            for locale in config["locales"]:
                body = item / f"{locale}.html"
                if not body.exists():
                    errors.append(f"missing localized body: {body}")
                    continue
                if locale not in titles or not str(titles[locale]).strip():
                    errors.append(f"missing localized title: {locale}")
                description = str(descriptions.get(locale, "")).strip()
                if not description:
                    errors.append(f"missing localized search description: {locale}")
                elif "\n" in description or "\r" in description:
                    errors.append(f"localized search description must be one line: {locale}")
                elif len(description) < 20:
                    errors.append(f"localized search description is too short: {locale}")
                elif len(description) > 220:
                    errors.append(f"localized search description is too long: {locale}")
                errors.extend(validate_html(body, source=(locale == "ko")))
                if locale != "ko":
                    try:
                        expected_source = apply_localized_media(item, source, locale)
                        expected_source = apply_localized_post_links(expected_source, locale)
                        assert_structure(expected_source, body.read_text(encoding="utf-8"))
                    except ValueError as exc:
                        errors.append(f"{body}: {exc}")

    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors), file=sys.stderr)
        return 1
    print(f"[OK] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
