#!/usr/bin/env python3
"""
wiki_aggregate_claims.py — claim 证据聚合预计算(批次4,ChatGPT §26)

从 evidence frontmatter 的边数组 + verify_n **确定性**聚合出 claim 级统计表,
喂给 synthesis 的 Evidence Matrix——synthesis 的 LLM 只负责叙事,数字全部来自本脚本。

输出(每 claim 一块 markdown,可粘贴进 synthesis):
  - supporting / contradicting 证据数与总 N(去重按论文)
  - 涉及论文列表(sources)
  - 每条证据的关键数值(stat/effect/p + test_method)
  - CONFLICTING 标记(supports∩contradicts 均非空)

用法:python3 wiki_aggregate_claims.py [claim 名 ...]   # 不带参数=输出全部 CONFLICTING 优先
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def load_fm(p: Path) -> dict:
    m = FM_RE.match(p.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _name(link) -> str:
    if isinstance(link, list):
        link = link[0] if link else ""
    return str(link).strip().strip("[]").split("|")[0].strip().split("/")[-1]


def _wl(link) -> str:
    n = _name(link)
    return f"[[{n}]]" if n else "—"


def aggregate(wiki_root: Path, claim_name: str) -> str | None:
    cf = wiki_root / "claims" / f"{claim_name}.md"
    if not cf.is_file():
        return None
    cfm = load_fm(cf)
    ev_names = [_name(x) for x in (cfm.get("evidence_targets") or [])]
    # 双向:evidence 侧 supports/contradicts 指向本 claim 的也纳入(批次4补)
    for ef in (wiki_root / "evidence").glob("*.md"):
        efm = load_fm(ef)
        if (any(_name(x) == claim_name for x in (efm.get("supports_targets") or [])) or
            any(_name(x) == claim_name for x in (efm.get("contradicts_targets") or []))):
            if ef.stem not in ev_names:
                ev_names.append(ef.stem)

    rows = []
    papers = set()
    n_total = 0
    for evn in ev_names:
        ef = wiki_root / "evidence" / f"{evn}.md"
        if not ef.is_file():
            continue
        efm = load_fm(ef)
        paper = _name(efm.get("prov_paper") or efm.get("source"))
        papers.add(paper)
        try:
            n_total += int(efm.get("verify_n") or 0)
        except (TypeError, ValueError):
            pass
        nums = []
        for lbl, k1, k2 in (("stat", "verify_test_stat_type", "verify_test_stat_value"),
                            ("eff", "verify_effect_size_type", "verify_effect_size_value"),
                            ("p", None, "verify_p_value")):
            v = efm.get(k2) if k2 else None
            t = efm.get(k1) if k1 else lbl
            if v not in (None, "", "null"):
                nums.append(f"{t}={v}" if t else f"p={v}")
        sup = "✓" if any(_name(x) == claim_name for x in (efm.get("supports_targets") or [])) else (
            "✗" if any(_name(x) == claim_name for x in (efm.get("contradicts_targets") or [])) else "·")
        rows.append(f"| [[{evn}]] | {_wl(paper)} | {sup} | {', '.join(nums) or '—'} |")

    sup_n = len([r for r in rows if "| ✓ |" in r])
    con_n = len([r for r in rows if "| ✗ |" in r])
    flag = " ⚡CONFLICTING" if sup_n and con_n else ""
    out = [f"### [[{claim_name}]]{flag}",
           f"- 证据 {len(rows)} 条(✓{sup_n} / ✗{con_n}) · 涉及论文 {len(papers)} 篇 · N 合计 {n_total}",
           "- 论文: " + " ".join(f"[[{p}]]" for p in sorted(papers) if p),
           "", "| 证据 | 论文 | 方向 | 关键数值 |", "|---|---|---|---|"]
    out.extend(rows or ["| — | — | — | — |"])
    return "\n".join(out)


def main() -> int:
    root = Path(__file__).resolve().parent.parent.parent
    import wiki_stat_sanity as wss
    args = sys.argv[1:]
    if not args:
        confs = [c.replace("CONFLICT[", "").split("]")[0] for c in wss.conflicting(root)]
        args = confs[:10]
        print(f"(未指定 claim,输出前 {len(args)} 个 CONFLICTING)\n")
    for name in args:
        block = aggregate(root, name)
        if block:
            print(block + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
