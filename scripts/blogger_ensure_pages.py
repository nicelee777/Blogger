#!/usr/bin/env python3
"""Ensure configured ShiftMate Blogger Pages exist before content sync.

Existing Pages are never recreated. Missing localized Pages are created from the
configured source file. The generated Blogger URL is verified immediately; if
Blogger does not create the expected path, the new Page is deleted and the run
fails instead of leaving an incorrectly addressed Page behind.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Any

from blogger_sync import (
    BLOGGER_API,
    access_token,
    get_blog,
    http_json,
    list_collection,
    url_path,
)


def expected_title(target_path: str) -> str:
    """Use the requested permalink stem as the initial Blogger Page title."""
    name = Path(urllib.parse.urlparse(target_path).path).name
    return name.removesuffix(".html") or "shiftmate-page"


def ensure_pages(config: dict[str, Any], *, dry_run: bool) -> None:
    token = access_token()
    blog = get_blog(token, str(config["blog_url"]))
    blog_id = str(blog["id"])
    pages = list_collection(token, blog_id, "pages", status="live")
    by_path = {url_path(str(page.get("url", ""))): page for page in pages}

    print(f"Blog: {blog.get('name')} ({blog_id}), existing pages={len(pages)}")

    for page_type, page_cfg in config.get("page_types", {}).items():
        directory = Path(str(page_cfg["directory"]))
        path_key = str(page_cfg["path_key"])
        create_missing = bool(page_cfg.get("create_missing_pages", False))
        source_locale = str(config.get("source_locale", "ko"))

        if not (directory / f"{source_locale}.html").exists():
            if bool(page_cfg.get("required", False)):
                raise RuntimeError(f"missing required {page_type} source: {directory}/{source_locale}.html")
            print(f"[{page_type}] source absent; skipped")
            continue

        for locale, info in config.get("locales", {}).items():
            target = str(info.get(path_key, "")).strip()
            source = directory / f"{locale}.html"
            if not target:
                raise RuntimeError(f"{page_type}/{locale}: missing {path_key}")
            if not source.exists():
                raise RuntimeError(f"{page_type}/{locale}: missing localized source {source}")

            wanted = target.rstrip("/") or "/"
            if wanted in by_path:
                page = by_path[wanted]
                print(f"[{page_type}/{locale}] exists: {wanted} -> {page.get('id')}")
                continue

            if not create_missing:
                raise RuntimeError(f"{page_type}/{locale}: Blogger Page missing: {wanted}")

            if dry_run:
                print(f"[{page_type}/{locale}] would create: {wanted}")
                continue

            body = {
                "title": expected_title(wanted),
                "content": source.read_text(encoding="utf-8"),
            }
            created = http_json(
                f"{BLOGGER_API}/blogs/{blog_id}/pages?isDraft=false",
                method="POST",
                token=token,
                body=body,
            )
            created_id = str(created.get("id", ""))
            actual = url_path(str(created.get("url", "")))
            if actual != wanted:
                if created_id:
                    http_json(
                        f"{BLOGGER_API}/blogs/{blog_id}/pages/{created_id}",
                        method="DELETE",
                        token=token,
                    )
                raise RuntimeError(
                    f"{page_type}/{locale}: Blogger generated {actual!r}, expected {wanted!r}; "
                    "the incorrectly addressed Page was deleted"
                )

            by_path[wanted] = created
            print(f"[{page_type}/{locale}] created: {wanted} -> {created_id}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    ensure_pages(config, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
