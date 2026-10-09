#!/usr/bin/env python3
"""
wiki_search.py — 跨论文检索

按关键词搜索 papers/、topics/、claims/、syntheses/ 中的所有 markdown 文件。
支持 frontmatter title/tags/description 和 body 全文搜索。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def search_in_files(files: list[Path], query: str, max_results: int = 10) -> list[tuple[Path, int, str]]:
    """
    在给定文件列表中搜索 query。
    返回 [(file_path, score, snippet), ...]
    """
    query_lower = query.lower()
    query_words = re.findall(r"\w+", query_lower)

    results = []

    for f in files:
        text = wc.read_text(f)
        if not text:
            continue

        text_lower = text.lower()

        # 评分：frontmatter 命中 +2，正文命中 +1
        score = 0
        fm, body = wc.parse_frontmatter(text)

        # Frontmatter title/tags/description 加权
        for key in ("title", "tags", "description"):
            value = fm.get(key, "")
            if isinstance(value, list):
                value = " ".join(value)
            value_lower = value.lower()
            for w in query_words:
                if w in value_lower:
                    score += 3

        # 正文命中
        for w in query_words:
            score += text_lower.count(w)

        if score > 0:
            # 提取 snippet
            snippet = extract_snippet(body or text, query_words)
            results.append((f, score, snippet))

    results.sort(key=lambda x: -x[1])
    return results[:max_results]


def extract_snippet(text: str, query_words: list[str], context_chars: int = 80) -> str:
    """提取包含 query 的 snippet。"""
    text_lower = text.lower()
    for w in query_words:
        idx = text_lower.find(w)
        if idx >= 0:
            start = max(0, idx - context_chars)
            end = min(len(text), idx + len(w) + context_chars)
            snippet = text[start:end].replace("\n", " ")
            return f"...{snippet}..."
    return text[:200].replace("\n", " ")


def collect_all_pages(wiki_root: Path) -> list[Path]:
    """收集所有 wiki 页面（含 00-pending/）。"""
    files = []
    for sub in ("papers", "topics", "claims", "syntheses", "00-pending"):
        d = wiki_root / sub
        if d.is_dir():
            for f in d.iterdir():
                if f.suffix == ".md":
                    files.append(f)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-paper search in Evidence Wiki")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")
    parser.add_argument("--max-results", type=int, default=10, help="Max results")
    parser.add_argument("--include-pending", action="store_true", help="Include 00-pending/")

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    files = collect_all_pages(wiki_root)
    if not args.include_pending:
        files = [f for f in files if not str(f).startswith(str(wc.pending_dir(wiki_root)))]

    results = search_in_files(files, args.query, args.max_results)

    if not results:
        wc.eprint(f"No results for '{args.query}'")
        return 1

    for path, score, snippet in results:
        rel = path.relative_to(wiki_root)
        print(f"\n{rel} (score={score})")
        print(f"  {snippet}")

    return 0


def run(args: list[str]) -> int:
    sys.argv = ["wiki_search"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())