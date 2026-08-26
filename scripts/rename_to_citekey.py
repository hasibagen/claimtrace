#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本用于 zotero-key → BBT citekey 一次性重命名。
wiki 当前已迁移到 BBT citekey 命名(ARCHITECTURE §3),新项目无需此脚本。
如需回填或重跑,保留此脚本作为应急工具。
原 docstring 保留如下:

rename_to_citekey.py — 把 papers/ 下 zotero-key 命名的文件重命名为 BBT citekey 命名

用户痛点:
  - 145 个 papers/ 文件用 zk 命名 (WTBP2G4H.md 风格) — 不是用户想要的
  - 用户期望 BBT citekey 命名 (xia_2026_biorxiv_cold_spring_harb_lab.md)

策略:
  - 读每个 papers/*.md 的 frontmatter, 提取 citekey 字段
  - 当前文件名 ≠ citekey → 重命名
  - 同步修复 wikilink 引用 (topics/claims/papers/index.md/log.md/EXTRACT_QUEUE.md)

参考:
  - AGENTS.md §1.3 节点命名约定
  - AGENTS.md §1.4 wikilink 双向链接维护
"""

from __future__ import annotations
import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# 默认 wiki root
DEFAULT_WIKI_ROOT = Path("/home/mind/nut/edu/wiki")

# 引用文件目录 (markdown)
REF_DIRS = ["topics", "claims", "raw"]
REF_FILES = ["index.md", "log.md", "EXTRACT_QUEUE.md", "README.md", "AGENTS.md"]


def parse_frontmatter(path: Path) -> dict | None:
    """读 frontmatter 提取 citekey / zotero-key"""
    try:
        content = path.read_text(errors="ignore")
    except Exception:
        return None
    ck = re.search(r'^citekey:\s*["\']?(\S+?)["\']?\s*$', content, re.MULTILINE)
    zk = re.search(r'^zotero-key:\s*(\S+)', content, re.MULTILINE)
    return {
        "path": path,
        "stem": path.stem,
        "citekey": ck.group(1).rstrip('"').rstrip("'").rstrip(",") if ck else None,
        "zotero_key": zk.group(1) if zk else None,
    }


def collect_ref_files(wiki: Path, papers_files: list[Path]) -> list[Path]:
    """收集所有可能含 wikilink 引用的 md 文件"""
    refs = set()
    # 引用目录
    for d_name in REF_DIRS:
        d = wiki / d_name
        if d.exists():
            for p in d.rglob("*.md"):
                refs.add(p)
    # 单文件
    for f_name in REF_FILES:
        f = wiki / f_name
        if f.exists():
            refs.add(f)
    # papers 自身 (反向链接)
    refs.update(papers_files)
    return list(refs)


def build_rename_plan(wiki: Path) -> dict:
    """构建重命名计划"""
    papers_dir = wiki / "papers"
    pending_dir = wiki / "00-pending"

    files = []
    for d in [papers_dir, pending_dir]:
        if d.exists():
            for p in d.iterdir():
                if p.suffix == ".md":
                    info = parse_frontmatter(p)
                    if info:
                        files.append(info)

    rename_plan = []
    skipped_conflict = []

    # 先建立已存在 citekey 集合 (避免冲突)
    existing_ck = set()
    for f in files:
        if f["citekey"]:
            target = papers_dir / f"{f['citekey']}.md"
            if target.exists():
                existing_ck.add(f["citekey"])

    for f in files:
        stem = f["stem"]
        ck = f["citekey"]
        if not ck:
            continue
        if stem == ck:
            continue  # 已对
        target_path = papers_dir / f"{ck}.md"
        if target_path.exists():
            skipped_conflict.append(
                {"old_stem": stem, "wanted_ck": ck, "zotero_key": f["zotero_key"]}
            )
            continue
        src = (
            papers_dir / f"{stem}.md"
            if (papers_dir / f"{stem}.md").exists()
            else pending_dir / f"{stem}.md"
        )
        rename_plan.append(
            {
                "old_stem": stem,
                "new_stem": ck,
                "old_path": str(src.relative_to(wiki)),
                "new_path": str((papers_dir / f"{ck}.md").relative_to(wiki)),
                "zk": f["zotero_key"],
            }
        )

    # 引用扫描
    ref_files = collect_ref_files(wiki, [f["path"] for f in files])
    old_stems = set(r["old_stem"] for r in rename_plan)
    ref_count: dict[str, dict] = defaultdict(lambda: {"files": set(), "count": 0})
    for rf in ref_files:
        try:
            c = rf.read_text(errors="ignore")
        except Exception:
            continue
        for stem in old_stems:
            for pat in [f"[[{stem}]]", f"[[{stem}|", f"[[{stem}#"]:
                n = c.count(pat)
                if n > 0:
                    ref_count[stem]["files"].add(str(rf.relative_to(wiki)))
                    ref_count[stem]["count"] += n

    return {
        "total_rename": len(rename_plan),
        "total_skipped": len(skipped_conflict),
        "rename": rename_plan,
        "skipped": skipped_conflict,
        "refs_to_update": {
            stem: {
                "files": sorted(info["files"]),
                "count": info["count"],
            }
            for stem, info in ref_count.items()
            if info["count"] > 0
        },
    }


def apply_rename(wiki: Path, plan: dict, dry_run: bool = False) -> None:
    """执行重命名 + 引用修复"""
    rename_map = {r["old_stem"]: r["new_stem"] for r in plan["rename"]}

    # 1. 文件重命名
    print(f"\n=== Phase 1: 重命名 {len(rename_map)} 个文件 ===")
    for old_stem, new_stem in rename_map.items():
        # 可能在 papers/ 或 00-pending/
        src_papers = wiki / "papers" / f"{old_stem}.md"
        src_pending = wiki / "00-pending" / f"{old_stem}.md"
        src = src_papers if src_papers.exists() else src_pending
        dst = wiki / "papers" / f"{new_stem}.md"
        if not src.exists():
            print(f"  ⚠️  跳过 (源不存在): {old_stem}")
            continue
        if dry_run:
            print(f"  [DRY] {src.relative_to(wiki)} → {dst.relative_to(wiki)}")
        else:
            shutil.move(str(src), str(dst))

    # 2. 修复 wikilink 引用
    print(f"\n=== Phase 2: 修复 wikilink 引用 ===")
    ref_count = plan["refs_to_update"]
    affected_files = set()
    for info in ref_count.values():
        affected_files.update(info["files"])

    if not affected_files:
        print(f"  (无 wikilink 需要修复)")
    else:
        print(f"  涉及 {len(affected_files)} 个文件, {sum(v['count'] for v in ref_count.values())} 处引用")
        for rel_path in sorted(affected_files):
            path = wiki / rel_path
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            original = content
            for old_stem, new_stem in rename_map.items():
                # 修复模式:
                # [[old_stem]] → [[new_stem]]
                # [[old_stem|alias]] → [[new_stem|alias]]
                # [[old_stem#heading]] → [[new_stem#heading]]
                # 注意: 严格用 stem 边界, 避免误替换 (例如 "meier_2021" 不会被 "meier_2021_" 替换)
                for pat_old, pat_new in [
                    (f"[[{old_stem}]]", f"[[{new_stem}]]"),
                    (f"[[{old_stem}|", f"[[{new_stem}|"),
                    (f"[[{old_stem}#", f"[[{new_stem}#"),
                ]:
                    if pat_old in content:
                        content = content.replace(pat_old, pat_new)
            if content != original:
                if dry_run:
                    print(f"  [DRY] 修复: {rel_path}")
                else:
                    path.write_text(content)

    # 3. 报告
    print(f"\n=== Phase 3: 完成 ===")
    if dry_run:
        print(f"  (dry-run, 未实际修改)")
    else:
        print(f"  ✅ 重命名 + 引用修复完成")


def main():
    parser = argparse.ArgumentParser(description="重命名 papers/ 下 zk 命名文件为 BBT citekey")
    parser.add_argument(
        "--wiki-root",
        type=Path,
        default=DEFAULT_WIKI_ROOT,
        help=f"Wiki root (default: {DEFAULT_WIKI_ROOT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行 (覆盖 --dry-run)",
    )
    parser.add_argument(
        "--plan-out",
        type=Path,
        default=None,
        help="保存计划到 JSON 文件",
    )
    args = parser.parse_args()

    dry_run = not args.execute

    wiki = args.wiki_root
    if not wiki.exists():
        print(f"❌ Wiki root 不存在: {wiki}")
        sys.exit(1)

    print(f"Wiki root: {wiki}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")

    plan = build_rename_plan(wiki)
    print(f"\n=== 计划摘要 ===")
    print(f"  重命名: {plan['total_rename']}")
    print(f"  跳过 (目标已存在): {plan['total_skipped']}")
    print(f"  引用修复文件: {sum(len(v['files']) for v in plan['refs_to_update'].values())}")
    print(f"  总引用次数: {sum(v['count'] for v in plan['refs_to_update'].values())}")

    if args.plan_out:
        args.plan_out.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
        print(f"  计划写入: {args.plan_out}")

    if plan["total_rename"] == 0:
        print("\n✅ 无需重命名")
        return

    apply_rename(wiki, plan, dry_run=dry_run)


if __name__ == "__main__":
    main()