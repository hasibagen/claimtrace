# 架构

> **wiki 是如何组织的、为什么这样选择、每个部分做什么。**

**语言版本:** [English](../en/architecture.md) | [中文](./architecture.md)

---

## 11 条铁律

不可谈判。其他设计选择都从这里流出。

| # | 铁律 | 禁止什么 |
|---|---|---|
| 1 | **RAW IS IMMUTABLE** | 编辑 `raw/<citekey>/full.md`(Zotero / MinerU 输出是一次写入) |
| 2 | **MARKDOWN IS THE SOURCE OF TRUTH** | 把 wiki 内容放数据库;JSON 只作临时缓冲 |
| 3 | **LLM EXTRACTS, SCRIPTS VALIDATE** | 让脚本做语义任务,或让 LLM 做机械化任务 |
| 4 | **NO REGEX ON MEANING** | 写正则抽取任何语义字段(数字、姓名、claims) |
| 5 | **PROGRESSIVE DISCLOSURE** | frontmatter 显示所有可见字段;body 按需 Transclusion |
| 6 | **CONTEXT OPTIMIZATION** | 只需要一节却把整篇论文塞进 LLM 上下文 |
| 7 | **EVERY FACT HAS PROVENANCE** | claim 或 evidence 没有论文 + 节 + 页码引用 |
| 8 | **EVERY NUMBER IS VERIFIABLE** | 数字在 `raw/full.md` 中 grep 不到 |
| 9 | **CLAIM ≠ PAPER CONCLUSION** | 把论文结论当作 `claim` 节点 |
| 10 | **HUMAN REVIEWS PENDING** | LLM 直接写到 `papers/`、`claims/`、`evidence/` |
| 11 | **GRAPH EDGES ARE TYPED & CONFIDENT** | 无类型的边(没有 `supports`/`contradicts`/`qualifies` + 置信度的 wikilink) |

---

## 节点架构(5 核心 + 2 辅助 + raw 层)

### 核心节点(5)

```
┌──────────────┐
│  paperinfo   │  ──书目──>  paper
└──────────────┘                    │
                                    ▼
                                 claim ◀──── 跨论文 ────► claim
                                    ▲                            ▲
                                    │                            │
                                 evidence                    evidence
                                    │                            │
                                    ▼                            ▼
                                 paper ──> paper ──> paper ──> ...
                                 (raw full.md 是真相之源)
```

| 节点 | 数量 | frontmatter 锚点 |
|---|---|---|
| `paperinfo` | 每篇论文一个 | DOI、期刊、摘要、作者、年份 |
| `paper` | 每篇论文一个 | `paperinfo:` 链接 + `raw_path:` + `claims:` 列表 |
| `claim` | 每个主题一个(跨论文) | `related_papers:` + `supports/contradicts/qualifies_evidence:` |
| `evidence` | 每个事实一个 | 11 个 `verify_*` 字段 + `prov_source_text:` |
| `synthesis` | 每个主题一个(长篇) | `related_claims:` + 主题叙事 |

### 辅助节点(2)

