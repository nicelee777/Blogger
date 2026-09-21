#!/usr/bin/env python3
"""Regression checks for the GitHub-managed ShiftMate Blogger theme runtime."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "runtime",
        nargs="?",
        type=Path,
        default=Path("blogger/theme/shiftmate-menu-runtime-v6.js"),
    )
    args = ap.parse_args()
    text = args.runtime.read_text(encoding="utf-8")

    errors: list[str] = []
    if re.search(r"return\s+v\s*\+\s*['\"]\?sm-lang=", text):
        errors.append("runtime must not generate ?sm-lang Page URLs")
    for required in (
        "cleanLegacyPageUrl",
        "syncPageSeo",
        "history.replaceState",
        "hreflang",
        "x-default",
        "localStorage",
    ):
        if required not in text:
            errors.append(f"missing required theme behavior: {required}")

    for path in (
        "/p/faq-ko.html",
        "/p/guide-ko.html",
        "/p/faq.html",
        "/p/guide.html",
    ):
        if path not in text:
            errors.append(f"missing canonical Page path: {path}")

    if errors:
        print(f"[FAIL] {args.runtime}")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"[OK] {args.runtime}: clean Page URLs + canonical/hreflang safeguards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
