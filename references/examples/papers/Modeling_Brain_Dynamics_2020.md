---
type: paper
schema_version: "plan_final_v1"
title: "Modeling Brain Dynamics in Brain Tumor Patients Using the Virtual Brain"
authors: [Aerts, H., et al.]
year: 2020
journal: eNeuro
doi: "10.1523/ENEURO.XXXX"
modality: fmri
tags: [brain-tumor, virtual-brain, graph-theory, computational-modeling]
citekey: aerts_2020_eneuro
generated: { by: "evidence-wiki-skill/pi", at: "2026-08-20" }
source: raw/Modeling_Brain_Dynamics_2020/full.md
paperinfo: "[[paperinfo/aerts_2020_eneuro]]"
---

# Modeling Brain Dynamics in Brain Tumor Patients Using the Virtual Brain

> **注意**:本文件为 v4 时期示例,plan_final 之前的 paper 节点结构(T-W4-028 标注)。
> 完整 plan_final §3.2 paper 节点 schema 升级待 Phase 2 实施。
> 仅作历史参考,**新抽取论文请用 wiki-extract-paper Skill 按 plan_final §3.2 + §5 流水线生成**。

**元信息**
- **作者**: Aerts H, et al.
- **年份**: 2020
- **期刊**: eNeuro
- **DOI**: 10.1523/ENEURO.XXXX
- **类型**: [方法]
- **领域**: [fMRI / 计算建模]

**研究目的**

本研究用 Virtual Brain (TVB) 框架对脑肿瘤患者的脑动力学进行建模,检验肿瘤对脑区间功能连接的影响。

**被试**

- n=52, 人群=脑肿瘤患者(WHO III/IV 级), 年龄=35-72 岁, 母语=N/A
- 对照组:n=52 匹配的健康成人

**实验设计**

cross-sectional(单时间点)

**实验范式**

resting-state(无任务扫描)

**刺激材料**

N/A(resting-state 无刺激)

**测量工具**

- fMRI: 3T Siemens scanner;TR=2 s;体素=3×3×3 mm
- TVB 框架建模(基于个体结构 MRI + DTI)

**数据分析**

- **预处理**: 软件=SPM12;头动阈值=3mm;平滑核=8mm FWHM
- **静息态分析**: 节点定义=TVB 脑区模板;边定义=皮尔逊相关;图论分析(全局指标+节点指标)
- **统计方法**: 置换检验(5000 次)
- **多重比较校正**: FDR q < 0.05

**结果**

- > "Brain tumor patients showed significantly reduced global efficiency in the tumor-affected hemisphere"(§3.2)
- > "The effect was most pronounced in patients with grade IV tumors"(§3.3)

**结论**

本研究证实 TVB 框架可用于脑肿瘤患者的脑动力学建模,肿瘤区域导致局部和全局网络效率下降。

**核心主张**(扁平化,plan_final §3.5 semantic-slug 引用)

- [[claims/tvb-multiscale-platform]] [author_claim] [direct] — TVB 框架可建模脑肿瘤患者脑动力学
  - 依据: §3.1
  - 类型: empirical_result

**证据条目**(扁平化 wikilink 引用)

- [[evidence/aerts-2020-tvb-tumor-network]] claim: [[claims/tvb-multiscale-platform]] | relation: SUPPORT | section: §3.2 | quote: "TVB successfully captured the brain dynamics"

**关联主题**

- [[topics/brain-tumor]]
- [[topics/virtual-brain]]
- [[topics/graph-theory]]

**引用本论文的页面**

(反向链接,由后续维护自动填充)

---

## 抽取说明(本节点由 wiki-extract-paper Skill T0-T4 流水线生成)

