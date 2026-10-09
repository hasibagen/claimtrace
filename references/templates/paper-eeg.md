<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 eeg 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证
- **领域**: EEG（含 ERP / ERD / TFR / 微状态 / 网络分析等）
- **modality**: eeg
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）

**研究目的**

（1-3 句话。这篇 EEG 研究要回答的核心问题。注意区分 ERP / 频谱 / 时频 / 微状态 / 网络。）

**被试**

- n=..., 人群=..., 年龄范围=..., 利手=..., 母语=..., 视力/矫正=...

**实验设计**

[within-subjects / between-subjects / RCT / longitudinal / cross-sectional]

**实验范式**

- **范式**: oddball / n-back / Flanker / Go/NoGo / passive listening / resting-state（eyes open/closed）/ ...
- **block / event-related / continuous**: 
- **试次**: 每条件 N trials
- **试次内时长**: ISI / SOA（ms）

**刺激材料**

（必备。语言/范式/时长/声压级/呈现软件等关键参数。）

**测量工具**

- **EEG 系统**: Brain Products actiCHamp / Neuroscan SynAmps / BioSemi ActiveTwo / EGI / g.tec / ANT Neuro / Kernel Flow
- **电极数**: 32 / 64 / 128 / 256 通道
- **电极帽型号**: 10-20 国际标准 / 10-10 / 高密度
- **参考电极**: 在线参考（如 FCz）/ 双耳平均 / Cz / mastoids（TP9/TP10）
- **地线**: AFz / 独立接地电极
- **采样率**: Hz（如 500 / 1000 / 2048 / 4096）
- **电极阻抗阈值**: < 5 kΩ / < 10 kΩ / < 20 kΩ
- **刺激呈现同步**: E-Prime / Psychopy / Presentation

**数据分析**

- **预处理软件**: EEGLAB / MNE-Python / Brainstorm / FieldTrip / Curry / NeuroGuide / 自定义
  - **滤波**: 带通（Hz）；陷波 50 / 60 Hz
  - **重参考**: REST / 平均 / 双耳 / 表面 Laplacian / 不重参考
  - **ICA 成分**: 多少成分、是否剔除眼电（眨眼、水平眼动）/ 肌电 / 心脏伪迹
  - **伪迹检测**: 振幅阈值 / 梯度阈值 / 自动 vs 人工
  - **坏导插补**: 插值（spline）/ 删除
- **分段 epoch**: -200 ~ 800 ms / 跨任务分段
- **基线校正**: -200 ~ 0 ms / 其他
- **ERP 分析**: 感兴趣成分（N170 / P300 / N400 / P600 / MMN / N400-like / FRN）
- **时频分析**: 小波 / Morlet / 多锥 / 短时傅里叶；频段（delta/theta/alpha/beta/gamma）
- **微状态分析**: 微状态数量 / 地形图（k-means）/ 时域参数（GEV）
- **源定位**: LORETA / sLORETA / eLORETA / beamforming / dipole
- **连通性**: PLV / ITC / AEC / Granger / DCM / 网络指标
- **统计方法**: cluster-based permutation / mass-univariate t/F / mixed-effects / Bayes factor
- **多重比较校正**: cluster permutation / FDR / Bonferroni / TFCE

**结果**

（用原文 quote 嵌入关键统计值，不要自己翻译）

- > "P300 振幅在条件 A 显著大于条件 B（Fz: t(39)=3.42, p_FDR=0.012, d=0.54）"（§3.2）
- > "theta ERD 在条件 A 显著强于条件 B（cluster p<0.05, max t=4.10）"（§3.3）

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