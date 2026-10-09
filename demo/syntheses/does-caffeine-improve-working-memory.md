---
type: synthesis
schema_version: plan_final_v1
id: does-caffeine-improve-working-memory
question: "Does caffeine improve working-memory performance, and under which sleep states? (demo synthesis over 3 fictional papers)"
generated_by: "demo-generator + human review"
generated_at: "2026-10-08"
evidence_cutoff: "2026-10-08"
strength: {grade: moderate, evidence_count: 4, consistency: high, strength_reason: "3 small fictional RCTs (n=24/48/32), direction consistent across total deprivation, partial restriction and rested states; effects large under sleep loss, null at rested baseline; single-lab montage continuity"}
---

# Does caffeine improve working memory? (demo synthesis)

> **Demo artifact.** Synthesizes 3 *fictional* papers to demonstrate the
> Evidence × Claim matrix, GRADE strength rating, typed-edge handling of a
> boundary condition, and the ABT narrative format.

## 研究问题(Question)

咖啡因是否改善工作记忆表现?在什么睡眠状态下成立?

## Evidence × Claim 矩阵

| Evidence ↓ / Claim → | C1 咖啡因修复睡眠剥夺后 WM 准确率 | C2 左DLPFC hbO 增益与行为修复耦合 | C3 剂量-反应为倒U(峰值≈200mg) | C4 充分休息时无获益 |
|---|---|---|---|---|
| [[chen-2024-caffeine-3back-accuracy]] | **supports**(direct/high) | — | — | — |
| [[chen-2024-dlpfc-hbo-behavior-coupling]] | — | **supports**(direct/high) | — | — |
| [[okafor-2025-dose-response-inverted-u]] | **qualifies**(partial/medium):部分剥夺同向 | — | **supports**(direct/high) | — |
| [[dias-2023-null-rested-wm]] | **qualifies**(partial/high):边界=充分休息 | — | — | **supports**(direct/high) |

## 强度评级(GRADE 简化版)

**moderate** — 3 个小样本 RCT(n=24/48/32)方向一致;睡眠剥夺/限制下效应量大(d=0.86),静息基线 null(BF01=4.6);同一 22 通道前额叶 montage 提高了跨研究可比性;无直接 contradicting 证据,唯一的"冲突"是 Dias 2023 的 null,经 qualifies 边界定为 C1 的边界条件而非反例。

## ABT 叙事(And-But-Therefore)

**And**:睡眠剥夺损害工作记忆并降低前额叶氧合,咖啡因是最常用的对策——Chen([[chen_2024_neurophotonics]])显示 24 h 剥夺后 200 mg 使 3-back 准确率提升 7.5 个百分点(d=0.86),且个体行为增益与左 DLPFC hbO 增益耦合(r=0.61);Okafor([[okafor_2025_j_neuroeng_rehab]])在 5 h 限制下复现同向效应并定位血流峰值于 200 mg(400 mg 无增益且紧张感 9/16)。**But**:Dias([[dias_2023_psychophysiol]])在体动记录仪验证充分休息的样本中,同一剂量对行为与血流均为 null(p=.424;BF01=4.6)。**Therefore**:咖啡因的获益是**恢复性的而非增强性的**——它修复睡眠损失造成的功能缺陷,不把静息基线推得更高;实践含义是"咖啡因只在你缺觉时帮你,且 200 mg 附近最优",研究含义是咖啡因-WM 研究必须报告并控制睡眠状态,否则效应不可解释。

## 边界与矛盾处理

- Dias 2023 的 null 以 `qualifies`(partial/high)边挂在 C1 上,而不是 contradicts:C1 的 scope 限定"睡眠损失后",null 出现在 scope 之外,构成边界条件(铁律 #9:claim ≠ paper conclusion;铁律 #11:矛盾作为知识保留并类型化)。
- Okafor 2025 的 qualifies(partial/medium):5 h 部分剥夺 < 24 h 完全剥夺,剂量设计为被试间,外推强度打折。
- 缺口:无 400 mg 在完全剥夺下的数据;无女性月经周期控制报告;无长期习惯摄入的调节分析。

## 更新历史

- 2026-10-08 demo vault 初版(3 篇虚构论文,4 evidence,4 claims)。

