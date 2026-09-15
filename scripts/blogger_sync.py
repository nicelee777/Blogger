#!/usr/bin/env python3
"""Publish ShiftMate GitHub-managed content to Blogger API v3."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
POST_STATUSES = ("live", "draft", "scheduled")


def http_json(url: str, method: str = "GET", token: str | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Blogger API error {exc.code} {method} {url}: {detail}") from exc


def access_token() -> str:
    required = ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"]
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise RuntimeError("missing Blogger OAuth secret(s): " + ", ".join(missing))

    data = urllib.parse.urlencode(
        {
            "client_id": os.environ["BLOGGER_CLIENT_ID"],
            "client_secret": os.environ["BLOGGER_CLIENT_SECRET"],
            "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"OAuth token refresh failed ({exc.code}): {exc.read().decode(errors='replace')}"
        ) from exc
    if not result.get("access_token"):
        raise RuntimeError("OAuth response has no access_token")
    return str(result["access_token"])


def get_blog(token: str, blog_url: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"url": blog_url})
    return http_json(f"{BLOGGER_API}/blogs/byurl?{query}", token=token)


def list_collection(
    token: str,
    blog_id: str,
    kind: str,
    *,
    fetch_bodies: bool = False,
    status: str | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        params: dict[str, Any] = {
            "fetchBodies": "true" if fetch_bodies else "false",
            "maxResults": 50,
            "view": "ADMIN",
        }
        if status:
            params["status"] = status
        if page_token:
            params["pageToken"] = page_token
        result = http_json(
            f"{BLOGGER_API}/blogs/{blog_id}/{kind}?{urllib.parse.urlencode(params)}",
            token=token,
        )
        items.extend(result.get("items", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            return items


def list_all_posts(token: str, blog_id: str, *, fetch_bodies: bool) -> list[dict[str, Any]]:
    """Fetch live, draft, and scheduled posts so managed drafts are idempotent."""
    by_id: dict[str, dict[str, Any]] = {}
    for status in POST_STATUSES:
        for post in list_collection(
            token, blog_id, "posts", fetch_bodies=fetch_bodies, status=status
        ):
            post_id = str(post.get("id", ""))
            if post_id:
                by_id[post_id] = post
    return list(by_id.values())


def url_path(url: str) -> str:
    path = urllib.parse.urlparse(url).path or "/"
    return path.rstrip("/") or "/"


def find_page_by_path(pages: list[dict[str, Any]], target_path: str) -> dict[str, Any]:
    wanted = target_path.rstrip("/") or "/"
    matches = [page for page in pages if url_path(page.get("url", "")) == wanted]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one Blogger page for {wanted}, found {len(matches)}"
        )
    return matches[0]


def sync_faq(config: dict[str, Any], token: str, dry_run: bool = False) -> None:
    blog = get_blog(token, config["blog_url"])
    blog_id = str(blog["id"])
    pages = list_collection(token, blog_id, "pages", status="live")
    print(f"Blog: {blog.get('name')} ({blog_id}), pages={len(pages)}")

    for locale, info in config["locales"].items():
        source = Path("blogger/faq") / f"{locale}.html"
        if not source.exists():
            raise RuntimeError(f"missing FAQ source file: {source}")
        page = find_page_by_path(pages, info["faq_path"])
        html = source.read_text(encoding="utf-8")
        print(
            f"[{locale}] {info['faq_path']} -> page {page['id']} "
            f"({page.get('title', '')})"
        )
        if not dry_run:
            http_json(
                f"{BLOGGER_API}/blogs/{blog_id}/pages/{page['id']}",
                method="PATCH",
                token=token,
                body={"content": html},
            )
            print("  updated")


def content_marker(category: str, slug: str, locale: str) -> str:
    return f"<!--shiftmate-content-id:{category}/{slug}/{locale}-->"


def reconcile_post_state(
    token: str,
    blog_id: str,
    post: dict[str, Any],
    *,
    should_publish: bool,
    dry_run: bool,
) -> dict[str, Any]:
    status = str(post.get("status", ""))
    post_id = str(post["id"])

    if should_publish and status != "live":
        print(f"  publication state: {status or 'unknown'} -> live")
        if dry_run:
            return {**post, "status": "live"}
        if status == "scheduled":
            http_json(
                f"{BLOGGER_API}/blogs/{blog_id}/posts/{post_id}/revert",
                method="POST",
                token=token,
            )
        return http_json(
            f"{BLOGGER_API}/blogs/{blog_id}/posts/{post_id}/publish",
            method="POST",
            token=token,
        )

    if not should_publish and status in {"live", "scheduled"}:
        print(f"  publication state: {status} -> draft")
        if dry_run:
            return {**post, "status": "draft"}
        return http_json(
            f"{BLOGGER_API}/blogs/{blog_id}/posts/{post_id}/revert",
            method="POST",
            token=token,
        )

    return post


def sync_posts(
    config: dict[str, Any],
    token: str,
    dry_run: bool = False,
    root: Path = Path("blogger/posts"),
) -> None:
    blog = get_blog(token, config["blog_url"])
    blog_id = str(blog["id"])
    remote_posts = list_all_posts(token, blog_id, fetch_bodies=True)
    meta_files = sorted(root.glob("*/*/meta.json"))
    print(
        f"Blog: {blog.get('name')} ({blog_id}), "
        f"remote posts={len(remote_posts)}, managed items={len(meta_files)}"
    )

    for meta_path in meta_files:
        item = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        category = meta.get("category") or item.parent.name
        slug = meta.get("slug") or item.name
        if category not in config.get("post_categories", {}):
            raise RuntimeError(f"unsupported category {category}: {meta_path}")

        titles_path = item / "titles.json"
        if not titles_path.exists():
            raise RuntimeError(f"missing titles.json: {titles_path}")
        titles = json.loads(titles_path.read_text(encoding="utf-8"))
        base_labels = list(meta.get("labels", []))
        category_label = config["post_categories"][category]
        should_publish = bool(meta.get("publish", False))

        for locale, info in config["locales"].items():
            body_path = item / f"{locale}.html"
            if not body_path.exists():
                raise RuntimeError(f"missing localized body: {body_path}")
            if locale not in titles:
                raise RuntimeError(f"missing localized title {locale}: {titles_path}")

            marker = content_marker(category, slug, locale)
            content = marker + "\n" + body_path.read_text(encoding="utf-8")
            matches = [
                post
                for post in remote_posts
                if marker in (post.get("content") or "")
            ]
            if len(matches) > 1:
                raise RuntimeError(f"duplicate remote Blogger posts for {marker}")

            labels: list[str] = []
            for label in [category_label, info["language_label"], *base_labels]:
                if label and label not in labels:
                    labels.append(label)
            payload = {
                "title": titles[locale],
                "content": content,
                "labels": labels,
            }

            if matches:
                post = matches[0]
                print(
                    f"[{category}/{slug}/{locale}] update post {post['id']} "
                    f"status={post.get('status', '?')} -> {titles[locale]}"
                )

                # If this managed item should be a draft, take a currently live/scheduled
                # post offline before updating its content to avoid a transient public edit.
                if not should_publish and str(post.get("status", "")) in {"live", "scheduled"}:
                    post = reconcile_post_state(
                        token,
                        blog_id,
                        post,
                        should_publish=False,
                        dry_run=dry_run,
                    )

                if not dry_run:
                    post = http_json(
                        f"{BLOGGER_API}/blogs/{blog_id}/posts/{post['id']}",
                        method="PATCH",
                        token=token,
                        body=payload,
                    )
                    matches[0].update(post)

                if should_publish:
                    reconcile_post_state(
                        token,
                        blog_id,
                        post,
                        should_publish=True,
                        dry_run=dry_run,
                    )
            else:
                target_state = "live" if should_publish else "draft"
                print(
                    f"[{category}/{slug}/{locale}] create ({target_state}) "
                    f"-> {titles[locale]}"
                )
                if not dry_run:
                    endpoint = (
                        f"{BLOGGER_API}/blogs/{blog_id}/posts?"
                        + urllib.parse.urlencode(
                            {"isDraft": "false" if should_publish else "true"}
                        )
                    )
                    created = http_json(
                        endpoint, method="POST", token=token, body=payload
                    )
                    remote_posts.append(created)


def discover(config: dict[str, Any], token: str) -> None:
    blog = get_blog(token, config["blog_url"])
    blog_id = str(blog["id"])
    pages = list_collection(token, blog_id, "pages")
    posts = list_all_posts(token, blog_id, fetch_bodies=False)
    counts = {status: 0 for status in POST_STATUSES}
    for post in posts:
        status = str(post.get("status", ""))
        if status in counts:
            counts[status] += 1
    print(
        json.dumps(
            {
                "blog": {
                    "id": blog.get("id"),
                    "name": blog.get("name"),
                    "url": blog.get("url"),
                },
                "pages": [
                    {
                        "id": page.get("id"),
                        "title": page.get("title"),
                        "url": page.get("url"),
                        "path": url_path(page.get("url", "")),
                        "status": page.get("status"),
                    }
                    for page in pages
                ],
                "post_counts": counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["discover", "faq", "posts", "all"])
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--posts-root", type=Path, default=Path("blogger/posts"))
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))

    try:
        token = access_token()
        if args.command == "discover":
            discover(config, token)
        if args.command in {"faq", "all"}:
            sync_faq(config, token, args.dry_run)
        if args.command in {"posts", "all"}:
            sync_posts(config, token, args.dry_run, args.posts_root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
