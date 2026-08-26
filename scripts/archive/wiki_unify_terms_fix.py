#!/usr/bin/env python3
"""
wiki_unify_terms_fix.py — 修复批次 1 的遗留问题(2026-08-26)

问题:
  1. N2 表漏列了 2 个大写 CI 开头的 claim 文件:
     - CI 儿童展现正常视听整合无组间异常.md
     - CI 植入越早视觉皮层反应越分化.md
     这些文件也需要改名,但没在 N2 表里。
  2. B1 把 [[CI xxx]] wikilink 改成 [[耳蜗植入(CI) xxx]],但目标文件如果以"CI 大写"开头,
     现在要改成[[耳蜗植入 xxx]],需修复。

策略:
  - 扩 N2 改名表:加入 2 个大写 CI 开头的文件
  - 先把所有 [[耳蜗植入(CI) xxx]] wikilink 改回 [[耳蜗植入 xxx]] (去掉括号)
  - 再把所有 [[ci xxx]] wikilink 改回 [[耳蜗植入 xxx]]
  - 再跑 N2 重命名(包括大写文件)+ 反向链接同步
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import wiki_unify_terms as w

# 扩展的 N2 改名表(原7 个 + 新2 个)
EXTENDED_RENAMES = dict(w.CI_CLAIM_RENAMES)
EXTENDED_RENAMES.update({
    "CI 儿童展现正常视听整合无组间异常.md": "耳蜗植入儿童展现正常视听整合无组间异常.md",
    "CI 植入越早视觉皮层反应越分化.md": "耳蜗植入植入越早视觉皮层反应越分化.md",
})


def fix_wikilinks(dry_run=True):
    """修复 wikilink:
       1. [[耳蜗植入(CI) xxx]] → [[耳蜗植入 xxx]]
       2. [[ci xxx]] / [[claims/ci xxx]] / [[00-pending/.../ci xxx]] → [[耳蜗植入 xxx]]
       3. 同步处理大写 [[CI xxx]] 形式
    """
    # 构造所有可能的旧 wikilink 形式
    rename_old = {old[:-3] for old in EXTENDED_RENAMES}  # 不带 .md
    rename_new = {old[:-3]: new[:-3] for old, new in EXTENDED_RENAMES.items()}

    # 反向模式:
    # 形式 A:[[ci xxx]]
    # 形式 B:[[claims/ci xxx]]
    # 形式 C:[[00-pending/xxx/claims/ci xxx]]
    # 大写也支持

    fixed_count = 0
    files_touched = set()
    samples = []

    for p in w.iter_target_files():
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        original = text

        # 模式 1:耳蜗植入(CI) xxx → 耳蜗植入 xxx (仅当目标是 claim slug 时)
        def repl_paren(m):
            nonlocal fixed_count
            link = m.group(1)
            basename = link.split('/')[-1].strip()
            if basename.startswith("耳蜗植入(CI) "):
                stripped = basename.replace("耳蜗植入(CI) ", "耳蜗植入 ", 1)
                # 还原前缀
                prefix = link[:-(len(basename))]
                new_link = prefix + stripped
                fixed_count += 1
                return f"[[{new_link}]]"
            return m.group(0)
        text = re.sub(r"\[\[([^\]]+)\]\]", repl_paren, text)

        # 模式 2: ci/CI xxx → 耳蜗植入 xxx (小写 ci + 大写 CI, 仅当目标是 N2 表中的 slug)
        def repl_ci(m):
            link = m.group(1)
            # 提取 basename
            basename = link.split('/')[-1].strip()
            for old_slug, new_slug in rename_new.items():
                # 检查是否匹配
                if basename == old_slug or basename == f"claims/{old_slug}":
                    # 直接命中
                    prefix = link[:-(len(basename))]
                    return f"[[{prefix}{new_slug}]]"
                if basename == f"CI {old_slug[len('ci '):]}" or basename == f"ci {old_slug[len('CI '):]}" if old_slug.startswith(('ci ', 'CI ')) else False:
                    # 处理 ci/CI 大小写不一致
                    pass
            # 大小写兜底: CI/Ci/cI/ci 开头的 slug 也匹配
            for old_slug, new_slug in rename_new.items():
                # 旧 slug 可能是 "ci xxx" 或 "CI xxx"
                alt_slug_lower = old_slug.lower()
                alt_slug_upper = old_slug.upper() if old_slug[0].islower() else old_slug
                if basename.lower() == alt_slug_lower:
                    prefix = link[:-(len(basename))]
                    return f"[[{prefix}{new_slug}]]"
            return m.group(0)
        text = re.sub(r"\[\[([^\]]+)\]\]", repl_ci, text)

        if text != original:
            files_touched.add(p)
            if len(samples) < 5:
                samples.append((p, [m.group(0) for m in re.finditer(r"\[\[耳蜗植入[^\]]+\]\]", text)][:3]))
            if not dry_run:
                p.write_text(text, encoding="utf-8")

    return fixed_count, files_touched, samples


def rename_extended(dry_run=True):
    """扩展 N2 重命名 + 反向链接"""
    rename_log = []
    link_updates = 0

    # 1) 找所有待改文件
    search_dirs = [REPO_ROOT / "claims"]
    pending_root = REPO_ROOT / "00-pending"
    if pending_root.exists():
        for sub in pending_root.iterdir():
            if sub.is_dir() and (sub / "claims").exists():
                search_dirs.append(sub / "claims")

    rename_pairs = []
    for d in search_dirs:
        if not d.exists():
            continue
        for old_name, new_name in EXTENDED_RENAMES.items():
            old_path = d / old_name
            if old_path.exists():
                new_path = d / new_name
                rename_pairs.append((old_path, new_path))

    print(f"\n=== EXT N2 重命名: 待改 {len(rename_pairs)} 个 claim 文件 ===")
    for old, new in rename_pairs:
        print(f"  {old.relative_to(REPO_ROOT)} → {new.relative_to(REPO_ROOT)}")

    # 2) 反向链接更新
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
            # 处理所有可能的变体
            for old_name, new_name in EXTENDED_RENAMES.items():
                old_slug = old_name[:-3]
                new_slug = new_name[:-3]
                # 大小写不敏感匹配
                if basename.lower() == old_slug.lower():
                    # 构造新链接
                    prefix = link[:-(len(basename))]
                    new_link = f"{prefix}{new_slug}"
                    updates.append((m.group(0), f"[[{new_link}]]"))
        if updates:
            # 去重
            seen = set()
            unique_updates = []
            for old, new in updates:
                if old not in seen:
                    seen.add(old)
                    unique_updates.append((old, new))
            wikilink_files_to_update[md_file] = unique_updates

    total_links = sum(len(v) for v in wikilink_files_to_update.values())
    print(f"\n=== EXT 反向 wikilink: {total_links} 处 in {len(wikilink_files_to_update)} 文件 ===")

    if dry_run:
        print("\n[DRY-RUN] 未执行任何写入")
        return {"renames": len(rename_pairs), "wikilinks": total_links, "files": len(wikilink_files_to_update)}

    # 3) 执行重命名
    for old, new in rename_pairs:
        if old.exists():
            old.rename(new)
            rename_log.append((old, new))

    # 4) 执行 wikilink 更新
    for f, updates in wikilink_files_to_update.items():
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        original = text
        for old_link, new_link in updates:
            text = text.replace(old_link, new_link)
        if text != original:
            f.write_text(text, encoding="utf-8")
            link_updates += len(updates)

    return {"renames": len(rename_log), "wikilinks": link_updates, "files": len(wikilink_files_to_update)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    dry_run = not args.execute
    print(f"{'[DRY-RUN]' if dry_run else '[EXECUTE]'} fix\n")

    print("=== Phase 1: 修复 wikilink ([[耳蜗植入(CI) xxx]] / [[ci xxx]] 残余) ===")
    fixed, files, samples = fix_wikilinks(dry_run=dry_run)
    print(f"  修复 {fixed} 处 wikilink in {len(files)} 文件")
    for f, s in samples[:3]:
        print(f"  {f.relative_to(REPO_ROOT)}:")
        for link in s[:2]:
            print(f"    → {link}")

    print("\n=== Phase 2: 扩展 N2 重命名(2 个大写 CI 文件) + 同步 wikilink ===")
    result = rename_extended(dry_run=dry_run)
    print(f"\n  结果: {result}")


if __name__ == "__main__":
    main()