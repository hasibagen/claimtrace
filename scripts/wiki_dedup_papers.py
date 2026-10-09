#!/usr/bin/env python3
"""wiki_dedup_papers.py · 00-pending + raw 目录去重 + canonical 重命名

设计原则:
  1. paperinfo 节点名是 canonical citekey (BBT citekey, 短)
  2. 同一论文只 1 个 00-pending 目录 + 1 个 raw 目录
  3. 增量更新: 只补缺失内容, 不重建已有
  4. 不创建多个 paper.md / 多个空目录

用法:
  python3 wiki_dedup_papers.py --scan                       # 扫描重复
  python3 wiki_dedup_papers.py --scan --execute           # 扫描 + 合并 + 删
  python3 wiki_dedup_papers.py --rename --execute         # 重命名为 paperinfo canonical
  python3 wiki_dedup_papers.py --canonical <ck> <dirs>     # 手动指定
"""
import argparse, os, re, shutil, sys
from pathlib import Path


def main():
    global WIKI_ROOT, PENDING_DIR, RAW_DIR, PAPERINFO_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", action="store_true", help="扫描重复")
    parser.add_argument("--execute", action="store_true", help="执行合并")
    parser.add_argument("--rename", action="store_true", help="重命名为 paperinfo canonical")
    parser.add_argument("--canonical", type=str, help="手动指定 canonical citekey")
    parser.add_argument("--dirs", nargs="+", help="手动指定要合并的目录")
    parser.add_argument("--wiki-root", type=str, default=None)
    args = parser.parse_args()

    WIKI_ROOT = Path(args.wiki_root)
    PENDING_DIR = WIKI_ROOT / "00-pending"
    RAW_DIR = WIKI_ROOT / "raw"
    PAPERINFO_DIR = WIKI_ROOT / "paperinfo"

    if args.canonical and args.dirs:
        manual_merge(args.canonical, args.dirs, dry_run=not args.execute)
    elif args.rename:
        rename_to_canonical(dry_run=not args.execute)
    elif args.scan or not args.execute:
        scan_duplicates(verbose=True)
    else:
        groups = scan_duplicates(verbose=False)
        print(f"\n=== 自动合并 {len(groups)} 组 ===")
        total = 0
        for canonical, dirs in groups:
            if len(dirs) > 1:
                print(f"\n  canonical: {canonical} | {len(dirs)} 个变体")
                total += merge_dirs(canonical, dirs, dry_run=not args.execute)
        print(f"\n[完成] 合并 {total} 个重复目录")


def extract_prefix(name: str) -> str:
    """提取目录的 citekey 前缀(<author>_<year>)

    支持多种命名格式:
    - "Guo_2025_epl_..." (author 在前)
    - "2025_Guo_et_al._..." (year 在前, author 紧跟)
    - "Xie_2026_..." (author 在前)
    - "dollomaja__medrxiv_..." (无 year, 只取 author)
    """
    parts = name.split("_")
    # 找 year 4 位数字段
    year_idx = None
    for i, p in enumerate(parts):
        if re.fullmatch(r"[0-9]{4}", p):
            year_idx = i
            break
    if year_idx is None:
        # 无 year,只取 author
        for p in parts:
            if p and len(p) >= 3:
                return p.lower()
        return name
    year = parts[year_idx]
    # author = year 前面或后面的非空段(取第一个)
    if year_idx > 0:
        for i in range(year_idx - 1, -1, -1):
            if parts[i]:
                return f"{parts[i].lower()}_{year}"
    # year_idx == 0, 在第一个位置
    for i in range(year_idx + 1, len(parts)):
        if parts[i]:
            return f"{parts[i].lower()}_{year}"
    return name


def load_paperinfo_index():
    """建立 paperinfo 索引:
    - (author, year) → BBT citekey (主索引)
    - author → BBT citekey (只 author 索引, 用于没 year 的论文)
    返回: (index_author_year, index_author)
    """
    index_ay = {}
    index_a = {}
    if not PAPERINFO_DIR.exists():
        return index_ay, index_a
    for f in PAPERINFO_DIR.iterdir():
        if f.suffix != ".md":
            continue
        citekey = f.stem
        author = citekey.split("_")[0].lower() if "_" in citekey else citekey.lower()
        year_match = re.search(r"[0-9]{4}", citekey)
        year = year_match.group(0) if year_match else ""
        if author and year:
            index_ay[(author, year)] = citekey
        if author:
            index_a.setdefault(author, []).append(citekey)
    return index_ay, index_a


def find_canonical(prefix: str, paperinfo_index, index_author=None) -> str:
    """从 paperinfo 找 canonical citekey"""
    parts = prefix.split("_")
    if not parts:
        return ""
    author = parts[0]
    year = parts[1] if len(parts) > 1 else ""
    # 优先 (author, year) 精确匹配
    if year and (author, year) in paperinfo_index:
        return paperinfo_index[(author, year)]
    # 其次遍历查找
    for (a, y), ck in paperinfo_index.items():
        if a == author and y == year:
            return ck
    # fallback: 只 author 匹配(论文没 year,例如 dollomaja)
    if index_author is not None and author in index_author:
        candidates = index_author[author]
        if len(candidates) == 1:
            return candidates[0]
        # 多个候选:用最长的(最具体的)
        return max(candidates, key=len)
    return ""


