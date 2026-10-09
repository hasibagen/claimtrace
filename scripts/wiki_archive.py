#!/usr/bin/env python3
"""
wiki_archive.py — 归档过期页

将节点标记为 archived（借鉴 OKF/llm-wiki-okf 的 archive 模式）。
不删除内容，只是设置 status: archived 并追加一条 log。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def find_page(wiki_root: Path, page_id: str) -> Path | None:
    """找页面文件。"""
    for sub in ("papers", "topics", "claims", "syntheses", "00-pending"):
        p = wiki_root / sub / f"{page_id}.md"
        if p.is_file():
            return p
    return None


def archive_page(wiki_root: Path, page_id: str, reason: str = "") -> bool:
    """归档页面：设置 status: archived。"""
    page_path = find_page(wiki_root, page_id)
    if not page_path:
        wc.eprint(f"Page not found: {page_id}")
        return False

    text = wc.read_text(page_path)
    fm, body = wc.parse_frontmatter(text)

    if fm.get("status") == "archived":
        wc.eprint(f"Already archived: {page_id}")
        return True

    fm["status"] = "archived"
    fm["archived_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if reason:
        fm["archived_reason"] = reason

    new_text = wc.write_frontmatter(fm, body)
    wc.write_text(page_path, new_text)

    # Append log
    log_path = wc.log_file(wiki_root)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n## [{today}] archive | {page_id}" + (f" | {reason}" if reason else "") + "\n")

    wc.ok(f"Archived: {page_path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive Evidence Wiki page")
    parser.add_argument("page_id", help="Page ID (filename without .md)")
    parser.add_argument("--reason", default="", help="Archive reason")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    ok = archive_page(wiki_root, args.page_id, args.reason)
    return 0 if ok else 1


def run(args: list[str]) -> int:
    sys.argv = ["wiki_archive"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())