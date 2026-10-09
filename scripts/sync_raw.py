#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本功能仍可用,但调用方式已被 wiki-zotero-sync Skill 取代。
新 raw 同步请用 wiki-zotero-sync 微 Skill,不走直调 Python 脚本。
原 docstring 保留如下:

sync_raw.py — 同步 Zotero MinerU 导出到 wiki/raw/

每个 paper.md 对应一个 wiki/raw/<citekey>/ 目录, 含:
- full.md  (MinerU 导出的论文正文)
- images/  (MinerU 提取的所有图片, 相对路径被 full.md 引用)

匹配策略 (按优先级):
1. **BEST**: 用 sqlite 直接查 Zotero 库: zotero_key → item_id → 找对应 collection
   关联的 MinerU 导出目录 (通过 pdf_filename 模糊匹配)
2. **GOOD**: 用 paper.md 的 csv-source-path 字段 (已存正确路径)
3. **FALLBACK**: citekey 严格匹配 (前 2 关键词 AND 关系 + 排除 common surnames)

用法:
  python sync_raw.py [--wiki-root PATH] [--dry-run] [--verbose]
  python sync_raw.py --force     # 覆盖已有 raw 副本
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


# 默认路径
DEFAULT_WIKI_ROOT = Path.cwd()
DEFAULT_ZOTERO_MD = Path.home() / "zotero_md"
DEFAULT_ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"

# Common surnames / short citekey 前缀 - 单独匹配容易误中, 需要更严格验证
COMMON_SURNAMES = {
    "martin", "xia", "guo", "wang", "li", "zhang", "liu", "chen",
    "yang", "huang", "zhao", "wu", "zhou", "sun", "ma", "lin",
    "hu", "zhu", "gao", "luo", "song", "shi", "ye", "tang",
}


# 手动 fallback: paper.md 文件名 → zotero_md 目录名
# 用于命名规则不匹配 (旧 paper 用 Firstname_Lastname_Year vs 新 BBT lastname_year_journal)
MANUAL_CITKEY_MAP = {
    "PaulaSanzLeon_2013_The_Virtual_Brain": "sanzleon_2013_front_neuroinform",
    "RitterPetra_2013_The_virtual_brain": "ritter_2013_brain_connectivit",
    "TriebkornPaul_2022_Brain_simulation_augments": "triebkorn_2022_a_d_transl_res",
    "aerts_2019": "aerts_2020_neuroimage",       # 用户命名 2019, 实际 2020
    "marti-juan_2022_cereb_cortex": "marti-juan_2023_cereb_cortex",  # 用户 2022, 实际 2023
    "meier_2021": "meier_2022_experimental_neuro",  # 用户 2021, 实际 2022
    "p_2022_alzheimers_dement_n_y": "p_2022_alzheimers_dement_n_y",  # 同名
}


