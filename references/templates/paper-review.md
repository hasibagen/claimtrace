<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件只提供 review 叙事字段检查单。schema 权威版: .skill/scripts/schemas/ -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"` 以促进 claim/evidence 跨论文追踪。 -->
<!-- T2 阶段抽 paper 叙事字段;CLAIM/T3 EVIDENCE 在 T2-T3 阶段按 claim.md/evidence.md frontmatter 契约创建,body 由渲染器生成。 -->
<!-- 与 paper-meta-analysis 区别：综述侧重定性综合（不合并统计）；meta-analysis 合并定量效应。 -->
<!-- 综述论文的"被试"维度被"覆盖范围"取代；"结果"维度被"核心发现汇总"取代。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 综述
- **子类型**: [narrative review / systematic review / scoping review / umbrella review / narrative synthesis / qualitative review]
- **领域**: （综述的母领域，例如 神经影像方法学 / 临床干预 / 认知发展 / 教育干预）
- **modality**: other（综述无单一模态）/ multimodal（综述覆盖多模态时）
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）
- **注册号**: PROSPERO / OSF / 其他（如有）
- **PRISMA 报告**: 是否遵循 PRISMA 2020 / PRISMA-ScR (scoping) / 特定主题指南 (PRISMA-NMA, PRISMA-Equity 等)

**研究目的**

（1-3 句话。这篇综述要回答的核心问题。是 narrative 还是 systematic？是否覆盖某时间窗口/某语言/某数据库？）

**覆盖范围**

- **覆盖研究数**: k=... 篇
- **时间跨度**: YYYY-YYYY
- **研究设计**: RCT / 观察性 / 横断面 / 实验 / 混合
- **人群**: 临床 / 健康 / 跨人群 / 不限
- **纳入研究是否包含定量 meta**: 否（纯综述） / 是（则按 paper-meta-analysis 模板填）
- **语言限制**: 英语 / 中文 / 多语 / 无限制

**检索策略**

- **数据库**: PubMed / Web of Science / Scopus / Embase / Cochrane / PsycINFO / Google Scholar / 其他
- **检索时间跨度**: 至 YYYY-MM
- **检索式**: 关键词 + 主题词 / MeSH / 自由词组合（PICOS / SPIDER / SPICE 等框架）
- **手工检索**: 参考列表追溯 / 引文追踪 / 专家咨询 / 灰色文献

**筛选流程（PRISMA）**

- **初始检索**: 记录数 N1
- **去重后**: N2
- **标题/摘要筛选**: 排除 N3
- **全文筛选**: 排除 N4（含排除原因记录）
- **最终纳入**: N5（含更新检索/追踪结果）
- （若非 systematic 而无 PRISMA 流程，则填"N/A (narrative review)"）

**质量评估**

- **评估工具**: AMSTAR 2 / JBI / CASP / 自定义清单 / 风险偏倚评估工具
- **评估人**: 1 / 2 名独立 / 协商

**综合方法**

- **综合框架**: narrative synthesis / thematic synthesis / framework synthesis / meta-ethnography / realist synthesis / vote counting / best-evidence synthesis
- **结构化提取**: 数据提取模板 / 标准化字段 / 双盲提取
- **证据等级**: GRADE / OCEBM / 自定义
- **结果呈现**: 表 + 文字叙述 / 概念框架 / 主题图 / 证据矩阵

**核心发现汇总**

（按主题/亚组/争议性议题汇总，不嵌入统计值除非有 vote-counting）

- **核心共识**: 主题 A 多篇论文支持（k=X/N）；主题 B 多篇支持
- **核心争议**: 主题 C 存在 SUPPORT vs CONTRADICT（如半数以上综述作者倾向支持、其余反对）
- **研究空白**: 主题 D 缺乏 RCT / 缺乏纵向 / 缺乏跨文化 / 缺乏客观测量

**结论**

（作者自己的总结：当前证据状态、临床/学术建议、未来研究方向）

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