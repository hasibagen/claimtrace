<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 eye-tracking 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->
<!-- 注：模态枚举 [fnirs, eeg, fmri, multimodal, ml, meta, other]；眼动归类 `other` 或 `multimodal`（与 fNIRS/EEG/fMRI 联用时）。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证
- **领域**: 眼动追踪 (Eye Tracking)
- **modality**: other（眼动单模态）/ multimodal（眼动 + EEG/fNIRS/fMRI/行为）
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）

**研究目的**

（1-3 句话。这篇眼动研究要回答的核心问题。注意区分注视/扫视/瞳孔/微扫视。）

**被试**

- n=..., 人群=..., 年龄范围=..., 视力/矫正（正常/佩戴）/ 色觉（正常/筛查）

**实验设计**

[within-subjects / between-subjects / RCT / cross-sectional / longitudinal]

**实验范式**

- **范式**: visual world / free viewing / visual search / reading / scene viewing / social attention / RSVP / change blindness
- **block / trial / continuous**: 
- **试次**: 每条件 N trials
- **刺激呈现**: 屏幕尺寸 + 分辨率 + 观看距离 + 视角

**刺激材料**

（必备。图片/视频/文字材料。数量、来源、版权、是否标准化语料。）

**测量工具**

- **眼动设备**: EyeLink 1000 / 1000 Plus / Portable Duo / Tobii Pro Spectrum / Tobii T60 / Gazepoint GP3 / Pupil Labs / SMI / SR Research
- **采样率**: Hz（1000 / 2000 / 500 / 60-300 Tobii 桌面）
- **追踪模式**: 瞳孔 角膜反射 (P-CR) / 暗瞳孔 / 亮瞳孔
- **空间精度**: 亚像素精度（如 0.25°-0.5°）
- **头部固定**: 托架 (chinrest) / 自由头动 / 桌面 (Tobii 红外)
- **校准**: 9 点 / 5 点；漂移校正频率（每 N trials / 每 block）
- **双眼 / 单眼**: 双眼记录 / 主眼 / 单眼
- **瞳孔记录**: 是 / 否（mm / 任意单位）
- **刺激呈现同步**: E-Prime / Psychopy / Presentation / Tobii Studio

**数据分析**

- **预处理软件**: Tobii Studio / EyeLink Data Viewer / Pupil Player / GazeR / EM/EEG pipeline (MNE)
  - **眨眼检测**: 自动 vs 人工；线性插值窗口
  - **采样降噪**: 中值滤波 / Savitzky-Golay
  - **事件定义**: fixation / saccade / blink 的速度+加速度阈值
  - **兴趣区 (AOI)**: 矩形 / 多边形 / 圆形；是否基于坐标
  - **事件剔除**: 注视时长 < 80 ms / 偏差阈值
- **指标体系**:
  - **注视**: 首次注视时间 (FFT) / 凝视时间 (Dwell Time) / 总注视时长 / 注视次数 / 注视位置
  - **扫视**: 扫视潜伏期 / 幅度 / 峰值速度 / 扫视路径
  - **瞳孔**: 基线校正后瞳孔直径变化 / 瞳孔响应曲线
  - **回视**: 回视次数 / 回视潜伏期
  - **序列指标**: 转移概率 / 路径相似度 / scanpath comparison
- **统计方法**: 线性混合模型 (LMM) / 重复测量 ANOVA / GAM / Bayesian
- **多重比较校正**: FDR / Bonferroni / cluster permutation / 留一交叉
- **单试次 vs 聚合**: 单 trial-level（gazeR/pupil-premium）/ 聚合条件均值

**结果**

（用原文 quote 嵌入关键统计值，不要自己翻译）

- > "在目标 AOI 的首次注视时间显著短于对照条件（t(39)=-3.21, p<0.01, d=0.51）"（§3.2）
- > "瞳孔直径在情绪刺激后 1-3 秒扩张显著大于中性刺激（F(2,38)=8.5, p<0.001, η²p=0.31）"（§3.3）

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