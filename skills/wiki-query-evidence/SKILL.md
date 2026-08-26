---
name: wiki-query-evidence
description: >-
  ANSWER research questions by **READING** (no writes) claim + evidence +
  topic + synthesis nodes from `index.md` and `claims/`, `evidence/`,
  `topics/`, `syntheses/` subdirs. Dynamic synthesis: aggregate Evidence ×
  Claim matrix into a generated answer, then OFFER to persist as syntheses/
  if valuable (requires user confirmation). **NOT for**: creating new
  evidence/claim nodes (use wiki-build-evidence/wiki-build-claim), fixing
  duplicates across papers (use wiki-stitch-knowledge). Use when user asks
  "X 的证据是什么" or "/query <question>".
---

# Wiki Query Evidence

回答研究问题:动态综合 claim + evidence,可选固化到 synthesis。

## 何时使用

- 用户说:`X 的证据是什么?` / `/query <question>` / `查一下 WM 与阅读的关系`
- 用户问任何"关于 X 的研究现状 / 证据 / 共识"

## 工作流

### 1. 读 index.md(强制)

**`index.md` 是所有 query 的必经入口**。不要直接读 raw files。

### 2. 路由到相关节点

- 读 `index.md` 找到相关 topic / claim / evidence wikilink
- 如涉及多篇论文 → 触发动态 synthesis

### 3. 动态生成 synthesis(ARCHITECTURE §2.2)

```
用户问: "儿童 DLPFC 活动是否随年龄增加?"
         │
         ▼
   读 index.md → 找到 CLAIM-007 (语义 slug: dlpfc-hbo-age)
         │
         ▼
   读 dlpfc-hbo-age.md + 所有 supports 的 evidence
         │
         ▼
   Evidence × Claim 矩阵聚合
         │
         ▼
   生成 ABT 叙事(And-But-Therefore)
   - And: 3+ 项横断研究一致支持
   - But: 全部横断,无法确立因果
   - Therefore: Moderate support,适用 6-12 岁
         │
         ▼
   用户确认有价值 → 固化到 syntheses/dlpfc-development.md
```

### 4. ABT 叙事模板

```markdown
# <Question>

## 共识(And)
<多研究支持的观点>

## 缺口(But)
<研究空白或矛盾>

## 结论(Therefore)
<综合判断 + 适用边界>

## 证据矩阵
| 证据 | Paper 1 | Paper 2 | Paper 3 |
|------|:---:|:---:|:---:|
| DLPFC HbO ↑ | +++ | ++ | +++ |

## 关键论文
- [[papers/<author>_<year>_<short>]]
- [[papers/<BBT-citekey>]]
```

### 5. 固化判断

问用户:
- "这个综合值得固化吗?"
- 是 → 写 `syntheses/<question-key>.md`(ARCHITECTURE §3.7 模板)
- 否 → 只在主会话回答

## Synthesis 供给侧四件套(批次4,固化前强制)

1. **聚合先行**:先跑 `python3 .skill/scripts/wiki_aggregate_claims.py <claim名>`,证据矩阵的数字全部来自脚本输出,LLM 只写叙事
2. **句尾引用键**:正文每个论断句尾必须 `([[evidence-名]])`;lint 会验证目标存在——无引用的句子删掉或补引用(证据不足时写"证据不足",不硬答)
3. **Coverage Ledger**:固化前对范围内每篇论文显式分类(直接证据/机制/条件/情境/相关/范围外 + 一句话理由),禁止樱桃挑拣(只引支持结论的)
4. **Maturity Gate + evidence_cutoff**:建 synthesis 需 ≥2 条稳定跨论文关系 + ≥1 个值得写的缺口(争议/条件/机制);frontmatter 写 `evidence_cutoff: <日期>`(本综合只考虑截至该日的证据,学术检索窗口声明)

## 边界

- **永远从 index.md 开始**(ARCHITECTURE §2.2)
- synthesis 是**问题驱动**的,不是论文驱动的
- 不直接写 `syntheses/`,先给用户看,确认才固化(ARCHITECTURE §2.2)
- 跨论文综合时,**不**替代某个 topic(那也是聚合,但更静态)

## 关联

- 节点模型:`ARCHITECTURE.md §2.2`(Synthesis 动态视图)
- ABT 叙事:`ARCHITECTURE.md §1.3` 方法论家族

## Resources

- `ARCHITECTURE.md §3.7` Synthesis 节点完整 schema
- `ARCHITECTURE.md §2.2` Synthesis 动态视图
- `ARCHITECTURE.md §1.3` ABT 叙事方法
- `wiki/index.md` 全局索引