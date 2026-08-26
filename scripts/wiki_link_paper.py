#!/usr/bin/env python3
"""
wiki_link_paper_to_evidence_claim.py — 批次2.3 桥接(Batch 2 修复)

paper frontmatter 缺 related_evidence / related_claims → Transclusion 嵌入段空。
本脚本从 evidence.supports_targets 反推到源 paper.related_evidence;
从 claim.sources_targets 反推到 paper.related_claims。
幂等(单字段去重 + 排序)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "schemas"))
import wiki_common as wc

FM_RE = __import__("re").compile(r"^---\s*\n(.*?)\n---\s*\n?", __import__("re").DOTALL)


def split_fm_body(content: str):
    m = FM_RE.match(content)
    if not m:
        return "", content
    return content[: m.end()], content[m.end():]


def load_fm(content: str) -> dict:
    m = FM_RE.match(content)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _wikilink_name(link) -> str:
    if isinstance(link, list):
        link = link[0] if link else ""
    s = str(link).strip().strip("[]").split("|")[0].strip()
    return s.split("/")[-1].strip()


def _as_list(v) -> list[str]:
    if v is None: return []
    if isinstance(v, list): return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    return [s] if s else []


def add_paper_field(wiki_root: Path, citekey: str, field: str, vals: list[str]) -> bool:
    """在 papers/<citekey>.md frontmatter 添加/合并 field 数组(去重+排序,幂等)。"""
    p = wiki_root / "papers" / f"{citekey}.md"
    if not p.is_file():
        return False
    fm_raw, body = split_fm_body(p.read_text(encoding="utf-8"))
    if not fm_raw:
        return False
    fm = load_fm(fm_raw)
    existing = _as_list(fm.get(field))
    merged = sorted(set(existing) | {v for v in vals if v})
    if merged == existing:
        return False
    fm[field] = merged
    # 批次修复 2026-08-25:改用 dump_frontmatter_safe(拍平嵌套 + wikilink 强制引号),
    # 旧 write_frontmatter 会把 [[x]] 写成无引号 → 下次解析成嵌套列表(papers 损坏事故链)
    p.write_text(wc.dump_frontmatter_safe(fm, body), encoding="utf-8")
    return True


def main() -> int:
    wiki_root = Path(__file__).resolve().parent.parent.parent
    # evidence → paper.related_evidence(从 source / prov_paper)
    paper_to_evs: dict[str, set[str]] = {}
    ev_dir = wiki_root / "evidence"
    if ev_dir.is_dir():
        for f in ev_dir.glob("*.md"):
            fm = load_fm(f.read_text(encoding="utf-8"))
            src = fm.get("prov_paper") or fm.get("source")
            if not src:
                continue
            pk = _wikilink_name(src)
            if pk:
                paper_to_evs.setdefault(pk, set()).add(f.stem)

    # claim → paper.related_claims(从 sources_targets)
    paper_to_claims: dict[str, set[str]] = {}
    cl_dir = wiki_root / "claims"
    if cl_dir.is_dir():
        for f in cl_dir.glob("*.md"):
            fm = load_fm(f.read_text(encoding="utf-8"))
            for src in _as_list(fm.get("sources_targets")):
                pk = _wikilink_name(src)
                if pk:
                    paper_to_claims.setdefault(pk, set()).add(f.stem)

    changes = 0
    for pk, evs in paper_to_evs.items():
        if add_paper_field(wiki_root, pk, "related_evidence", sorted(evs)):
            changes += 1
    for pk, cs in paper_to_claims.items():
        if add_paper_field(wiki_root, pk, "related_claims", sorted(cs)):
            changes += 1

    print(f"paper frontmatter 补字段: {changes} 个文件已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
