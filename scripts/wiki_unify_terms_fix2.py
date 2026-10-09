#!/usr/bin/env python3
"""
wiki_unify_terms_fix2.py — 二次修复(2026-08-26)

问题:
  - claims/NH 组辨别双音节但 CI 组无法辨别.md 文件名含 "CI",
body 里 B1 把 "CI 组" 改成了 "耳蜗植入(CI) 组",导致反向链接 [[NH 组辨别双音节但 耳蜗植入(CI) 组无法辨别]] 断链
  - 修复策略:把文件名也改成 "耳蜗植入(CI)" 风格,与 body 保持一致
  - 同步更新所有反向 wikilink

新增 N2 改名 1 个,反向链接同步。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import wiki_unify_terms as w


# 仅本批次需要追加的1 个文件名
EXTRA_RENAMES = {
    "NH 组辨别双音节但 CI 组无法辨别.md": "NH 组辨别双音节但 耳蜗植入(CI) 组无法辨别.md",
}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    dry_run = not args.execute
    print(f"{'[DRY-RUN]' if dry_run else '[EXECUTE]'} fix2\n")

    # 1) 找出文件
    rename_pairs = []
    for d in [REPO_ROOT / "claims"]:
        for old_name, new_name in EXTRA_RENAMES.items():
            old_path = d / old_name
            if old_path.exists():
                new_path = d / new_name
                rename_pairs.append((old_path, new_path))

    print(f"=== Phase 1: 重命名 {len(rename_pairs)} 个 claim 文件 ===")
    for old, new in rename_pairs:
        print(f"  {old.name} → {new.name}")

    # 2) 扫反向 wikilink
    link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
    wikilink_files_to_update = {}
    for md_file in w.iter_target_files():
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        updates = []
        for m in link_pattern.finditer(text):
            link = m.group(1)
            basename = link.split('/')[-1].strip()
            for old_name, new_name in EXTRA_RENAMES.items():
                old_slug = old_name[:-3]
                new_slug = new_name[:-3]
                if basename == old_slug or basename == f"claims/{old_slug}":
                    prefix = link[:-(len(basename))]
                    updates.append((m.group(0), f"[[{prefix}{new_slug}]]"))
        if updates:
            seen = set()
            unique = []
            for o, n in updates:
                if o not in seen:
                    seen.add(o); unique.append((o, n))
            wikilink_files_to_update[md_file] = unique

    total = sum(len(v) for v in wikilink_files_to_update.values())
    print(f"\n=== Phase 2: 反向 wikilink {total} 处 in {len(wikilink_files_to_update)} 文件 ===")
    for f, ups in list(wikilink_files_to_update.items())[:5]:
        print(f"  {f.name}: {len(ups)} 处")

    if dry_run:
        print("\n[DRY-RUN] 未执行任何写入")
        return

    # 3) 执行
    for old, new in rename_pairs:
        old.rename(new)
    for f, updates in wikilink_files_to_update.items():
        text = f.read_text(encoding="utf-8", errors="ignore")
        original = text
        for o, n in updates:
            text = text.replace(o, n)
        if text != original:
            f.write_text(text, encoding="utf-8")

    print(f"\n执行完成: 重命名 {len(rename_pairs)}, wikilink 修复 {total} 处")


if __name__ == "__main__":
    main()