---
type: synthesis
schema_version: "plan_final_v1"
question: "用 TVB/DCM 等框架建模脑动力学时,应该遵循哪些处理流程和参数选择?"
generated_by: "user-question"
generated_at: "2026-08-20"
updated_at: "2026-08-24T18:00:00Z"
status: active

# 脑动力学建模的最佳实践是什么?

**问题**

用 TVB/DCM 等框架建模脑动力学时,应该遵循哪些处理流程和参数选择?

**结论**

基于当前 wiki 收录证据,建议:

1. **预处理**: 用 SPM12/FSL/FreeSurfer 做标准 fMRI 预处理
2. **头动阈值**: 3mm(FD < 0.5)
3. **平滑核**: 6-8mm FWHM
4. **模型选择**: 根据研究问题选 TVB(全脑网络)或 DCM(特定连接)
5. **统计校正**: FDR q < 0.05 或置换检验 5000 次
6. **模板**: TVB 脑区模板或 Power 264 节点

**关键证据链**

1. [[claims/tvb-multiscale-platform]](1 支持 / 0 反对 / preliminary)
   - 支持: [[papers/Modeling_Brain_Dynamics_2020]]

**证据强度**

- 方向 TVB 建模: preliminary(仅 1 篇支持)
- 方向 DCM 建模: insufficient(无证据)

**边界**

- 仅适用于 fMRI resting-state 数据
- 不能推广到 task-based fMRI 或 EEG 数据
- 需要更多独立研究的复制验证

**涉及页面**

- [[topics/brain-tumor-modeling]]
- [[claims/tvb-multiscale-platform]]
- [[papers/Modeling_Brain_Dynamics_2020]]

**更新历史**

- 2026-08-20: 首次创建(基于 [[papers/Modeling_Brain_Dynamics_2020]] 一篇论文)
- 2026-08-24: 按 plan_final §3.5 重写 frontmatter(wikilink 用 semantic-slug)
