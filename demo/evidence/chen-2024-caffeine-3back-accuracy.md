---
type: evidence
evidence_id: chen_2024_neurophotonics-E1-3back-accuracy
fact_type: empirical_result
source: "[[chen_2024_neurophotonics]]"
observation: "In a 24-h total sleep deprivation crossover (n = 24), 200 mg caffeine raised 3-back accuracy from 78.2 ± 6.4% (placebo) to 85.7 ± 5.9% (t(23) = 4.21, p < .001, d = 0.86) [§Results/Behavior]."
interp_origin: author
interp_text: "After total sleep deprivation a moderate caffeine dose recovers a substantial part of the working-memory accuracy deficit; the paired effect size is large, so the rescue is detectable at single-dose granularity in this sample."
prov_paper: "[[chen_2024_neurophotonics]]"
prov_section: "§Results / Behavior"
prov_page: null
prov_paragraph: null
prov_source_text: "Across participants, 3-back accuracy was higher after caffeine than after placebo (85.7 ± 5.9% vs. 78.2 ± 6.4%; t(23) = 4.21, p < .001, d = 0.86)."
verify_status: verified
verify_verifier: LLM
verify_n: 24
verify_test_method: t_test_paired
verify_test_stat_type: t
verify_test_stat_value: 4.21
verify_effect_size_type: cohen_d
verify_effect_size_value: 0.86
verify_ci_95: null
verify_df: null
verify_p_value: null
verify_p_method: uncorrected
verify_note: "Crossover counterbalancing and 60-min post-dose timing align the behavioral and hemodynamic readouts; RT showed the same direction (689 vs. 741 ms)."
supports_targets: ["[[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]]"]
supports_confidences: [high]
supports_relations: [direct]
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: ["[[caffeine-wm-benefit-absent-when-fully-rested]]"]
qualifies_confidences: [medium]
qualifies_relations: [partial]
strength: strong
extraction_confidence: 0.95
field_status: {mode: reported}
scope_region: "left DLPFC"
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# chen-2024-caffeine-3back-accuracy

## 观察(Observation)

In a 24-h total sleep deprivation crossover (n = 24), 200 mg caffeine raised 3-back accuracy from 78.2 ± 6.4% (placebo) to 85.7 ± 5.9% (t(23) = 4.21, p < .001, d = 0.86) [§Results/Behavior].

## 原文引用

> [!quote]+ **来源**: §Results / Behavior
> Across participants, 3-back accuracy was higher after caffeine than after placebo (85.7 ± 5.9% vs. 78.2 ± 6.4%; t(23) = 4.21, p < .001, d = 0.86).

## 解释(Interpretation)

- 解释来源: author
- After total sleep deprivation a moderate caffeine dose recovers a substantial part of the working-memory accuracy deficit; the paired effect size is large, so the rescue is detectable at single-dose granularity in this sample.

## 出处(Provenance)

- 论文: [[chen_2024_neurophotonics]]
- 章节: §Results / Behavior
- 原文: Across participants, 3-back accuracy was higher after caffeine than after placebo (85.7 ± 5.9% vs. 78.2 ± 6.4%; t(23) = …

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]] | direct | high |

## 限定的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-wm-benefit-absent-when-fully-rested]] | partial | medium |

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `24` | 总样本数 |
| 检验方法 | `t_test_paired` | t_test_one_sample, t_test_independent, t_test_paired 等(共 37 候选,见 paper_stats) |
| 统计量类型 | `t` | t, F, r 等(共 21 候选,见 paper_stats) |
| 统计量数值 | `4.21` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `cohen_d` | cohen_d, hedges_g, r 等(共 16 候选,见 paper_stats) |
| 效应量数值 | `0.86` | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | _(论文未报告)_ | 如 [0.18, 0.50](null=未报告) |
| 自由度 (df) | _(论文未报告)_ | 统计量对应的自由度(null=未报告) |
| p 值 | _(论文未报告)_ | 原始 p 值(null=未报告) |
| p 值校正 | `uncorrected` | uncorrected, bonferroni, holm_bonferroni 等(共 11 候选,见 paper_stats) |
| 备注 | `Crossover counterbalancing and 60-min post-dose timing align the behavioral and hemodynamic readouts; RT showed the same direction (689 vs. 741 ms).` | 上下文或限制说明 |

## 使用此证据的页面

- [[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]]
- [[chen_2024_neurophotonics]]
- [[does-caffeine-improve-working-memory]]
