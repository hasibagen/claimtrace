---
type: topic
schema_version: "plan_final_v1"
id: brain-tumor-modeling
status: active

# Brain Tumor Modeling(脑肿瘤建模)

**主题描述**

用计算建模方法(TVB、动态因果模型 DCM、网络模型)研究脑肿瘤对患者脑动力学的影响。聚焦肿瘤局部压迫对全脑功能连接和网络效率的远端效应。

**涉及论文**

- [[papers/Modeling_Brain_Dynamics_2020]] — TVB 建模 fMRI resting-state
- (待补充)

**核心主张**

- [[claims/tvb-multiscale-platform]] — TVB 框架可建模脑肿瘤患者(preliminary)

**共识**

1. TVB/DCM 等计算模型可捕捉脑肿瘤患者的脑动力学变化(来源:[[papers/Modeling_Brain_Dynamics_2020]])

**矛盾**

- (暂无)

**空白**

- 缺乏在儿童脑肿瘤患者中的研究
- 缺乏治疗前后纵向建模对比
- 缺乏多模态(fMRI + EEG + fNIRS)融合建模

**关联主题**

- [[brain-network]]
- [[computational-neuroscience]]
- [[cancer-neuroscience]]

---

## 创建触发

本主题节点创建触发条件(满足任一):

- 用户明确说"建主题 brain-tumor-modeling"
- 2+ 论文聚集到此主题
- 用户提问涉及此主题

当前状态:1 篇论文聚集 + 用户明确意图 → 已创建。

未来若有 2+ 论文引用同一主题,paper 节点的 `**关联主题**` 字段会直接 wikilink 到本节点。
