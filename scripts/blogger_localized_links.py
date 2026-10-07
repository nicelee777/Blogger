"""Localize only registered Post links, preserving all other HTML and URLs."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

DEFAULT_REGISTRY = Path("blogger/post-links.json")
ANCHOR_RE = re.compile(r'''<a\b(?:[^>"']|"[^"]*"|'[^']*')*>''', re.I)
ATTRIBUTE_RE = re.compile(r'''(?P<prefix>\s+(?P<name>[^\s=/>]+)\s*=\s*)(?P<quote>["'])(?P<url>.*?)(?P=quote)''', re.S)


def load_link_index(registry: Path) -> dict[str, dict[str, str]]:
    if not registry.exists():
        return {}
    data = json.loads(registry.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("posts"), dict):
        raise ValueError(f"Invalid Post link registry: {registry}")
    blog = urlsplit(data.get("blog_url", ""))
    if blog.scheme != "https" or not blog.netloc or blog.query or blog.fragment:
        raise ValueError(f"Invalid registry blog URL: {registry}")
    index: dict[str, dict[str, str]] = {}
    for content_id, targets in data["posts"].items():
        if not re.fullmatch(r"(?:story|notice)/[a-z0-9-]+", content_id):
            raise ValueError(f"Invalid content ID: {content_id}")
        if not isinstance(targets, dict) or not targets.get("ko"):
            raise ValueError(f"Missing Korean Post URL: {content_id}")
        for locale, url in targets.items():
            if not isinstance(url, str):
                raise ValueError(f"Invalid URL: {content_id}/{locale}")
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.netloc != blog.netloc or not parsed.path.endswith(".html") or parsed.query or parsed.fragment:
                raise ValueError(f"Invalid canonical Post URL: {content_id}/{locale}")
            if url in index:
                raise ValueError(f"Duplicate registered Post URL: {url}")
            index[url] = targets
    return index


def apply_localized_post_links(content: str, locale: str, registry: Path = DEFAULT_REGISTRY) -> str:
    index = load_link_index(registry)
    if not index:
        return content

    def replace_anchor(match: re.Match[str]) -> str:
        tag = match.group(0)
        href = next((attribute for attribute in ATTRIBUTE_RE.finditer(tag) if attribute["name"].lower() == "href"), None)
        if not href:
            return tag
        original = urlsplit(html.unescape(href["url"]))
        canonical = urlunsplit((original.scheme, original.netloc, original.path, "", ""))
        targets = index.get(canonical)
        if targets is None:
            return tag
        if not targets.get(locale):
            raise ValueError(f"Missing {locale} target for registered Post link: {canonical}")
        target = urlsplit(targets[locale])
        url = urlunsplit((target.scheme, target.netloc, target.path, original.query, original.fragment))
        return tag[:href.start("url")] + html.escape(url, quote=True) + tag[href.end("url"):]

    return ANCHOR_RE.sub(replace_anchor, content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("blogger/posts"))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    args = parser.parse_args()
    locales = json.loads(args.config.read_text(encoding="utf-8"))["locales"]
    updated = 0
    for meta in sorted(args.root.glob("*/*/meta.json")):
        for locale in locales:
            path = meta.parent / f"{locale}.html"
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            localized = apply_localized_post_links(source, locale, args.registry)
            if source != localized:
                path.write_text(localized, encoding="utf-8")
                updated += 1
    print(f"Localized registered Post links in {updated} HTML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