- **`topic/`** —— 落地页,聚合某标签下的相关 claims、evidence、syntheses(如 `topic/dm-network.md`)。只有 ≥3 个相关 claim 才创建。
- **`00-pending/`** —— LLM 暂存缓冲。不是"正式"节点目录,是人工审阅区(铁律 #10)。

### Raw 层

```
raw/<citekey>/full.md       # 所有数字/引文的唯一权威源
raw/<citekey>/images/       # 抽取的图(可选)
raw/<citekey>/tables/       # 抽取的表(可选)
```

进入此目录后, raw 文件**永不**修改。

---

## 抽取流水线(T0–T4)

| 阶段 | 耗时 | 做什么 | 输出 |
|---|---|---|---|
| T0 · 摄入 | ~30s | 复制论文到 `raw/`,导出 citekey | `raw/<citekey>/full.md` |
| T1 · 扫描 | ~30s | 读论文,识别节,计算字符密度 | `sections.json` |
| T2 · 抽取 | ~5–8m | 生成 claim/evidence JSON 骨架 | `00-pending/<citekey>/claims/*.json` + `evidence/*.json` |
| T3 · Evidence | ~3m | 添加 11 个 verify_* 字段,在 raw 中找 prov_source_text | `evidence/*.json`(填充) |
| T4 · 审计 | ~2m | 对抗式:LLM 是否捏造数字? | `audit_report.md` |

LLM 写 JSON → 脚本转 Markdown → 人工在 `00-pending/` 审阅 → `wiki promote` 移到 `papers/`、`claims/`、`evidence/`。

---

## 验证层(L0–L4.6)

| 层 | 检查什么 | 机械/LLM |
|---|---|---|
| **L0 Structure** | 文件名、目录布局、frontmatter 必填字段 | 脚本 |
| **L0.5 Type** | 所有 `type:` 值是合法 enum(paper / paperinfo / claim / evidence / synthesis / topic) | 脚本 |
| **L1 Evidence** | 每条 evidence 有全部 11 个 verify_* 字段(填或 `null`) | 脚本 |
| **L1.5 Schema** | 对 `scripts/schemas/*.json` 的 JSON-Schema 校验 | 脚本 |
| **L2 Semantic** | claims 可证伪(`statement:` 是完整句子),evidence → paper 反向链接存在 | 脚本 + LLM |
| **L3 Consistency** | frontmatter 里的数字在 `raw/full.md` 中可 grep(exact / fuzzy / LaTeX 容错) | 脚本(grounding) |
| **L4.6 Edges** | 所有边有类型(`supports`/`contradicts`/`qualifies`) + 置信度(`high`/`medium`/`low`) | 脚本 |

跑:`wiki lint --layer L3`(省略 `--layer` 跑全部)。

---

## 边类型与置信度

节点间每个连接都有类型:

```
evidence.supports_evidence:    [[smith-2022-dmn-fc-reduction]]      (类型: supports)
        .contradicts_evidence: []
        .qualifies_evidence:   [[doe-2020-motion-confound]]        (类型: qualifies)

每条 evidence 还带:
    .supports_targets:      [paper-id-1, paper-id-2]   # 3 个平行数组
    .supports_relations:    [direct, indirect]
    .supports_confidences:  [high, medium]

    .contradicts_targets / .contradicts_relations / .contradicts_confidences
    .qualifies_targets  / .qualifies_relations  / .qualifies_confidences
```

铁律 #11 禁止无类型边。一个没有 type+confidence 的裸 `[[wikilink]]` 在 L4.6 是 lint 错误。

---

## 为什么是这些选择?

| 决策 | 理由 |
|---|---|
| **纯 Markdown 而非 DB** | 可 diff、可 git、Obsidian 可渲染、面向未来(铁律 #2) |
| **YAML frontmatter 而非 JSON sidecar** | 每个节点一个文件 = 一个真相之源,无断链 |
| **`00-pending/` 缓冲** | LLM 快但不一定对;人类慢但可靠(铁律 #10) |
| **Raw 不可改** | 如果抽取逻辑改进,总能重新抽取(铁律 #1) |
| **类型化边 + 置信度** | 图是*可查询*的("所有高置信度反驳 X 的证据"),不只是*可浏览* |
| **11 个 verify_* 字段** | 数字是最容易被捏造的内容;让每个数字显式 + 可 grep 验证能在早期阻止捏造(铁律 #8) |
| **JSON-Schema 校验** | LLM 输出自由形式 JSON;schema 强制结构可预测 |
| **NO REGEX ON MEANING** | "r = 0.65" 经过 LaTeX OCR 变成 "r = 0 . 6 5";正则两边都抓不到。LLM 读它,写 `r=0.65`。(铁律 #4) |

---

## 目录布局

```
claimtrace-skill/                  <- skill 仓库(就是这个)
├── README.md / README.zh.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── pyproject.toml
├── install.sh
├── docs/                              <- 人读文档(en + zh)
├── scripts/                           <- 校验 + 维护 CLI
│   ├── wiki                           <- 统一 CLI 入口
│   ├── wiki_common.py
│   ├── wiki_lint.py                   <- L0-L4.6
│   ├── wiki_check_evidence.py         <- L3 grounding grep
│   ├── wiki_render_nodes.py           <- body 表格自动渲染
│   ├── wiki_render_evidence_body.py   <- 单 evidence 自动渲染
│   ├── wiki_promote.py                <- 00-pending → papers/claims/evidence
│   ├── wiki_zotero.py                 <- Zotero SQLite 桥接
│   ├── ... (共 31 个 .py)
│   ├── archive/                       <- 历史修补脚本(保留以追溯)
│   ├── schemas/                       <- JSON-Schema 定义
│   └── tests/
├── skills/                            <- 9 个 micro-skills (slash-commands)
├── specs/                             <- 架构文档
├── references/                        <- 模板、风格指南、示例
│   ├── templates/                     <- paper.md、claim.md、evidence.md、...
│   └── examples/
└── __init__.py
```

用户用 `wiki init` 创建的 wiki:

```
my-research-wiki/
├── AGENTS.md          <- 11 条铁律(pi 自动加载)
├── index.md           <- 自动生成目录
├── log.md             <- 仅追加
├── paperinfo/         <- 每篇论文一个 .md
├── raw/<citekey>/     <- 不可改 MinerU 输出
├── 00-pending/<citekey>/  <- LLM 暂存(铁律 #10)
├── papers/<citekey>.md    <- 已提升论文节点
├── claims/<slug>.md       <- 已提升跨论文 claim
├── evidence/<slug>.md     <- 已提升 evidence 节点
├── syntheses/         <- 长篇综合文档
└── topics/            <- 主题落地页
```

---

## 何时打破规则

**不打破**。规则是铁。

唯一可以"违反"规则的时机是 **T0 摄入** 步骤,`wiki ingest` 读 MinerU 输出并复制。之后 raw 文件被冻结。

如果某条规则真的阻碍您的工作,正确的做法是**开 issue**,提议新规则,而不是悄悄违反。

---

## 延伸阅读

- [教程](./tutorial.md) —— 实践演练
- [Micro-skills](./micro-skills.md) —— 9 个 slash-commands
- [Schemas](../../scripts/schemas/) —— `claim.schema.json`、`evidence.schema.json`、`topic.schema.json`
- [Templates](../../references/templates/) —— `paper.md`、`claim.md`、`evidence.md`