def scan_duplicates(verbose=True):
    """扫描重复"""
    if not PENDING_DIR.exists():
        return []
    paperinfo_index, index_author = load_paperinfo_index()
    print(f"paperinfo 索引: {len(paperinfo_index)} 个节点 + {len(index_author)} 个 author 索引")

    groups = {}
    orphans = []
    for d in sorted(PENDING_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        prefix = extract_prefix(name)
        canonical = find_canonical(prefix, paperinfo_index, index_author)
        if canonical and canonical != name:
            groups.setdefault(canonical, []).append(name)
        elif not canonical:
            orphans.append(name)

    if verbose:
        print(f"\n=== 重复组 (共 {len(groups)} 组) ===")
        for canonical, dirs in sorted(groups.items()):
            if len(dirs) > 1:
                print(f"\n  🔁 canonical: {canonical} ({len(dirs)} 个变体)")
                for d in dirs:
                    print(f"      - {d}")

        if orphans:
            print(f"\n=== 无 paperinfo 匹配的孤儿 (共 {len(orphans)} 个) ===")
            for d in orphans[:20]:
                print(f"      - {d}")
            if len(orphans) > 20:
                print(f"      ... +{len(orphans) - 20} more")

    return list(groups.items())


def merge_dirs(canonical: str, dir_names: list, dry_run: bool = True):
    """合并一组目录到 canonical"""
    canonical_full = PENDING_DIR / canonical
    canonical_raw = RAW_DIR / canonical
    canonical_full.mkdir(exist_ok=True)
    canonical_raw.mkdir(exist_ok=True)

    merged = 0
    for name in dir_names:
        if name == canonical:
            continue
        src = PENDING_DIR / name
        src_raw = RAW_DIR / name

        src_paper = src / f"{name}.md"
        alt_paper = src / f"{canonical}.md"
        cand_paper = canonical_full / f"{canonical}.md"
        for p in [src_paper, alt_paper]:
            if p.exists():
                src_size = p.stat().st_size
                cand_size = cand_paper.stat().st_size if cand_paper.exists() else 0
                if src_size > cand_size and not dry_run:
                    shutil.copy2(p, cand_paper)
                break

        src_claims = src / "claims"
        if src_claims.exists():
            for f in src_claims.iterdir():
                if f.is_file():
                    dst = canonical_full / "claims" / f.name
                    if not dst.exists() and not dry_run:
                        shutil.copy2(f, dst)

        src_ev = src / "evidence"
        if src_ev.exists():
            for f in src_ev.iterdir():
                if f.is_file():
                    dst = canonical_full / "evidence" / f.name
                    if not dst.exists() and not dry_run:
                        shutil.copy2(f, dst)

        if src_raw.exists():
            src_full = src_raw / "full.md"
            if src_full.exists() and not (canonical_raw / "full.md").exists() and not dry_run:
                shutil.copy2(src_full, canonical_raw / "full.md")
            src_images = src_raw / "images"
            if src_images.exists():
                dst_images = canonical_raw / "images"
                if not dry_run:
                    shutil.copytree(src_images, dst_images, dirs_exist_ok=True)

        if src.exists() and not dry_run:
            shutil.rmtree(src)
        if src_raw.exists() and not dry_run:
            shutil.rmtree(src_raw)
        merged += 1
    return merged


def rename_to_canonical(dry_run: bool = True):
    """重命名 00-pending/raw 目录为 paperinfo canonical(短 BBT citekey)"""
    paperinfo_index, index_author = load_paperinfo_index()
    renamed_00 = []
    renamed_raw = []

    for d in list(PENDING_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        prefix = extract_prefix(name)
        canonical = find_canonical(prefix, paperinfo_index, index_author)
        if not canonical or canonical == name:
            continue
        target = PENDING_DIR / canonical
        if not target.exists():
            if not dry_run:
                d.rename(target)
            renamed_00.append((name, canonical, "rename"))
            print(f"  00-pending: {name} → {canonical}")
        else:
            for f in d.iterdir():
                if f.is_file():
                    dst = target / f.name
                    if not dst.exists() and not dry_run:
                        shutil.copy2(f, dst)
            if not dry_run:
                shutil.rmtree(d)
            renamed_00.append((name, canonical, "merge"))
            print(f"  00-pending: {name} → {canonical} (merge)")

    for d in list(RAW_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        prefix = extract_prefix(name)
        canonical = find_canonical(prefix, paperinfo_index)
        if not canonical or canonical == name:
            continue
        target = RAW_DIR / canonical
        if not target.exists():
            if not dry_run:
                d.rename(target)
            renamed_raw.append((name, canonical, "rename"))
            print(f"  raw: {name} → {canonical}")
        else:
            for f in d.iterdir():
                if f.is_file():
                    dst = target / f.name
                    if not dst.exists() and not dry_run:
                        shutil.copy2(f, dst)
            if not dry_run:
                shutil.rmtree(d)
            renamed_raw.append((name, canonical, "merge"))
            print(f"  raw: {name} → {canonical} (merge)")

    print(f"\n[完成] 00-pending 重命名/合并 {len(renamed_00)} 个")
    print(f"[完成] raw 重命名/合并 {len(renamed_raw)} 个")


def manual_merge(canonical: str, dir_names: list, dry_run: bool = True):
    """手动指定 canonical 合并"""
    print(f"[手动合并] canonical={canonical}, {len(dir_names)} 个目录")
    merged = merge_dirs(canonical, dir_names, dry_run=dry_run)
    print(f"[完成] 合并 {merged} 个目录")


if __name__ == "__main__":
    main()