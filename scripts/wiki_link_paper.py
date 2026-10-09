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


def resolve_paper_path(wiki_root: Path, citekey: str) -> Path | None:
    """paper 节点定位:正式区 papers/<ck>.md 优先;否则 00-pending/<ck>/<ck>.md(2026-09-05 夜班:补嵌套 pending 布局)。"""
    for cand in (wiki_root / "papers" / f"{citekey}.md",
                 wiki_root / "00-pending" / citekey / f"{citekey}.md"):
        if cand.is_file():
            return cand
    return None


def add_paper_field(wiki_root: Path, citekey: str, field: str, vals: list[str]) -> bool:
    """在 paper 节点(正式区或 pending)frontmatter 添加/合并 field 数组(去重+排序,幂等)。"""
    p = resolve_paper_path(wiki_root, citekey)
    if p is None:
        return False
    fm_raw, body = split_fm_body(p.read_text(encoding="utf-8"))
    if not fm_raw:
        return False
    fm = load_fm(fm_raw)
    existing = _as_list(fm.get(field))
    merged = sorted({str(x).strip() for x in existing} | {v for v in vals if v})
    if merged == existing:
        return False
    fm[field] = merged
    # 批次修复 2026-08-25:改用 dump_frontmatter_safe(拍平嵌套 + wikilink 强制引号),
    # 旧 write_frontmatter 会把 [[x]] 写成无引号 → 下次解析成嵌套列表(papers 损坏事故链)
    p.write_text(wc.dump_frontmatter_safe(fm, body), encoding="utf-8")
    return True


def main() -> int:
    wiki_root = Path(__file__).resolve().parent.parent.parent
    # evidence → paper.related_evidence(从 source / prov_paper);含 00-pending/<ck>/evidence/
    def evidence_files():
        yield from (wiki_root / "evidence").glob("*.md")
        pend = wiki_root / "00-pending"
        if pend.is_dir():
            for d in sorted(pend.iterdir()):
                if d.is_dir():
                    yield from (d / "evidence").glob("*.md")

    paper_to_evs: dict[str, set[str]] = {}
    for f in evidence_files():
        fm = load_fm(f.read_text(encoding="utf-8"))
        src = fm.get("prov_paper") or fm.get("source")
        if not src:
            continue
        pk = _wikilink_name(src)
        if pk:
            paper_to_evs.setdefault(pk, set()).add(f"[[{f.stem}]]")

    # claim → paper.related_claims(从 sources_targets);含 00-pending/<ck>/claims/
    def claim_files():
        yield from (wiki_root / "claims").glob("*.md")
        pend = wiki_root / "00-pending"
        if pend.is_dir():
            for d in sorted(pend.iterdir()):
                if d.is_dir():
                    yield from (d / "claims").glob("*.md")

    paper_to_claims: dict[str, set[str]] = {}
    for f in claim_files():
        fm = load_fm(f.read_text(encoding="utf-8"))
        for src in _as_list(fm.get("sources_targets")):
            pk = _wikilink_name(src)
            if pk:
                paper_to_claims.setdefault(pk, set()).add(f"[[{f.stem}]]")

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
