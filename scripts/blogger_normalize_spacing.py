#!/usr/bin/env python3
"""Normalize spacing around inline formatting tags in Latin-script locales.

Korean source text can attach grammatical particles directly after inline tags,
for example ``<strong>...</strong>는``. When translated segment-by-segment into
English, Spanish, or Vietnamese, the following word can remain attached to the
closing tag (``</strong>is``). This post-process fixes only that boundary while
leaving markup, URLs, CSS, IDs, and non-Latin locales untouched.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LATIN_LOCALES = {"en", "es", "vi"}
INLINE_TAGS = "strong|em|span|a"
# Latin letters, extended Latin (incl. Vietnamese), and digits.
LATIN_WORD_START = r"A-Za-zÀ-ÖØ-öø-ÿĀ-žẠ-ỹ0-9"
AFTER_INLINE_RE = re.compile(
    rf"</(?P<tag>{INLINE_TAGS})>(?=[{LATIN_WORD_START}])",
    flags=re.I,
)


def normalize_text(text: str) -> str:
    return AFTER_INLINE_RE.sub(lambda m: f"</{m.group('tag')}> ", text)


def locale_for_file(path: Path) -> str | None:
    stem = path.stem.lower()
    return stem if stem in LATIN_LOCALES else None


def iter_html(paths: list[Path]):
    seen: set[Path] = set()
    for root in paths:
        if root.is_file() and root.suffix.lower() == ".html":
            candidates = [root]
        elif root.is_dir():
            candidates = root.rglob("*.html")
        else:
            continue
        for path in candidates:
            path = path.resolve()
            if path not in seen:
                seen.add(path)
                yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("blogger/faq"), Path("blogger/guide"), Path("blogger/posts")],
    )
    args = parser.parse_args()

    changed = 0
    checked = 0
    for path in iter_html(args.paths):
        if locale_for_file(path) is None:
            continue
        checked += 1
        original = path.read_text(encoding="utf-8")
        normalized = normalize_text(original)
        if normalized != original:
            path.write_text(normalized, encoding="utf-8")
            changed += 1
            print(f"[FIX] {path}")
        else:
            print(f"[OK]  {path}")

    print(f"Localized spacing: checked={checked} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
