#!/usr/bin/env python3
"""wiki_unify_terms_fix3.py — 第三次清理 cochlear 旧 ci/CI 残留(精简版)

详见 memory/2026-08-26.md 注释。
"""
from __future__ import annotations
import re, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import wiki_unify_terms as w

CI_DELETES = [
    "CI 儿童展现正常视听整合无组间异常.md",
    "CI 植入越早视觉皮层反应越分化.md",
    "ci 用户听觉皮层激活低于对照.md",
    "ci 用户听觉适应降低反映康复不完全.md",
    "ci 用户视觉皮层激活低于对照.md",
    "ci 用户视觉适应增强支持编码效率.md",
    "ci 视听解耦失同步.md",
    "ci 语言延迟视觉反应弱.md",
    "ci 跨模态可塑性适应不良.md",
]

COCHLEAR_LINK_FIXES = {
    "ci 用户听觉皮层激活低于对照": "耳蜗植入用户听觉皮层激活低于对照",
    "ci 用户听觉适应降低反映康复不完全": "耳蜗植入用户听觉适应降低反映康复不完全",
    "ci 用户视觉皮层激活低于对照": "耳蜗植入用户视觉皮层激活低于对照",
    "ci 用户视觉适应增强支持编码效率": "耳蜗植入用户视觉适应增强支持编码效率",
    "ci 视听解耦失同步": "耳蜗植入视听解耦失同步",
    "ci 语言延迟视觉反应弱": "耳蜗植入语言延迟视觉反应弱",
    "ci 跨模态可塑性适应不良": "耳蜗植入跨模态可塑性适应不良",
    "CI 儿童展现正常视听整合无组间异常": "耳蜗植入儿童展现正常视听整合无组间异常",
    "CI 植入越早视觉皮层反应越分化": "耳蜗植入植入越早视觉皮层反应越分化",
    "NH 组辨别双音节但 CI 组无法辨别": "NH 组辨别双音节但 耳蜗植入组无法辨别",
}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    dry_run = not args.execute
    print(f"{'[DRY-RUN]' if dry_run else '[EXECUTE]'} fix3 (minimal)")

    # 1) Delete 9 ci/CI files
    deleted = 0
    for fname in CI_DELETES:
        p = REPO_ROOT / "claims" / fname
        if p.exists():
            if not dry_run:
                p.unlink()
            deleted += 1
    print(f"  deleted: {deleted}")

    # 2) Fix wikilinks
    total = 0
    files = set()
    link_re = re.compile(r"\[\[([^\]]+)\]\]")
    for p in w.iter_target_files():
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        original = text
        def repl(m):
            nonlocal total
            link = m.group(1)
            basename = link.split('/')[-1].strip()
            if basename in COCHLEAR_LINK_FIXES:
                total += 1
                return f"[[{link[:-(len(basename))]}{COCHLEAR_LINK_FIXES[basename]}]]"
            return m.group(0)
        new_text = link_re.sub(repl, text)
        if new_text != original:
            files.add(p)
            if not dry_run:
                p.write_text(new_text, encoding="utf-8")
    print(f"  wikilink updates: {total} in {len(files)} files")

    # 3) Verify
    remaining = sum(1 for f in CI_DELETES if (REPO_ROOT / "claims" / f).exists())
    print(f"  remaining ci/CI files: {remaining}")


if __name__ == "__main__":
    main()