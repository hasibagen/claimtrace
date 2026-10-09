---
type: claim
claim_id: demo-C1
statement: "After total or partial sleep loss, a moderate caffeine dose (200 mg) partially restores working-memory accuracy relative to placebo."
claim_type: empirical_result
origin: extracted
atomic: true
scope_population: "healthy adults 18-34 years, habitual low-to-moderate caffeine users"
scope_modality: "fNIRS (prefrontal hbO) + behavioral task"
scope_task: "n-back working memory (2/3-back), sustained attention"
scope_region: na
scope_study_design: "randomized double-blind crossover (total deprivation) + between-subjects dose (partial restriction)"
verify_status: supported
verify_confidence: high
verify_strength: moderate
verify_consensus: emerging
verify_evidence_count: 2
verify_supporting_count: 2
verify_contradicting_count: 0
verify_evidence_quality: high
verify_last_updated: "2026-10-08"
reasoning: "Two independent experiments converge: a within-subject rescue after 24-h total deprivation (Chen 2024) and a hemodynamic dose-response under 5-h restriction peaking at the same 200 mg dose (Okafor 2025). The rest-state null (Dias 2023) does not weaken the sleep-loss claim; it bounds it."
reasoning_type: empirical_inference
sources_targets: ["[[chen_2024_neurophotonics]]", "[[okafor_2025_j_neuroeng_rehab]]"]
sources_confidences: [high, medium]
sources_relations: [direct, partial]
supports_targets: []
supports_confidences: []
supports_relations: []
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
evidence_targets: ["[[chen-2024-caffeine-3back-accuracy]]", "[[okafor-2025-dose-response-inverted-u]]"]
evidence_confidences: [high, medium]
evidence_relations: [direct, partial]
claim_origin: extracted
role_in_paper: central
polarity: positive
epistemic_stance: demonstrated
qualifier: "Okafor 2025 qualifies with partial (5 h) rather than total deprivation and a between-subjects design."
boundary: "Dias 2023: no benefit in fully rested adults — the claim does not extend above rested baseline."
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# caffeine-restores-wm-accuracy-after-total-sleep-deprivation

## 主张陈述

After total or partial sleep loss, a moderate caffeine dose (200 mg) partially restores working-memory accuracy relative to placebo.

## 推理桥

Two independent experiments converge: a within-subject rescue after 24-h total deprivation (Chen 2024) and a hemodynamic dose-response under 5-h restriction peaking at the same 200 mg dose (Okafor 2025). The rest-state null (Dias 2023) does not weaken the sleep-loss claim; it bounds it.

- 推理类型: `empirical_inference`

## 来源论文

[[chen_2024_neurophotonics]] [[okafor_2025_j_neuroeng_rehab]]

## 支持证据

| 证据 | 关系 | 置信度 |
|------|------|--------|
| [[chen-2024-caffeine-3back-accuracy]] | direct | high |
| [[okafor-2025-dose-response-inverted-u]] | partial | medium |

## 限定条件

- 人群: healthy adults 18-34 years, habitual low-to-moderate caffeine users
- 模态: fNIRS (prefrontal hbO) + behavioral task
- 任务: n-back working memory (2/3-back), sustained attention
- 脑区: na
- 设计: randomized double-blind crossover (total deprivation) + between-subjects dose (partial restriction)

## 证据强度

- 验证状态: `supported`  · 强度: `moderate`  · 共识: `emerging`
- 证据计数: 2(支持 2 / 反对 0)

## 引用此主张的页面

- [[caffeine-sleep-attention]]
- [[chen-2024-caffeine-3back-accuracy]]
- [[chen_2024_neurophotonics]]
- [[dias-2023-null-rested-wm]]
- [[okafor-2025-dose-response-inverted-u]]
- [[okafor_2025_j_neuroeng_rehab]]
