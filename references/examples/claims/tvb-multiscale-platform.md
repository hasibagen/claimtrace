---
type: claim
schema_version: "plan_final_v1"
statement: "TVB 框架可建模脑肿瘤患者的脑动力学,肿瘤区域导致局部和全局网络效率下降"
claim_type: empirical_generalization
origin: author
atomic: true

# 作用域(扁平化)
scope_population: "脑肿瘤患者(WHO III/IV 级,35-72 岁)"
scope_modality: "fMRI resting-state"
scope_task: "resting-state"
scope_region: "全脑(基于 TVB 脑区模板)"
scope_study_design: "cross-sectional"

# 验证状态(扁平化)
verify_status: preliminary
verify_confidence: 0.6
verify_strength: weak
verify_consensus: fringe
verify_evidence_count: 1
verify_supporting_count: 1
verify_contradicting_count: 0
verify_evidence_quality: low
verify_last_updated: "2026-08-24T18:00:00Z"

# 推理桥
reasoning: |
  作者基于 1 项 cross-sectional TVB 建模研究推断 TVB 框架适用于脑肿瘤患者。
  依据:建模可拟合患者脑动力学 + 全局网络效率显著下降(p<0.001,置换检验 5000 次)。
reasoning_type: empirical_generalization

# 关联(扁平化为 3 平行数组)
sources_targets: ["[[papers/Modeling_Brain_Dynamics_2020]]"]
sources_confidences: ["high"]
sources_relations: ["direct"]
supports_targets: []
supports_confidences: []
supports_relations: []
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
evidence_targets: ["[[evidence/aerts-2020-tvb-tumor-network]]"]
evidence_confidences: ["high"]
evidence_relations: ["direct"]
---

# TVB 框架可建模脑肿瘤患者脑动力学

**主张陈述**

TVB(The Virtual Brain)框架可建模脑肿瘤患者的脑动力学,肿瘤区域导致局部和全局网络效率下降。

**首次出现**

- [[papers/Modeling_Brain_Dynamics_2020]] §3.1, p.1
  > "TVB successfully captured the brain dynamics of brain tumor patients"

**支持证据**

- [[evidence/aerts-2020-tvb-tumor-network]] §3.2
  > "Brain tumor patients showed significantly reduced global efficiency in the tumor-affected hemisphere"
  - **验证**: p < 0.001(置换检验 5000 次,FDR 校正)
  - **样本**: n=52 患者 vs n=52 对照

**反对证据**

- (暂无)

**限定条件**

- 仅在 WHO III/IV 级脑肿瘤患者中显著
- 仅在 resting-state 下验证

**证据强度**

- **direct 实证**: 1 篇 § Modeling_Brain_Dynamics_2020
- **indirect 关联**: 0 篇
- **contradict**: 0 篇
- **综合**: preliminary(仅 1 篇支持,需更多独立研究验证)

**引用此主张的页面**

- [[papers/Modeling_Brain_Dynamics_2020]]
- [[topics/brain-tumor-modeling]]
- [[syntheses/brain-dynamics-modeling-best-practices]]
