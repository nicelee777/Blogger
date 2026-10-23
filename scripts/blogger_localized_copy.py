"""Apply reviewed locale-specific text while preserving the Korean source and HTML."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


def apply_localized_copy(item: Path, content: str, locale: str) -> str:
    path = item / "copy.json"
    if not path.exists():
        return content
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError(f"Unsupported localized copy manifest: {path}")
    source = (item / "ko.html").read_text(encoding="utf-8")
    replacements = []
    seen = set()
    for block in manifest["blocks"]:
        tag, index = block["tag"], block["index"]
        if tag not in {"p", "h2", "h3"} or type(index) is not int or index < 0:
            raise ValueError(f"Invalid localized copy selector: {path}")
        if (tag, index) in seen:
            raise ValueError(f"Duplicate localized copy selector: {path}")
        seen.add((tag, index))
        pattern = rf"(<{tag}\b[^>]*>)(.*?)(</{tag}\s*>)"
        original = list(re.finditer(pattern, source, re.S | re.I))
        targets = list(re.finditer(pattern, content, re.S | re.I))
        if index >= len(original) or index >= len(targets):
            raise ValueError(f"Missing localized copy block: {path}/{tag}/{index}")
        if html.unescape(original[index][2]) != block["source_text"]:
            raise ValueError(f"Korean copy changed; review locale override: {path}/{tag}/{index}")
        if locale == "ko" or locale not in block["locales"]:
            continue
        text = block["locales"][locale]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Missing locale copy: {path}/{locale}")
        target = targets[index]
        if "<" in target[2]:
            raise ValueError(f"Locale copy must target a text-only block: {path}")
        replacements.append((target.start(2), target.end(2), html.escape(text, quote=False)))
    for start, end, value in sorted(replacements, reverse=True):
        content = content[:start] + value + content[end:]
    return content
