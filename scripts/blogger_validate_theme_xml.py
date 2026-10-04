#!/usr/bin/env python3
"""Validate the committed complete ShiftMate Blogger theme XML."""
from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_RE = re.compile(
    r"(?P<open><script\s+id=(?P<q>['\"])shiftmate-menu-runtime(?P=q)[^>]*>\s*)"
    r"(?P<body>.*?)"
    r"(?P<close>\s*</script>)",
    flags=re.I | re.S,
)

LABEL_DATA_SINGLE_RE = re.compile(
    r"<b:if cond=['\"]data:view\.isSingleItem and data:widget\.type == &quot;Blog&quot;['\"]>"
    r"\s*<span aria-hidden=['\"]true['\"] class=['\"]sm-post-language-data['\"]",
    flags=re.I,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--theme",
        type=Path,
        default=Path("blogger/theme/shiftmate-theme.xml"),
    )
    ap.add_argument(
        "--runtime",
        type=Path,
        default=Path("blogger/theme/shiftmate-menu-runtime-v6.js"),
    )
    args = ap.parse_args()

    errors: list[str] = []
    if not args.theme.exists():
        errors.append(f"missing committed theme: {args.theme}")
    if not args.runtime.exists():
        errors.append(f"missing canonical runtime: {args.runtime}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    theme = args.theme.read_text(encoding="utf-8")
    runtime = args.runtime.read_text(encoding="utf-8").strip()

    try:
        ET.fromstring(theme.encode("utf-8"))
    except ET.ParseError as exc:
        errors.append(f"theme XML parse failed: {exc}")

    matches = list(SCRIPT_RE.finditer(theme))
    if len(matches) != 1:
        errors.append(
            f"expected exactly one shiftmate-menu-runtime script, found {len(matches)}"
        )
    else:
        embedded = html.unescape(matches[0].group("body")).strip()
        if embedded != runtime:
            errors.append(
                "committed theme runtime differs from "
                "blogger/theme/shiftmate-menu-runtime-v6.js"
            )

    for required in (
        "ShiftMate Blogger theme v1.2.2",
        "syncPostSeo",
        "article:published_time",
        "twitter:card",
        "sm-notice-badge-type-incident",
        "sm-notice-badge-type-maintenance",
        "sm-notice-badge-type-feature",
        "sm-notice-badge-type-service",
        "sm-notice-badge-type-policy",
        "data:widget.type == &quot;Blog&quot;",
        "sm-post-language-data",
    ):
        if required not in theme:
            errors.append(f"committed theme is missing required marker: {required}")

    if LABEL_DATA_SINGLE_RE.search(theme):
        errors.append("post label data must be available on feed pages, not only single items")

    if errors:
        print(f"[FAIL] {args.theme}")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"[OK] {args.theme}: XML parsed; embedded runtime matches canonical source"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