1. `wiki-extract-paper T0 Ingest` 读 full.md + 加载 paper-fmri.md 模板
2. T1 Scan 抽 5 字段摘要
3. T2 Extract 按模板字段白名单抽 14 字段 + CLAIM + EVIDENCE
4. T3 Evidence 读 paper_stats.md 统计契约 + verify_* 11 字段
5. T4 Audit 校验 quote/数值/wikilink + 跑 `wiki_render_evidence_body.py` 渲染 body
6. 用户审阅后移到 `papers/<BBT-citekey>.md`
7. `python3 wiki_lint.py` 4 层校验

# Modeling Brain Dynamics in Brain Tumor Patients Using the Virtual Brain

**元信息**
- **作者**: Aerts H, et al.
- **年份**: 2020
- **期刊**: eNeuro
- **DOI**: 10.1523/ENEURO.XXXX
- **类型**: [方法]
- **领域**: [fMRI / 计算建模]

**研究目的**

本研究用 Virtual Brain (TVB) 框架对脑肿瘤患者的脑动力学进行建模，检验肿瘤对脑区间功能连接的影响。

**被试**

- n=52, 人群=脑肿瘤患者（WHO III/IV 级）, 年龄=35-72 岁, 母语=N/A
- 对照组：n=52 匹配的健康成人

**实验设计**

cross-sectional（单时间点）

**实验范式**

resting-state（无任务扫描）

**刺激材料**

N/A（resting-state 无刺激）

**测量工具**

- fMRI：3T Siemens scanner；TR=2 s；体素=3×3×3 mm
- TVB 框架建模（基于个体结构 MRI + DTI）

**数据分析**

- **预处理**: 软件=SPM12；头动阈值=3mm；平滑核=8mm FWHM
- **静息态分析**: 节点定义=TVB 脑区模板；边定义=皮尔逊相关；图论分析（全局指标+节点指标）
- **统计方法**: 置换检验（5000 次）
- **多重比较校正**: FDR q < 0.05

**结果**

- > "Brain tumor patients showed significantly reduced global efficiency in the tumor-affected hemisphere"（§3.2）
- > "The effect was most pronounced in patients with grade IV tumors"（§3.3）

**结论**

本研究证实 TVB 框架可用于脑肿瘤患者的脑动力学建模，肿瘤区域导致局部和全局网络效率下降。

**核心主张**

1. **CLAIM-001** [author_claim] [direct] — TVB 框架可建模脑肿瘤患者的脑动力学
   - 依据: §3.1
   - 类型: empirical_result
   - 关联: [new claim]

2. **CLAIM-002** [author_claim] [direct] — 肿瘤区域导致脑网络全局效率下降
   - 依据: §3.2
   - 类型: empirical_result
   - 关联: [new claim]

**证据条目**

- [EVID-001] claim: CLAIM-001 | relation: SUPPORT | section: §3.1 | quote: "TVB successfully captured the brain dynamics"
- [EVID-002] claim: CLAIM-002 | relation: SUPPORT | section: §3.2 | quote: "global efficiency significantly reduced (p<0.001)"
- [EVID-003] claim: CLAIM-002 | relation: QUALIFY | section: §3.3 | quote: "effect most pronounced in grade IV tumors"

**关联主题**

- [[brain-tumor]]
- [[virtual-brain]]
- [[graph-theory]]
- candidate: [[fnirs-tumor-screening]]

**关联主张**

- [new claim]（如未来跨论文复用，再升级为 CLAIM-XXX 节点）

**引用本论文的页面**

（反向链接，由后续维护自动填充）

---

## 抽取说明（本节点由 wiki_ingest 流程生成）

1. `wiki ingest <pdf-path>` 创建本骨架（00-pending/Modeling_Brain_Dynamics_2020.md）
2. pi 读取 full.md 和 references/AGENTS.md §2.5，按 15 个字段抽取
3. `wiki check-evidence Modeling_Brain_Dynamics_2020` 校验数值可 grep
4. `wiki lint` 4 层校验
5. 用户审阅后移到 papers/Modeling_Brain_Dynamics_2020.md
6. `wiki index` 重建 INDEX.md
7. `wiki status` 查看状态