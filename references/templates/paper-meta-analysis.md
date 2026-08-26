<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 meta-analysis 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->
<!-- 注：meta-analysis 的"被试"实际上是各研究的样本量汇总；"结果"是合并效应量而非原始统计。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: meta 分析
- **领域**: （meta 分析的母领域，例如 神经影像 / 临床干预 / 心理测量 / 教育干预）
- **modality**: stats（统计方法学论文，无单一模态）
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）
- **注册号**: PROSPERO / OSF / 其他（如有）
- **PRISMA 报告**: 是否遵循 PRISMA 2020 / PRISMA-NMA

**研究目的**

（1-3 句话。这篇 meta 要回答的核心问题：合并什么效应、为什么需要合并。）

**纳入研究样本**

- **纳入研究数**: k=... 篇
- **总被试数**: N=...（实验组 n=... + 对照组 n=...）
- **人群**: 临床人群 / 健康被试 / 混合
- **跨研究范围**: 年份范围（如 2000-2024）、地理分布、语言
- **研究设计**: RCT / 准实验 / 观察性 / 横断面

**检索策略**

- **数据库**: PubMed / Web of Science / Scopus / Embase / Cochrane / PsycINFO / 其他
- **检索时间跨度**: 至 YYYY-MM
- **检索式**: 完整关键词组合（PICOS 拆解: Population/Intervention/Comparator/Outcome/Study design）
- **语言限制**: 英语 / 中文 / 多语 / 无限制
- **手工检索**: 参考列表 / 引文追踪 / 会议论文 / 灰色文献

**筛选流程（PRISMA）**

- **初始检索**: 记录数 N1
- **去重后**: N2
- **标题/摘要筛选**: 排除 N3
- **全文筛选**: 排除 N4（含排除原因记录）
- **最终纳入**: N5（含更新检索/追踪结果）

**质量评估**

- **评估工具**: Cochrane RoB 2 / ROBINS-I / Newcastle-Ottawa Scale (NOS) / JBI / AMSTAR 2 / 自定义清单
- **评估人**: 2 名独立 / 双盲 / 冲突协商
- **结果图表**: traffic light plot / summary plot

**数据分析**

- **效应量**: Cohen's d / Hedges' g / OR / RR / MD / SMD / r / 风险比
- **合并模型**: 固定效应 / 随机效应 (REML / DerSimonian-Laird / Paule-Mandel / Knapp-Hartung)
- **异质性检验**: Q 统计量 / I² / τ² / H² / 95% PI
- **亚组分析**: 按年龄/性别/疾病/模态/剂量等
- **meta 回归**: 调节变量 + meta-regression 系数 + Knapp-Hartung
- **敏感性分析**: 留一法 (leave-one-out) / 逐项剔除 / 仅高质量 / 固定 vs 随机
- **发表偏倚**: funnel plot / Egger 检验 / Begg 检验 / trim-and-fill / PET-PEESE / selection model
- **证据等级**: GRADE
- **软件**: R metafor / R meta / RevMan 5/6 / CMA / Stata metan / Python statsmodels

**结果**

（用原文 quote 嵌入关键统计值，不要自己翻译）

- > "整体合并效应 Hedges' g = 0.45 (95% CI [0.31, 0.59], p<0.001, k=24, N=1830)"（§3.1）
- > "异质性 I² = 58% (τ²=0.04, p=0.002)，采用随机效应模型"（§3.1）
- > "Egger 检验 t=1.32, p=0.20，未发现显著发表偏倚"（§3.4）
- > "亚组差异：fMRI vs EEG 子组效应差异 Δg=0.18, p=0.04"（§3.5）

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

**包含的研究列表**（反向链接）

- [[paper-001]] / [[paper-002]] / ...

**引用本论文的页面**

（反向链接，由后续维护自动填充）