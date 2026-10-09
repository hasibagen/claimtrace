#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本仅用于 Phase 2 一次性迁移 126 CLAIM-NNN → semantic-slug。
ARCHITECTURE §2.3 已废 CLAIM-NNN 编号,未来不再使用此脚本。
新创建 claim 节点请用 wiki-build-claim Skill(直接生成 slug 命名)。
原 docstring 保留如下:

rename_claims.py · CLAIM-NNN → 语义 slug 重命名工具(ARCHITECTURE §9)

用法:
    # 1. LLM 生成 rename_mapping.md(CLAIM-XXX → new-slug)
    # 2. 模拟运行:
    python3 .skill/scripts/rename_claims.py --mapping rename_mapping.md --dry-run
    # 3. 实际运行(自动 git tag checkpoint):
    python3 .skill/scripts/rename_claims.py --mapping rename_mapping.md

rename_mapping.md 格式:
    | old_id | new_slug |
    |--------|----------|
    | CLAIM-001 | tvb-multiscale-platform |
    | CLAIM-007 | dlpfc-hbo-age |
    ...

操作:
    1. 读 mapping
    2. git tag pre-claim-rename
    3. 重命名 claims/<old>.md → claims/<new>.md
    4. 扫描所有 .md 文件,更新 [[CLAIM-XXX]] → [[new-slug]]
    5. git tag post-claim-rename
    6. 报告:重命名 N 个文件,更新 M 个 wikilink
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).parent.parent.parent
CLAIMS_DIR = WIKI_ROOT / "claims"

# 旧 CLAIM-NNN 格式
CLAIM_OLD_PATTERN = re.compile(r"CLAIM-(\d{3})")

# rename_mapping.md 表格行
MAPPING_PATTERN = re.compile(r"\|\s*(CLAIM-\d+)\s*\|\s*([a-z0-9-]+)\s*\|")


def parse_mapping(mapping_file: Path) -> dict[str, str]:
    """解析 rename_mapping.md,返回 {CLAIM-007: dlpfc-hbo-age}"""
    if not mapping_file.exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        sys.exit(1)

    content = mapping_file.read_text(encoding="utf-8")
    mapping = {}
    for match in MAPPING_PATTERN.finditer(content):
        old_id = match.group(1)
        new_slug = match.group(2)
        mapping[old_id] = new_slug

    if not mapping:
        print(f"⚠️ No mapping found in {mapping_file}")
        print("Expected format:")
        print("| CLAIM-001 | new-slug |")
        print("| CLAIM-007 | another-slug |")

    return mapping


def git_tag(tag: str, message: str) -> None:
    """创建 git tag"""
    try:
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", message],
            cwd=WIKI_ROOT,
            check=True,
        )
        print(f"✅ Created tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Tag creation failed: {e}")


def rename_files(mapping: dict[str, str], dry_run: bool = True) -> int:
    """重命名 claims/<old>.md → claims/<new>.md"""
    renamed = 0
    for old_id, new_slug in mapping.items():
        old_file = CLAIMS_DIR / f"{old_id}_<unknown>.md"
        # 实际文件名是 CLAIM-NNN_<old-slug>.md,我们只重命名 CLAIM-NNN 部分
        # 但用户可能映射整个文件名,这里灵活处理
        candidates = list(CLAIMS_DIR.glob(f"{old_id}_*.md"))
        if not candidates:
            print(f"⚠️ No file for {old_id}")
            continue

        old_file = candidates[0]
        old_slug = old_file.stem.replace(f"{old_id}_", "")
        new_file = CLAIMS_DIR / f"{new_slug}.md"

        if dry_run:
            print(f"[DRY] {old_file.name} → {new_file.name}")
        else:
            old_file.rename(new_file)
            print(f"✅ {old_file.name} → {new_file.name}")
            renamed += 1

    return renamed


def update_wikilinks(mapping: dict[str, str], dry_run: bool = True) -> int:
    """扫描所有 .md,更新 [[CLAIM-NNN_*]] → [[new-slug]]"""
    updated_files = 0

    # 扫描的目录
    dirs = ["paperinfo", "papers", "claims", "evidence", "topics", "syntheses"]
    for d in dirs:
        for md_file in (WIKI_ROOT / d).glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            original = content

            # 替换 [[CLAIM-NNN_<anything>]] → [[new-slug>]]
            for old_id, new_slug in mapping.items():
                # 匹配 [[CLAIM-NNN_xxx]]
                pattern = re.compile(rf"\[\[{re.escape(old_id)}_[^\]]+\]\]")
                content = pattern.sub(f"[[{new_slug}]]", content)

            if content != original:
                updated_files += 1
                if dry_run:
                    print(f"[DRY] Would update: {md_file.relative_to(WIKI_ROOT)}")
                else:
                    md_file.write_text(content, encoding="utf-8")
                    print(f"✅ Updated: {md_file.relative_to(WIKI_ROOT)}")

    return updated_files


def main():
    parser = argparse.ArgumentParser(description="CLAIM-NNN → slug 重命名工具")
    parser.add_argument("--mapping", required=True, help="rename_mapping.md 路径")
    parser.add_argument("--dry-run", action="store_true", help="只显示,不实际执行")
    args = parser.parse_args()

    mapping_file = Path(args.mapping)
    mapping = parse_mapping(mapping_file)

    if not mapping:
        sys.exit(1)

    print(f"\n📋 解析到 {len(mapping)} 个映射:")
    for old, new in list(mapping.items())[:5]:
        print(f"  {old} → {new}")
    if len(mapping) > 5:
        print(f"  ... ({len(mapping) - 5} more)")

    print(f"\n{'[DRY RUN]' if args.dry_run else '[实际执行]'}")

    if not args.dry_run:
        # git tag checkpoint
        git_tag("pre-claim-rename", "Before CLAIM-NNN → slug rename")

    print("\n📁 重命名文件:")
    renamed = rename_files(mapping, dry_run=args.dry_run)

    print("\n🔗 更新 wikilink:")
    updated = update_wikilinks(mapping, dry_run=args.dry_run)

    print("\n📊 总结:")
    print(f"  - 重命名文件: {renamed}")
    print(f"  - 更新 wikilink: {updated} 个文件")

    if not args.dry_run:
        git_tag("post-claim-rename", f"After rename: {renamed} files, {updated} wikilinks updated")
        print("\n✅ 完成。回滚命令:`git reset --hard pre-claim-rename` 或 `jj undo`")
    else:
        print("\n💡 这是 dry-run。加上 `--dry-run`(去掉) 来实际执行。")


if __name__ == "__main__":
    main()