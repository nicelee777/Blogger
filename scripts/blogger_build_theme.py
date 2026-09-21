#!/usr/bin/env python3
"""Build a paste-ready Blogger theme by embedding the GitHub-managed ShiftMate runtime."""
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

VERSION_RE = re.compile(
    r"ShiftMate Blogger theme v[^|]+\|\s*\d{4}-\d{2}-\d{2}\s*\|"
)


def escape_runtime(runtime: str) -> str:
    return html.escape(runtime.rstrip() + "\n", quote=True).replace("&#x27;", "&#39;")


def build(theme: str, runtime: str, version: str | None, date: str | None) -> str:
    matches = list(SCRIPT_RE.finditer(theme))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one shiftmate-menu-runtime script, found {len(matches)}"
        )

    match = matches[0]
    replacement = (
        match.group("open")
        + escape_runtime(runtime)
        + match.group("close")
    )
    result = theme[: match.start()] + replacement + theme[match.end() :]

    if version or date:
        if not (version and date):
            raise ValueError("--theme-version and --theme-date must be supplied together")
        result, count = VERSION_RE.subn(
            f"ShiftMate Blogger theme v{version} | {date} |",
            result,
            count=1,
        )
        if count != 1:
            raise ValueError("ShiftMate theme version header comment was not found")

    return result


def validate(result: str) -> None:
    match = SCRIPT_RE.search(result)
    if not match:
        raise ValueError("embedded runtime is missing")
    runtime = html.unescape(match.group("body"))

    if re.search(r"return\s+v\s*\+\s*['\"]\?sm-lang=", runtime):
        raise ValueError("runtime still generates ?sm-lang Page URLs")
    for required in ("cleanLegacyPageUrl", "syncPageSeo", "x-default"):
        if required not in runtime:
            raise ValueError(f"runtime is missing required SEO behavior: {required}")

    ET.fromstring(result.encode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Exported Blogger theme XML")
    ap.add_argument(
        "--runtime",
        type=Path,
        default=Path("blogger/theme/shiftmate-menu-runtime-v6.js"),
    )
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--theme-version")
    ap.add_argument("--theme-date")
    args = ap.parse_args()

    theme = args.input.read_text(encoding="utf-8")
    runtime = args.runtime.read_text(encoding="utf-8")
    result = build(theme, runtime, args.theme_version, args.theme_date)
    validate(result)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Wrote {args.output} ({len(result.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
