#!/usr/bin/env python3
"""
wiki_promote.py — S7 promote 闸门(ARCHITECTURE §5.0 S7,2026-08-25 脚本化)

三条件过闸(全部机械校验,无 LLM):
  ① L1.5:00-pending/<citekey>/{claims,evidence} 的 frontmatter schema 校验 0 error
  ② banner:全部 evidence/claim body 含 AUTO-RENDERED-BODY,且与 frontmatter 重渲染一致
     (陈旧 body 带 banner 也过不了——内存重渲染 diff 为空才过)
  ③ 无 raw_path:evidence frontmatter 不含已废除的 raw_path 字段(§15.4.11)

用法:
  python3 wiki_promote.py <citekey> --check      # 只预检
  python3 wiki_promote.py <citekey> --execute    # 过闸后执行 promote
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "schemas"))
import wiki_common as wc
import _registry
import wiki_render_nodes as wrn

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def gate_check(wiki_root: Path, citekey: str) -> tuple[bool, list[str]]:
    """返回 (是否过闸, 失败清单)。"""
    errors: list[str] = []
    pending = wiki_root / "00-pending" / citekey
    if not pending.is_dir():
        return False, [f"00-pending/{citekey} 不存在"]

    claim_files = sorted((pending / "claims").glob("*.md")) if (pending / "claims").is_dir() else []
    ev_files = sorted((pending / "evidence").glob("*.md")) if (pending / "evidence").is_dir() else []
    paper_file = pending / f"{citekey}.md"
    if not paper_file.is_file():
        errors.append(f"缺少主文件 00-pending/{citekey}/{citekey}.md")
    if not claim_files and not ev_files:
        errors.append("claims/ 与 evidence/ 均为空(骨架未抽取,不允许 promote)")

    # ① L1.5 schema
    for f, kind in [(x, "claim") for x in claim_files] + [(x, "evidence") for x in ev_files]:
        text = f.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            errors.append(f"① {f.name}: 无 frontmatter")
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            errors.append(f"① {f.name}: YAML 解析失败 {str(e)[:60]}")
            continue
        ok, err = _registry.validate(kind, fm)
        if not ok:
            errors.append(f"① {f.name}: {(err or '')[:100]}")

    # ② banner + 渲染一致性(内存重渲染比对;反向索引用真实索引,与渲染器行为一致)
    rev = wrn.build_reverse_index(wiki_root, skip_body_scan=set())
    for f, kind in [(x, "claim") for x in claim_files] + [(x, "evidence") for x in ev_files]:
        content = f.read_text(encoding="utf-8")
        if "AUTO-RENDERED-BODY" not in content:
            errors.append(f"② {f.name}: body 无 AUTO-RENDERED-BODY banner")
            continue
        m = FM_RE.match(content)
        fm = yaml.safe_load(m.group(1)) or {}
        fm_raw, _ = wrn.split_file(content)
        if kind == "evidence":
            rendered = wrn.render_evidence_body(fm, f.stem, rev, wrn.load_schema_for_promote())
        else:
            rendered = wrn.render_claim_body(fm, f.stem, rev)
        # 与 process_nodes 完全一致的拼接(fm_raw + body.lstrip)
        expected = fm_raw + rendered.lstrip("\n")
        if content.strip() != expected.strip():
            errors.append(f"② {f.name}: body 与 frontmatter 重渲染不一致(陈旧,请重跑渲染器)")

    # ③ raw_path
    for f in ev_files:
        m = FM_RE.match(f.read_text(encoding="utf-8"))
        if m and re.search(r"^raw_path\s*:", m.group(1), re.MULTILINE):
            errors.append(f"③ {f.name}: 含已废除的 raw_path 字段(§15.4.11)")

    return (not errors), errors


def do_promote(wiki_root: Path, citekey: str) -> list[str]:
    """执行移动;返回日志行。"""
    pending = wiki_root / "00-pending" / citekey
    moved = []
    pairs = []
    paper_src = pending / f"{citekey}.md"
    if paper_src.is_file():
        pairs.append((paper_src, wiki_root / "papers"))
    for sub, dest in (("claims", wiki_root / "claims"), ("evidence", wiki_root / "evidence")):
        d = pending / sub
        if d.is_dir():
            pairs.extend((c, dest) for c in sorted(d.glob("*.md")))
    for src, dest_dir in pairs:
        shutil.move(str(src), str(dest_dir / src.name))
        moved.append(f"{src.relative_to(wiki_root)} → {dest_dir.name}/{src.name}")
    # 清理空目录
    for sub in ("claims", "evidence"):
        d = pending / sub
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    if pending.is_dir() and not any(pending.iterdir()):
        pending.rmdir()
    return moved


def main() -> int:
    ap = argparse.ArgumentParser(description="S7 promote 闸门")
    ap.add_argument("citekey")
    ap.add_argument("--check", action="store_true", help="只预检")
    ap.add_argument("--execute", action="store_true", help="过闸后执行")
    args = ap.parse_args()

    wiki_root = Path(__file__).resolve().parent.parent.parent
    ok, errors = gate_check(wiki_root, args.citekey)

    if errors:
        print(f"❌ {args.citekey} 未过闸({len(errors)} 项):")
        for e in errors:
            print("  -", e)
        return 1
    print(f"✅ {args.citekey} 过闸(L1.5=0 + banner 一致 + 无 raw_path)")

    if args.execute:
        moved = do_promote(wiki_root, args.citekey)
        for m in moved:
            print("  📦", m)
        with open(wiki_root / "log.md", "a", encoding="utf-8") as f:
            f.write(f"\n## [promote] {args.citekey}\n" + "\n".join(f"- {m}" for m in moved) + "\n")
        print("→ 建议随后:wiki_link_paper.py + wiki_render_nodes.py paper papers/ + lint 全量")
    elif not args.check:
        print("(预检通过;加 --execute 执行移动)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
