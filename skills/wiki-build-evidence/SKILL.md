---
name: wiki-build-evidence
description: >-
  Create a single evidence node with full provenance from a paper's quote.
  Frontmatter fields (ARCHITECTURE §3.4, T-W4-026 升级 + T-W4-027 脚本渲染):
  fact_type (empirical_result/observation/methodology), observation (verbatim ≥20字),
  interp_origin/interp_text (扁平化), prov_paper/prov_section/prov_page/prov_paragraph/
  prov_source_text/extract_* (扁平化), verify_n + verify_test_method (required)
  + verify_test_stat_type/value + verify_effect_size_type/value + verify_ci_95 +
  verify_df + verify_p_value + verify_p_method + verify_note (9 optional, paper_stats
  enum 整合:37/20/16/11 候选), supports_targets/confidences/relations +
  contradicts_targets/confidences/relations + qualifies_targets/confidences/relations
  (3 parallel arrays). Use when user says "/evidence <text>" or "这是事实".
---

# Wiki Build Evidence

创建一条 evidence 节点(独立,跨论文复用)。

## 何时使用

- 用户说:`/evidence <text>` 或 "这是一个事实" 或 "建 evidence"
- 来自 `wiki-extract-paper` 的 T2/T3 阶段

## T0 加载统计契约(必走,ARCHITECTURE §3.4 + §15.4.11)

证据抽取前**必须**显式 `read .skill/references/templates/paper_stats.md`,作为统计字段契约。

paper_stats.md 定义了完整的:

- **检验方法候选清单**(`verify_test_method` enum):t_test / anova / regression / correlation / ancova / mann_whitney / permutation / mixed_effects / bayesian / ...
- **效应量候选清单**(`verify_effect_size_type` enum):cohen_d / hedges_g / eta_squared / R_squared / cramers_v / odds_ratio / beta / bayes_factor / ...
- **多重比较候选清单**(`verify_p_method` enum):uncorrected / bonferroni / fdr_bh / fdr_by / fwe / cluster_based / tfce / maxT / bayes_factor / na

LLM 抽取每条数值事实时,**必须**从这些候选清单中精确匹配,evidence.schema.json 顶层 `verify_*` 字段用 enum + `additionalProperties: false` 强制校验,reject 时必须修正。

**设计原则**:论文未报告的字段标 `null`(明确缺失,不漏填);无假设检验的方法论/软件论文整组统计字段 null,只填 `verify_n` + `verify_test_method: methodology` + `verify_note` 说明。

## 字段(ARCHITECTURE §3.4)

11 字段平铺(用户实测经验:Obsidian 不支持嵌套结构,所有 verify_* 均为顶层字段)

```yaml
---
type: evidence
schema_version: "plan_final_v1"
source: "[[paper-id]]"             # 来源论文 wikilink
fact_type: empirical_result         # empirical_result / observation / methodology

# Observation + Interpretation(GPT §11)
observation: |                      # 原文 verbatim,20+ 字符
  "<exact quote from raw full.md>"
interpretation: |
  origin: author / reviewer / system
  text: |
    <作者/审稿人/系统对这条 observation 的解读>

# Provenance(ARCHITECTURE §3.4 GPT §12)
provenance:
  paper: "[[paper-id]]"
  section: "§3.2 Results"
  page: 5
  paragraph: 3
  source_text: "<exact quote>"
  extraction:
    model: minimax-m3
    timestamp: "2026-08-24T10:30:00Z"
    method: llm_semantic
    temperature: 0.1

# 数值校验(scripts 必查,11 字段平铺)
verify_n: 120
verify_test_method: regression_multiple      # 完整候选见 schema $defs.test_method_enum(37 候选)
verify_test_stat_type: beta                  # 完整候选见 schema $defs.test_stat_type_enum(20 候选)
verify_test_stat_value: 0.34
verify_effect_size_type: R_squared           # 完整候选见 schema $defs.effect_size_type_enum(16 候选)
verify_effect_size_value: 0.12
verify_ci_95: [0.08, 0.16]                   # 95% CI 下界/上界(null=未报告)
verify_df: [118, 1]                          # 自由度(null=未报告)
verify_p_value: 0.001                        # null=未报告
verify_p_method: fdr_bh                      # 完整候选见 schema $defs.p_method_enum(11 候选)
verify_note: 回归系数,校正年龄/性别

# 关系(多对多)
supports: ["[[claim-slug]]"]
contradicts: []
qualifies: []

# 强度(科学证据强度 ≠ LLM 抽取置信度)
strength: strong                   # strong / moderate / weak
---
```

## 命名

**文件**:`evidence/<first-author>-<year>-<short-keyword>.md`(ARCHITECTURE §2.3 + T-W4-030)
- **优先中文 + 真实空格**(如 `evidence/boisgontier-2026 PWS 婴儿 3 脑区 CBF 增高.md`)
- `<first-author>-<year>-` 前缀用 ASCII(citekey 形式避免重名)
- `<short-keyword>` 主体部分中英混合 / kebab-case 也允许
- **不用 `-` 替代真实空格**(ARCHITECTURE §15.4.7)
- **不**用 EVID-012 内部编号

## Grounding Invariant(ARCHITECTURE §5.3)

```
∀ quantitative_fact f ∈ evidence.md:
    ∃ quote q ∈ raw full.md:
        numeric_value(f) ∈ numeric_values(q)
```

scripts 用 grep 校验,失败则 reject 让 LLM 重写。

## 边界

