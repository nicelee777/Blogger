#!/usr/bin/env python3
"""Check known obsolete FAQ/Guide claims before translation and publication.

Rules must be revised as part of every release editorial review.
This is a regression gate for recorded stale phrases, not AI fact-checking.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "template"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template"}:
            self.hidden_depth = max(0, self.hidden_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def visible_text(source: str) -> str:
    parser = VisibleTextParser()
    parser.feed(source)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def relevant_section(source: str, section_id: str) -> str:
    match = re.search(
        r'<details\b[^>]*\bid=["\']' + re.escape(section_id) +
        r'["\'][^>]*>[\s\S]*?</details>',
        source,
        re.I,
    )
    return match.group(0) if match else ""


def scan_document(source: str, page_type: str, locale: str, rules: list[dict]) -> list[str]:
    failures: list[str] = []
    # Check all locales for both unused CSS and retired markup.
    if page_type == "faq" and "sm-faq-update" in source:
        failures.append("retired feature-announcement markup/CSS still present")
    for rule in rules:
        if rule["type"] not in (page_type, "both") or rule["locale"] != locale:
            continue
        section = relevant_section(source, rule["section"]) if rule.get("section") else source
        if rule.get("section") and not section:
            failures.append(f'{rule["id"]}: required FAQ section is missing')
            continue
        match = re.search(rule["pattern"], visible_text(section), re.I)
        if match:
            failures.append(f'{rule["id"]}: {rule["message"]} ({match.group(0)!r})')
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", type=Path, default=Path("blogger/content-freshness-rules.json"))
    ap.add_argument("--root", type=Path, default=Path("blogger"))
    args = ap.parse_args()
    rules = json.loads(args.rules.read_text(encoding="utf-8"))["rules"]
    failures = []
    checked = 0
    for page_type in ("faq", "guide"):
        for path in sorted((args.root / page_type).glob("*.html")):
            checked += 1
            source = path.read_text(encoding="utf-8")
            for message in scan_document(source, page_type, path.stem, rules):
                failures.append(f"{path}: {message}")
    for message in failures:
        print("FAIL " + message)
    if failures:
        return 1
    print(f"OK: {checked} FAQ/Guide files checked for known stale release copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
