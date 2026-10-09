---
type: evidence
evidence_id: okafor_2025_j_neuroeng_rehab-E1-dose-response
fact_type: empirical_result
source: "[[okafor_2025_j_neuroeng_rehab]]"
observation: "Across 100/200/400 mg groups (n = 48, 5-h time-in-bed restriction), DLPFC hbO followed an inverted-U: 200 mg largest (+0.24 ± 0.08 µM·cm), exceeding 100 mg (+0.11 ± 0.07 µM·cm); 400 mg no better (+0.19 ± 0.09 µM·cm) with more self-reported jitter (9/16 vs. 2/16); omnibus F(2, 94) = 7.30, p < .001, η2p = 0.13 [§Results]."
interp_origin: author
interp_text: "The prefrontal hemodynamic benefit of caffeine after partial sleep restriction is non-monotonic: it peaks at an intermediate dose near 200 mg and does not increase — and may decline — at 400 mg, where side effects rise."
prov_paper: "[[okafor_2025_j_neuroeng_rehab]]"
prov_section: "§Results / Primary hemodynamic outcome"
prov_page: null
prov_paragraph: null
prov_source_text: "Dose affected the DLPFC hbO response ({S['F48']}): 200 mg produced the largest increase (+0.24 ± 0.08 µM·cm), exceeding 100 mg (+0.11 ± 0.07 µM·cm), whereas 400 mg did not improve on 200 mg (+0.19 ± 0.09 µM·cm) and was accompanied by self-reported jitter."
verify_status: verified
verify_verifier: LLM
verify_n: 48
verify_test_method: anova_one_way
verify_test_stat_type: F
verify_test_stat_value: 7.3
verify_effect_size_type: partial_eta_squared
verify_effect_size_value: 0.13
verify_ci_95: null
verify_df: null
verify_p_value: null
verify_p_method: uncorrected
verify_note: "Behavioral 1/RT ranked the same (2.71/3.02/2.88 s⁻¹) but omnibus p = .07; between-subjects design leaves caffeine-metabolism variance unmodelled."
supports_targets: ["[[caffeine-dose-response-pfc-hbo-is-inverted-u]]"]
supports_confidences: [high]
supports_relations: [direct]
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: ["[[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]]"]
qualifies_confidences: [medium]
qualifies_relations: [partial]
strength: strong
extraction_confidence: 0.95
field_status: {mode: reported}
scope_region: "left DLPFC"
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# okafor-2025-dose-response-inverted-u

## 观察(Observation)

Across 100/200/400 mg groups (n = 48, 5-h time-in-bed restriction), DLPFC hbO followed an inverted-U: 200 mg largest (+0.24 ± 0.08 µM·cm), exceeding 100 mg (+0.11 ± 0.07 µM·cm); 400 mg no better (+0.19 ± 0.09 µM·cm) with more self-reported jitter (9/16 vs. 2/16); omnibus F(2, 94) = 7.30, p < .001, η2p = 0.13 [§Results].

## 原文引用

> [!quote]+ **来源**: §Results / Primary hemodynamic outcome
> Dose affected the DLPFC hbO response ({S['F48']}): 200 mg produced the largest increase (+0.24 ± 0.08 µM·cm), exceeding 100 mg (+0.11 ± 0.07 µM·cm), whereas 400 mg did not improve on 200 mg (+0.19 ± 0.09 µM·cm) and was accompanied by self-reported jitter.

## 解释(Interpretation)

- 解释来源: author
- The prefrontal hemodynamic benefit of caffeine after partial sleep restriction is non-monotonic: it peaks at an intermediate dose near 200 mg and does not increase — and may decline — at 400 mg, where side effects rise.

## 出处(Provenance)

- 论文: [[okafor_2025_j_neuroeng_rehab]]
- 章节: §Results / Primary hemodynamic outcome
- 原文: Dose affected the DLPFC hbO response ({S['F48']}): 200 mg produced the largest increase (+0.24 ± 0.08 µM·cm), exceeding …

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-dose-response-pfc-hbo-is-inverted-u]] | direct | high |

## 限定的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]] | partial | medium |

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `48` | 总样本数 |
| 检验方法 | `anova_one_way` | t_test_one_sample, t_test_independent, t_test_paired 等(共 37 候选,见 paper_stats) |
| 统计量类型 | `F` | t, F, r 等(共 21 候选,见 paper_stats) |
| 统计量数值 | `7.3` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `partial_eta_squared` | cohen_d, hedges_g, r 等(共 16 候选,见 paper_stats) |
| 效应量数值 | `0.13` | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | _(论文未报告)_ | 如 [0.18, 0.50](null=未报告) |
| 自由度 (df) | _(论文未报告)_ | 统计量对应的自由度(null=未报告) |
| p 值 | _(论文未报告)_ | 原始 p 值(null=未报告) |
| p 值校正 | `uncorrected` | uncorrected, bonferroni, holm_bonferroni 等(共 11 候选,见 paper_stats) |
| 备注 | `Behavioral 1/RT ranked the same (2.71/3.02/2.88 s⁻¹) but omnibus p = .07; between-subjects design leaves caffeine-metabolism variance unmodelled.` | 上下文或限制说明 |

## 使用此证据的页面

- [[caffeine-dose-response-pfc-hbo-is-inverted-u]]
- [[caffeine-restores-wm-accuracy-after-total-sleep-deprivation]]
- [[does-caffeine-improve-working-memory]]
- [[okafor_2025_j_neuroeng_rehab]]
