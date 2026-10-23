"""Select changed Posts for the existing Blogger production sync."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ITEM_RE = re.compile(r"(?:story|notice)/[a-z0-9][a-z0-9-]{1,79}")


def resolve_scope(changed: list[str], *, manual=False, requested_item="") -> dict:
    if manual:
        if not requested_item:
            return {"full": True, "pages": True, "items": []}
        if not ITEM_RE.fullmatch(requested_item):
            raise ValueError("item must be story/<slug> or notice/<slug>")
        return {"full": False, "pages": False, "items": [requested_item]}
    items = set()
    for path in changed:
        match = re.fullmatch(r"blogger/posts/((?:story|notice)/[^/]+)/[^/]+", path)
        if match:
            if not ITEM_RE.fullmatch(match[1]):
                raise ValueError(f"Invalid changed Post path: {path}")
            items.add(match[1])
    pages = any(p.startswith(("blogger/faq/", "blogger/guide/")) for p in changed)
    # A concrete content change defines the publication scope, even when its
    # validators/helpers/config are released in the same commit.
    if items or pages:
        return {"full": False, "pages": pages, "items": sorted(items)}
    # Preserve full sync for explicit automation/config-only releases.
    full = any(p.startswith(("scripts/", ".github/workflows/")) or
               p == "blogger/config.json" for p in changed)
    return {"full": full, "pages": full, "items": []}


def stage_items(root: Path, items: list[str]) -> Path:
    target = Path(tempfile.mkdtemp(prefix="blogger-posts-"))
    for item in items:
        if not ITEM_RE.fullmatch(item):
            raise ValueError("Invalid Post selector")
        source = root / item
        if source.is_symlink() or not (source / "meta.json").is_file():
            raise ValueError(f"Selected Post does not exist: {item}")
        meta = json.loads((source / "meta.json").read_text())
        if f"{meta['category']}/{meta['slug']}" != item:
            raise ValueError(f"Selected Post identity mismatch: {item}")
        shutil.copytree(source, target / item)
    if len(list(target.glob("*/*/meta.json"))) != len(items):
        raise ValueError("Selected Post count mismatch")
    return target


def main():
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event not in {"push", "workflow_dispatch"}:
        raise ValueError("Publication scope is only resolved for main pushes or manual runs")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Production publication requires main")
    changed = []
    if event == "push":
        before = os.environ.get("BEFORE_SHA", "")
        if not re.fullmatch(r"[0-9a-f]{40}", before) or before == "0" * 40:
            raise ValueError("A valid previous main commit is required")
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", before, "HEAD"], text=True
        ).splitlines()
    scope = resolve_scope(changed, manual=event == "workflow_dispatch",
                          requested_item=os.environ.get("REQUESTED_ITEM", "").strip())
    if scope["full"]:
        root = Path("blogger/posts")
    elif scope["items"]:
        root = stage_items(Path("blogger/posts"), scope["items"])
    else:
        root = Path(tempfile.mkdtemp(prefix="blogger-no-posts-"))
    count = len(list(root.glob("*/*/meta.json")))
    if (scope["items"] or scope["full"]) and count == 0:
        raise ValueError("Publication selected zero managed Posts")
    print(json.dumps({**scope, "post_items": count}, ensure_ascii=False))
    outputs = {"full": str(scope["full"]).lower(), "pages": str(scope["pages"]).lower(),
               "posts": str(count > 0).lower(), "posts_root": str(root)}
    with open(os.environ["GITHUB_OUTPUT"], "a") as out:
        for key, value in outputs.items():
            out.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
