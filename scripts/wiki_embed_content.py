#!/usr/bin/env python3
"""
wiki_embed_content.py — 把 claims/evidence/topics/mechanisms 的完整内容嵌入 paper.md

目的: 让每篇 paper.md 自包含 — 阅读时不需要打开其他节点,所有内容都在这一页。
同时保留 wikilink,让 Obsidian Backlinks 面板照常工作。

用法:
  python3 wiki_embed_content.py <citekey>          # 单篇
  python3 wiki_embed_content.py --all              # 所有 papers/
  python3 wiki_embed_content.py --dry-run <citekey> # 只显示, 不写入
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def read_frontmatter_and_body(md_path: Path) -> tuple[dict, str]:
    """解析 YAML frontmatter 和 body"""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    body = parts[2].lstrip("\n")
    # 简单解析 frontmatter (只读 claims/evidence 字段)
    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def extract_wikilinks(text: str) -> list[str]:
    """提取所有 [[xxx]] 形式的 wikilink"""
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def render_node_inline(node_path: Path, node_type: str) -> str:
    """渲染单个节点(claim/evidence/topic/mechanism)为可嵌入的 markdown"""
    text = node_path.read_text(encoding="utf-8")

    # 提取标题 (H1)
    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = title_match.group(1) if title_match else node_path.stem

    # 提取 body (H1 之后)
    body = re.sub(r"^# .+\n+", "", text, count=1, flags=re.MULTILINE)

    # 简单 YAML 解析: 提取关键字段
    fm_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL | re.MULTILINE)
    fm_lines = []
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ["claim_statement", "topic_description", "evidence_strength",
                         "primary_source", "ceric", "grade", "author_claim_type",
                         "empirical_evidence_type", "causal_inference_supported"]:
                    fm_lines.append(f"- **{k}**: {v}")

    # 嵌入模板
    icon = {"claim": "📑", "evidence": "📊", "topic": "📁", "mechanism": "⚙️"}.get(node_type, "📄")
    wikilink = f"[[{node_path.parent.name}/{node_path.stem}]]"

    embed = f"\n### {icon} {wikilink}\n\n"
    if fm_lines:
        embed += "\n".join(fm_lines) + "\n\n"
    embed += f"> **详细内容**:\n\n{body.strip()}\n\n"

    return embed


def embed_into_paper(paper_path: Path, wiki_root: Path, dry_run: bool = False) -> str:
    """把 paper.md 引用的所有 claim/evidence/topic/mechanism 内容嵌入"""
    text = paper_path.read_text(encoding="utf-8")
    fm, body = read_frontmatter_and_body(paper_path)

    # 收集所有 wikilink 引用的节点
    wikilinks = set(extract_wikilinks(body))

    # 按节点类型分组
    grouped = {"claims/": [], "evidence/": [], "topics/": [], "mechanisms/": []}
    for link in wikilinks:
        for prefix in grouped:
            if link.startswith(prefix):
                grouped[prefix].append(link)
                break

    # 构建嵌入内容
    embed_sections = []
    for prefix, links in grouped.items():
        if not links:
            continue
        node_type = prefix.rstrip("/")
        embed_sections.append(f"\n---\n\n## 📚 嵌入内容 ({node_type})\n")
        for link in sorted(links):
            # link 格式: "claims/<semantic-slug>" 或 "evidence/<author>-<year>-<slug>"(ARCHITECTURE §2.3 无编号)
            node_path = wiki_root / f"{link}.md"
            if not node_path.is_file():
                wc.eprint(f"  ⚠️ 节点不存在: {node_path}")
                continue
            embed_sections.append(render_node_inline(node_path, node_type.rstrip("s")))

    embed_content = "".join(embed_sections)

    # 在 paper.md 末尾追加(保留原内容)
    new_body = body + "\n" + embed_content

    if dry_run:
        wc.ok(f"[DRY-RUN] {paper_path.name}: 将嵌入 {sum(len(v) for v in grouped.values())} 个节点")
        return new_body

    # 写回 (保留 frontmatter)
    new_text = f"---\n{fm.get('_raw', '')}\n---\n\n{new_body}"
    paper_path.write_text(new_text, encoding="utf-8")
    wc.ok(f"✓ {paper_path.name}: 嵌入 {sum(len(v) for v in grouped.values())} 个节点")
    return new_body


def main() -> int:
    parser = argparse.ArgumentParser(
        description="把 claim/evidence/topic/mechanism 内容嵌入 paper.md"
    )
    parser.add_argument("citekey", nargs="?", help="论文 citekey")
    parser.add_argument("--all", action="store_true", help="处理所有 papers/")
    parser.add_argument("--dry-run", action="store_true", help="只显示, 不写入")
    parser.add_argument("--wiki-root", type=Path, default=None)

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    if args.all:
        papers_dir = wiki_root / "papers"
        if not papers_dir.is_dir():
            wc.die(f"papers/ 目录不存在: {papers_dir}")
        for paper in sorted(papers_dir.glob("*.md")):
            embed_into_paper(paper, wiki_root, dry_run=args.dry_run)
        return 0

    if args.citekey:
        paper_path = wiki_root / "papers" / f"{args.citekey}.md"
        if not paper_path.is_file():
            wc.die(f"paper 不存在: {paper_path}")
        embed_into_paper(paper_path, wiki_root, dry_run=args.dry_run)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())