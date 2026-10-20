"""Localize ShiftMate store URLs in Blogger HTML, preserving other links."""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ANCHOR = re.compile(r'<a\b[^>]*>', re.I | re.S)
HREF = re.compile(r"(\bhref\s*=\s*)([\"'])(.*?)\2", re.I | re.S)

def localize_store_links(content: str, locale: str, config: dict) -> str:
    urls = config["store_links"][locale]
    def rewrite(match):
        tag = match.group(0)
        def replace(m):
            raw = html.unescape(m.group(3))
            parsed = urlsplit(raw)
            host = (parsed.hostname or "").lower()
            if host == "apps.apple.com" and "/app/" in parsed.path:
                target = urls["app_store_url"]
            elif host == "play.google.com" and parsed.path == "/store/apps/details" and "id=juho.interrobang.yjdiary2" in parsed.query:
                target = urls["google_play_url"]
            else:
                return m.group(0)
            return m.group(1) + m.group(2) + html.escape(target, quote=True) + m.group(2)
        return HREF.sub(replace, tag, count=1)
    return ANCHOR.sub(rewrite, content)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("blogger/posts"))
    parser.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    updated = 0
    for path in args.root.glob("*/*/*.html"):
        locale = path.stem
        if locale not in config["store_links"]:
            continue
        original = path.read_text(encoding="utf-8")
        modified = localize_store_links(original, locale, config)
        if modified != original:
            path.write_text(modified, encoding="utf-8")
            updated += 1
    print(f"Localized store links in {updated} files")

if __name__ == "__main__":
    main()
