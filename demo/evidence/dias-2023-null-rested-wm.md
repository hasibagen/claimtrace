---
type: evidence
evidence_id: dias_2023_psychophysiol-E1-null-rested
fact_type: empirical_result
source: "[[dias_2023_psychophysiol]]"
observation: "In fully rested adults (n = 32, actigraphy-verified 7-9 h sleep), 200 mg caffeine changed neither 3-back accuracy (t(30) = 0.81, p = .424, d = 0.09) nor left-DLPFC hbO (+0.03 vs. +0.02 µM·cm; t(30) = 0.57, p = .573); BF01 = 4.6 favors the null [§Results]."
interp_origin: author
interp_text: "Under rested baseline conditions the working-memory benefit of caffeine is absent, bounding the scope of positive effects: caffeine restores degraded function after sleep loss rather than enhancing performance above baseline."
prov_paper: "[[dias_2023_psychophysiol]]"
prov_section: "§Results / Behavior + Hemodynamics"
prov_page: null
prov_paragraph: null
prov_source_text: "In fully rested participants, 200 mg caffeine produced no change in 3-back accuracy relative to placebo (t(30) = 0.81, p = .424, d = 0.09)."
verify_status: verified
verify_verifier: LLM
verify_n: 32
verify_test_method: t_test_paired
verify_test_stat_type: t
verify_test_stat_value: 0.81
verify_effect_size_type: cohen_d
verify_effect_size_value: 0.09
verify_ci_95: null
verify_df: null
verify_p_value: 0.424
verify_p_method: uncorrected
verify_note: "Same 22-channel montage and task family as Chen et al. (2024), so the contrast is apples-to-apples on rested vs. deprived state."
supports_targets: ["[[caffeine-wm-benefit-absent-when-fully-rested]]"]
supports_confidences: [high]
supports_relations: [direct]
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: ["[[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]]"]
qualifies_confidences: [high]
qualifies_relations: [partial]
strength: moderate
extraction_confidence: 0.95
field_status: {mode: reported}
scope_region: "left DLPFC"
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# dias-2023-null-rested-wm

## 观察(Observation)

In fully rested adults (n = 32, actigraphy-verified 7-9 h sleep), 200 mg caffeine changed neither 3-back accuracy (t(30) = 0.81, p = .424, d = 0.09) nor left-DLPFC hbO (+0.03 vs. +0.02 µM·cm; t(30) = 0.57, p = .573); BF01 = 4.6 favors the null [§Results].

## 原文引用

> [!quote]+ **来源**: §Results / Behavior + Hemodynamics
> In fully rested participants, 200 mg caffeine produced no change in 3-back accuracy relative to placebo (t(30) = 0.81, p = .424, d = 0.09).

## 解释(Interpretation)

- 解释来源: author
- Under rested baseline conditions the working-memory benefit of caffeine is absent, bounding the scope of positive effects: caffeine restores degraded function after sleep loss rather than enhancing performance above baseline.

## 出处(Provenance)

- 论文: [[dias_2023_psychophysiol]]
- 章节: §Results / Behavior + Hemodynamics
- 原文: In fully rested participants, 200 mg caffeine produced no change in 3-back accuracy relative to placebo (t(30) = 0.81, p…

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-wm-benefit-absent-when-fully-rested]] | direct | high |

## 限定的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]] | partial | high |

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `32` | 总样本数 |
| 检验方法 | `t_test_paired` | t_test_one_sample, t_test_independent, t_test_paired 等(共 37 候选,见 paper_stats) |
| 统计量类型 | `t` | t, F, r 等(共 21 候选,见 paper_stats) |
| 统计量数值 | `0.81` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `cohen_d` | cohen_d, hedges_g, r 等(共 16 候选,见 paper_stats) |
| 效应量数值 | `0.09` | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | _(论文未报告)_ | 如 [0.18, 0.50](null=未报告) |
| 自由度 (df) | _(论文未报告)_ | 统计量对应的自由度(null=未报告) |
| p 值 | `0.424` | 原始 p 值(null=未报告) |
| p 值校正 | `uncorrected` | uncorrected, bonferroni, holm_bonferroni 等(共 11 候选,见 paper_stats) |
| 备注 | `Same 22-channel montage and task family as Chen et al. (2024), so the contrast is apples-to-apples on rested vs. deprived state.` | 上下文或限制说明 |

## 使用此证据的页面

- [[caffeine-wm-benefit-absent-when-fully-rested]]
- [[dias_2023_psychophysiol]]
- [[does-caffeine-improve-working-memory]]
