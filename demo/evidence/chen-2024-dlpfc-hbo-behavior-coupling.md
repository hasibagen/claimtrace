---
type: evidence
evidence_id: chen_2024_neurophotonics-E2-hbo-behavior-coupling
fact_type: empirical_result
source: "[[chen_2024_neurophotonics]]"
observation: "Caffeine reversed the sleep-loss-related left-DLPFC hbO decline (+0.28 ± 0.09 µM·cm vs. -0.05 ± 0.11 µM·cm under placebo), and per-participant accuracy gain correlated with hbO gain (r = 0.61, p = .002) [§Results/Hemodynamics]."
interp_origin: author
interp_text: "The behavioral rescue and the prefrontal hemodynamic rescue co-vary across individuals, supporting left-DLPFC hbO as a surrogate marker of the functional recovery rather than an unrelated vascular effect."
prov_paper: "[[chen_2024_neurophotonics]]"
prov_section: "§Results / Hemodynamics + coupling"
prov_page: null
prov_paragraph: null
prov_source_text: "Caffeine reversed the sleep-deprivation-related decrease in left DLPFC hbO (change from pre-dose baseline +0.28 ± 0.09 µM·cm under caffeine vs. -0.05 ± 0.11 µM·cm under placebo), and the behavioral improvement correlated with the hemodynamic change across participants (r = 0.61, p = .002)."
verify_status: verified
verify_verifier: LLM
verify_n: 24
verify_test_method: correlation_pearson
verify_test_stat_type: r
verify_test_stat_value: 0.61
verify_effect_size_type: r
verify_effect_size_value: 0.61
verify_ci_95: null
verify_df: null
verify_p_value: 0.002
verify_p_method: uncorrected
verify_note: "Right DLPFC showed the same direction at smaller magnitude (+0.14 ± 0.10 µM·cm); medial PFC and HbR null (all p > .15)."
supports_targets: ["[[pfc-hbo-increase-tracks-caffeine-behavioral-rescue]]"]
supports_confidences: [high]
supports_relations: [direct]
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: []
qualifies_confidences: []
qualifies_relations: []
strength: strong
extraction_confidence: 0.95
field_status: {mode: reported}
scope_region: "left DLPFC"
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# chen-2024-dlpfc-hbo-behavior-coupling

## 观察(Observation)

Caffeine reversed the sleep-loss-related left-DLPFC hbO decline (+0.28 ± 0.09 µM·cm vs. -0.05 ± 0.11 µM·cm under placebo), and per-participant accuracy gain correlated with hbO gain (r = 0.61, p = .002) [§Results/Hemodynamics].

## 原文引用

> [!quote]+ **来源**: §Results / Hemodynamics + coupling
> Caffeine reversed the sleep-deprivation-related decrease in left DLPFC hbO (change from pre-dose baseline +0.28 ± 0.09 µM·cm under caffeine vs. -0.05 ± 0.11 µM·cm under placebo), and the behavioral improvement correlated with the hemodynamic change across participants (r = 0.61, p = .002).

## 解释(Interpretation)

- 解释来源: author
- The behavioral rescue and the prefrontal hemodynamic rescue co-vary across individuals, supporting left-DLPFC hbO as a surrogate marker of the functional recovery rather than an unrelated vascular effect.

## 出处(Provenance)

- 论文: [[chen_2024_neurophotonics]]
- 章节: §Results / Hemodynamics + coupling
- 原文: Caffeine reversed the sleep-deprivation-related decrease in left DLPFC hbO (change from pre-dose baseline +0.28 ± 0.09 µ…

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[pfc-hbo-increase-tracks-caffeine-behavioral-rescue]] | direct | high |

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `24` | 总样本数 |
| 检验方法 | `correlation_pearson` | t_test_one_sample, t_test_independent, t_test_paired 等(共 37 候选,见 paper_stats) |
| 统计量类型 | `r` | t, F, r 等(共 21 候选,见 paper_stats) |
| 统计量数值 | `0.61` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `r` | cohen_d, hedges_g, r 等(共 16 候选,见 paper_stats) |
| 效应量数值 | `0.61` | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | _(论文未报告)_ | 如 [0.18, 0.50](null=未报告) |
| 自由度 (df) | _(论文未报告)_ | 统计量对应的自由度(null=未报告) |
| p 值 | `0.002` | 原始 p 值(null=未报告) |
| p 值校正 | `uncorrected` | uncorrected, bonferroni, holm_bonferroni 等(共 11 候选,见 paper_stats) |
| 备注 | `Right DLPFC showed the same direction at smaller magnitude (+0.14 ± 0.10 µM·cm); medial PFC and HbR null (all p > .15).` | 上下文或限制说明 |

## 使用此证据的页面

- [[chen_2024_neurophotonics]]
- [[does-caffeine-improve-working-memory]]
- [[pfc-hbo-increase-tracks-caffeine-behavioral-rescue]]
