#!/usr/bin/env python3
"""Publish ShiftMate GitHub-managed Pages and Posts to Blogger API v3."""
from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
POST_STATUSES = ("live", "draft", "scheduled")


def http_json(
    url: str,
    method: str = "GET",
    token: str | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    retryable_codes = {429, 500, 502, 503, 504}
    delays = (5, 10, 20, 40, 80)
    for attempt in range(len(delays) + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = resp.read()
                result = json.loads(payload) if payload else {}
                if method.upper() != "GET":
                    try:
                        write_delay = max(
                            0.0,
                            float(os.environ.get("BLOGGER_WRITE_DELAY_SECONDS", "4.0")),
                        )
                    except ValueError:
                        write_delay = 4.0
                    if write_delay:
                        time.sleep(write_delay)
                return result
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            if exc.code in retryable_codes and attempt < len(delays):
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = max(delays[attempt], float(retry_after or 0))
                except ValueError:
                    delay = delays[attempt]
                print(
                    f"Blogger API {exc.code} for {method}; retrying after "
                    f"{delay:g}s (attempt {attempt + 2}/{len(delays) + 1})",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise RuntimeError(
                f"Blogger API error {exc.code} {method} {url}: {detail}"
            ) from exc
    raise RuntimeError(f"Blogger API retry loop exhausted: {method} {url}")


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
            f"OAuth token refresh failed ({exc.code}): "
            f"{exc.read().decode(errors='replace')}"
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


def list_all_posts(
    token: str,
    blog_id: str,
    *,
    fetch_bodies: bool,
) -> list[dict[str, Any]]:
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


def normalized_post_path(url: str) -> str:
    path = url_path(url)
    for suffix in (".html", ".htm"):
        if path.lower().endswith(suffix):
            return path[: -len(suffix)]
    return path


def post_url_matches(left: str, right: str) -> bool:
    return normalized_post_path(left) == normalized_post_path(right)


def permalink_slug_for(meta: dict[str, Any], locale: str) -> str:
    values = meta.get("permalink_slugs", {})
    if values in (None, ""):
        return ""
    if not isinstance(values, dict):
        raise RuntimeError("permalink_slugs must be an object keyed by locale")
    slug = str(values.get(locale, "")).strip()
    if not slug:
        return ""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", slug):
        raise RuntimeError(
            f"invalid permalink slug for {locale}: {slug!r}; "
            "use lowercase ASCII letters, digits, and hyphens"
        )
    return slug


def permalink_url_matches(url: str, slug: str) -> bool:
    if not slug:
        return True
    path = url_path(url)
    filename = path.rsplit("/", 1)[-1]
    for suffix in (".html", ".htm"):
        if filename.lower().endswith(suffix):
            filename = filename[: -len(suffix)]
            break
    return filename == slug


def seeded_payload(payload: dict[str, Any], slug: str) -> dict[str, Any]:
    if not slug:
        return payload
    return {**payload, "title": slug}


def post_payload_matches(post: dict[str, Any], payload: dict[str, Any]) -> bool:
    remote_labels = {str(value) for value in post.get("labels", [])}
    wanted_labels = {str(value) for value in payload.get("labels", [])}
    return (
        str(post.get("title", "")) == str(payload.get("title", ""))
        and str(post.get("content", "")) == str(payload.get("content", ""))
        and remote_labels == wanted_labels
    )


def create_seeded_live_post(
    token: str,
    blog_id: str,
    payload: dict[str, Any],
    slug: str,
) -> dict[str, Any]:
    endpoint = (
        f"{BLOGGER_API}/blogs/{blog_id}/posts?"
        + urllib.parse.urlencode({"isDraft": "false"})
    )
    created = http_json(
        endpoint,
        method="POST",
        token=token,
        body=seeded_payload(payload, slug),
    )
    created_url = str(created.get("url", ""))
    if not permalink_url_matches(created_url, slug):
        raise RuntimeError(
            f"Blogger did not create expected permalink slug {slug!r}: "
            f"{created_url}"
        )
    updated = http_json(
        f"{BLOGGER_API}/blogs/{blog_id}/posts/{created['id']}",
        method="PATCH",
        token=token,
        body=payload,
    )
    return updated


def find_page_by_path(
    pages: list[dict[str, Any]], target_path: str
) -> dict[str, Any]:
    wanted = target_path.rstrip("/") or "/"
    matches = [page for page in pages if url_path(page.get("url", "")) == wanted]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one Blogger page for {wanted}, found {len(matches)}"
        )
    return matches[0]


def page_type_config(config: dict[str, Any], page_type: str) -> dict[str, Any]:
    page_types = config.get("page_types", {})
    if page_type not in page_types:
        raise RuntimeError(f"unsupported managed page type: {page_type}")
    return page_types[page_type]


def sync_page_type(
    config: dict[str, Any],
    token: str,
    page_type: str,
    dry_run: bool = False,
) -> None:
    page_cfg = page_type_config(config, page_type)
    source_dir = Path(page_cfg["directory"])
    path_key = str(page_cfg["path_key"])
    required = bool(page_cfg.get("required", False))
    source_locale = str(config.get("source_locale", "ko"))
    source_entry = source_dir / f"{source_locale}.html"

    if not source_entry.exists():
        if required:
            raise RuntimeError(
                f"missing required {page_type} source file: {source_entry}"
            )
        print(f"[{page_type}] {source_entry} not present; managed page skipped")
        return

    blog = get_blog(token, config["blog_url"])
    blog_id = str(blog["id"])
    pages = list_collection(token, blog_id, "pages", status="live")
    print(
        f"Blog: {blog.get('name')} ({blog_id}), pages={len(pages)}, "
        f"managed page={page_type}"
    )

    for locale, info in config["locales"].items():
        source = source_dir / f"{locale}.html"
        if not source.exists():
            raise RuntimeError(
                f"missing localized {page_type} source file: {source}"
            )
        target_path = info.get(path_key)
        if not target_path:
            raise RuntimeError(
                f"missing {path_key} for locale {locale} in blogger/config.json"
            )
        page = find_page_by_path(pages, str(target_path))
        html = source.read_text(encoding="utf-8")
        print(
            f"[{page_type}/{locale}] {target_path} -> page {page['id']} "
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


def sync_pages(
    config: dict[str, Any], token: str, dry_run: bool = False
) -> None:
    for page_type in config.get("page_types", {}):
        sync_page_type(config, token, page_type, dry_run)


def content_marker(category: str, slug: str, locale: str) -> str:
    return f"<!--shiftmate-content-id:{category}/{slug}/{locale}-->"


def seo_description_marker(description: str) -> str:
    value = html_lib.escape(description.strip(), quote=True)
    return (
        '<span class="sm-post-seo" data-sm-description="'
        + value
        + '" hidden></span>'
    )


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
    source_locale = str(config.get("source_locale", "ko"))
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
            raise RuntimeError(
                f"unsupported post category {category}: {meta_path}. "
                "Only notice/story are managed as Blogger posts."
            )

        titles_path = item / "titles.json"
        descriptions_path = item / "descriptions.json"
        if not titles_path.exists():
            raise RuntimeError(f"missing titles.json: {titles_path}")
        if not descriptions_path.exists():
            raise RuntimeError(f"missing descriptions.json: {descriptions_path}")
        titles = json.loads(titles_path.read_text(encoding="utf-8"))
        descriptions = json.loads(descriptions_path.read_text(encoding="utf-8"))
        base_labels = list(meta.get("labels", []))
        if category == "notice":
            notice_type = str(meta.get("notice_type", "")).strip()
            if notice_type and notice_type not in base_labels:
                base_labels.insert(0, notice_type)
        category_label = config["post_categories"][category]
        should_publish = bool(meta.get("publish", False))
        source_url = str(meta.get("source_url", "")).strip()
        recreate_permalink_locales = set(meta.get("recreate_permalink_locales", []))

        for locale, info in config["locales"].items():
            body_path = item / f"{locale}.html"
            if not body_path.exists():
                raise RuntimeError(f"missing localized body: {body_path}")
            if locale not in titles:
                raise RuntimeError(
                    f"missing localized title {locale}: {titles_path}"
                )
            description = str(descriptions.get(locale, "")).strip()
            if not description:
                raise RuntimeError(
                    f"missing localized search description {locale}: {descriptions_path}"
                )

            marker = content_marker(category, slug, locale)
            content = (
                marker
                + "\n"
                + seo_description_marker(description)
                + "\n"
                + body_path.read_text(encoding="utf-8")
            )
            matches = [
                post
                for post in remote_posts
                if marker in (post.get("content") or "")
            ]
            if not matches and locale == source_locale and source_url:
                matches = [
                    post
                    for post in remote_posts
                    if post_url_matches(str(post.get("url", "")), source_url)
                ]
                if not matches:
                    raise RuntimeError(
                        f"source_url did not match an existing Blogger post: {source_url}"
                    )
                print(
                    f"[{category}/{slug}/{locale}] bound existing source URL "
                    f"to post {matches[0].get('id', '?')}"
                )
            if len(matches) > 1:
                raise RuntimeError(
                    f"duplicate remote Blogger posts for {marker}"
                )

            labels: list[str] = []
            for label in [category_label, info["language_label"], *base_labels]:
                if label and label not in labels:
                    labels.append(label)
            payload = {
                "title": titles[locale],
                "content": content,
                "labels": labels,
            }
            permalink_slug = permalink_slug_for(meta, locale)

            if matches:
                post = matches[0]
                status = str(post.get("status", "")).lower()
                print(
                    f"[{category}/{slug}/{locale}] update post {post['id']} "
                    f"status={post.get('status', '?')} -> {titles[locale]}"
                )

                if (
                    should_publish
                    and permalink_slug
                    and status == "live"
                    and not permalink_url_matches(str(post.get("url", "")), permalink_slug)
                ):
                    if locale not in recreate_permalink_locales:
                        raise RuntimeError(
                            f"live post permalink does not match configured slug "
                            f"{permalink_slug!r} for {category}/{slug}/{locale}: "
                            f"{post.get('url', '')}. Add the locale to "
                            "recreate_permalink_locales for an intentional one-time migration."
                        )
                    print(
                        f"  permalink migration: {post.get('url', '')} -> "
                        f".../{permalink_slug}.html"
                    )
                    if dry_run:
                        post = {
                            **post,
                            "title": titles[locale],
                            "url": f".../{permalink_slug}.html",
                            "status": "live",
                        }
                    else:
                        replacement = create_seeded_live_post(
                            token, blog_id, payload, permalink_slug
                        )
                        old_id = str(post["id"])
                        http_json(
                            f"{BLOGGER_API}/blogs/{blog_id}/posts/{old_id}",
                            method="DELETE",
                            token=token,
                        )
                        remote_posts[:] = [
                            p for p in remote_posts if str(p.get("id", "")) != old_id
                        ]
                        remote_posts.append(replacement)
                        post = replacement
                    print(f"  url={post.get('url', '')}")
                    continue

                if (
                    not should_publish
                    and status in {"live", "scheduled"}
                ):
                    post = reconcile_post_state(
                        token,
                        blog_id,
                        post,
                        should_publish=False,
                        dry_run=dry_run,
                    )
                    status = str(post.get("status", "")).lower()

                if should_publish and permalink_slug and status != "live":
                    # Blogger API has no custom-permalink field. Publish the draft
                    # while its title is the ASCII slug seed, then restore the
                    # localized title without changing the generated permalink.
                    seed_payload = seeded_payload(payload, permalink_slug)
                    if not dry_run and not post_payload_matches(post, seed_payload):
                        post = http_json(
                            f"{BLOGGER_API}/blogs/{blog_id}/posts/{post['id']}",
                            method="PATCH",
                            token=token,
                            body=seed_payload,
                        )
                    post = reconcile_post_state(
                        token,
                        blog_id,
                        post,
                        should_publish=True,
                        dry_run=dry_run,
                    )
                    if not dry_run:
                        if not permalink_url_matches(
                            str(post.get("url", "")), permalink_slug
                        ):
                            raise RuntimeError(
                                f"Blogger did not publish expected permalink slug "
                                f"{permalink_slug!r}: {post.get('url', '')}"
                            )
                        post = http_json(
                            f"{BLOGGER_API}/blogs/{blog_id}/posts/{post['id']}",
                            method="PATCH",
                            token=token,
                            body=payload,
                        )
                    print(f"  url={post.get('url', '')}")
                    continue

                if not dry_run and not post_payload_matches(post, payload):
                    post = http_json(
                        f"{BLOGGER_API}/blogs/{blog_id}/posts/{post['id']}",
                        method="PATCH",
                        token=token,
                        body=payload,
                    )
                    matches[0].update(post)
                elif not dry_run:
                    print("  content unchanged; Blogger write skipped")

                if should_publish:
                    post = reconcile_post_state(
                        token,
                        blog_id,
                        post,
                        should_publish=True,
                        dry_run=dry_run,
                    )
                print(f"  url={post.get('url', '')}")
            else:
                target_state = "live" if should_publish else "draft"
                print(
                    f"[{category}/{slug}/{locale}] create ({target_state}) "
                    f"-> {titles[locale]}"
                )
                if not dry_run:
                    if should_publish and permalink_slug:
                        created = create_seeded_live_post(
                            token, blog_id, payload, permalink_slug
                        )
                    else:
                        endpoint = (
                            f"{BLOGGER_API}/blogs/{blog_id}/posts?"
                            + urllib.parse.urlencode(
                                {"isDraft": "false" if should_publish else "true"}
                            )
                        )
                        create_payload = (
                            seeded_payload(payload, permalink_slug)
                            if permalink_slug
                            else payload
                        )
                        created = http_json(
                            endpoint, method="POST", token=token, body=create_payload
                        )
                    remote_posts.append(created)
                    print(f"  url={created.get('url', '')}")


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

    configured_pages: dict[str, dict[str, str]] = {}
    for page_type, page_cfg in config.get("page_types", {}).items():
        path_key = str(page_cfg["path_key"])
        configured_pages[page_type] = {
            locale: str(info.get(path_key, ""))
            for locale, info in config.get("locales", {}).items()
        }

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
                "configured_pages": configured_pages,
                "post_counts": counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "command",
        choices=["discover", "faq", "guide", "pages", "posts", "all"],
    )
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--posts-root", type=Path, default=Path("blogger/posts"))
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))

    try:
        token = access_token()
        if args.command == "discover":
            discover(config, token)
        elif args.command in {"faq", "guide"}:
            sync_page_type(config, token, args.command, args.dry_run)
        else:
            if args.command in {"pages", "all"}:
                sync_pages(config, token, args.dry_run)
            if args.command in {"posts", "all"}:
                sync_posts(config, token, args.dry_run, args.posts_root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
