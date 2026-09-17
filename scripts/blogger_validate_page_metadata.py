#!/usr/bin/env python3
"""Validate Git-managed metadata for Blogger static Pages."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page_type")
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    page_cfg = config.get("page_types", {}).get(args.page_type)
    if not page_cfg:
        print(f"ERROR: unsupported page type: {args.page_type}", file=sys.stderr)
        return 2

    metadata_path = page_cfg.get("search_descriptions")
    if not metadata_path:
        print(f"[{args.page_type}] no search-description metadata configured")
        return 0

    path = Path(str(metadata_path))
    if not path.exists():
        print(f"ERROR: missing search descriptions: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    locales = config.get("locales", {})

    for locale in locales:
        value = data.get(locale)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{locale}: missing search description")
            continue
        text = value.strip()
        if "\n" in text or "\r" in text:
            errors.append(f"{locale}: search description must be one line")
        if re.search(r"<[^>]+>", text):
            errors.append(f"{locale}: search description must not contain HTML")
        if len(text) < 20:
            errors.append(f"{locale}: search description is too short ({len(text)} chars)")
        if len(text) > 220:
            errors.append(f"{locale}: search description is too long ({len(text)} chars)")

    extras = sorted(set(data) - set(locales))
    if extras:
        errors.append("unknown locale key(s): " + ", ".join(extras))

    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        return 1

    print(f"[OK] {args.page_type} search descriptions: {path}")
    if args.show:
        for locale in locales:
            print(f"[{locale}] {data[locale].strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
