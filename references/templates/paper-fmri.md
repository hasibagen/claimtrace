<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 fmri 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证
- **领域**: fMRI
- **modality**: fmri
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）

**研究目的**

（1-3 句话。这篇 fMRI 研究要回答的核心问题。注意区分 task-based / resting-state / structural。）

**被试**

- n=..., 人群=..., 年龄范围=..., 利手=..., 排除标准（含头动阈值/疾病/药物等）

**实验设计**

[task-based / resting-state / diffusion MRI (DTI/DKI) / perfusion (ASL) / spectroscopy]

**实验范式**

- **task**: block design / event-related / mixed
- **scan 类型**: T1 结构 / T2* 功能 / DTI / FLAIR
- **任务模式**: 静息态 6 分钟、任务态 (条件数 × 试次数) 等

**刺激材料**

（必备。语言/范式/时长/呈现软件 E-Prime/Psychopy/Presentation 等。）

**测量工具**

- **MRI 设备**: 厂商 + 场强（3T Siemens Prisma / 7T GE / ...）
- **头线圈**: 32 通道 / 64 通道
- **TR / TE**: ms
- **flip angle**:
- **体素大小**: mm × mm × mm
- **slice 数 / gap**: 
- **run 数 / 时长**:
- **fieldmap**: 有 / 无（用于 EPI 畸变校正）
- **刺激呈现同步**: E-Prime / Psychopy / 北斗星 sync box

**数据分析**

- **预处理软件**: SPM12 / SPM25 / FSL (FEAT) / AFNI / FreeSurfer / fmriprep / 自定义
  - **头动校正**: motion correction（6/12/36 参数模型）；framewise displacement 阈值
  - **配准**: T1→功能像→MNI 模板
  - **空间平滑**: FWHM（mm）
  - **去趋势 / 滤波**: 高通 / 低通 / 不滤波
  - **scrubbing**: FD > ? mm 时剔除 volume
  - **ICA-AROMA / FIX**: 自动成分清理
  - **生理噪声回归**: RETROICOR / aCompCor / 6/24/36 motion params
- **HRF 模型**: 标准 SPM canonical / FIR / tent basis / gamma + derivative + dispersion
- **GLM 设计**: 条件数 / 对照 / 调节因子（parametric modulator）/ 混淆变量
- **一/二阶分析**: OLS / 混合效应（FSL FLAME / SPM RFX）
- **多重比较校正**: FWE / FDR / cluster-level p<0.05 + cluster-defining threshold / TFCE / permutation
- **ROI 分析**: 基于 atlas（AAL / Brainnetome / Schaefer / 自定义 mask）
- **FC 分析**: seed-based / ROI-to-ROI / graph theory / ICA

**结果**

（用原文 quote 嵌入关键统计值，不要自己翻译）

- > "左侧 IFG 在条件 A 显著激活（peak MNI=[-46,18,28], Z=4.32, p_FWE<0.05, k=246）"（§3.2）
- > "DMN 内部 FC 在组间差异显著（t=…, p_FDR=…）"（§3.3）

**结论**

（作者自己的总结）

**核心主张 / 证据条目**(由渲染器从 frontmatter 生成表与全文嵌入,LLM 不手写;禁 CLAIM-001/EVID-NNN 编号)

- claim → `claims/<semantic-slug>.md`,frontmatter 契约见 `claim.md`
- evidence → `evidence/<author>-<year>-<slug>.md`,frontmatter 契约见 `evidence.md`
- paper 正文两大嵌入章节(`## 本论文的 Evidence(全文)` / `## 本论文支持的 Claims(全文)`)由 `wiki_render_nodes.py paper` 生成

**关联主题**

- [[topic-xxx]]

**关联主张**

- [[claim 语义 slug]]（如已存在）

**引用本论文的页面**

（反向链接，由后续维护自动填充）