- `observation` **必须**是原文 verbatim(从 raw full.md 复制)
- `provenance.source_text` 必须可定位到 raw 中
- `verify_*` 数值字段必须真实存在于 raw(否则标 FLAGGED)
- `verify_test_method` / `verify_test_stat_type` / `verify_effect_size_type` / `verify_p_method` **必须** ∈ paper_stats 候选清单(否则 lint reject)
- 写 `00-pending/` → 审阅 → `evidence/`

## 数量原则(ARCHITECTURE §2.4 + T-W4-032)

**EVIDENCE 节点无硬性数量限制**(设计原则:质量优先,反映实际知识结构)。

- **每篇 paper 推荐 3-10 个 EVIDENCE**(实证核心论文典型范围)
- **上限警告阈值:> 30 EVIDENCE/paper** — 需 LLM 评估是否拆得过细
- **每条 CLAIM 通常对应 1-5 个 EVIDENCE**;**每条 EVIDENCE 通常支持 1-5 个 CLAIM**(边的双向稀疏)
- **非假设检验论文**(方法论 / 软件 / 综述)可能只有 1-3 个 EVIDENCE(描述性) — 这是正常的,不警告

## 关联

- 数据模型:`ARCHITECTURE.md §3.4`
- Evidence Contract:`ARCHITECTURE.md §3.8` JSON Schema
- Grounding Invariant:`ARCHITECTURE.md §5.3`
- 统计契约:`.skill/references/templates/paper_stats.md`
- 字段 enum 定义:`.skill/scripts/schemas/evidence.schema.json`(`$defs.test_method_enum` / `test_stat_type_enum` / `effect_size_type_enum` / `p_method_enum` 区块)

## 模板(T-W4-027 升级 + T-W4-031 supports/contradicts/qualifies 表格)

> **设计原则**:body 表格 **只渲染、不维护** —— 永远从 frontmatter 生成,不允许手工编辑。所有自动渲染段(`## 支持的 Claim` / `## 反对的 Claim` / `## 限定的 Claim` / `## 数值校验`)由 `.skill/scripts/wiki_render_evidence_body.py` 负责。
>
> - LLM 输出 frontmatter 后 → 跑 `wiki_render_evidence_body.py <file>` 自动生成 body 表格
> - schema enum 是说明列的唯一真相源(`$defs.test_method_enum` / `test_stat_type_enum` / `effect_size_type_enum` / `p_method_enum`)
> - 论文未报告的字段(frontmatter 中为 null)→ 表格值列显示 `_(论文未报告)_`
> - **维度分离**(ARCHITECTURE §1.2 #11):`strength` 是 evidence 节点全局属性,在 frontmatter `strength` 字段体现一次,不重复在每条边后;每条边只显示 `关系(direct/indirect/partial)` + `置信度(high/medium/low)`

```markdown
# Evidence: <作者 年份 关键词>

**事实陈述**
<observation 的人话版>

**原文引用**
> "<observation verbatim>"
> — [[paper-id]], §<section>

**出处**
- 论文: [[paper-id]]
- 章节: <section>
- 页码: <page>

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[claim-slug-1]] | direct | high |
| [[claim-slug-2]] | indirect | medium |

(若无 supports_targets,本段省略)

## 反对的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[claim-slug-3]] | partial | low |

(若无 contradicts_targets,本段省略)

## 限定的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[claim-slug-4]] | direct | medium |

(若无 qualifies_targets,本段省略)

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `<n>` | 总样本数 |
| 检验方法 | `<verify_test_method>` | t_test_one_sample / ... / anova / regression / permutation / mixed_effects / bayesian / methodology(共 37 候选,见 schema $defs.test_method_enum) |
| 统计量类型 | `<verify_test_stat_type>` | t / F / r / rho / chi2 / OR / RR / beta / z / u / W / H / Q / BF / d / g / R2 / eta2 / V / phi(共 20 候选) |
| 统计量数值 | `<verify_test_stat_value>` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `<verify_effect_size_type>` | cohen_d / hedges_g / r / rho / r_squared / R_squared / adjusted_R_squared / eta_squared / partial_eta_squared / beta / OR / RR / phi / cramers_v / bayes_factor / na(共 16 候选) |
| 效应量数值 | `<verify_effect_size_value>` | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | `<verify_ci_95>` | 如 [0.18, 0.50](null=未报告) |
| 自由度 (df) | `<verify_df>` | 统计量对应的自由度(null=未报告) |
| p 值 | `<verify_p_value>` | 原始 p 值(null=未报告) |
| p 值校正 | `<verify_p_method>` | uncorrected / bonferroni / holm_bonferroni / fwe / maxT / fdr_bh / fdr_by / cluster_based / tfce / bayes_factor / na(共 11 候选) |
| 备注 | `<verify_note>` | 上下文或限制说明 |

**使用此证据的页面**
- [[paper-id]]
```

### body 渲染脚本

```bash
# 单文件重生成
python3 .skill/scripts/wiki_render_evidence_body.py evidence/<file>.md

# 目录所有 evidence 重生成
python3 .skill/scripts/wiki_render_evidence_body.py evidence/

# 仅预览(不写文件)
python3 .skill/scripts/wiki_render_evidence_body.py --dry-run evidence/<file>.md

# 一致性检查(有差异 exit 1)
python3 .skill/scripts/wiki_render_evidence_body.py --check evidence/
```

## Resources

- `ARCHITECTURE.md §3.4` Evidence 节点完整 schema
- `ARCHITECTURE.md §3.8` Evidence Contract
- `ARCHITECTURE.md §5.3` Grounding Invariant
- `.skill/scripts/schemas/evidence.schema.json`