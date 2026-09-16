#!/usr/bin/env python3
"""Validate localized ShiftMate Blogger Guide Page HTML."""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.aria_refs: list[str] = []
        self.media_sources: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"] or "")
        if attr.get("href"):
            self.hrefs.append(attr["href"] or "")
        if attr.get("aria-labelledby"):
            self.aria_refs.extend((attr["aria-labelledby"] or "").split())
        if tag in {"img", "iframe", "video", "source"} and attr.get("src"):
            self.media_sources.append((tag, attr["src"] or ""))


def style_blocks(text: str) -> list[str]:
    return re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.I | re.S)


def inspect(path: Path) -> tuple[str, Inspector]:
    text = path.read_text(encoding="utf-8")
    parser = Inspector()
    parser.feed(text)
    return text, parser


def validate(path: Path, expected_lang: str | None = None) -> dict:
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

    if "shiftmate-guide" not in text:
        errors.append(".shiftmate-guide root marker is missing")

    if expected_lang:
        patterns = [
            rf'class=["\'][^"\']*shiftmate-guide[^"\']*["\'][^>]*\blang=["\']{re.escape(expected_lang)}["\']',
            rf'\blang=["\']{re.escape(expected_lang)}["\'][^>]*class=["\'][^"\']*shiftmate-guide',
        ]
        if not any(re.search(pattern, text, re.I) for pattern in patterns):
            errors.append(f'root .shiftmate-guide lang must be "{expected_lang}"')

    return {
        "file": str(path),
        "ok": not errors,
        "errors": errors,
        "_ids": parser.ids,
        "_styles": style_blocks(text),
        "_media": parser.media_sources,
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
    if args.config.exists():
        config = json.loads(args.config.read_text(encoding="utf-8"))
        locale_by_name = {
            key: value.get("html_lang", key)
            for key, value in config.get("locales", {}).items()
        }

    reports = [validate(path, locale_by_name.get(path.stem)) for path in args.paths]
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
