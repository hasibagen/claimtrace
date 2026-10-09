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
# ↓↓↓ 深度契约 6 字段(2026-09-16,全部 optional,无则不写、禁空串;详见下方「深度契约」节)
role_in_paper: central           # ∷ central|supporting|ancillary(缺省=supporting);central 通常 1-3 条
polarity: positive               # ∷ positive|negative|null_result|mixed;零结果默认建 claim 并标 null_result
epistemic_stance: demonstrated   # ∷ demonstrated|inferred|hypothetical|contested(作者立场,≠origin 出处语义)
qualifier: >-                    # 作者 hedging 原文(may/suggests/…)原样保留+中文一句话说明
boundary: >-                     # 成立边界与失效条件:作者明示局限+未覆盖人群/条件(该证据不能证明什么)
alternative_explanations: >-     # 替代解释:作者承认的+承认未排除的
---
```

## 深度契约(2026-09-16,源自书籍/方法论批次 + mn 笔记金标准)

**statement 五要素构成式**(deep-read 的 empirical claim 应尽量齐备):
①方向与形状(增/减/优于/仅在 X 时) ②关键数值(F/p/r/n,与证据同源) ③作用对象与人群(scope 内嵌)
④条件与对照(vs 什么基线) ⑤有则给机制结论。纯数值罗列而无方向/条件 = 浅抽取,S4 深度记分板预警。

**reasoning 深度契约**:reasoning = 推理桥(warrant:证据为何支持该陈述)+ 机制(结果为何发生)。
必须区分「作者解释」与「抽取者推演」(后者显式标注「抽取者推演:」)。deep-read 的 empirical claim
必填且 ≥40 字;「论文 §4.2 直接报告」式一句话 reasoning 视为未完成。

**深度五问**(每条 claim 自检,第 3-5 问答案落 reasoning/qualifier/boundary/alternative_explanations):
1. 方向与大小?(效应方向、数值、极性→polarity)
2. 在谁/什么条件下成立?(人群/任务/对照→scope_* + statement 内嵌)
3. 为什么发生?(机制/推理→reasoning)
4. 什么情况下不成立/作者如何限定?(→boundary + qualifier,英文 hedging 原样保留)
5. 有没有别的解释?与哪些前人一致或矛盾?(→alternative_explanations + supports/contradicts 边)

**负结果规则**:null/negative 发现默认建 claim(polarity 标注),禁因"不显著"丢弃。

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
