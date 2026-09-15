#!/usr/bin/env python3
"""Validate ShiftMate Blogger FAQ HTML before translation or publishing."""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

REQUIRED_FAQ_IDS = {
    "toc",
    "work",
    "alarm",
    "data",
    "calendar",
    "link",
    "platform",
    "etc",
    "help",
    "faq-long-shift-name",
}


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.aria_refs: list[str] = []
        self.details = 0
        self.summaries = 0
        self.mailtos: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "details":
            self.details += 1
        if tag == "summary":
            self.summaries += 1
        if attr.get("id"):
            self.ids.append(attr["id"] or "")
        if attr.get("href"):
            href = attr["href"] or ""
            self.hrefs.append(href)
            if href.startswith("mailto:"):
                self.mailtos.append(href)
        if attr.get("aria-labelledby"):
            self.aria_refs.extend((attr["aria-labelledby"] or "").split())


def style_blocks(text: str) -> list[str]:
    return re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.I | re.S)


def inspect(path: Path) -> tuple[str, Inspector]:
    text = path.read_text(encoding="utf-8")
    parser = Inspector()
    parser.feed(text)
    return text, parser


def validate_faq(path: Path, expected_lang: str | None = None) -> dict:
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

    missing = sorted(REQUIRED_FAQ_IDS - ids)
    if missing:
        errors.append("missing required id(s): " + ", ".join(missing))
    if parser.details < 10:
        errors.append(f"too few FAQ details blocks: {parser.details}")
    if parser.details != parser.summaries:
        errors.append(
            f"details/summary count mismatch: {parser.details}/{parser.summaries}"
        )
    if not parser.mailtos:
        errors.append("support mailto link is missing")
    if "shiftmate-faq" not in text:
        errors.append(".shiftmate-faq root/style marker is missing")

    if expected_lang:
        patterns = [
            rf'class=["\'][^"\']*shiftmate-faq[^"\']*["\'][^>]*\blang=["\']{re.escape(expected_lang)}["\']',
            rf'\blang=["\']{re.escape(expected_lang)}["\'][^>]*class=["\'][^"\']*shiftmate-faq',
        ]
        if not any(re.search(pattern, text, re.I) for pattern in patterns):
            errors.append(f'root .shiftmate-faq lang must be "{expected_lang}"')

    return {
        "file": str(path),
        "ok": not errors,
        "details": parser.details,
        "ids": len(parser.ids),
        "errors": errors,
        "_id_set": ids,
        "_id_list": parser.ids,
        "_styles": style_blocks(text),
    }


def cross_validate(reports: list[dict]) -> None:
    """Ensure localized FAQs retain the same stable structure as Korean source."""
    source = next((report for report in reports if Path(report["file"]).stem == "ko"), None)
    if not source:
        return

    for report in reports:
        if report is source:
            continue
        if report["_id_set"] != source["_id_set"]:
            missing = sorted(source["_id_set"] - report["_id_set"])
            extra = sorted(report["_id_set"] - source["_id_set"])
            if missing:
                report["errors"].append("IDs missing vs ko: " + ", ".join(missing))
            if extra:
                report["errors"].append("extra IDs vs ko: " + ", ".join(extra))
        if report["_id_list"] != source["_id_list"]:
            report["errors"].append("ID order differs from ko source")
        if report["_styles"] != source["_styles"]:
            report["errors"].append("CSS/style blocks differ from ko source")
        report["ok"] = not report["errors"]


def public_report(report: dict) -> dict:
    return {key: value for key, value in report.items() if not key.startswith("_")}


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

    reports = [
        validate_faq(path, locale_by_name.get(path.stem)) for path in args.paths
    ]
    cross_validate(reports)

    if args.json:
        print(
            json.dumps(
                [public_report(report) for report in reports],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for report in reports:
            print(
                f"[{'OK' if report['ok'] else 'FAIL'}] {report['file']} "
                f"details={report['details']} ids={report['ids']}"
            )
            for error in report["errors"]:
                print("  - " + error)

    return 0 if all(report["ok"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
