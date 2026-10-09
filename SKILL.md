---
name: evidence-wiki
description: >-
  Maintain an evidence wiki from academic papers using the evidence-wiki
  extension suite (AGENTS.md / SKILL.md / Prompt / Extension) + 10 micro-skills
  + 10 commands. Engine-agnostic: pi / codex / zcode all valid (2026-09-04
  decoupling, see .skill/INVOKE.md). Process full.md → paper/claim/evidence
  nodes via LLM semantic extraction
  (LLM→JSON→MD pipeline), validate via 3 JSON schemas, lint via L0-L3 +
  Grounding grep. 5 core nodes (paperinfo/paper/claim/evidence/synthesis) +
  2 auxiliary (topic/00-pending). Use for: paper ingestion ("/extract"),
  claim tracking ("/claim"), cross-paper synthesis ("/query"), wiki health
  ("/lint"), Zotero sync ("/sync"). Trigger on "处理 full.md", "处理 pdf", "/extract",
  "追踪 claim", "evidence for X", "lint wiki". Do NOT use for: one-off
  summaries without traceability, raw file reads, or questions unrelated to
  recorded knowledge.
---

# ClaimTrace Skill

You are the long-term maintainer of an evidence wiki. Read `ARCHITECTURE.md` for full design + `wiki/AGENTS.md` for the 11 iron rules.

> **`ARCHITECTURE.md` 是合并 19 + 21 + AI 共识的终版,所有冲突以此为准。**

## 路由(意图 → 微 Skill)

`处理 [full.md|pdf]` / `/extract` → wiki-extract-paper(pdf 先 S0a 转 md)   |  `/claim` → wiki-build-claim  |  `/evidence` → wiki-build-evidence  |  `/topic` → wiki-build-topic  |  `/query` → wiki-query-evidence  |  `/lint` → wiki-lint-wiki  |  `/sync` → wiki-zotero-sync  |  `/audit` → wiki-extract-paper(T4)|  `/stitch` → wiki-stitch-knowledge  |  `建模拆解 [论文]` / `/modeling` → wiki-extract-modeling(训练-验证-测试协议深读)

## 关键铁律(5/11,完整列表见 wiki/AGENTS.md §1)

1. **RAW IS IMMUTABLE** — Zotero / MinerU 永不修改
2. **MARKDOWN IS THE SOURCE OF TRUTH** — JSON 仅作临时
3. **LLM EXTRACTS, SCRIPTS VALIDATE** — 语义靠 LLM,机械靠 scripts
4. **NO REGEX ON MEANING** — 不写正则抽取任何语义字段
5. **HUMAN REVIEWS PENDING** — LLM 写 `00-pending/`,人审阅才进正式目录
6. **GRAPH EDGES ARE TYPED & CONFIDENT** — 边有类型和置信度

## 抽取流程(T0-T4)

```
T0 Ingest(30s) → T1 Scan(30s) → T2 Extract(5-8min) → T3 Evidence(3m) → T4 Audit(2m)
流水线:LLM → JSON → scripts/jsonschema 校验 → Markdown → 00-pending/
```

3 模式 × 5 阶段 矩阵:quick-scan / deep-read / audit,详见 ARCHITECTURE §5.1。

## 节点架构(5 核心 + 2 辅助 + raw 层)

| 类 | 节点 | 目录 | 命名 |
|---|---|---|---|
| 核心 1 | paperinfo | `paperinfo/` | `<BBT-citekey>.md` |
| 核心 2 | paper | `papers/` | `<BBT-citekey>.md` |
| 核心 3 | claim | `claims/` | `<semantic-slug>.md` |
| 核心 4 | evidence | `evidence/` | `<author>-<year>-<slug>.md` |
| 核心 5 | synthesis | `syntheses/` | `<question-key>.md` |
| 辅助 A | topic | `topics/` | 跨论文才创建 |
| 辅助 B | pending | `00-pending/` | 审阅缓冲带 |
| **raw 层** | (权威源) | **`raw/<citekey>/full.md`** | MinerU 复制品(Grounding grep 都在这里) |

**唯一标识** = 文件名(slug),无需 evidence_id / claim_id 字段。

**raw 重要原则**:
- raw 是 wiki 内部权威源,**不依赖** 外部 zotero_md 路径
- 复制命令:`cp -r <zotero_md>/<paper> wiki/raw/<citekey>/`
- 引用格式:evidence **不存** raw 指针(§15.4.11);原文即证据(prov_source_text),脚本按 source citekey 推导路径
- Grounding grep 在 `wiki/raw/<citekey>/full.md` 进行

## 扩展机制(5 件套,引擎无关:pi / codex / zcode 共用,2026-09-04)

- **AGENTS.md**(`wiki/AGENTS.md`)— 宪法(启动无条件加载:pi 自动发现,codex 按 cwd 自动加载,zcode 会话遵守)
- **SKILL.md**(本文件)— Skill 入口
- **Prompt** (`.pi/prompts/`)— 10 个命令(`/extract` 等)
- **Extension** (`.pi/extensions/wiki-tools.ts`)— 5 个工具
- **微 Skill** (`.skill/skills/`)— 8 个,按需 read
- **调用规范** (`.skill/INVOKE.md`)— 三引擎(pi/codex/zcode)统一唤起方式与 INVOKE-PREFIX

## Discipline

- Always start with index/README for any query
- Never modify raw layer
- scripts 只做机械校验,**不**抽取
- Write to `00-pending/` first;human review moves to `papers/`
- claim/evidence must have provenance + section + quote
- Numeric values must be grep-able in raw full.md
- Preserve contradictions as knowledge
- **三件套同步**:ARCHITECTURE.md + tasks.md + log/ops.md(全局)/ log/batch-*.md(批次)

## Resources

## Resources

- `wiki/AGENTS.md` — 11 铁律 + 路由表(必读)
- `ARCHITECTURE.md` — **权威设计**(所有冲突以此为准)
- `wiki/tasks.md` — 任务清单
- `.skill/scripts/schemas/` — 3 套 jsonschema + `_registry.py`(EDGE_TYPE_SPECS)
- `.skill/skills/` — 10 个微 Skill(按需 read)
- `.pi/prompts/` · `.pi/extensions/wiki-tools.ts` — 10 命令 + 5 工具
- `.skill/references/BATCH_PIPELINE.md` — Week 2-4 批量方法

> 修改 SKILL.md 时**必须**同步:ARCHITECTURE.md + tasks.md + log/ops.md。
