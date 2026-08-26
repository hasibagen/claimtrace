# Evidence Wiki Skill · 中文版

> **学术证据 wiki 的长期维护 skill** — 论文 → claim → evidence 节点,LLM 抽取 JSON,脚本校验 markdown,Obsidian 原生双向链接。

[English version](./README.md) | [文档导航](./docs/zh/README.md) | [教程](./docs/zh/tutorial.md)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]() [![License: MIT](https://img.shields.io/badge/license-MIT-green)]() [![Stars](https://img.shields.io/github/stars/hasibagen/evidence-wiki)]()

---

## 这是什么?

**Evidence Wiki Skill** 是一个把您读过的论文变成**可查询、可追溯的知识图谱**的结构化系统。所有节点都是纯 Markdown 文件,可在 Obsidian 中原生渲染。它为需要长期阅读数百篇文献的个人研究者设计——不是一次性摘要,而是可持续的个人知识库。

**三大设计支柱:**

1. **Markdown 是真相之源** — 每个节点都是带 YAML frontmatter 的 `.md` 文件。无数据库,无私有格式。可 diff、可 git、Obsidian 可渲染。
2. **LLM 抽语义,脚本验机制** — LLM 擅长读论文写结构化 JSON;脚本擅长强制 schema、修正 YAML、grep 引文。各司其职。
3. **原始资料不可改** — 您的 Zotero 库和 MinerU 输出永不修改。所有 wiki 产物都在自己的目录里。

**11 条铁律**(完整列表见 [`docs/zh/architecture.md`](./docs/zh/architecture.md)):

> RAW IS IMMUTABLE · MARKDOWN IS THE SOURCE OF TRUTH · LLM EXTRACTS, SCRIPTS VALIDATE · **NO REGEX ON MEANING** · PROGRESSIVE DISCLOSURE · CONTEXT OPTIMIZATION · EVERY FACT HAS PROVENANCE · EVERY NUMBER IS VERIFIABLE · CLAIM ≠ PAPER CONCLUSION · HUMAN REVIEWS PENDING · GRAPH EDGES ARE TYPED & CONFIDENT

---

## 为什么用它?

| "普通"文献笔记的问题 | Evidence Wiki 如何解决 |
|---|---|
| 笔记散落在 Notion / Word / 各种 app | 一个 Obsidian vault,纯文件,面向未来 |
| 一年后重读一篇论文,忘了为什么重要 | 每个 claim 都有出处:谁说的、什么证据、多强 |
| 笔记里的数字跟原文对不上 | 每个数字都对照 `raw/full.md` grep 验证 |
| claim 被改写,论文结论丢失 | `claim`(您的综合) 与 `paper.md`(作者结论) 是独立节点 |
| 跨论文综合很难 | 类型化边(`supports` / `contradicts` / `qualifies`) + 置信度(`high` / `medium` / `low`) |
| LLM 幻觉偷偷溜进来 | LLM 写到 `00-pending/`(人工审阅缓冲带);您读完才成为正式节点 |

---

## 快速开始

### 前置依赖

- Python ≥ 3.10
- [Obsidian](https://obsidian.md/) (可选,但强烈推荐)
- 一个 LLM(任何 provider)— pi-coding-agent / Claude / GPT 都可,用于抽取步骤

### 安装

```bash
git clone https://github.com/hasibagen/evidence-wiki.git
cd evidence-wiki
pip install -e .

# 可选:集成 pi-coding-agent(安装 5 个扩展工具)
./install.sh
```

`install.sh` 脚本会:

- 把 5 个 wiki 工具软链接到您的 pi-coding-agent extensions 目录
- 设置 9 个 micro-skills 的 slash-command 前缀
- **不会触碰**您已有的数据

### 初始化新 wiki

```bash
mkdir my-research-wiki
cd my-research-wiki
wiki init          # 创建 AGENTS.md、index.md、log.md 和目录骨架
```

### 摄入第一篇论文

```bash
# 把 MinerU 处理过的 full.md 放进 vault,然后:
wiki ingest path/to/paper.md
```

这会跑一个 **6 阶段流水线**:

1. 把论文放入 `00-pending/<citekey>/`
2. 生成 frontmatter + claim/evidence JSON 骨架
3. LLM 抽取(通过 `/extract` slash-command)
5. 自动渲染 body 表格
6. 审计、lint、链接

完整流程见 **[`docs/zh/tutorial.md`](./docs/zh/tutorial.md)**。

---

## 您得到什么

```
my-research-wiki/
├── AGENTS.md              # 11 条铁律(pi 自动加载)
├── index.md               # 自动生成的目录
├── log.md                 # 仅追加的审计日志
├── paperinfo/             # 书目元数据(每篇论文一个节点)
├── raw/<citekey>/         # 原始 MinerU full.md(不可改)
├── 00-pending/<citekey>/  # LLM 抽取后,等待人工审阅
├── papers/<citekey>.md    # 已发布的"这篇论文声称什么"节点
├── claims/<slug>.md       # 跨论文 claim(您的综合)
├── evidence/<...>.md      # 具体证据(数字、引文)
├── syntheses/             # 长篇综合文档
└── topics/                # 主题标签入口
```

Obsidian 原生渲染。graph view 直接显示 claim 如何跨论文连接。

---

## 文档

| | English | 中文 |
|---|---|---|
| **教程** | [docs/en/tutorial.md](./docs/en/tutorial.md) | [docs/zh/tutorial.md](./docs/zh/tutorial.md) |
| **架构** | [docs/en/architecture.md](./docs/en/architecture.md) | [docs/zh/architecture.md](./docs/zh/architecture.md) |
| **微技能** | [docs/en/micro-skills.md](./docs/en/micro-skills.md) | [docs/zh/micro-skills.md](./docs/zh/micro-skills.md) |
| **Schemas** | [specs/](./specs/) | — |
| **模板** | [references/templates/](./references/templates/) | — |

---

## 9 个 micro-skills

每个都是一个专业化的 wiki 操作子例程。通过 slash-command 调用:

| Slash 命令 | 功能 |
|---|---|
| `/extract` | 在 `full.md` 上跑 4 阶段抽取流水线 |
| `/claim` | 跨多篇论文追踪一个 claim |
| `/evidence` | 把具体证据提升为节点 |
| `/topic` | 从相关 claim 构建主题落地页 |
| `/query` | 在 wiki 中搜索关于 X 的证据 |
| `/lint` | 跑 4 层 lint 检查 |
| `/sync` | Zotero 库 → `paperinfo/` 同步 |
| `/stitch` | 跨论文去重相似 claim |
| `/audit` | 批判性对抗式审阅一篇论文 |

> 注:`/dedup` 实现为 CLI 脚本(`wiki_dedup_papers.py`),不是 micro-skill。见 [`scripts/wiki_dedup_papers.py`](./scripts/)。

详细用法见 **[`docs/zh/micro-skills.md`](./docs/zh/micro-skills.md)**。

---

## 许可证

MIT — 见 [`LICENSE`](./LICENSE)。

## 贡献

见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。欢迎 bug 报告和 PR。

## 引用

如果您在已发表的研究中使用了这个 skill,请引用(占位符 — 归档后会添加 DOI):

```bibtex
@software{evidence_wiki_skill,
  author = {hasibagen},
  title = {Evidence Wiki Skill: Long-term Maintenance of Academic Evidence Graphs},
  year = {2026},
  url = {https://github.com/hasibagen/evidence-wiki}
}
```