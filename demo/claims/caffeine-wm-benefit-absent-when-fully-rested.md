---
type: claim
claim_id: demo-C4
statement: "In fully rested adults with actigraphy-verified 7-9 h sleep, 200 mg caffeine does not improve working-memory accuracy or prefrontal hemodynamics."
claim_type: empirical_result
origin: extracted
atomic: true
scope_population: "fully rested healthy adults 19-33 years"
scope_modality: "fNIRS (hbO) + behavioral task"
scope_task: "2-back and 3-back"
scope_region: "prefrontal cortex"
scope_study_design: "randomized double-blind crossover with Bayes-factor sensitivity analysis"
verify_status: supported
verify_confidence: high
verify_strength: moderate
verify_consensus: emerging
verify_evidence_count: 1
verify_supporting_count: 1
verify_contradicting_count: 0
verify_evidence_quality: high
verify_last_updated: "2026-10-08"
reasoning: "Null effect on both outcomes with moderate evidence for the null (BF01 = 4.6) in a sample verified as rested — an informative boundary condition, not a failed replication."
reasoning_type: empirical_inference
sources_targets: ["[[dias_2023_psychophysiol]]"]
sources_confidences: [high]
sources_relations: [direct]
supports_targets: []
supports_confidences: []
supports_relations: []
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
evidence_targets: ["[[dias-2023-null-rested-wm]]"]
evidence_confidences: [high]
evidence_relations: [direct]
claim_origin: extracted
role_in_paper: central
polarity: null_result
epistemic_stance: demonstrated
qualifier: "Absence of evidence at n = 32 becomes evidence of absence only via the Bayes factor."
boundary: "Rested baseline only; says nothing about sleep-restricted states."
---

<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->

# caffeine-wm-benefit-absent-when-fully-rested

## 主张陈述

In fully rested adults with actigraphy-verified 7-9 h sleep, 200 mg caffeine does not improve working-memory accuracy or prefrontal hemodynamics.

## 推理桥

Null effect on both outcomes with moderate evidence for the null (BF01 = 4.6) in a sample verified as rested — an informative boundary condition, not a failed replication.

- 推理类型: `empirical_inference`

## 来源论文

[[dias_2023_psychophysiol]]

## 支持证据

| 证据 | 关系 | 置信度 |
|------|------|--------|
| [[dias-2023-null-rested-wm]] | direct | high |

## 限定条件

- 人群: fully rested healthy adults 19-33 years
- 模态: fNIRS (hbO) + behavioral task
- 任务: 2-back and 3-back
- 脑区: prefrontal cortex
- 设计: randomized double-blind crossover with Bayes-factor sensitivity analysis

## 证据强度

- 验证状态: `supported`  · 强度: `moderate`  · 共识: `emerging`
- 证据计数: 1(支持 1 / 反对 0)

## 引用此主张的页面

- [[caffeine-sleep-attention]]
- [[chen-2024-caffeine-3back-accuracy]]
- [[dias-2023-null-rested-wm]]
- [[dias_2023_psychophysiol]]
