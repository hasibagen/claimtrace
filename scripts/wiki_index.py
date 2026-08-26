#!/usr/bin/env python3
"""
wiki_index.py — 重建 INDEX.md

扫描所有 wiki 页面，生成简洁的目录列表。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def extract_title(text: str, fm: dict, fallback: str) -> str:
    """从 H1 或 frontmatter 提取标题。"""
    # 优先 H1
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    # 次选 frontmatter title
    return fm.get("title", fallback)


def collect_pages(wiki_root: Path) -> list[tuple[str, Path, str, dict]]:
    """收集所有 wiki 页面（含子目录和 frontmatter）。"""
    pages = []
    sub_dirs = [
        ("paper", wc.papers_dir(wiki_root)),
        ("topic", wc.topics_dir(wiki_root)),
        ("claim", wc.claims_dir(wiki_root)),
        ("synthesis", wc.syntheses_dir(wiki_root)),
        ("pending", wc.pending_dir(wiki_root)),
    ]

    for kind, d in sub_dirs:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.suffix != ".md":
                continue
            text = wc.read_text(f)
            fm, body = wc.parse_frontmatter(text)
            title = extract_title(body, fm, f.stem)
            pages.append((kind, f, title, fm))

    return pages


def render_index(pages: list[tuple[str, Path, str, dict]], wiki_root: Path) -> str:
    """渲染 INDEX.md。"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    sections = {"paper": [], "topic": [], "claim": [], "synthesis": [], "pending": []}
    section_titles = {
        "paper": "论文 (Papers)",
        "topic": "主题 (Topics)",
        "claim": "主张 (Claims)",
        "synthesis": "综合 (Syntheses)",
        "pending": "待审阅 (Pending)",
    }

    for kind, path, title, fm in pages:
        rel = path.relative_to(wiki_root)
        tags = fm.get("tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        else:
            tags = str(tags) if tags else ""
        line = f"- `[{rel}]({rel})` — {title}"
        if tags:
            line += f" (tags: {tags})"
        sections[kind].append(line)

    lines = [
        "# Wiki 索引",
        "",
        f"> 最后更新: {today}",
        "",
        "四类平等节点 + 待审阅队列。论文 ↔ 主题通过 `[[wikilink]]` 自然形成多对多关系（见 Obsidian Graph View）。",
        "",
    ]

    for kind in ["paper", "topic", "claim", "synthesis", "pending"]:
        lines.append(f"## {section_titles[kind]}")
        lines.append("")
        if sections[kind]:
            lines.extend(sections[kind])
        else:
            lines.append("（暂无）")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 反向索引（按主题聚合的论文）")
    lines.append("")
    lines.append("（待主题节点创建后自动填充）")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild INDEX.md")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")
    args = parser.parse_args()

    wiki_root = args.wiki_root or wc.find_wiki_root()
    pages = collect_pages(wiki_root)
    index_content = render_index(pages, wiki_root)

    index_path = wc.index_file(wiki_root)
    wc.write_text(index_path, index_content)
    wc.ok(f"Rebuilt {index_path} with {len(pages)} pages")
    return 0


def run(args: list[str]) -> int:
    sys.argv = ["wiki_index"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())