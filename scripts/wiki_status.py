#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本状态报告逻辑可保留,但部分输出仍引用 CLAIM-NNN 编号
(ARCHITECTURE §2.3 已废)。新统计用 wiki-lint-wiki Skill + scripts/_registry.py。
如继续使用此脚本,需更新 CLAIM 计数逻辑。
原 docstring 保留如下:

wiki_status.py — Wiki 状态报告

显示节点数、CLAIM 状态、最后操作时间等。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def count_md_files(dir_path: Path) -> int:
    if not dir_path.is_dir():
        return 0
    return sum(1 for f in dir_path.iterdir() if f.suffix == ".md")


def count_claims_by_status(wiki_root: Path) -> dict[str, int]:
    """统计 CLAIM 状态。"""
    status_count = {"candidate": 0, "promoted": 0, "active": 0, "deprecated": 0, "unknown": 0}
    papers_dir = wc.papers_dir(wiki_root)

    if not papers_dir.is_dir():
        return status_count

    for f in papers_dir.iterdir():
        if f.suffix != ".md":
            continue
        text = wc.read_text(f)
        # CLAIM 后的 `关联: [candidate]` 或 `[[CLAIM-XXX]]`
        if "关联: [candidate]" in text:
            status_count["candidate"] += 1
        elif "[[CLAIM-" in text:
            status_count["promoted"] += 1
        elif "CLAIM-" in text:
            status_count["unknown"] += 1

    return status_count


def get_last_log_entry(wiki_root: Path) -> str:
    """读 log.md 最后一条。"""
    log_path = wc.log_file(wiki_root)
    if not log_path.is_file():
        return "(no log)"
    text = wc.read_text(log_path)
    lines = [l for l in text.splitlines() if l.startswith("## [")]
    return lines[-1] if lines else "(empty log)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Evidence Wiki status")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    papers = count_md_files(wc.papers_dir(wiki_root))
    topics = count_md_files(wc.topics_dir(wiki_root))
    claims = count_md_files(wc.claims_dir(wiki_root))
    syntheses = count_md_files(wc.syntheses_dir(wiki_root))
    pending = count_md_files(wc.pending_dir(wiki_root))
    claim_status = count_claims_by_status(wiki_root)

    if args.json:
        import json
        print(json.dumps({
            "wiki_root": str(wiki_root),
            "papers": papers,
            "topics": topics,
            "claims": claims,
            "claim_status": claim_status,
            "syntheses": syntheses,
            "pending": pending,
            "last_log": get_last_log_entry(wiki_root),
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"Evidence Wiki status ({wiki_root}):")
    print(f"  Papers:       {papers}")
    print(f"  Topics:       {topics}")
    print(f"  Claims:       {claims} ({sum(claim_status.values())} inline refs)")
    print(f"    - candidate: {claim_status['candidate']}")
    print(f"    - promoted:  {claim_status['promoted']}")
    print(f"    - active:    {claim_status['active']}")
    print(f"  Syntheses:    {syntheses}")
    print(f"  Pending:      {pending} (待审阅)")
    print(f"  Last log:     {get_last_log_entry(wiki_root)}")
    return 0


def run(args: list[str]) -> int:
    sys.argv = ["wiki_status"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())