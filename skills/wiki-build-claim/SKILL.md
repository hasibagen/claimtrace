---
name: wiki-build-claim
description: >-
  CREATE a single claim node (atomic proposition, 跨论文追踪). Writes to
  claims/<semantic-slug>.md (优先中文 + 真实空格, NO numbering, ARCHITECTURE §2.3
  + T-W4-030). Frontmatter fields (ARCHITECTURE §3.5): type/statement/claim_type/
  origin/atomic, scope_* (5 扁平字段), verify_* (8 字段), reasoning/reasoning_type,
  sources_targets + 3 平行数组, supports/contradicts/evidence_targets + 3 平行
  数组. **NOT for**: reading/answering questions (use wiki-query-evidence),
  cross-paper merge (use wiki-stitch-knowledge). Use when user says "/claim
  <text>" or "跨论文追踪这条".
---

# Wiki Build Claim

创建一条 claim 节点。

## 何时使用

- 用户说:`/claim <text>` 或 "这条跨论文追踪" 或 "固化这条 claim"
- 来自 `wiki-extract-paper` 的 T2/T3 阶段(批量创建)

## 字段(ARCHITECTURE §3.5)

```yaml
---
type: claim
schema_version: "plan_final_v1"
statement: "<一句陈述,关键命题>"
claim_type: empirical_generalization  # empirical_result / empirical_generalization / theoretical_interpretation / methodological / meta_analytic
verification:
  status: supported    # supported / partial / contradicted / no_evidence
  confidence: 0.82     # 0-1
  strength: moderate   # strong / moderate / weak / inconclusive
scope:                  # ARCHITECTURE §3.5 GPT §23
  population: "..."
  modality: "..."
  task: "..."
  region: "..."
  study_design: "..."
reasoning: |             # Toulmin warrant 降级
  <推理桥 — 为什么 evidence 支持 statement>
sources: ["[[paper-id]]", ...]   # wikilink
evidence: ["[[evidence-slug]]", ...]  # wikilink
supports: []
contradicts: []
---
```

## 命名

**文件**:`claims/<semantic-slug>.md`(ARCHITECTURE §2.3 + T-W4-030)
- **优先中文 + 真实空格**(如 `claims/PWS 婴儿早期脑高灌注.md`)
- 中英混合 / kebab-case 也允许(如 `claims/dlpfc-hbo-age.md`)
- **不用 `-` 替代真实空格**(ARCHITECTURE §15.4.7)
- 从 statement 语义生成
- **不**用 CLAIM-001 / CLAIM-007 内部编号(ARCHITECTURE §2.3)

**⚠️ 文件名禁例(2026-08-25 lint 修复)**:
- **禁数学符号**:`+` `=` `[` `]` `(` `)` `^` `%` `,` — 这些**公式应写在 `statement` 或 body 里的代码块**,**不**在文件名
- **禁附加标记**:`(paula 2015 抽取)`、`(author 抽取)`、`(2024 重抽)` 等抽取元信息**不**写在文件名 — 文件名是**语义 slug**,**不**是抽取日志
- **字符集**:中文(CJK) / 日文(假名) / ASCII 字母数字 / 空格 / `-` `_` `.`(wiki_lint 字符白名单)
- **长度**:建议 ≤ 30 字,过长截取核心语义(例:`BNM 通过三层耦合支持双尺度空间` 而非 `BNM 通过三层耦合 ν0 ν1 ν2 支持双尺度空间 (paula 2015 抽取)`)
- **正确 vs 错误**:
 - ✓ `BNM 通过三层耦合支持双尺度空间.md`
 - ✗ `BNM 通过三层耦合 ν0 ν1 ν2 支持双尺度空间 (paula 2015 抽取).md`
 - ✓ `TVB 集成八套神经质量模型与四类前向模型.md`
 - ✗ `TVB 集成 8 套神经质量模型与 4 类多模态前向模型于同一神经活动源 (paula 2015 抽取).md`
 - ✓ `BVEP 100 准确反演 84 脑区空间癫痫源性.md`
 - ✗ `BVEP 100% 准确反演 84 脑区空间癫痫源性.md`
 - ✓ `z3 全局潜状态作为虚拟药物干预靶点.md`
 - ✗ `z(3) 全局潜状态作为虚拟药物干预靶点.md`

## 边界

- 必须有 `statement` + `verification` + 至少 1 个 evidence wikilink
- claim 必须**原子化**(一条只表达一个命题)
- 写 `00-pending/` → 用户审阅 → `claims/`

## 数量原则(ARCHITECTURE §2.4 + T-W4-032)

**CLAIM 节点无硬性数量限制**(设计原则:质量优先,反映实际知识结构)。

- **每篇 paper 推荐 3-8 个 CLAIM**(实证核心论文典型范围)
- **上限警告阈值:> 20 CLAIM/paper** — 需 LLM 评估是否过度拆解
- **单一来源 claim 应标 DRAFT**(`verify_status: no_evidence`),待 2+ 论文支持升级为 supported
- **同义 claim 合并**:同一发现的多个表述合并为一条,避免节点膨胀

## 关联

- 数据模型:`ARCHITECTURE.md §3.5`
- Evidence Contract:`ARCHITECTURE.md §3.8`
- 验证方法论:SciFact(ARCHITECTURE §1.3)

## 模板

```markdown
# Claim: <semantic-slug 的人类可读标题>

**主张陈述**
<statement>

**支持证据**
| 证据 | 来源 | 关键数值 | 关系 |
|------|------|---------|------|
| [[evidence-slug]] | Author Year | r=0.42 | direct |

**反对证据**
(暂无)

**推理桥**
<reasoning>

**限定条件**
<scope 转写为人话>

**证据强度**
<strength>(<evidence_count> 项研究)

**引用此主张的页面**
<反链>
```

## Resources

- `ARCHITECTURE.md §3.5` Claim 节点完整 schema
- `ARCHITECTURE.md §3.8` Evidence Contract (JSON Schema)
- `.skill/scripts/schemas/claim.schema.json`