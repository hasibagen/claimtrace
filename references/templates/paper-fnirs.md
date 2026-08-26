<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 fnirs 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证
- **领域**: fNIRS
- **modality**: fnirs
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）

**研究目的**

（1-3 句话。这篇 fNIRS 研究要回答的核心问题。）

**被试**

- n=..., 人群=..., 年龄范围=..., 母语=..., 利手=..., 视力/矫正=...

**实验设计**

[cross-sectional / longitudinal / RCT / within-subjects / between-subjects / ...]

**实验范式**

[block design / event-related / resting-state / 自然刺激 / ...]

**刺激材料**

（必备。语言/范式/时长/声压级/呈现方式等关键参数。）

**测量工具**

- **fNIRS 设备**: 厂商 + 型号（如 Hitachi ETG-4000、Artinis Brite、NIRx NIRScout、Kernel Flow 等）
- **通道数**: source × detector → N 通道
- **光源波长**: 常用 695 + 830 nm 双波长；自定义波长需说明
- **采样率**: Hz
- **覆盖脑区**: 额叶/颞叶/顶叶/枕叶；是否覆盖全脑
- **空间配准**: 10-20 系统 / 概率/确定 atlas（MNI/Colin）
- **刺激呈现同步**: E-Prime / Psychopy / Presentation / 其他

**数据分析**

- **预处理软件**: Homer3 / NIRS-SPM / Brain AnalyzIR / fNIRS Toolbox / 自定义脚本
  - **坏导检测**: 阈值（如 SCI > 0.5 / CV > 7.5%）
  - **运动伪迹校正**: spline / wavelet / targeted PCA / CBSI / 没做
  - **滤波**: 带通范围（Hz）
  - **基线校正**: 窗口（s）
  - **HRF 卷积**: 标准双 gamma / 典型 HRF / 自定义 / 不卷积
- **GLM 设计**: 条件/对照；回归因子（行为指标/混淆变量）
- **一/二阶分析**: 组水平（OLS / 混合效应 LMM）
- **多重比较校正**: FDR q < / FWE / cluster-based permutation / TFCE
- **HbO / HbR 选择**: 主报告 HbO / 主报告 HbR / 同时报告 / t 值

**结果**

（用原文 quote 嵌入关键统计值，不要自己翻译）

- > "通道 X 的 HbO 在条件 A 显著高于条件 B（t=…, p_FDR=…, d=…）"（§3.2, p.5）
- > "发育相关：HbO 峰值振幅与年龄呈正相关 r=0.45, p<0.01"（§3.3, p.6）

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