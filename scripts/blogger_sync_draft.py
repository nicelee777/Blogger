#!/usr/bin/env python3
"""Create/update Blogger drafts for one managed Notice/Story item without touching live posts."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

from blogger_sync import (
    BLOGGER_API,
    access_token,
    content_marker,
    get_blog,
    http_json,
    list_all_posts,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    item = args.item
    meta_path = item / "meta.json"
    titles_path = item / "titles.json"
    if not meta_path.exists() or not titles_path.exists():
        print(f"ERROR: missing meta/titles for {item}", file=sys.stderr)
        return 1

    config = json.loads(args.config.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    titles = json.loads(titles_path.read_text(encoding="utf-8"))
    category = str(meta.get("category") or item.parent.name)
    slug = str(meta.get("slug") or item.name)
    if category not in config.get("post_categories", {}):
        print(f"ERROR: unsupported post category: {category}", file=sys.stderr)
        return 1

    token = access_token()
    blog = get_blog(token, config["blog_url"])
    blog_id = str(blog["id"])
    remote_posts = list_all_posts(token, blog_id, fetch_bodies=True)
    category_label = config["post_categories"][category]
    base_labels = list(meta.get("labels", []))

    print(f"Draft sync: {category}/{slug} -> {blog.get('name')} ({blog_id})")
    if meta.get("publish") is True:
        print("NOTICE: publish=true is ignored by develop draft sync; production publication remains main-only.")

    for locale, info in config["locales"].items():
        body_path = item / f"{locale}.html"
        if not body_path.exists():
            raise RuntimeError(f"missing localized body: {body_path}")
        if locale not in titles:
            raise RuntimeError(f"missing localized title {locale}: {titles_path}")

        marker = content_marker(category, slug, locale)
        content = marker + "\n" + body_path.read_text(encoding="utf-8")
        matches = [p for p in remote_posts if marker in (p.get("content") or "")]
        if len(matches) > 1:
            raise RuntimeError(f"duplicate remote Blogger posts for {marker}")

        labels: list[str] = []
        for label in [category_label, info["language_label"], *base_labels]:
            if label and label not in labels:
                labels.append(label)
        payload = {"title": titles[locale], "content": content, "labels": labels}

        if matches:
            post = matches[0]
            status = str(post.get("status", "")).lower()
            if status in {"live", "scheduled"}:
                print(
                    f"[{locale}] canonical post {post['id']} is {status}; "
                    "develop draft preview skipped to avoid changing a public post."
                )
                continue
            print(f"[{locale}] update existing draft {post['id']} -> {titles[locale]}")
            if not args.dry_run:
                updated = http_json(
                    f"{BLOGGER_API}/blogs/{blog_id}/posts/{post['id']}",
                    method="PATCH",
                    token=token,
                    body=payload,
                )
                post.update(updated)
        else:
            print(f"[{locale}] create draft -> {titles[locale]}")
            if not args.dry_run:
                endpoint = (
                    f"{BLOGGER_API}/blogs/{blog_id}/posts?"
                    + urllib.parse.urlencode({"isDraft": "true"})
                )
                created = http_json(endpoint, method="POST", token=token, body=payload)
                remote_posts.append(created)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
