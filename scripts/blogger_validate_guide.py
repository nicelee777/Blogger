#!/usr/bin/env python3
"""Validate localized ShiftMate Blogger Guide Page HTML."""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.aria_refs: list[str] = []
        self.media_sources: list[tuple[str, str]] = []
        self.search_attrs: list[str] = []
        self.data_titles: list[str] = []
        self.placeholders: list[str] = []
        self.video_buttons: list[tuple[str, bool]] = []
        self.guide_root_found = False
        self.guide_root_lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = (attr.get("class") or "").split()
        if (
            not self.guide_root_found
            and tag.lower() == "article"
            and "sm-guide" in classes
            and (attr.get("data-shiftmate-guide") or "").lower() == "true"
        ):
            self.guide_root_found = True
            self.guide_root_lang = attr.get("lang") or ""

        if attr.get("id"):
            self.ids.append(attr["id"] or "")
        if attr.get("href"):
            self.hrefs.append(attr["href"] or "")
        if attr.get("aria-labelledby"):
            self.aria_refs.extend((attr["aria-labelledby"] or "").split())
        if tag in {"img", "iframe", "video", "source"} and attr.get("src"):
            self.media_sources.append((tag, attr["src"] or ""))
        if "data-search" in attr:
            self.search_attrs.append(attr.get("data-search") or "")
        if "data-title" in attr:
            self.data_titles.append(attr.get("data-title") or "")
        if "placeholder" in attr:
            self.placeholders.append(attr.get("placeholder") or "")
        if tag.lower() == "button" and "sm-guide-video" in classes:
            self.video_buttons.append(
                (attr.get("data-video-id") or "", "hidden" in attr)
            )


def style_blocks(text: str) -> list[str]:
    return re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.I | re.S)


def inspect(path: Path) -> tuple[str, Inspector]:
    text = path.read_text(encoding="utf-8")
    parser = Inspector()
    parser.feed(text)
    return text, parser


def validate(
    path: Path,
    expected_lang: str | None = None,
    expected_faq_path: str | None = None,
) -> dict:
    text, parser = inspect(path)
    errors: list[str] = []

    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicates:
        errors.append("duplicate id(s): " + ", ".join(duplicates))

    ids = set(parser.ids)
    for href in parser.hrefs:
        if href.startswith("#") and href[1:] not in ids:
            errors.append(f"broken internal link: {href}")
    for ref in parser.aria_refs:
        if ref not in ids:
            errors.append(f"broken aria-labelledby reference: {ref}")

    if expected_faq_path:
        for href in parser.hrefs:
            parsed = urlparse(href)
            if parsed.path.startswith("/p/faq") and parsed.path != expected_faq_path:
                errors.append(
                    f"localized FAQ link must target {expected_faq_path}: {href}"
                )

    if not parser.guide_root_found:
        errors.append(
            'Guide root must be <article class="sm-guide" data-shiftmate-guide="true" ...>'
        )
    elif expected_lang and parser.guide_root_lang != expected_lang:
        errors.append(
            f'root .sm-guide lang must be "{expected_lang}" '
            f'(found "{parser.guide_root_lang}")'
        )

    for name, values in (
        ("data-search", parser.search_attrs),
        ("data-title", parser.data_titles),
        ("placeholder", parser.placeholders),
    ):
        if any(not value.strip() for value in values):
            errors.append(f"empty localized {name} value")

    for index, (video_id, hidden) in enumerate(parser.video_buttons, start=1):
        if not video_id.strip() and not hidden:
            errors.append(
                f"Guide video button #{index} has no data-video-id and must be hidden"
            )
        if video_id.strip() and hidden:
            errors.append(
                f"Guide video button #{index} has a data-video-id and must not be hidden"
            )

    return {
        "file": str(path),
        "ok": not errors,
        "errors": errors,
        "_ids": parser.ids,
        "_styles": style_blocks(text),
        "_media": parser.media_sources,
        "_search_count": len(parser.search_attrs),
        "_title_count": len(parser.data_titles),
        "_placeholder_count": len(parser.placeholders),
        "_video_buttons": parser.video_buttons,
    }


def cross_validate(reports: list[dict]) -> None:
    source = next((r for r in reports if Path(r["file"]).stem == "ko"), None)
    if not source:
        return

    for report in reports:
        if report is source:
            continue
        if report["_ids"] != source["_ids"]:
            report["errors"].append("ID list/order differs from ko source")
        if report["_styles"] != source["_styles"]:
            report["errors"].append("CSS/style blocks differ from ko source")
        if report["_media"] != source["_media"]:
            report["errors"].append("media source URLs/order differ from ko source")
        if report["_search_count"] != source["_search_count"]:
            report["errors"].append("data-search attribute count differs from ko source")
        if report["_title_count"] != source["_title_count"]:
            report["errors"].append("data-title attribute count differs from ko source")
        if report["_placeholder_count"] != source["_placeholder_count"]:
            report["errors"].append("placeholder attribute count differs from ko source")
        if report["_video_buttons"] != source["_video_buttons"]:
            report["errors"].append("Guide video button IDs/visibility differ from ko source")
        report["ok"] = not report["errors"]


def public(report: dict) -> dict:
    return {k: v for k, v in report.items() if not k.startswith("_")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    locale_by_name: dict[str, str] = {}
    faq_path_by_name: dict[str, str] = {}
    if args.config.exists():
        config = json.loads(args.config.read_text(encoding="utf-8"))
        locale_by_name = {
            key: value.get("html_lang", key)
            for key, value in config.get("locales", {}).items()
        }
        faq_path_by_name = {
            key: value.get("faq_path", "")
            for key, value in config.get("locales", {}).items()
        }

    reports = [
        validate(
            path,
            locale_by_name.get(path.stem),
            faq_path_by_name.get(path.stem),
        )
        for path in args.paths
    ]
    cross_validate(reports)

    if args.json:
        print(json.dumps([public(r) for r in reports], ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"[{'OK' if report['ok'] else 'FAIL'}] {report['file']}")
            for error in report["errors"]:
                print("  - " + error)

    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