def find_zotero_paper_dir(zotero_md: Path, citekey: str, zotero_key: str = "") -> Path | None:
    """在 zotero_md 里找 citekey 对应的 paper 目录。

    策略 (按优先级):
    1. 手动映射表 MANUAL_CITKEY_MAP (命名不一致情况)
    2. citekey 严格匹配 (前 3 关键词 AND 关系)
    3. 排除 common surnames 单独匹配
    4. 多候选时, 选择最长的 (最具体的)
    """
    if not citekey:
        return None

    # 策略 1: 手动映射
    if citekey in MANUAL_CITKEY_MAP:
        mapped = MANUAL_CITKEY_MAP[citekey]
        import subprocess
        result = subprocess.run(
            ["find", str(zotero_md), "-type", "d", "-name", f"*{mapped}*"],
            capture_output=True, text=True, timeout=30
        )
        candidates = [Path(p) for p in result.stdout.strip().split("\n") if p]
        candidates_with_full = sorted(
            [c for c in candidates if (c / "full.md").is_file()],
            key=lambda p: -len(str(p))
        )
        if candidates_with_full:
            return candidates_with_full[0]
        if candidates:
            return sorted(candidates, key=lambda p: -len(str(p)))[0]

    # 策略 2: citekey 严格匹配
    keywords = [k.lower() for k in re.split(r"[_\s]+", citekey) if len(k) >= 4]
    if not keywords:
        keywords = [citekey.lower()]

    first_kw = keywords[0]
    second_kw = keywords[1] if len(keywords) > 1 else ""
    third_kw = keywords[2] if len(keywords) > 2 else ""

    is_common = first_kw in COMMON_SURNAMES

    if is_common or third_kw:
        kw_pattern = "*".join([first_kw, second_kw, third_kw] if third_kw else [first_kw, second_kw])
    else:
        kw_pattern = f"*{first_kw}*{second_kw}*"

    import subprocess
    result = subprocess.run(
        ["find", str(zotero_md), "-type", "d", "-name", f"*{kw_pattern}*"],
        capture_output=True, text=True, timeout=30
    )
    candidates = [Path(p) for p in result.stdout.strip().split("\n") if p]
    candidates_with_full = sorted(
        [c for c in candidates if (c / "full.md").is_file()],
        key=lambda p: -len(str(p))
    )
    if candidates_with_full:
        return candidates_with_full[0]
    if candidates:
        return sorted(candidates, key=lambda p: -len(str(p)))[0]

    return None


def copy_paper_dir(src: Path, dst: Path, dry_run: bool = False, verbose: bool = False) -> str:
    """完整复制 paper 目录 (含 full.md + images/ + 其他文件) 到 dst。

    返回:
    - 'skipped'    - dst 已完整, 跳过
    - 'new'        - dst 不存在, 完整复制
    - 'incremental' - dst 部分缺失, 增量补全
    - 'src_invalid' - src 缺 full.md, 跳过
    """
    # 验证源至少有 full.md
    if not (src / "full.md").is_file():
        if verbose:
            print(f"      ✗ src 缺 full.md, 跳过 ({src})")
        return 'src_invalid'

    # dst 完整, 跳过
    if dst.exists() and (dst / "full.md").is_file() and (dst / "images").is_dir():
        if verbose:
            print(f"      → dst 已有完整 raw, 跳过")
        return 'skipped'

    # dst 不存在 → 完整复制
    if not dst.exists():
        if dry_run:
            print(f"      DRY-RUN: cp -r {src} {dst}")
            return 'new'
        shutil.copytree(src, dst, dirs_exist_ok=False)
        if verbose:
            n_files = sum(1 for _ in dst.rglob("*"))
            print(f"      ✓ copied {n_files} files (new)")
        return 'new'

    # dst 存在但不完整 → 增量补全
    if not dry_run:
        # 补 full.md
        if not (dst / "full.md").is_file():
            shutil.copy2(src / "full.md", dst / "full.md")
        # 补 images/
        src_images = src / "images"
        if src_images.is_dir():
            if not (dst / "images").is_dir():
                shutil.copytree(src_images, dst / "images")
            else:
                # 逐个文件同步
                for f in src_images.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(src_images)
                        dst_f = dst / "images" / rel
                        dst_f.parent.mkdir(parents=True, exist_ok=True)
                        if not dst_f.exists() or f.stat().st_mtime > dst_f.stat().st_mtime:
                            shutil.copy2(f, dst_f)
    if verbose:
        n_files = sum(1 for _ in dst.rglob("*"))
        print(f"      ✓ synced incrementally ({n_files} total files)")
    return 'incremental'


