"""Apply explicit per-item media overrides without changing unrelated links."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def apply_localized_media(item: Path, content: str, locale: str) -> str:
    path = item / "media.json"
    if not path.exists():
        return content
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError(f"Unsupported media manifest: {path}")
    for entry in manifest["images"]:
        target = entry.get("locales", {}).get(locale)
        if target is None:
            continue
        for key in ("src", "href"):
            parsed = urlparse(target[key])
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"Media {key} must be HTTPS: {path}")
        if not target["alt"].strip():
            raise ValueError(f"Missing localized media alt: {path}/{locale}")

        def replace_tag(match: re.Match[str]) -> str:
            tag = match.group(0)
            attr = "src" if tag.lower().startswith("<img") else "href"
            original = entry["source"][attr]
            value = re.search(rf'\b{attr}="([^"]*)"', tag)
            if not value or html.unescape(value.group(1)) not in (original, target[attr]):
                return tag
            tag = re.sub(rf'\b{attr}="[^"]*"', f'{attr}="{html.escape(target[attr], quote=True)}"', tag)
            if attr == "src":
                for name, new_value in (("alt", target["alt"]), ("data-original-width", target["width"]), ("data-original-height", target["height"])):
                    rendered = f'{name}="{html.escape(str(new_value), quote=True)}"'
                    if re.search(rf'\b{name}="[^"]*"', tag):
                        tag = re.sub(rf'\b{name}="[^"]*"', lambda _: rendered, tag)
                    else:
                        tag = tag.replace("<img", "<img " + rendered, 1)
            return tag

        content = re.sub(r'<(?:img|a)\b[^>]*>', replace_tag, content, flags=re.I)
    return content
