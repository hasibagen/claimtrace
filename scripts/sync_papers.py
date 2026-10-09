#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本为 Phase 1 zotero_key 命名 papers 的一次性回填。
当前 wiki 已用 BBT citekey 命名(sync_raw.py 已足够),新同步走 wiki-zotero-sync Skill。
原 docstring 保留如下:

sync_papers.py — 从 zotero_md 同步所有 papers/ 的 raw 副本

解决 168 个 zk 命名的 papers/ 没有 wiki/raw/ 副本的问题:
1. 扫 papers/ 所有 .md, 抽 zotero-key
2. 用 zk 去 zotero_md 找对应 full.md (通过 SQLite 查 attachment)
3. 完整复制 (含 images/) → wiki/raw/<citekey>/

但 zk 在 zotero_md 目录名里没直接出现 — 需要通过 attachment → parent 找到 paper 目录

策略:
- 用 SQLite 直接查 items.attachment → parent item 关联
- 找 zk 对应的 paper 的 full.md 路径
- 跟 sync_raw 不同: 这个走 SQL, 更可靠
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc

DEFAULT_WIKI_ROOT = Path.cwd()
DEFAULT_ZOTERO_MD = Path.home() / "zotero_md"
DEFAULT_ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"


def get_zotero_item_dir(zk: str) -> Path | None:
    """用 SQLite 找 zk 对应的 paper 目录 (zotero_md 里)。

    流程:
    1. 在 items 表找 zk → itemID
    2. 找 parent_item 的 pdf attachment 路径
    3. 找 full.md (MinerU 导出目录里的)
    """
    try:
        conn = sqlite3.connect(f"file:{DEFAULT_ZOTERO_DB}?mode=ro", uri=True)
        c = conn.cursor()
        # 找 item_id
        c.execute("SELECT itemID FROM items WHERE key = ?", (zk,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        item_id = row[0]
        # 找 attachment item → 它可能没 path, MinerU 是单独流程
        # MinerU 输出目录命名: <Year>_<Author>_<Journal>_<Title>
        # 没有 zk, 只能从 paperinfo / paper.md 的 citekey 找

        conn.close()
        return None  # 不通过 SQLite 找, 走 fallback
    except Exception:
        return None


def find_zotero_paper_dir_simple(zotero_md: Path, citekey: str, zotero_key: str) -> Path | None:
    """用 zotero_key 找 (因为 full.md 路径含 zk hash, 不含 zk)"""
    if not zotero_key:
        return None

    # 1. 用 SQLite 查 itemID + parent
    try:
        conn = sqlite3.connect(f"file:{DEFAULT_ZOTERO_DB}?mode=ro", uri=True)
        c = conn.cursor()
        c.execute("SELECT itemID FROM items WHERE key = ?", (zotero_key,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        item_id = row[0]

        # 找 attachment path (itemAttachments table)
        c.execute("""SELECT path FROM itemAttachments
                     WHERE parentItemID = ? AND path IS NOT NULL""",
                  (item_id,))
        attachments = [r[0] for r in c.fetchall()]

        # 找 zotero_md 里的 full.md (依赖 attachment 的 file basename)
        for att_path in attachments:
            # att_path 例: "files/123/paper.pdf"
            # basename 例: "paper.pdf" 或 hash 名
            if att_path:
                # 找 zotero_md 里的 full.md 路径, 用 attachment 的 basename 在 zotero_md 递归搜
                # 简化: 用 attachment path 的 hash 名搜 (MinerU 目录名不含 zk)
                # 直接 find 整个 zotero_md 找 full.md, 在 path 里包含 attachment 的 hash 名
                # 实际最简单: 用 citekey 搜
                pass
        conn.close()
    except Exception:
        pass

    # 2. 走 citekey 模糊匹配 (跟 sync_raw 一样)
    import subprocess
    result = subprocess.run(
        ["find", str(zotero_md), "-name", "full.md"],
        capture_output=True, text=True, timeout=120
    )
    all_fulls = [Path(p) for p in result.stdout.strip().split("\n") if p]

    # 用 citekey 拆词
    keywords = [k.lower() for k in re.split(r"[_\s]+", citekey) if len(k) >= 4]
    if not keywords:
        keywords = [citekey.lower()]

    # 找含全 keywords 的 paper 目录
    candidates = []
    for full_path in all_fulls:
        paper_dir = full_path.parent
        dir_name_lower = paper_dir.name.lower()
        if all(kw in dir_name_lower for kw in keywords[:3]):  # 至少前 3 关键词
            candidates.append(paper_dir)

    if candidates:
        # 选最长的 (最具体的)
        return sorted(candidates, key=lambda p: -len(str(p)))[0]

    return None


def copy_paper_dir(src: Path, dst: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    if dst.exists():
        if (dst / "full.md").is_file() and (dst / "images").is_dir():
            return True  # skip
        if not dry_run:
            shutil.rmtree(dst)

    if not (src / "full.md").is_file():
        return False

    if dry_run:
        print(f"      DRY-RUN: cp -r {src} {dst}")
        return True

    shutil.copytree(src, dst, dirs_exist_ok=False)
    if verbose:
        n_files = sum(1 for _ in dst.rglob("*"))
        print(f"      ✓ copied {n_files} files")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki-root", type=Path, default=DEFAULT_WIKI_ROOT)
    parser.add_argument("--zotero-md", type=Path, default=DEFAULT_ZOTERO_MD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wiki = args.wiki_root
    zotero_md = args.zotero_md
    papers_dir = wiki / "papers"
    raw_dir = wiki / "raw"

    if not papers_dir.is_dir():
        wc.die(f"找不到 {papers_dir}")

    raw_dir.mkdir(parents=True, exist_ok=True)

    # 找所有 缺 raw 的 papers
    candidates = []
    for p in papers_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        m_ck = re.search(r'^citekey:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        m_zk = re.search(r"^zotero-key:\s*(\S+)", text, re.MULTILINE)
        if not (m_ck and m_zk):
            continue
        ck = m_ck.group(1).strip()
        zk = m_zk.group(1).strip()
        # 已有 raw?
        if (raw_dir / ck / "full.md").is_file():
            continue
        candidates.append((p, ck, zk))

    print(f"=== 缺 raw 的 papers: {len(candidates)} ===\n")

    stats = {"copied": 0, "not_found": 0, "error": 0}

    for i, (paper_md, ck, zk) in enumerate(candidates, 1):
        src = find_zotero_paper_dir_simple(zotero_md, ck, zk)
        if not src:
            stats["not_found"] += 1
            if i <= 5:
                print(f"  [{i}/{len(candidates)}] ✗ {ck} ({zk})")
            continue

        dst = raw_dir / ck
        if copy_paper_dir(src, dst, dry_run=args.dry_run, verbose=False):
            stats["copied"] += 1
            if i % 20 == 0:
                print(f"  进度: {i}/{len(candidates)} (copied: {stats['copied']})")
        else:
            stats["error"] += 1
            if i <= 5:
                print(f"  [{i}/{len(candidates)}] ✗ src 缺 full.md: {ck}")

    print(f"\n=== 结果 ===")
    print(f"  ✓ 复制: {stats['copied']}")
    print(f"  ✗ 找不到: {stats['not_found']}")
    print(f"  ! 错误: {stats['error']}")


if __name__ == "__main__":
    main()