def update_csv_source_path(paper_md: Path, new_path: Path, dry_run: bool = False) -> bool:
    """更新 paper.md 的 csv-source-path 字段指向新路径。"""
    text = paper_md.read_text(encoding="utf-8")
    new_quote_path = str(new_path).replace("\\", "/")
    new_text = re.sub(
        r'^(csv-source-path:)\s*".*?"',
        rf'\1 "{new_quote_path}"',
        text,
        count=1,
        flags=re.MULTILINE
    )
    if new_text == text:
        return False
    if not dry_run:
        paper_md.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="同步 Zotero 原始素材到 wiki/raw/")
    parser.add_argument("--wiki-root", type=Path, default=DEFAULT_WIKI_ROOT,
                       help=f"Wiki 根目录 (默认: {DEFAULT_WIKI_ROOT})")
    parser.add_argument("--zotero-md", type=Path, default=DEFAULT_ZOTERO_MD,
                       help=f"Zotero MinerU 导出目录 (默认: {DEFAULT_ZOTERO_MD})")
    parser.add_argument("--dry-run", action="store_true", help="只显示不执行")
    parser.add_argument("--force", action="store_true", help="覆盖已有 raw 副本")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    wiki = args.wiki_root
    zotero_md = args.zotero_md
    papers_dir = wiki / "papers"
    raw_dir = wiki / "raw"

    if not papers_dir.is_dir():
        wc.die(f"找不到 papers/: {papers_dir}")
    if not zotero_md.is_dir():
        wc.die(f"找不到 zotero_md: {zotero_md}")
    raw_dir.mkdir(parents=True, exist_ok=True)

    papers = sorted(papers_dir.glob("*.md"))
    print(f"=== 扫 {len(papers)} 个 paper ===\n")

    stats = {"copied": 0, "synced_incrementally": 0, "skipped_existing": 0, "not_found": 0, "error": 0}

    for i, paper_md in enumerate(papers, 1):
        citekey = paper_md.stem
        text = paper_md.read_text(encoding="utf-8")
        m_ck = re.search(r"^zotero-key:\s*(\S+)", text, re.MULTILINE)
        zk = m_ck.group(1) if m_ck else ""
        m_csv = re.search(r'^csv-source-path:\s*"(.+?)"', text, re.MULTILINE)
        csv_path = m_csv.group(1) if m_csv else ""

        print(f"[{i:2d}/{len(papers)}] {citekey}")
        if args.verbose:
            print(f"      zotero-key: {zk}")
            print(f"      csv-source-path: {csv_path}")

        src_dir = find_zotero_paper_dir(zotero_md, citekey, zk)
        if not src_dir:
            stats["not_found"] += 1
            print(f"      ✗ zotero_md 找不到 (citekey={citekey})")
            continue

        if args.verbose:
            n_files = sum(1 for _ in src_dir.rglob("*"))
            print(f"      → src: {src_dir} ({n_files} files)")

        dst_dir = raw_dir / citekey
        result = copy_paper_dir(src_dir, dst_dir, dry_run=args.dry_run, verbose=args.verbose)
        if result == 'src_invalid':
            stats["not_found"] += 1
            print(f"      ✗ src 缺 full.md, 跳过")
            continue

        if result == 'new':
            stats["copied"] += 1
        elif result == 'incremental':
            stats["synced_incrementally"] += 1
        elif result == 'skipped':
            stats["skipped_existing"] += 1

        new_csv = dst_dir / "full.md"
        if update_csv_source_path(paper_md, new_csv, dry_run=args.dry_run):
            if args.verbose:
                print(f"      ✓ updated csv-source-path → {new_csv}")

    print(f"\n=== 同步结果 ===")
    print(f"  ✓ 完整同步: {stats['copied'] + stats['synced_incrementally'] + stats['skipped_existing']}")
    print(f"    - 新建: {stats['copied']}")
    print(f"    - 增量补全: {stats['synced_incrementally']}")
    print(f"    - 跳过 (已完整): {stats['skipped_existing']}")
    print(f"  ✗ 失败: {stats['not_found'] + stats['error']}")
    print(f"    - zotero_md 找不到: {stats['not_found']}")
    print(f"    - 错误: {stats['error']}")
    print(f"  输出: {raw_dir}")
    if args.dry_run:
        print(f"\n  (DRY-RUN, 未实际复制)")
    return 0 if stats["error"] == 0 else 1


def run(argv: list[str]) -> int:
    """统一 CLI 入口: `wiki sync-raw [args]`"""
    sys.argv = ["sync_raw"] + argv
    return main()


if __name__ == "__main__":
    sys.exit(main())
