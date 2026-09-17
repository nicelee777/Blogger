#!/usr/bin/env python3
"""Merge optional QA glossary overrides into the working glossary file."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path("blogger/glossary.json")
OVERRIDES = Path("blogger/glossary-overrides.json")


def main() -> int:
    if not OVERRIDES.exists():
        print("No glossary overrides configured.")
        return 0

    base = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else {}
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))

    if not isinstance(base, dict) or not isinstance(overrides, dict):
        raise ValueError("glossary files must contain JSON objects")

    for locale, terms in overrides.items():
        if not isinstance(terms, dict):
            raise ValueError(f"override glossary for {locale} must be an object")
        target = base.setdefault(locale, {})
        if not isinstance(target, dict):
            raise ValueError(f"base glossary for {locale} must be an object")
        target.update({str(k): str(v) for k, v in terms.items()})

    BASE.write_text(
        json.dumps(base, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Applied glossary overrides from {OVERRIDES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
