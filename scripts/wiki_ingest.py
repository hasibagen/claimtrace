#!/usr/bin/env python3
"""
wiki_ingest.py — 辅助：复制用户提供的 paper.md 模板到 00-pending/

设计原则：
- paper.md 模板由用户提供（references/templates/paper.md）
- LLM (pi) 用模板**填写**实际字段值
- scripts/ 最多是辅助（文件复制、路径管理）

本脚本只做：
1. 解析论文路径
2. 检查 raw/<id>/full.md 是否存在
3. 复制 references/templates/paper.md 到 00-pending/<id>.md（替换最小占位）
4. 提示 LLM 接管

完整工作流见 references/AGENTS.md §5.7。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


def find_raw_full_md(wiki_root: Path, paper_id: str) -> Path | None:
    """找 raw/<paper_id>/full.md 或 raw/<paper_id>.md。"""
    candidates = [
        wiki_root / "raw" / paper_id / "full.md",
        wiki_root / "raw" / f"{paper_id}.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def paper_id_from_path(paper_path: Path) -> str:
    """
    从路径推断 paper ID：<Author>_<Year>_<short>
    默认：取文件名（不含扩展名）+ 去特殊字符
    """
    name = paper_path.stem
    return name.replace(" ", "_")


def find_user_template(wiki_root: Path, template_name: str = "paper") -> Path | None:
    """找用户提供的 paper.md 模板（按论文类型选择）。

    template_name: paper / paper-fnirs / paper-fmri / paper-eeg /
                   paper-eye-tracking / paper-meta-analysis / paper-review
    """
    candidates = [
        wiki_root / "references" / "templates" / f"{template_name}.md",
        wiki_root / "templates" / f"{template_name}.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    # Fallback: 用 skill 自己的模板（如果用户 wiki 没有）
    skill_root = Path(__file__).parent.parent
    skill_template = skill_root / "references" / "templates" / f"{template_name}.md"
    if skill_template.is_file():
        return skill_template
    return None


def create_pending(wiki_root: Path, paper_path: Path, template_name: str = "paper") -> bool:
    """
    在 00-pending/ 创建骨架。
    复制用户提供的模板 + 替换最小占位（{Title}、{modality}）。

    template_name: paper / paper-fnirs / paper-fmri / paper-eeg /
                   paper-eye-tracking / paper-meta-analysis / paper-review
    """
    # 1. 找 raw full.md
    paper_id = paper_id_from_path(paper_path)
    full_md = find_raw_full_md(wiki_root, paper_id)
    if not full_md:
        wc.eprint(f"Raw full.md not found for {paper_path}")
        wc.eprint("Hint: 用 MinerU 把 PDF 转成 full.md，放在 PDF 同目录或 raw/<id>/ 下")
        return False

    # 2. 找用户模板
    template_path = find_user_template(wiki_root, template_name)
    if not template_path:
        wc.eprint(f"User template not found: {template_name}.md")
        wc.eprint(f"  expected: {wiki_root}/references/templates/{template_name}.md")
        wc.eprint(f"  fallback: {wiki_root}/templates/{template_name}.md")
        return False

    # 3. 检查目标文件
    pending_path = wc.pending_dir(wiki_root) / f"{paper_id}.md"
    if pending_path.exists():
        wc.eprint(f"Already exists: {pending_path}")
        wc.eprint("Hint: 删除或改名后再运行")
        return False

    # 4. 复制模板 + 替换最小占位
    template = wc.read_text(template_path)
    template = template.replace("# {Title}", f"# {paper_id}", 1)
    template = template.replace("{modality}", "unknown")
    # 在 frontmatter 后加注释提示 LLM
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prompt_comment = f"""<!--
  Paper node skeleton created by wiki_ingest.py at {timestamp}
  LLM 任务：
    1. 读取 raw/{paper_id}/full.md
    2. 按 references/AGENTS.md §2.5 抽取 15 个字段
    3. 自由组织 body（不强求固定章节顺序）
    4. 完成后运行 `wiki check-evidence --list` 校验
    5. 用户审阅后移到 papers/
-->
"""
    # 在 frontmatter 之后插入注释
    if "---" in template:
        parts = template.split("---", 2)
        if len(parts) >= 3:
            template = parts[0] + "---" + parts[1] + "---\n" + prompt_comment + parts[2]
        else:
            template = prompt_comment + template
    else:
        template = prompt_comment + template

    wc.write_text(pending_path, template)
    wc.ok(f"Created: {pending_path}")
    wc.eprint(f"  Template: {template_path}")
    wc.eprint("")
    wc.eprint("下一步：让 pi 读取 full.md，按 §2.5 抽取字段填充")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="辅助：复制 paper.md 模板到 00-pending/（让 LLM 接管）",
    )
    parser.add_argument("paper_path", nargs="?", type=Path, default=None, help="Path to paper PDF or full.md（可选）")
    parser.add_argument("--paper-id", type=str, default=None, help="明确指定 paper ID（跳过路径推断）")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")
    parser.add_argument(
        "--template",
        type=str,
        default="paper",
        choices=["paper", "paper-fnirs", "paper-fmri", "paper-eeg",
                 "paper-eye-tracking", "paper-meta-analysis", "paper-review"],
        help="模板类型（按论文研究类型选择；默认 paper）",
    )

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    if args.paper_id:
        # 明确指定 paper_id，不需路径
        create_pending_with_id(wiki_root, args.paper_id, args.template)
        return 0
    elif args.paper_path:
        if not args.paper_path.is_file():
            wc.die(f"Paper not found: {args.paper_path}")
        ok = create_pending(wiki_root, args.paper_path, args.template)
        return 0 if ok else 1
    else:
        wc.die("Either paper_path or --paper-id is required")
        return 1


def create_pending_with_id(wiki_root: Path, paper_id: str, template_name: str = "paper") -> bool:
    """用明确 paper_id 创建骨架（不需 paper_path）。"""
    template_path = find_user_template(wiki_root, template_name)
    if not template_path:
        wc.eprint(f"User template not found: {template_name}.md")
        return False

    full_md = wiki_root / "raw" / paper_id / "full.md"
    if not full_md.is_file():
        wc.eprint(f"Raw full.md not found: {full_md}")
        return False

    pending_path = wc.pending_dir(wiki_root) / f"{paper_id}.md"
    if pending_path.exists():
        wc.eprint(f"Already exists: {pending_path}")
        return False

    template = wc.read_text(template_path)
    template = template.replace("# {Title}", f"# {paper_id}", 1)
    template = template.replace("{modality}", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prompt_comment = f"""<!--
  Paper node skeleton created by wiki_ingest.py at {timestamp}
  LLM 任务：
    1. 读取 raw/{paper_id}/full.md
    2. 按 references/AGENTS.md §2.5 抽取 15 个字段
    3. 自由组织 body（不强求固定章节顺序）
    4. 完成后运行 `wiki check-evidence --list` 校验
    5. 用户审阅后移到 papers/
-->
"""
    if "---" in template:
        parts = template.split("---", 2)
        if len(parts) >= 3:
            template = parts[0] + "---" + parts[1] + "---\n" + prompt_comment + parts[2]
        else:
            template = prompt_comment + template
    else:
        template = prompt_comment + template

    wc.write_text(pending_path, template)
    wc.ok(f"Created: {pending_path}")
    return True


def run(args: list[str]) -> int:
    sys.argv = ["wiki_ingest"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())