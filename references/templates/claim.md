# CLAIM 节点模板(frontmatter 契约,2026-08-26 对齐 claim.schema.json)

> **本文件 = claim 的字段契约**。schema 权威版:`.skill/scripts/schemas/claim.schema.json`。
> **LLM 只写 frontmatter,body 全部由 `wiki_render_nodes.py claim` 渲染**——不写 论断陈述/核心要点/关联证据/数值校验 等任何 body 段。

## 文件与命名

- 路径:`00-pending/<citekey>/claims/<semantic-slug>.md`(promote 后 → `claims/`)
- 命名:**语义 slug,禁编号**(禁 CLAIM-001/EVID-NNN)、禁数学符号(`+ = [ ] ( ) ^ % ,`)、禁抽取标记;中文优先 + 真实空格,≤30 字
- 例:`TVB 个体化建模大幅提升 FC 拟合度.md`(✓) / `CLAIM-001_WM.md`(✗)

## frontmatter 字段(必填 ★ / 枚举 ∷)

```yaml
---
type: claim                      # ★ 固定
schema_version: plan_final_v1
claim_id: <citekey>-C<n>-<slug>   # 内部 id(文件名不带编号,此字段可带)
statement: >-                    # ★ 原子化单命题中文陈述;禁退化成标题;
  #   含关键数值(F/p/r/n)与其证据同源;单行,禁 **bold**
claim_type: empirical_result     # ★ ∷ empirical_result|empirical_generalization|
                                 #      theoretical_interpretation|methodological|meta_analytic
origin: extracted                # ∷ extracted|author|normalized|synthesized
atomic: true                     # statement 是否单命题
scope_population: 成人 31-77 岁,脑肿瘤患者与健康对照   # 5 个 scope_* 限定边界
scope_modality: structural MRI + rs-fMRI + 计算建模
scope_task: resting-state
scope_region: 全脑 Desikan-Killiany 68 区
scope_study_design: 横断面计算建模
verify_status: supported         # ★ ∷ supported|partial|contradicted|no_evidence
verify_confidence: high          # ∷ high|medium|low
verify_strength: moderate        # ∷ strong|moderate|weak|inconclusive
verify_consensus: emerging       # ∷ established|emerging|fringe
verify_evidence_count: 1         # 证据计数 4 件套
verify_supporting_count: 1
verify_contradicting_count: 0
verify_evidence_quality: high
verify_last_updated: '2026-08-26'
reasoning: >-                    # 为何证据支持该陈述(推理链)
reasoning_type: empirical_inference   # ∷ empirical_inference|theoretical_assumption|methodological_design
sources_targets: ['[[<本论文 citekey>]]']   # 出处边:指向 paper,[[wikilink]] 列表
sources_confidences: [high]      # 与 sources_targets 平行等长 ∷ high|medium|low
sources_relations: [direct]      # ∷ direct|indirect|partial
supports_targets: ['[[已有上位 claim]]']   # 支持边:只链已有 claim,新建从严
supports_confidences: [medium]
supports_relations: [direct]
contradicts_targets: []          # 反对边(空也要给平行数组)
contradicts_confidences: []
contradicts_relations: []
evidence_targets: ['[[<author>-<year>-<slug>]]']   # ★ 证据边:指向本论文 evidence 节点
evidence_confidences: [high]
evidence_relations: [direct]
claim_origin: author_conclusion  # ∷ author_conclusion|extracted|normalized|synthesized|user
---
```

## 平行数组规则(铁律)

`*_targets / *_confidences / *_relations` 三组**必须等长**;渲染器与 lint 按下标对齐,错位 = L1.5 报错。

## 禁字段(旧架构残留,S4 见到即退回)

- `prov_paper: '[[papers/TODO]]'`、`prov_source_text: (待补)` —— **claim 契约无此二字段**;
  claim 的出处走 `sources_targets`(→paper),证据原文在 evidence 节点的 `prov_source_text` 上
- `related_papers` / `related_evidence` / `related_synthesis`(旧字段名)→ 用 `sources_targets` / `evidence_targets`
- `statement` 禁等于文件名标题(退化);短陈述(<25 字)会被 S4 退回

## 数值规范

- YAML 数值一律真数字;科学计数法**必须带小数点**(`1.0e-20` ✓,`1e-20` 会被 YAML 1.1 读回字符串)
- 布尔用 true/false;日期用引号字符串
