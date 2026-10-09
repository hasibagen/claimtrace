#!/usr/bin/env python3
"""
wiki_init.py — 初始化 wiki 结构

创建 AGENTS.md、index.md、log/ops.md 和子目录（00-pending/、papers/、topics/、claims/、syntheses/）。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


AGENTS_TEMPLATE = """# AGENTS.md — 证据 Wiki 操作规范

> **本文件由 `wiki init` 自动生成**。pi 在第一次处理本目录时，应当完整阅读本文件。
> 阅读后，所有页面写入与维护操作都必须遵守本规范。

---

## 0. 角色与边界

你是这个学术证据 Wiki 的**长期维护者**。

- 你的输入：用户提供的论文路径（Zotero PDF 或 MinerU full.md），或用户的提问。
- 你的输出：写入 `papers/`、`topics/`、`claims/`、`syntheses/` 等节点的 Markdown 页面；维护 `index.md` 与 `log/ops.md`。
- 你的禁区：**永不修改原始层**（Zotero 库、MinerU 导出目录）。

---

## 1. 节点模型与目录约定

四类节点：Paper / Topic / Claim / Synthesis。详见 references/AGENTS.md（如果存在）。

---

## 2. 字段命名与样式约定

字段标题用 `**xxx**` 而非 `#`（兼容 MinerU 输出）。页面顶级标题用 `# Title`。

---

## 3. CLAIM / EVIDENCE / RELATION 逻辑

CLAIM 状态机：paper-inline → candidate → promoted → active。

CLAIM 升级三选一触发条件：
1. 有张力（SUPPORT/CONTRADICT/QUALIFY 至少两种并存）
2. 被查询（用户明确追踪或提问）
3. 可综合（是某个 synthesis 的直接前提）

---

## 4. wikilink 约定

用 Obsidian wikilink(ARCHITECTURE §15.4.6 规定):
- `[[papers/<BBT-citekey>]]` — 论文节点(显式 papers/ 前缀,避免 paperinfo/ 歧义)
- `[[paperinfo/<BBT-citekey>]]` — Zotero 元数据节点
- `[[claims/<semantic-slug>]]` — claim 节点(无编号,kebab-case)
- `[[evidence/<author>-<year>-<slug>]]` — evidence 节点

---

## 5. 工作流

每次写入新节点必须：
1. 写入对应目录
2. 更新 `index.md`
3. 追加 `log/ops.md`：`## [YYYY-MM-DD] <op> | <summary>`

详细工作流见 references/AGENTS.md。

---

## 9. 一句话总结

> 让 pi 把论文 PDF → 一张可追溯的证据图，靠 Obsidian wikilink 自然形成多对多关联，用户负责审阅与质疑。
"""

INDEX_TEMPLATE = """# Wiki 索引

> 最后更新: {date}

四类平等节点 + 待审阅队列。论文 ↔ 主题通过 `[[wikilink]]` 自然形成多对多关系（见 Obsidian Graph View）。

## 论文 (Papers)

（暂无。从 `00-pending/` 审阅后移入。）

## 主题 (Topics)

（暂无。触发条件：用户明确说"建主题 xx"，或同一主题在 2+ 论文中聚集。）

## 主张 (Claims)

（暂无。触发条件：一条 claim 在 2+ 论文中出现，或用户明确要追踪。）

## 综合 (Syntheses)

（暂无。用户问了一个值得固化的研究问题后创建。）

## 待审阅 (Pending)

（暂无。pi 处理完新论文后会先放在这里。）

---

## 反向索引（按主题聚合的论文）

（待主题节点创建后自动填充）
"""

LOG_TEMPLATE = """# Wiki 操作日志

> Append-only。严格格式：`## [YYYY-MM-DD] <action> | <summary>`

---

（Wiki 创建于 {date}。等待第一次摄入。）
"""


def init_wiki(wiki_root: Path) -> None:
    """初始化 wiki 目录结构。"""
    # 创建子目录
    for sub in ("papers", "topics", "claims", "syntheses", "00-pending", "raw"):
        (wiki_root / sub).mkdir(parents=True, exist_ok=True)

    # 创建 AGENTS.md（如果不存在）
    agents_path = wiki_root / "AGENTS.md"
    if not agents_path.exists():
        wc.write_text(agents_path, AGENTS_TEMPLATE)
        wc.ok(f"Created {agents_path}")
    else:
        wc.eprint(f"⚠ AGENTS.md exists, skipping")

    # 创建 index.md（如果不存在）
    index_path = wc.index_file(wiki_root)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not index_path.exists():
        wc.write_text(index_path, INDEX_TEMPLATE.format(date=today))
        wc.ok(f"Created {index_path}")
    else:
        wc.eprint(f"⚠ index.md exists, skipping")

    # 创建 log/ops.md（如果不存在）
    log_path = wc.log_file(wiki_root)
    if not log_path.exists():
        (wiki_root / "log").mkdir(parents=True, exist_ok=True)
        wc.write_text(log_path, LOG_TEMPLATE.format(date=today))
        wc.ok(f"Created {log_path}")
    else:
        wc.eprint(f"⚠ log/ops.md exists, skipping")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Evidence Wiki structure")
    parser.add_argument(
        "--wiki-root",
        type=Path,
        default=None,
        help="Wiki root directory (default: cwd)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing AGENTS.md/index.md/log/ops.md",
    )
    args = parser.parse_args()

    wiki_root = args.wiki_root or Path.cwd()
    if not wiki_root.is_dir():
        wc.die(f"Not a directory: {wiki_root}")

    init_wiki(wiki_root)
    wc.ok(f"Wiki initialized at {wiki_root}")
    return 0


def run(args: list[str]) -> int:
    sys.argv = ["wiki_init"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())