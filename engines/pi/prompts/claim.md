---
description: 把一条陈述固化为 claim 节点
argument-hint: "<statement text>"
---

请创建一条 claim 节点,statement: $1

## 步骤

1. read `.skill/skills/wiki-build-claim/SKILL.md` 获取字段定义
2. 根据 statement 推断:
   - claim_type(empirical_result / empirical_generalization / theoretical_interpretation / methodological / meta_analytic)
   - scope(population/modality/task/region/study_design)
   - 至少 1 个 evidence wikilink(若用户未提供,标 DRAFT)
3. 命名:从 statement 生成 semantic slug(**优先中文 + 真实空格**,如 `PWS 婴儿早期脑高灌注`;中英混合 / kebab-case 也允许;不用 `-` 替代真实空格,plan_final §2.3 + T-W4-030)
4. write 到 `00-pending/<slug>.md`

## 约束

- 必须原子化(一条只表达一个命题)
- 必须有 provenance(指明来源论文)
- 不直接写 `claims/`,先放 `00-pending/`