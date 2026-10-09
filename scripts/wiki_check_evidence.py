#!/usr/bin/env python3
"""
wiki_check_evidence.py — 证据校验脚本

验证 paper 节点中的具体数值/quote 是否能在 raw full.md 中 grep 得到。
参考 Karpathy check_evidence.py 思路。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

# 允许从同目录导入
sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def find_raw_full_md(paper_id: str, wiki_root: Path) -> Optional[Path]:
    """
    找 raw/<paper_id>/full.md。
    候选路径：
      1. raw/<paper_id>/full.md
      2. raw/<paper_id>.md
    """
    candidates = [
        wiki_root / "raw" / paper_id / "full.md",
        wiki_root / "raw" / paper_id,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def find_paper_file(paper_id: str, wiki_root: Path) -> Optional[Path]:
    """找 papers/<paper_id>.md 或 00-pending/<paper_id>.md"""
    for sub in ("papers", "00-pending"):
        p = wiki_root / sub / f"{paper_id}.md"
        if p.is_file():
            return p
    return None


def extract_candidates(text: str) -> list[str]:
    """
    抽取候选可校验的字面值。
    包括：千分位数字、点分数字、ISO 日期、≥15 字符的引用片段。
    """
    candidates = []

    # 数字（带千分位或小数）
    for m in re.finditer(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d+\b", text):
        candidates.append(m.group())

    # ISO 日期
    for m in re.finditer(r"\b\d{4}-\d{2}-\d{2}\b", text):
        candidates.append(m.group())

    # 长引用片段（≥15 字符）
    for m in re.finditer(r'"([^"]{15,})"', text):
        candidates.append(m.group(1))

    return candidates


def normalize_text(s: str) -> str:
    """
    归一化文本(批次1.2,langextract/GPT 共识):消除 MinerU OCR 与 LLM 复述之间的
    Unicode 差异——NFKC + 弯引号/撇号/长破折号 + 空白折叠。
    """
    import unicodedata
    s = unicodedata.normalize("NFKC", s)
    for src, dst in (
        ("\u201c", '"'), ("\u201d", '"'),   # 弯双引号
        ("\u2018", "'"), ("\u2019", "'"),   # 弯单引号
        ("\u2014", "-"), ("\u2013", "-"), ("\u2212", "-"),  # em/en/minus 破折号
        ("\u00b7", "."),                     # 间隔号
        ("\u2026", "..."),                   # 省略号
    ):
        s = s.replace(src, dst)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def verify_in_source(value: str, source_text: str) -> str:
    """
    检查 value 是否在 source_text 中,返回三态(批次1.2,langextract 方案):
      "exact"  — 归一化后精确子串命中
      "fuzzy"  — LCS/词覆盖率 ≥ 0.75(容忍 OCR 变体、局部改写)
      "none"   — 找不到(疑似幻觉,退回 LLM 重写)
    """
    # 1. 原样精确
    if value in source_text:
        return "exact"

    v_n = normalize_text(value)
    s_n = normalize_text(source_text)

    # 2. 归一化后精确(去千分位逗号 + 空白折叠)
    if v_n.replace(",", "") in s_n.replace(",", ""):
        return "exact"

    # 3. 模糊回退:词级覆盖率(langextract fuzzy_alignment_threshold=0.75)
    #    窗口定位:用 value 的前几个词在 source 中找锚点,取窗口算覆盖率
    v_tokens = [t for t in v_n.split() if t]
    if not v_tokens:
        return "none"
    anchor = " ".join(v_tokens[:4])
    pos = s_n.find(anchor[: min(len(anchor), 40)])
    if pos < 0:
        # 退化:用最长 token 定位
        longest = max(v_tokens, key=len)
        pos = s_n.find(longest)
        if pos < 0:
            return "none"
    window = s_n[max(0, pos - 200): pos + len(v_n) + 600]
    window_tokens = set(window.split())
    hits = sum(1 for t in v_tokens if t in window_tokens)
    coverage = hits / len(v_tokens)
    return "fuzzy" if coverage >= 0.75 else "none"


def check_paper(paper_id: str, wiki_root: Path) -> tuple[int, int, list[str]]:
    """
    检查单篇 paper 节点。
    返回 (verified_count, unverified_count, unverified_list)。
    """
    paper_file = find_paper_file(paper_id, wiki_root)
    if not paper_file:
        wc.die(f"Paper not found: {paper_id}")

    raw_file = find_raw_full_md(paper_id, wiki_root)
    if not raw_file:
        wc.die(f"Raw full.md not found for {paper_id}")

    paper_text = wc.read_text(paper_file)
    source_text = wc.read_text(raw_file)

    candidates = extract_candidates(paper_text)

    verified = 0          # exact
    fuzzy = 0             # fuzzy(通过,但单独计数)
    unverified: list[str] = []

    for value in candidates:
        status = verify_in_source(value, source_text)
        if status == "exact":
            verified += 1
        elif status == "fuzzy":
            verified += 1
            fuzzy += 1
        else:
            unverified.append(value)

    return verified, len(unverified), unverified


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that paper's numeric values/quotes are grep-able in raw full.md",
    )
    parser.add_argument(
        "paper_id",
        nargs="+",
        help="Paper ID(s) to check (e.g., Smith_2020_WM_Reading)",
    )
    parser.add_argument(
        "--wiki-root",
        type=Path,
        default=None,
        help="Wiki root directory (default: auto-detect)",
    )

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    total_v, total_uv = 0, 0
    all_unverified: dict[str, list[str]] = {}

    for pid in args.paper_id:
        v, uv, uv_list = check_paper(pid, wiki_root)
        total_v += v
        total_uv += uv
        all_unverified[pid] = uv_list

        if uv == 0:
            wc.ok(f"{pid}: {v} verified, 0 unverified")
        else:
            wc.eprint(f"⚠ {pid}: {v} verified, {uv} unverified")
            for val in uv_list[:5]:  # 最多显示前 5 个
                wc.eprint(f"    - {val[:80]}")
            if len(uv_list) > 5:
                wc.eprint(f"    ... and {len(uv_list) - 5} more")

    wc.eprint("")
    wc.eprint(f"Total: {total_v} verified, {total_uv} unverified")

    return 1 if total_uv > 0 else 0


def run(args: list[str]) -> int:
    """供统一 CLI 调用。"""
    sys.argv = ["wiki_check_evidence"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())