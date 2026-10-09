# ARCHITECTURE · Wiki 架构契约(终版)

> **定位**: 本文件是 wiki 数据与 skill 工具链的**唯一权威架构契约**(原 `plan_final.md`,2026-08-25 升格迁至根目录)。**任何 agent/pi session 在修改 wiki 数据或 `.skill/` 之前,必须先读本文件的相关章节**;与本文件冲突的实现一律视为 bug。整合 `19mimo_pi_plan.md`(v5 Pi-Native)+ `21_minimiax_pi_plan.md` + `ai第三次建议.md` + 7 份 AI 原始建议的共识。
>
> **整合来源**:
> - **19mimo_pi_plan.md** (35.3 KB):6 条 pi 原则 / 13 铁律 / Synthesis 动态视图 / Stitch-knowledge 微 Skill / 3 级分流 / Pipeline 编排
> - **21_minimiax_pi_plan.md** (37.4 KB):Markdown-Native / LLM-Semantic / Human-Gated 铁律 / LLM→JSON→MD 流水线 / Evidence Contract / 显式路由表
> - **ai第三次建议.md** (200 KB,10 个 AI):Evidence-centric / Warrant 降级 / Observation+Interpretation 拆分 / Provenance 对象 / 4+1 阶段
> - **7 份 AI 原始建议**:CERIC / Toulmin / SciFact / GRADE / Cornwell 七步 / ABT 叙事 / PICO 等
> - **22 个开源工具包**:EmpiricalWiki(集中 Schema 注册表/边类型系统/paper_kind 分流) / SciClaim(细粒度主张 KG) / SciFact / PaperJury / ScanSci Pi / MindCite 等
>
> **用户硬需求**:
> - Paper.md **全文嵌入**所有 claim/evidence(不用 `^summary` 块引用)
> - 载体是 md,用 pi 构建 wiki,**不用正则抽取**
> - **方法论家族**显式化(上一轮要求)
>
> **前置阅读**:`handoff-to-other-ais.md` / `16_mimo-pi-architecture.md`
>
> **写给读者**:Pi(agent)+ 人。

## 0.1 架构文档体系(单一契约 + 指针文件)

**架构契约只维护一份**:本文 `ARCHITECTURE.md`(wiki 根目录),数据架构(§1-§3)与工具链架构(§4 含 §4.6)都在这里。

`.skill/ARCHITECTURE.md` 是**纯指针文件**,只写指向本文的一行地址——**不要在指针文件里写任何规则**(避免双源漂移;2026-08-25 前曾为独立工具链契约,已并入本文 §4.6)。

历史设计记录(已定型、不再维护):`.skill/ref/backup/`。

---

## 0. 一句话总览

> **用 pi 的五件套，在 Minimax M3 上跑一个 5 类核心节点 + Evidence-Centric 方法论家族 + 3 模式 × 5 阶段抽取 + LLM→JSON→MD 流水线 + 全文嵌入(callout 折叠)+ 类型化语义图谱 + 集中 Schema 注册表 + Sub-agent Pipeline + 分层 Lint 的证据 Wiki；载体是 markdown，scripts 只做机械校验，所有语义理解与抽取由 LLM 完成。**

## 根文件三件套

本文件与另外两个文件构成 wiki 运行的**根文件三件套**(三者必须同步维护):

| 文件 | 位置 | 角色 |
|---|---|---|
| **`ARCHITECTURE.md`**(本文,原 plan_final.md) | wiki 根目录 | **架构契约** — wiki 数据与 skill 工具链应该长什么样 |
| **`tasks.md`** | `wiki/tasks.md` | **施工单** — 20 个 task，按 Week 1-4 推进 |
| **`log/`** | `wiki/log/` | **日志文件夹**(2026-08-27 替代单文件 log.md):`ops.md` 全局施工日志(append-only)+ `README.md` 批次索引 + `batch-*.md` 批次档案 |

**修订铁律**: 任何对 wiki 实际数据的修改,完成后**必须**同步更新 tasks.md(改状态) + ARCHITECTURE.md(如架构有变) + log/ops.md 或对应批次文件(添加记录)。

---

## 1. 设计哲学(6 条 Pi 原则 + 11 条铁律 + 方法论家族)

### 1.1 Pi 的 6 条核心原则 → Wiki 原则(源自 19 §1.1)

| Pi 原则 | 含义 | Wiki 映射 |
|---|---|---|
| **Progressive Disclosure** | description 始终在上下文,完整内容按需加载 | 节点 frontmatter 始终可见,正文通过 Transclusion 按需展开 |
| **On-demand Loading** | 只加载当前任务需要的 Skill | SKILL.md 只做路由,微 Skill 按需加载 |
| **Description-driven Routing** | description 字段决定何时调用 | 节点的 `type` + `description` 字段驱动 pi 意图识别 |
| **Self-contained Packages** | 每个 Skill 是独立能力包 | 每个微 Skill 是独立工作流,不依赖其他 Skill 上下文 |
| **Context Optimization** | 最小化上下文,最大化信息密度 | 节点默认展示摘要,全文通过 `![[...]]` 按需嵌入 |
| **Code Validates** | LLM 生成,代码校验 | LLM 抽取 → JSON Schema 校验 → Markdown 渲染 |

### 1.2 不可违反的铁律(11 条,新增 #11)

合并原则:**保留两份都强调的,合并重叠的,删除单方冗余的**:

```
 1. RAW IS IMMUTABLE               ← 19 + 21 都强调
 2. MARKDOWN IS THE SOURCE OF TRUTH ← 21 单独
 3. LLM EXTRACTS, SCRIPTS VALIDATE  ← 19 + 21 都强调
 4. NO REGEX ON MEANING             ← 19 + 21 都强调(用户硬需求)
 5. PROGRESSIVE DISCLOSURE          ← 19 单独
 6. CONTEXT OPTIMIZATION            ← 19 单独
 7. EVERY FACT HAS PROVENANCE       ← 19 + 21 都强调
 8. EVERY NUMBER IS VERIFIABLE      ← 19 + 21 都强调(Grounding Invariant)
 9. CLAIM ≠ PAPER CONCLUSION        ← 19 + 21 都强调
10. HUMAN REVIEWS PENDING           ← 19 + 21 都强调
11. GRAPH EDGES ARE TYPED & CONFIDENT ← 新增(EmpiricalWiki 模式)
```

**#11 Graph Edges Are Typed & Confident** (源自 EmpiricalWiki):
- 所有语义关系(边)必须有**类型**和**置信度**
- 类型: `supports` / `contradicts` / `qualifies` / `same_claim_as` / `extends` / `refines`
- 置信度: `high` / `medium` / `low`
- 防止"LLM 编造关系"——每条边必须可追溯到 evidence

### 1.3 方法论家族(Methodology Stack)— 用户硬需求

不挂单一方法论,而是 **Evidence-Centric 的方法论家族**:

| 层级 | 方法论 | 职责 | 在本架构的落地 |
|---|---|---|---|
| **顶层命名** | Scientific Evidence & Argument Mining | 对外品牌 / 概念定位 | 文档标题层级 |
| **数据骨架** | Evidence-centric KG | 节点 / 边的拓扑 | evidence 是中心,所有 claim/topic 都指向 evidence |
| **论文层** | **CERIC**(Cambridge 2026) | 单篇论文 5 要素拆解 | paper frontmatter + 抽取 schema |
| **论证内** | **Toulmin**(降级) | 单条 claim 的推理桥 | claim.reasoning 字段 |
| **验证层** | **SciFact / Wadden 2020** | claim 支持/反驳/无信息 | claim.verification 4 态 + evidence.supports/contradicts |
| **强度层** | **GRADE 简化版** | 跨证据的合成可信度 | synthesis.strength(**不在 claim 上**) |
| **抽取流程** | **Keshav 三遍 + Cornwell 七步** | T0-T4 的阶段划分 | §5.1 |
| **叙事层** | **ABT(And-But-Therefore)** | 跨论文综合的叙事链 | synthesis 节点正文结构 |
| **筛选层** | **PRISMA / PICO**(可选) | 大规模文献筛选 | scripts/ Phase 2 再加 |
| **细粒度层** | **SciClaim**(已弃用) | 科学主张的细粒度 KG | **弃用**(2026-08-25:落地率 0/368,字段已从 schema 删除) |

**为什么不用单一方法论?**(综合 7 份 AI 共识)
- **Toulmin**: 偏哲学,6 要素过重,**降级为 claim.reasoning 字段**(GPT §四)
- **IMRaD**: 只是论文结构,不是论证骨架,**作为抽取辅助**(语义识别章节)
- **GRADE**: 是"系统综述"产物,**放在 synthesis 而非 claim**(AI 第三次建议 §25)
- **CERIC**: 最贴近"批判性阅读",**不**解释跨论文关系
- **Discourse Graph**: 太轻,**不**用作骨架
- **Knowledge Graph**: 是表示形式,**不是**方法论

**账本状态(2026-08-25 批次4 实测)**:CERIC 的 C/E/R/I 落地 100%(324/368),**Critique→wiki-audit-paper Skill(新建)**;Toulmin 100%;SciFact 字段 100%(计数待聚合脚本自动化);GRADE/ABT **空转待首 synthesis**(聚合脚本已就绪);Keshav 运行中;Cornwell 审问→audit Skill;SciClaim **弃用(0/368)**。

**核心立场(给后续接手者)**:
> 本架构顶层命名 = **"Evidence-Centric Research Knowledge Representation"**
> (ChatGPT 给出的概括,7 份 AI 中最准);
> 骨架 = **CERIC + Toulmin(降级) + SciFact**;
> 抽取流程 = **Keshav + Cornwell**;
> 强度评价 = **GRADE 简化版**;
> 叙事方式 = **ABT**。

---

## 2. 节点模型(5 类核心,Evidence-centric)

### 2.1 5 类核心节点(从 v4 的 8 类收缩)

| 类 | 节点 | 目录 | 命名 | 谁创建 |
|---|---|---|---|---|
| **核心 1** | paperinfo | `paperinfo/` | `<BBT-citekey>.md` | scripts(zotero pull) |
| **核心 2** | paper | `papers/` | `<BBT-citekey>.md` | LLM(extract-paper) |
| **核心 3** | claim | `claims/` | `<semantic-slug>.md`(优先中文 + 真实空格) | LLM(extract-paper 或 build-claim) |
| **核心 4** | evidence | `evidence/` | `<author>-<year>-<slug>.md`(中英混合 + 真实空格) | LLM(extract-paper 或 build-evidence) |
| **核心 5** | synthesis | `syntheses/` | `<question-key>.md` | LLM(query-evidence)+ 按需固化 |

**辅助节点**:`topics/`(只在跨论文时才创建)、`00-pending/`(审阅缓冲带)。

**raw 层**(权威源,不是 wiki 节点,是 wiki 之外的"原始素材"):
- `raw/<BBT-citekey>/full.md` — MinerU 导出的论文正文(MUST 复制到 wiki 内部,不依赖外部)
- `raw/<BBT-citekey>/images/` — 论文图片(相对路径被 full.md 引用)
- **RAW IS IMMUTABLE**(铁律 #1):绝不修改,Grounding 引用都从这里 grep
- 复制命令:从 MinerU 输出目录复制 `cp -r <zotero_md>/<paper> wiki/raw/<citekey>/`

**与 v4 / mimo 的差异**:

| 项 | v4 | mimo | **plan_final** |
|---|---|---|---|
| 节点数 | 8 类 | 6+2 | **5 核心 + 2 辅助** |
| warrant | 独立 | 降级 | **降级为 claim.reasoning** |
| mechanisms | 独立 | 可选 | **吸收进 claim/evidence 正文** |
| variables | 独立 | 可选 | **吸收进 evidence 正文** |
| topic | 核心 | 核心 | **辅助**(跨论文才创建) |
| synthesis | 静态 | 静态 | **动态 + 按需固化** |

### 2.2 为什么 Synthesis 是动态视图(源自 19 §2.3)

**GPT §二十七**:Synthesis 才是最终"科研价值最高"的节点,但应该是由 **Evidence × Claim 矩阵自动聚合产生** 的,而非手动维护的静态文件。

**实现**:
- 用户问"关于 X 的证据是什么" → pi 读取相关 claim + evidence,**动态生成** synthesis 回答
- 用户确认有价值 → **再固化**到 `syntheses/` 目录
- 永远不直接手动写 synthesis(那是"伪综合")

### 2.3 节点命名约定(§15.4.9 更新)

- 论文节点:`<BBT-citekey>.md`(如 `zhang_2021_fnirs.md`)
- claim:`<slug>.md`(**优先中文 slug 用真实空格**,如 `neurolib 启用可扩展的全脑建模.md`;**避免用 `-` 替代空格**)
- evidence:`<author>-<year>-<slug>.md`(中英混合 slug 如 `martin-2025 TVB-O 是统一语义知识库与软件工具.md`;**避免用 `-` 替代空格**)
- topic:`<topic-key>.md`(如 `fnirs-cognitive-control.md`)
- synthesis:`<question-key>.md`(如 `dlpfc-development.md`)

**规则**:
- slug 用**真实空格**或**kebab-case**(两种风格都允许)
- **中文文本中禁止 `-` 替代空格**(§15.4.7 / §15.4.8)
- 文件名 wikilink 引用:Obsidian 自动 URL-encode 中文文件名,直接 `[[中文文件名]]` 即可

---

### 2.4 节点数量设计原则(T-W4-032,无硬性数量限制)

**CLAIM 和 EVIDENCE 节点无硬性数量限制**。节点数由 LLM 语义判断决定,反映论文实际知识结构。

**为什么无硬性限制**:
- 论文类型差异大:实证论文 vs 方法论 vs 综述,合理的 claim/evidence 数差异巨大
- **质量优先 > 数量完整**:宁可少而精,不要多而杂(虚构或拆碎会污染知识图谱)
- stitch-knowledge 跨论文去重是核心,LLM 凭 atomic 原则(plan_final §1.2)自主决定

**推荐区间**(LLM 抽取参考,非硬约束):

| 节点 | 推荐区间 | 上限警告阈值 | 原因 |
|---|---|---|---|
| **CLAIM per paper** | 3-8 | > 20 | atomic 原则下,实证核心论文一般 3-8 条主张;超过 20 通常是过度拆解 |
| **EVIDENCE per paper** | 3-10 | > 30 | 每条 claim 通常对应 1-3 条 evidence;超过 30 需评估是否拆得过细 |
| **边 per evidence** | 1-5 | > 10 | 一个 evidence 通常支持/反对 1-5 个 claim;超过 10 可能边定义模糊 |
| **claim 跨论文复用度** | 2+ papers | 1 paper only | 单一来源 claim 应标 DRAFT 或合并到已有 claim |

**大量抽取的风险** (T-W4-032 警告):
- **stitch-knowledge 负担增加**:跨论文去重时 O(N²) 比较
- **知识图谱噪声**:过多节点掩盖核心命题
- **人工审阅成本**:00-pending/ → claims/ promotion 工作量

**LLM 抽取判断原则**:
1. **优先提取主要实证发现**,不要为"完整性"拆分结果
2. **同义 claim 合并**:同一发现的多个表述合并为一条
3. **不能 grep 到 raw 的不抽**(plan_final §5.3 Grounding Invariant)
4. **DRAFT 标记**:无独立来源的 claim 标 verify_status: no_evidence

**违反数量上限的处理**:
- LLM 不强制硬上限,但应在抽取日志中说明理由
- 人工审阅时可拆分、合并、删除节点

---

## 3. 数据模型(frontmatter + 正文 + JSON Schema)

### 3.1 Paperinfo 节点(scripts 维护,不手动改)

```yaml
---
type: paperinfo
schema_version: "plan_final_v1"

# 身份(scripts 写)
citekey: zhang_2021_fnirs
zotero-key: 3SQHGBWR
zotero-link: zotero://select/library/items/3SQHGBWR
zotero-lastmod: "2026-08-20T09:18:49Z"

# 标题
title: "Developmental changes in prefrontal cortex..."

# 作者
authors: ["Zhang W.", "Li X.", "Chen Y."]
first-author: Zhang
authors-short: "Zhang et al."

# 出版
year: 2021
publication: "NeuroImage"
DOI: 10.1016/j.neuroimage.2021.118xxx
language: en
item-type: journalArticle

# 摘要(Zotero 导入)
abstract: "..."

# 分类
zotero-collections: ["fNIRS / 认知控制"]
zotero-tags: ["/unread"]
---
```

### 3.2 Paper 节点(LLM 抽取,scripts 校验)

```yaml
---
type: paper
schema_version: "plan_final_v1"
citekey: zhang_2021_fnirs
paperinfo: "[[paperinfo/zhang_2021_fnirs]]"   # 必填,强制 link

# 研究分类(LLM 判断)
study_type: empirical        # empirical / review / meta_analysis / method / theoretical
paper_kind: empirical         # NEW: empirical | theory | both
                              # 决定 ingest 走哪条路径(EmpiricalWiki 模式)
modality: fNIRS              # fNIRS / EEG / fMRI / DTI / behavioral / mixed
population: children         # children / adults / elderly / clinical / mixed

# 抽取状态
extraction_mode: deep-read   # quick-scan / deep-read / audit
extraction_date: "2026-08-24"
extraction_model: "MiniMax-M3"
status: extracted            # 7 态(批次4): pending / scanning / extracted / pending_audit / reviewed / promoted / rejected

# 关联(wikilink 双向)
related_topics: ["[[fnirs-cognitive-control]]"]
related_claims: ["[[dlpfc-hbo-age]]"]
related_evidence: ["[[zhang-2021-dlpfc-hbo-age]]"]
cited_by: ["[[syntheses/dlpfc-development]]"]
---
```

### 3.3 Paper 节点正文(用户硬需求:全文嵌入 claim/evidence)

**用户硬需求**:"paper 里面我就是要全部的 claim 和 evidence 嵌入" → **全文 Transclusion**,不用 `^summary` 块引用。

```markdown
# Zhang et al. (2021) · fNIRS DLPFC 认知控制发展

**元信息**
- 作者: Zhang W., Li X., Chen Y.
- 年份: 2021 · 期刊: NeuroImage · DOI:10.1016/j.neuroimage.2021.118xxx
- 类型: 实证 · 模态: fNIRS · 状态: deep-read
- paperinfo: [[paperinfo/zhang_2021_fnirs]]

**研究目的** _[1-3 句]_
探究儿童前额叶皮层发育与认知控制能力的关系。

**被试** _[N, 人群, 年龄]_
N=120 健康儿童, 6-12 岁,男女各半。

**实验设计** _[横断面/纵向/RCT]_
横断面研究, 单时间点测量。

**实验范式** _[任务态/静息态]_
事件相关设计, Go/NoGo 任务。

**测量工具** _[仪器参数]_
Hitachi ETG-4000 fNIRS, 52 通道, 采样率 10Hz。

**数据分析** _[统计方法]_
偏相关分析(控制性别)+ FDR 多重比较校正。

**结果** _[关键统计值 + 原文 quote]_
> "age was significantly associated with DLPFC HbO (β=0.34, p<0.001)" (§Results, p.5)
> "task accuracy increased with age (r=0.42, p<0.001)" (§Results, p.6)

**结论** _[作者总结]_
儿童 DLPFC 功能活动随年龄增强,与认知控制能力发展一致。

**核心主张**(摘要表)

| # | claim_id | 一句话 | verification |
|---|---|---|---|
| 1 | dlpfc-hbo-age | 儿童 DLPFC HbO 与年龄正相关 | supported (3) |
| 2 | nback-accuracy-age | 儿童 n-back 准确率随年龄提升 | supported (2) |

**证据条目**(摘要表)

| # | evidence_id | fact_type | 关键数值 | 关联 claim |
|---|---|---|---|---|
| 1 | zhang-2021-dlpfc-hbo-age | empirical_result | β=0.34, p<0.001 | dlpfc-hbo-age |
| 2 | zhang-2021-dlpfc-accuracy | empirical_result | r=0.42, p<0.001 | nback-accuracy-age |

**关联主题**  [[fnirs-cognitive-control]] [[child-neurodevelopment]]
**关联主张**  [[dlpfc-hbo-age]] [[nback-accuracy-age]]
**引用本论文的页面** [[syntheses/dlpfc-development]]

---

## 本论文的 Evidence(全文)

> [!evidence]+ **zhang-2021-dlpfc-hbo-age · DLPFC HbO 与年龄**
> ![[zhang-2021-dlpfc-hbo-age]]

> [!evidence]+ **zhang-2021-dlpfc-accuracy · n-back 准确率**
> ![[zhang-2021-dlpfc-accuracy]]

---

## 本论文支持的 Claims(全文)

> [!claim]+ **dlpfc-hbo-age · 儿童 DLPFC HbO 与年龄正相关**
> ![[dlpfc-hbo-age]]

> [!claim]+ **nback-accuracy-age · 儿童 n-back 准确率随年龄提升**
> ![[nback-accuracy-age]]
```

**关键点**:
- **`![[dlpfc-hbo-age]]` 全文嵌入**(不是 `![[dlpfc-hbo-age#^summary]]`)
- **`> [!evidence]+`** 默认展开(callout 内的 `+` 表示默认展开,可改成 `-` 默认折叠)
- 用户需求:**paper 一处看全所有 claim/evidence**,不用跳转

### 3.4 Evidence 节点(独立,跨论文复用)

> **Obsidian 笔记属性友好**:frontmatter 必须是**单层键值对**,嵌套对象在 Obsidian 属性面板中会显示为 `{key:value, ...}` 原始 JSON 字符串,不可读。**所有嵌套对象必须扁平化**。scripts 写入时用嵌套结构做 JSON Schema 验证,序列化时拆为 `前缀_字段` 形式。

```yaml
---
type: evidence
schema_version: "plan_final_v1"
# **唯一标识** = 文件名 zhang-2021-dlpfc-hbo-age.md(不需 evidence_id 字段)

# 事实分类
fact_type: empirical_result                 # empirical_result / observation / methodology
source: "[[zhang_2021_fnirs]]"

# Observation + Interpretation(AI 第三次建议 §十一,扁平化)
observation: |
  "age was significantly associated with DLPFC HbO (β=0.34, p<0.001)"
interp_origin: author                       # author / reviewer / system
interp_text: |
  作者认为这一关系表明发育期 DLPFC 功能活动增强
  与认知控制改善同步,支持儿童认知控制发展的神经基础假设

# SciClaim 细粒度结构:已弃用(2026-08-25,落地率 0/368,batch1 从 schema 删除)

# Provenance(扁平化,原嵌套对象)
prov_paper: "[[zhang_2021_fnirs]]"
prov_section: "§3.2 Results"
prov_page: 5
prov_paragraph: 3
prov_source_text: "age was significantly associated with DLPFC HbO (β=0.34, p<0.001)"
# 注意(§15.4.11): evidence **不存** raw 指针字段(raw_path 已废除,2026-08-25)。
# 原文即证据:prov_source_text 直接复制原文;脚本需 grep raw 验真时,按 source/prov_paper
# 的 citekey 现场推导路径 raw/<citekey>/full.md,不存储冗余指针。

# Extraction(扁平化)
extract_model: minimax-m3
extract_timestamp: "2026-08-24T10:30:00Z"
extract_method: llm_semantic
extract_temperature: 0.1

# Verification(扁平化)
verify_status: verified                     # verified / unverified / flagged
verify_verifier: scripts:wiki_check_evidence.py

# 数值校验(扁平化,§15.4.11 增强,scripts 必查)
verify_n: 120                                  # 样本量
verify_test_method: regression_linear         # 检验方法: 见 paper_stats.md(test_method 候选清单 37 个)
verify_test_stat_type: t                     # 统计量类型: t / F / r / rho / chi2 / OR / RR / beta / z / u / W / H / Q / BF / d / g / R2 / eta2 / V / phi(共 20 候选)
verify_test_stat_value: 2.45                 # 统计量数值(论文报告的具体值;null 表示论文未给单点值)
verify_effect_size_type: beta                # 效应量类型: cohen_d / hedges_g / r / rho / r_squared / R_squared / adjusted_R_squared / eta_squared / partial_eta_squared / beta / OR / RR / phi / cramers_v / bayes_factor / na(共 16 候选)
verify_effect_size_value: 0.34              # 效应量数值(论文报告;null 表示未给)
verify_ci_95: "[0.18, 0.50]"                # 95% 置信区间(可选,字符串形式)
verify_df: 118                                 # 自由度(可选)
verify_p_value: 0.001                        # p 值(原始)
verify_p_method: uncorrected                  # p 值校正方法: uncorrected / bonferroni / holm_bonferroni / fwe / maxT / fdr_bh / fdr_by / cluster_based / tfce / bayes_factor / na(共 11 候选)
verify_note: "方法论/软件论文,无假设检验,该项置 null"  # 备注(论文未报告的字段置 null + 原因)

# 关系(扁平化为多个数组,平行的 3 个数组保持对齐)
# 数组:每个元素对应一个边
supports_targets: ["[[dlpfc-hbo-age]]"]    # 边目标 wikilink
supports_confidences: ["high"]             # high / medium / low
supports_relations: ["direct"]             # direct / indirect / partial
contradicts_targets: []                    # 数组,空表示无
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: []
qualifies_confidences: []
qualifies_relations: []

# 强度 + 置信度(分离!)
strength: strong                          # strong / moderate / weak(科学证据强度)
extraction_confidence: 0.92               # LLM 抽取自信程度
```

**扁平化映射**(scripts 写入时):
- `interpretation.origin` → `interp_origin`
- `interpretation.text` → `interp_text`
- `provenance.paper` → `prov_paper`
- `provenance.extraction.model` → `extract_model`
- `provenance.verification.status` → `verify_status`
- `verifies.n` → `verify_n`
- `supports[].target/confidence/relation` → `supports_targets/confidences/relations`(3 个平行数组)

**scripts 验证**(JSON Schema 仍用嵌套,`scripts/schemas/evidence.schema.json`):
- 接收 LLM 输出的 JSON(嵌套)
- 验证通过后,扁平化写 frontmatter(Obsidian 友好)
- wikilink target 仍可点击(数组中 wikilink)
- 数组对齐(supports_targets[i] 对应 supports_confidences[i] 对应 supports_relations[i])

**字段 enum 来源(T-W4-026 整合)**:`verify_test_method` / `verify_test_stat_type` / `verify_effect_size_type` / `verify_p_method` 四个 enum 候选清单从 `.skill/references/templates/paper_stats.md` 提取,由 `.skill/scripts/schemas/evidence.schema.json` 的 `$defs` 集中管理(37/20/16/11 个候选)。scripts 严格校验,候选外值 reject,LLM 必须从 paper_stats 清单精确匹配。

**body 渲染(T-W4-027 升级)**:`## 数值校验` 表格由 `.skill/scripts/wiki_render_evidence_body.py` 从 frontmatter + schema $defs **自动生成**,不允许手工编辑。设计原则:body **只渲染、不维护** —— schema 是 enum 的唯一真相源。脚本用法见 `.skill/skills/wiki-build-evidence/SKILL.md` "body 渲染脚本"段。

**设计原则**:(1) **β 方案 扁平化** — Obsidian 不支持嵌套,所有 verify_*/interp_*/prov_*/extract_* 必须为顶层单层键值对;(2) **null 容忍** — 论文未报告的字段标 null(明确缺失,不漏填);(3) **重量 lint** — 方法论/软件论文整组统计字段 null,只填 verify_n + verify_test_method + verify_note。

# zhang-2021-dlpfc-hbo-age · DLPFC HbO 与年龄(Zhang 2021)

## 观察(Observation)
> "age was significantly associated with DLPFC HbO (β=0.34, p<0.001)" (§Results, p.5)

## 解释(Interpretation)
作者将年龄相关 DLPFC HbO 增加解释为认知控制发展的神经相关指标。
- 解释来源: author_interpretation

## 出处(Provenance)
- 论文: [[zhang_2021_fnirs]]
- 章节: §3.2 Results
- 页码: 5
- 原文: "age was significantly associated with DLPFC HbO (β=0.34, p<0.001)"

## 支持的 Claim

| Claim wikilink | 关系 | 置信度 |
|----------------|------|--------|
| [[dlpfc-hbo-age]] | direct | high |
| [[zhang_2021_fnirs]] | indirect | medium |

(若有 contradicts / qualifies 也生成对应表格段)

## 数值校验

| 项目 | 值 | 说明 |
|------|------|------|
| 样本量 (n) | `120` | 总样本数 |
| 检验方法 | `regression_linear` | t_test / anova / regression / ...(共 37 候选) |
| 统计量类型 | `beta` | t / F / r / ...(共 20 候选) |
| 统计量数值 | `0.34` | 论文报告的具体值(null=未报告) |
| 效应量类型 | `beta` | cohen_d / hedges_g / ...(共 16 候选) |
| 效应量数值 | _(论文未报告)_ | 论文报告的效应量值(null=未报告) |
| 95% 置信区间 | `"[0.18, 0.50]"` | 字符串形式(null=未报告) |
| 自由度 (df) | `118` | 统计量对应的自由度(null=未报告) |
| p 值 | `0.001` | 原始 p 值(null=未报告) |
| p 值校正 | `uncorrected` | 候选清单(共 11 候选) |
| 备注 | ... | 上下文或限制说明 |

**维度分离** (plan_final §1.2 #11):
- `strength`(科学证据强度)是 evidence 节点全局属性,在 frontmatter `strength` 字段体现一次
- 每条边(支持/反对/限定)只显示 关系(direct/indirect/partial) + 置信度(high/medium/low)
- 不在每条边后重复 `strength`(避免冗余)

## 使用此证据的页面
- [[zhang_2021_fnirs]]
```

### 3.5 Claim 节点(原子化,吸收 warrant)

> **Obsidian 笔记属性友好**:与 evidence 一样,frontmatter 必须是**单层键值对**,嵌套对象拆为 `前缀_字段` 形式。

```yaml
---
type: claim
schema_version: "plan_final_v1"
statement: "儿童(6-12 岁)DLPFC 的 HbO 浓度与年龄正相关"

# 主张分类(单层)
claim_type: empirical_generalization      # 见下方枚举
origin: extracted                         # extracted / author / normalized / synthesized
atomic: true                              # 必填(GPT §22)

# 作用域(扁平化,GPT §23)
scope_population: "儿童 6-12 岁"
scope_modality: "fNIRS / HbO"
scope_task: "n-back"
scope_region: "DLPFC"
scope_study_design: "cross-sectional"

# 验证状态(扁平化,GPT §七, 简化 GRADE 不在 claim 上)
verify_status: supported                  # supported / partial / contradicted / no_evidence
verify_confidence: 0.82                  # 0-1
verify_strength: moderate                 # strong / moderate / weak / inconclusive
verify_consensus: emerging                # established / emerging / fringe
verify_evidence_count: 3
verify_supporting_count: 3
verify_contradicting_count: 0
verify_evidence_quality: moderate         # NEW: 类似 GRADE 的证据质量
verify_last_updated: "2026-08-24T10:30:00Z"

# 推理桥(替代独立 warrant 节点,GPT §四)
reasoning: |
  作者基于 3 项横断研究 + 1 项纵向研究的 HbO 浓度变化,
  推断发育期 DLPFC 功能活动增强与认知控制改善同步。
  依据:神经血管耦合增强 + 认知任务表现同步提升。
reasoning_type: theoretical_assumption

# 关联(扁平化为多个数组,3 个平行数组保持对齐)
sources_targets: ["[[papers/zhang_2021_fnirs]]", "[[papers/wang_2022_fnirs]]"]
sources_confidences: ["high", "high"]
sources_relations: ["direct", "direct"]
supports_targets: ["[[dlpfc-development]]"]
supports_confidences: ["high"]
supports_relations: ["direct"]
contradicts_targets: []                  # 数组,空表示无
contradicts_confidences: []
contradicts_relations: []
evidence_targets: ["[[zhang-2021-dlpfc-hbo-age]]", "[[zhang-2021-dlpfc-accuracy]]", "[[wang-2022-dlpfc-development]]"]
evidence_confidences: ["high", "high", "high"]
evidence_relations: ["direct", "direct", "direct"]
```

**扁平化映射**(scripts 写入时):
- `scope.population` → `scope_population`
- `scope.modality` → `scope_modality`
- `verification.status` → `verify_status`
- `sources[]` → `sources_targets` / `sources_confidences` / `sources_relations`(3 个平行数组)
- `supports[]` / `contradicts[]` / `evidence[]` 同理

**scripts 验证**(JSON Schema 仍用嵌套,`scripts/schemas/claim.schema.json`):
- 接收 LLM 输出的 JSON(嵌套)
- 验证通过后,扁平化写 frontmatter
- 数组对齐(targets[i] 对应 confidences[i] 对应 relations[i])

**wikilink 前缀约定**(§15.4.6):
- `sources_targets`: `[[papers/<citekey>]]`(显式 papers/ 前缀,避免 paperinfo/ 歧义)
- `evidence_targets`: `[[evidence/<author>-<year>-<slug>]]`(显式 evidence/ 前缀)
- `supports_targets`: `[[claims/<slug>]]`(或 `[[<slug>]]` 全局搜)

**文本内容规则**(§15.4.7):
- claim `statement` 允许中文(本 wiki 是中文研究笔记)
- evidence `observation` / `interp_text` 也允许中文
- evidence 头部用 paper citation(如 `"source": "[[papers/<citekey>]]"`)
- **中文文本中不要用 `-` 替代空格**(`-` 只用于专有术语如 `Prader-Willi` / `insula-temporal` / `TVB-O` / `whole-brain`)
  - ❌ `基于神经 行为发育关联`(用 `-` 替代空格)
  - ✅ `基于神经 行为发育关联`(英文术语 `neural-behavioral` 翻译为 `神经 行为` 用真实空格)
- 文件名 slug 优先中文 + **真实空格**(plan_final §2.3,T-W4-030)
- 字段名仍用 snake_case(`_` 分隔)
- 例外:专业术语保留 `-`(Prader-Willi / insula-temporal / striatum-pallidum / TVB-O / whole-brain 等)

# dlpfc-hbo-age · 儿童 DLPFC HbO 与年龄正相关

## 主张陈述
儿童(6-12 岁)DLPFC 的 HbO 浓度与年龄正相关,β=0.34, p<0.001。

## 推理桥
作者从 HbO 浓度的年龄梯度推断 DLPFC 功能成熟,
依据:发育期神经血管耦合增强 + 认知任务表现同步提升。

## 支持证据
| 证据 | 来源 | 强度 | 关系 |
|------|------|------|------|
| [[zhang-2021-dlpfc-hbo-age]] | Zhang 2021 | strong | direct |
| [[zhang-2021-dlpfc-accuracy]] | Wang 2022 | moderate | direct |
| [[wang-2022-dlpfc-development]] | Liu 2023 | moderate | indirect |

## 反对证据
_(无)_

## 限定条件
- 仅适用于 6-12 岁健康儿童
- 仅 fNIRS / HbO 模态
- 横断研究,无法推断因果

## 证据强度
moderate(3 项研究一致, n 总计 360)

## 引用此主张的页面
- [[syntheses/dlpfc-development]]
- [[topics/fnirs-cognitive-control]]
- [[zhang_2021_fnirs]]
```

**Claim 类型枚举**(沿用 19):

| 类型 | 含义 |
|---|---|
| `empirical_result` | 作者通过实验实际观察到的 |
| `empirical_generalization` | 从多个结果归纳的一般性结论 |
| `theoretical_interpretation` | 作者对结果的理论解释 |
| `methodological` | 关于方法的主张 |
| `meta_analytic` | 综合多个研究的结论 |

### 3.6 Topic 节点(MOC 模式,辅助)

```yaml
---
type: topic
schema_version: "plan_final_v1"
id: fnirs-cognitive-control
---

# fNIRS 认知控制研究

## 主题描述
使用 fNIRS 技术研究认知控制能力的神经基础。

## 核心主张
- [[dlpfc-hbo-age]] — DLPFC HbO 随年龄增强
- [[CLAIM-002_fNIRS_validity]] — fNIRS 适合测量发育中的大脑

## 关键证据
- [[zhang-2021-dlpfc-hbo-age]] — 6-12 岁 DLPFC 发展
- [[zhang-2021-dlpfc-accuracy_nback_accuracy]] — n-back 准确率年龄梯度

## 争议点
- 3 岁 vs 6 岁转折点存在争议

## 待解决问题
- [ ] 纵向研究证据不足
- [ ] 跨文化差异未探索

## 涉及论文
- [[zhang_2021_fnirs]]
- [[wang_2022_fnirs]]

## 关联主题
- [[cognitive-control]]
- [[prefrontal-cortex]]
```

### 3.7 Synthesis 节点(动态 + 按需固化)

```yaml
---
type: synthesis
schema_version: "plan_final_v1"
id: dlpfc-development
question: "儿童 DLPFC 活动是否随年龄增加？"

# 生成方式
generated_by: query-evidence             # query-evidence / manual / hybrid
generated_at: "2026-08-24"

# 强度评价(GRADE 在合成层,不在 claim 层)
strength:
  grade: moderate                        # high / moderate / low / very_low
  evidence_count: 5
  consistency: high                      # high / moderate / low
---

# 儿童 DLPFC 活动发展:证据综合(ABT 叙事)

## 研究问题(Question)
儿童 DLPFC 活动是否随年龄增加？

## 证据矩阵(Evidence Matrix)

| 证据 | Zhang 2021 | Li 2022 | Wang 2023 |
|------|:---:|:---:|:---:|
| DLPFC HbO ↑ | +++ | ++ | +++ |
| Accuracy ↑ | ++ | + | ++ |
| RT ↓ | + | 0 | + |

> 图例: +++ 强支持, ++ 中等, + 弱, 0 无信息, -- 弱反驳

## 共识(And) — ABT 叙事起点
- 5 篇横断研究一致支持 DLPFC HbO 随年龄增加
- 神经发育理论预期一致

## 缺口(But) — ABT 转折
- 全部为横断面设计,无法确立因果
- 样本量偏小(N<200)
- 跨文化差异未探索

## 结论(Therefore) — ABT 收束
- **总体证据强度**:Moderate support
- **适用边界**:6-12 岁健康儿童、fNIRS/HbO 模态
- **下一步**:纵向研究 + 大样本跨文化验证

## 关键论文
- [[zhang_2021_fnirs]] [[li_2022_fnirs_validity]] [[wang_2023_fNIRS_meta]]

## 关键主张
- [[dlpfc-hbo-age]] — supported (3)
- [[nback-accuracy-age]] — supported (2)

## 关键证据
- [[zhang-2021-dlpfc-hbo-age]] [[zhang-2021-dlpfc-accuracy]] [[wang-2022-dlpfc-development]]

## 更新历史
- 2026-08-24: 初始综合(5 篇论文)
```

### 3.8 Evidence Contract(JSON Schema,scripts 校验)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Evidence",
  "type": "object",
  "required": ["type", "evidence_id", "fact_type", "observation", "interpretation", "provenance", "verifies", "supports"],
  "properties": {
    "type": { "const": "evidence" },
    "evidence_id": { "pattern": "^EVID-[0-9]{3,}$" },
    "claim_id": { "pattern": "^CLAIM-[0-9]{3,}$" },
    "fact_type": { "enum": ["empirical_result", "observation", "methodology"] },
    "observation": { "type": "string", "minLength": 20 },
    "interpretation": {
      "type": "object",
      "required": ["origin", "text"],
      "properties": {
        "origin": { "enum": ["author", "reviewer", "system"] }
      }
    },
    "provenance": {
      "type": "object",
      "required": ["paper", "section", "source_text"],
      "properties": {
        "paper": { "pattern": "^\\[\\[.+\\]\\]$" },
        "section": { "type": "string" },
        "source_text": { "type": "string", "minLength": 10 }
      }
    },
    "verifies": {
      "type": "object",
      "required": ["n", "statistic", "value"],
      "properties": {
        "n": { "type": "integer", "minimum": 1 },
        "statistic": { "enum": ["r", "beta", "F", "t", "chi2", "OR", "p"] },
        "value": { "type": "number" },
        "p_value": { "type": "number", "maximum": 1 }
      }
    },
    "supports": {
      "type": "array",
      "description": "边关系(新增置信度 — EmpiricalWiki 模式)",
      "items": {
        "type": "object",
        "required": ["target", "confidence"],
        "properties": {
          "target": { "pattern": "^\\[\\[.+\\]\\]$" },
          "confidence": { "enum": ["high", "medium", "low"] },
          "relation": { "enum": ["direct", "indirect", "partial"] }
        }
      }
    }
  }
}
```

**scripts 校验流程**:LLM 输出 JSON → jsonschema 校验 → 失败 reject 重写 → 通过渲染为 md → 写入 `00-pending/`。

---

## 4. Pi 集成(本文核心)

### 4.1 AGENTS.md(< 80 行,只放宪法)

**位置**: `wiki/AGENTS.md`
**加载时机**: pi 启动时无条件加载
**职责**: 路由表 + 不可违反铁律 + 文件入口

```markdown
# Wiki AGENTS · 项目契约

## 0. 角色
你是这个学术证据 wiki 的长期维护者。输入:论文路径 / 用户提问;
输出:markdown 节点 + wikilink;**不**修改 Zotero / MinerU 原始层。

## 1. 不可违反的铁律(11 条,见 plan_final §1.2)

## 2. 路由表(意图 → skill)
| 用户说 | 调用 |
|---|---|
| "处理 [full.md]" / "/extract xxx" | wiki-extract-paper |
| "这条跨论文追踪" / "/claim" | wiki-build-claim |
| "这是一个事实" / "/evidence" | wiki-build-evidence |
| "建一个主题" / "/topic" | wiki-build-topic |
| "X 的证据" / "/query" | wiki-query-evidence |
| "检查 wiki" / "/lint" | wiki-lint-wiki |
| "zotero 同步" / "/sync" | wiki-zotero-sync |
| "审阅这篇" / "/audit" | wiki-extract-paper (T4 audit 模式) |

## 3. 文件入口
- AGENTS.md / index.md / log/(ops.md + README.md + batch-*.md)
- .skill/skills/ · .skill/scripts/ · .pi/prompts/ · .pi/extensions/

## 4. 失败时如何回滚
- git checkout <file> / jj undo
- 不破坏其他 session 工作
```

### 4.2 SKILL.md 入口 + 6 微 Skill

```
.skill/
├── SKILL.md                              # < 80 行,只做路由
└── skills/                               # 微 Skill(按需 read)
    ├── wiki-extract-paper/               # T0-T4 全流程
    ├── wiki-build-claim/                 # claim 节点创建
    ├── wiki-build-evidence/              # evidence 节点创建
    ├── wiki-build-topic/                 # topic 节点创建
    ├── wiki-query-evidence/              # synthesis 动态生成
    ├── wiki-stitch-knowledge/            # 跨论文去重 + 关联(19 §4.5 新增)
    ├── wiki-lint-wiki/                   # L0-L3 分层 lint
    └── wiki-zotero-sync/                 # Zotero 增量同步
```

**入口 SKILL.md 模板**:

```markdown
---
name: wiki
description: 维护个人科研证据 wiki。处理新论文、抽取 claim/evidence、回答研究问题、运行健康检查。Use when user says "处理 [full.md]"、"建一个主题"、"查证据"、"检查 wiki"。
---

# Wiki Skill · 入口(< 80 行)

## 你的工具集
- AGENTS.md(已读):宪法 + 路由表
- 7 个微 Skill(按需 read):见下表
- Extension wiki-tools(5 个):wikilink 校验、Zotero 同步等

## 路由
| 任务 | read 哪个 Skill |
|---|---|
| 处理新论文 | skills/wiki-extract-paper/SKILL.md |
| 创建 claim | skills/wiki-build-claim/SKILL.md |
| 创建 evidence | skills/wiki-build-evidence/SKILL.md |
| 跨论文去重 + 关联 | skills/wiki-stitch-knowledge/SKILL.md |
| 回答研究问题 | skills/wiki-query-evidence/SKILL.md |
| 检查 wiki | skills/wiki-lint-wiki/SKILL.md |

## 边界
- 不修改 Zotero / MinerU 原始层
- 不直接覆盖已抽取节点(必须显式说"覆盖")
- scripts 只做机械校验,不抽取
- LLM 写 00-pending/,人审阅后才进正式目录
```

### 4.3 Prompt Templates(10 个命令式入口)

**位置**: `.pi/prompts/`

| 命令 | 模板文件 | 触发场景 |
|---|---|---|
| `/extract <full.md>` | `extract.md` | 处理一篇论文 |
| `/claim <text>` | `claim.md` | 固化一条 claim |
| `/evidence <text>` | `evidence.md` | 固化一条 evidence |
| `/topic <text>` | `topic.md` | 创建主题 |
| `/query <question>` | `query.md` | 回答研究问题(综合) |
| `/lint` | `lint.md` | 健康检查 |
| `/audit <node>` | `audit.md` | 审阅节点(T4) |
| `/sync` | `sync.md` | Zotero 增量同步 |
| `/migrate` | `migrate.md` | 数据迁移 |
| `/batch` | `batch.md` | 批量处理队列 |

### 4.4 Extension(5 个自定义工具)

**位置**: `.pi/extensions/wiki-tools.ts`

| 工具 | 作用 | 何时调用 |
|---|---|---|
| `wiki_check_wikilinks` | 校验双向链接、孤立节点 | /lint、写入后 |
| `wiki_match_paperinfo` | 匹配 full.md → paperinfo citekey | extract-paper |
| `wiki_zotero_sync` | 增量同步 Zotero | /sync |
| `wiki_emit_progress` | 输出进度卡片(sub-agent) | 批量模式 |
| `wiki_snapshot` | git tag + 写 log | 关键节点操作后 |

### 4.5 显式路由表 + description 触发

**关键**(源自 21 §9):**LLM 不靠猜,description 是触发器**。

每个微 Skill 的 description 必须包含:
- **做什么**(动词)
- **何时用**(`Use when X`)

```yaml
# 反例
description: 处理论文。

# 正例
description: |
  抽取一篇论文的 full.md 到 paper/claim/evidence 节点。
  Use when user says "处理 [full.md]" or "/extract xxx"。
```

### 4.6 工具链架构(scripts / schemas / lint,原 .skill/ARCHITECTURE.md 并入,T-W5-004)

**修改 `.skill/` 下任何文件前,先读本节;改 scripts/schemas 后必须跑一遍 lint 验证。**

**scripts/ 结构与职责**:

| 类别 | 脚本 | 说明 |
|---|---|---|
| 单一真相源 | `schemas/_registry.py` | ENTITY_DIRS / EDGE_TYPE_SPECS / REQUIRED_FIELDS / check_edge,lint 与校验共享 |
| Schema | `schemas/{claim,evidence,topic}.schema.json` | LLM JSON 契约;verify_* 四 enum(37/20/16/11 候选)以 §3.4 为准 |
| 校验 | `wiki_lint.py` · `wiki_check_evidence.py` | lint 分层见下;Grounding 验真在 check_evidence |
| 渲染 | `wiki_render_evidence_body.py` | evidence body 只渲染不维护,schema 是 enum 唯一真相源 |
| 同步 | `wiki_zotero.py` · `wiki_zotero_csv.py` · `wiki_zotero_md.py` | CLI 入口 `wiki zotero <sub>`;**不存在 wiki_zotero_sync.py**(已知断链,见技术债表) |
| 批量 | 批量抽取按 §5.0 S0-S7 逐篇循环(LLM cli:pi/codex,`--engine` 切换),不用 legacy bulk_extract.py | — |
| 一次性迁移 | `rename_*.py` · `finalize_*.py` 等 | 已完成使命,保留存档,不新用 |

**schemas 注册表规范**:① `EDGE_TYPE_SPECS` 必须与 §7.1 一致(不一致 = bug);② `REQUIRED_FIELDS` 必须覆盖 §3 各节点必填字段,新增字段先改本契约再改代码;③ evidence 无 raw_path 字段(§15.4.11),需 raw 路径时按 source citekey 推导。

**lint 实现分层与逻辑分层映射**(§7 的 4 层是逻辑分层):

| 实现层 | 检查 | 工具 |
|---|---|---|
| L0 | 命名规范(semantic-slug / citekey / 中文+空格,禁数学符号与抽取标记) | wiki_lint.py |
| L0.5 | type ↔ 目录一致 | wiki_lint.py |
| L1 | papers raw 存在性 + DOI grep | wiki_lint.py |
| L1.5 | **claims/evidence frontmatter jsonschema 校验**(必填+enum,批次1 新增) | wiki_lint.py + schemas |
| L2 | wikilink 双向 / claims-evidence 关联 / 边类型合法(注册表派生) | wiki_lint.py |
| L3 | 数值区间 + Grounding grep(调 wiki_check_evidence) | wiki_lint.py + check_evidence |
| L4.6 | csv-source-path 等专项 | wiki_lint.py |

映射:实现 L0+L0.5 → 逻辑 L0;实现 L1 → 逻辑 L1;实现 L2 → 逻辑 L2;实现 L3+L4.6 → 逻辑 L3。

**已知技术债**(修改相关组件前先看):

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| 1 | ~~.pi/prompts/sync.md 与 wiki-tools.ts 调用不存在的 wiki_zotero_sync.py~~ | /sync 命令不可用 | ✅ 批次1 修复(改指 wiki zotero pull/sync,含 wiki_zotero_pull.py 幽灵引用) |
| 2 | ~~lint 未调用 wiki_check_evidence 做 Grounding;claims/evidence 未纳入扫描~~ | 数值验真闭环断 | ✅ 批次1 修复(L1.5 schema 校验 + L3 grounding 368 quote 全查;Grounding 升级 NFKC+词覆盖 fuzzy 三态) |
| 3 | tests/ 重建 | 重构安全网 | ✅ 批次1 最小集 16 用例(.skill/scripts/tests/) |
| 4 | ~~_registry.py EDGE_TYPE_SPECS 与 §7.1 有偏差~~ | 边校验口径不一 | ✅ 批次1 对齐(删 supersedes、加 cites+端点校验;claim.schema 扁平化) |
| 5 | 部分 raw 缺失(zotero_mn/md 找不到源) | 部分论文无权威源 | 待立项 |

**经验教训库**:`.skill/LESSONS.md`(过程问题沉淀,优化 skill 前必读;每次返工/事故追加一条)。

**一次性维护操作(勿日常使用)**:`rename_claims.py` · `rename_to_citekey.py` · `finalize_quotes.py` · `wiki_archive.py`。新需求优先写成 lint 规则或微 Skill,不新增一次性脚本。

---

## 5. 抽取工作流(单篇标准流程 S0-S7 + 3 模式 × 5 阶段 + LLM→JSON→MD)

### 5.0 单篇论文标准流程(S0-S7,一切抽取按此顺序执行)

> **输入**:外部 CSV(含 md 路径清单)、直接 md 路径、或直接 PDF(**S0a 可选步**:`wiki_pdf_to_md.py` 机械转换 → citekey 已知直转 `raw/<ck>/`,未知暂存 `raw/_incoming/` 待 S1 定名后由 S2 移入)。无论来源,**交给 wiki 的最终形态是 md**。
> **批量**:多篇 = S3-S7 逐篇循环,每篇一个独立 cli(独立 context,可并行);全部完成后跑 stitch-knowledge + 全量 lint。

| 步 | 动作 | 执行者 | 关键约束 |
|---|---|---|---|
| **S0** 输入规范化 | CSV 逐行解析出 md 路径,或直接接收 md 路径;**输入是 PDF 时先走 S0a**(`wiki_pdf_to_md.py`,--citekey 已知直转 raw/<ck>/,未知暂存 raw/_incoming/,>200 页提示本地 minerU)→ **幂等决策表**(批次4,Zotero-Analytical):已有完整产物→什么都不跑(ALREADY_COMPLETE);仅缺 claims→只跑 S3;仅缺渲染→只跑渲染器;**无任何知识变化也是合法成功**(NO_KNOWLEDGE_CHANGE,不重抽) | scripts | CSV 解析只做路径提取,不碰语义;**No Phantom Note:为未解析链接创建空文件是禁止的**(§15.2 病根) |
| **S1** paperinfo 先行 | 从 CSV 行或 md 标题/DOI 匹配已有 paperinfo;无则从 Zotero 创建(**用 paper key,勿用 attachment key**,§15.4.4)。**canonical citekey = paperinfo 节点名,后续一切命名以它为准**;**必须验证 raw full.md 标题与 paperinfo.title 匹配**(L-004:citekey 错位教训) | LLM + scripts | paperinfo 必须先于 raw 复制存在 |
| **S2** raw 复制 | 复制 md 所在文件夹 → `raw/<citekey>/`(full.md + images/),**一次命名到位,永不改名** | scripts | 铁律 #1;S1 先行保证目录名即 canonical |
| **S3** 单篇抽取 | **一篇论文 = 一次引擎调用**(2026-09-04 三引擎解耦:pi / codex 子进程,或 zcode 会话内;独立 context,互不污染。调用规范 = `.skill/INVOKE.md`,INVOKE-PREFIX 三引擎共用)(T0-T2 按 modality 模板)。**LLM 只写 frontmatter**(claim/evidence 全部字段 + paper 的叙事段/研究目的/被试/…/结论);body 全部由 `wiki_render_nodes.py` 生成 — S3 不写任何 body 段,S3 末尾跑一次渲染脚本写文件。claim **链接已有优先**(查 claims/ 索引),新建从严;**topic 只链接已有**,确需新建必须先查 topics/ 近重复;evidence 原文即证据(prov_source_text,无 raw_path,§15.4.11) | LLM 引擎(pi/codex/zcode) | LLM→JSON→jsonschema→frontmatter;渲染脚本出 body |
| **S4** 机械检查 | ① `_registry.py` frontmatter 校验(enum/必填) ② `wiki_lint.py` L0/L0.5/L1/L1.5/L3 ③ Grounding:数值/quote 可 grep 到 `raw/<citekey>/full.md`(路径按 source citekey 推导) ④ wikilink 目标全部存在 | scripts | **任何一项不过 → 退回 S3 修,不得进 S5** |
| **S5** 互联 | ① 跑 `wiki_link_paper.py` 自动补 paper.related_evidence/related_claims(从 evidence↔claim 正向边反推,批次2);② 跑 `wiki_render_nodes.py paper` 重生成嵌入段 + Backlinks Cache;③ claim↔evidence 边表格(由渲染器出,无需手写);④ 0 broken wikilink | scripts(自动)+ LLM(仅修) | 完成标准 = 0 broken wikilink,嵌入段非空 |
| **S6** 人审 | 用户审阅 `00-pending/<citekey>/`(审阅清单见 wiki-extract-paper SKILL) | 人 | 铁律 #10 |
| **S7** Promote | **promote 闸门(2026-08-25)**:① `wiki_lint.py --layer L1.5` 对该 citekey 0 error;② evidence/claim body 含 AUTO-RENDERED banner(即渲染器已跑);③ 调用方式符合 `.skill/INVOKE.md`。过闸才 00-pending → papers/ + claims/ + evidence/;更新 index.md + log/ops.md(promote 记录由 wiki_promote.py 自动追加)+ 对应批次文件状态;git commit(+tag);**批后**跑 wiki-stitch-knowledge | scripts | 不过闸禁止 promote |

**与直观顺序的两处关键差异**(为什么):
1. **paperinfo(S1)在 raw 复制(S2)之前**:raw 目录名 = canonical citekey,先定名再复制,目录一次到位。反序必然产生事后改目录名(raw 路径漂移事故的根因)。
2. **topic 不在单篇流程新建**(只链接):topic 是跨论文辅助节点(§2.1),单篇新建必然碎片化(digital-brain / brain-digital-twin / digital-twin-brain 三个近重复并存即教训)。新 topic 走 `/topic` 命令或批后 stitch。

### 5.1 3 模式 × 5 阶段 二维矩阵

**横向 = 5 阶段(T0-T4)**,**纵向 = 3 模式(quick-scan / deep-read / audit)**:

| 模式 \ 阶段 | T0 · Ingest | T1 · Scan | T2 · Extract | T3 · Evidence | T4 · Audit |
|---|---|---|---|---|---|
| **quick-scan**(综述/方法论) | ✓ | ✓ | × | × | × |
| **deep-read**(实证核心) | ✓ | ✓ | ✓ | ✓ | × |
| **audit**(用户质疑) | × | × | × | × | ✓ |

**5 阶段定义**(AI 第三次建议 §十六):

| 阶段 | 触发 | LLM 任务 | 耗时 | 输出 |
|---|---|---|---|---|
| **T0 · Ingest** | full.md 首次进入 | 读全文 + 识别论文类型 | 30s | paperinfo/<citekey>.md |
| **T1 · Scan** | T0 完成 | 抽 5 字段(目的/被试/方法/结果/结论)1-2 句摘要 | 30s | 00-pending/<citekey>-scan.md |
| **T2 · Extract** | T1 完成 | 抽 14 字段完整 + claim 列表 + evidence 列表 | 5-8min | 00-pending/<citekey>.md + semantic-slug + author-year-slug |
| **T3 · Evidence** | T2 完成 | evidence 提升到正式目录 + 建立 evidence × claim matrix | 3min | evidence/author-year-slug + 反向链接到 claims |
| **T4 · Audit** | 用户质疑 / 30 天复检 | 校验 quote / 数值 / wikilink 双向 | 2min | 修改原节点 + 写 log |

**3 模式判断**(源自 19 §5.2):
1. 检查 `study_type`:`empirical` → deep-read,`review/theoretical` → quick-scan
2. 检查是否已有相关 claim:有 → 可能只需 quick-scan + stitch
3. 用户明确指定 → 尊重用户

### 5.2 LLM → JSON → MD 三级流水线(源自 21 §5.2)

```
[Stage 1] LLM 输出 JSON
   ↓
[Stage 2] scripts 校验(JSON Schema)
   ├─ 字段类型 ✓ / ✗
   ├─ 必填字段 ✓ / ✗
   ├─ wikilink 目标存在 ✓ / ✗(只检查)
   ├─ provenance 完整 ✓ / ✗
   └─ 数值在合理区间 ✓ / ✗
   ↓
[Stage 3] LLM 渲染 Markdown
   ↓
[Stage 4] write 到 00-pending/
```

**为什么是 LLM→JSON→MD,而不是 LLM→MD 一锅端?**
- JSON 是契约:scripts 可以机械校验
- MD 是表现:Obsidian 渲染 + wikilink 友好
- LLM 写 JSON 时聚焦"结构",写 MD 时聚焦"叙事",**质量分离,质量更高**

### 5.3 Grounding Invariant(源自 19 §5.4)

```
∀ quantitative_fact f ∈ paper.md:
    ∃ quote q ∈ raw full.md:
        numeric_value(f) ∈ numeric_values(q)
```

**scripts 实现**:解析 paper.md 所有 `verifies.value` / `verifies.p_value`,对每个数字,在 full.md 中 grep 找到位置。**找不到** → reject,LLM 重写。

> 这条 invariant 把"LLM 是否准确引用原文"从语义判断降级为字符串匹配,**极大降低幻觉**。

### 5.4 Stitch Knowledge(源自 19 §4.5)— 跨论文去重 + 关联

**新增微 Skill `wiki-stitch-knowledge`** 解决 v4 痛点 #2(跨论文去重)。

**任务**:
1. 扫描 `claims/` 下所有 claim,检测内容相似的(LLM 语义判断,不是字符串匹配)
2. 检测到重复 → 合并到已有 claim,新 evidence 反向链接
3. 扫描 evidence → claim 关系是否完备,缺则补
4. **验证边的语义一致性**(新增):
   - 边类型必须在 `EDGE_TYPE_SPECS` 注册表中
   - 置信度必须合法(`high`/`medium`/`low`)
   - 目标必须有 evidence 支持
   - 不允许自环(`from ≠ to`)
5. 更新 `index.md` + 写 `log/ops.md`

**频率**:每次 T3 完成后,或 `/lint` 时调用。

### 5.5 scripts 只做机械校验(不抽取)

**scripts 白名单**(合并 19 + 21):

| 职责 | 例子 |
|---|---|
| 校验 YAML 语法 | `yaml.safe_load()` |
| 校验 frontmatter schema | jsonschema 库 |
| 校验 wikilink 目标存在 | `os.path.exists()` |
| 校验 semantic-slug / author-year-slug 唯一 | `os.listdir` 去重 |
| 校验数值区间 | `if 0 < p_value <= 1` |
| **Grounding grep** | **在 `wiki/raw/<citekey>/full.md` 找数字**(权威源在 wiki 内部) |
| 校验 raw 完整性 | `raw/<citekey>/full.md` 存在 + 可读 |
| 同步 Zotero | sqlite |
| 写 log/ops.md | append |
| git tag / jj snapshot | checkpoint |

**反例**(禁区):
- ❌ `re.findall(r'\d+\.\d+', text)` — 正则抽取
- ❌ `if "Methods" in sections:` — 关键词分类
- ❌ 任何 `text.split('## ')[1]` — 章节识别
- ❌ LLM 输出"修正" — 只 reject 让 LLM 重写

---

## 6. Obsidian 渲染策略

### 6.1 Paper View 二级(用户硬需求:全文嵌入)

| 视图 | 内容 | 折叠机制 | 何时用 |
|---|---|---|---|
| **L1 · Overview** | 元信息 + 14 字段摘要 + claim/evidence 表格 | 默认全文 | 第一次打开论文 |
| **L2 · Full** | L1 + 全文嵌入所有 claim + evidence | callout 折叠/展开 | 审阅 / 引用 / 复检 |

**用户硬需求**:`paper.md` 一处看全所有 claim/evidence。L2 = L1 + `![[CLAIM-xxx]]` + `![[EVID-xxx]]` **全文**(不是块引用)。

### 6.2 Transclusion 全文嵌入(callout 折叠)

```markdown
## 本论文的 Evidence(全文)

> [!evidence]+ **zhang-2021-dlpfc-hbo-age · DLPFC HbO 与年龄**
> ![[zhang-2021-dlpfc-hbo-age]]

> [!evidence]+ **zhang-2021-dlpfc-accuracy · n-back 准确率**
> ![[zhang-2021-dlpfc-accuracy]]
```

**callout 行为**:
- `[!evidence]+` — 默认**展开**(适合审阅)
- `[!evidence]-` — 默认**折叠**(适合概览)
- 在 paper frontmatter 加 `view_mode: full | summary` 控制全局

### 6.3 Graph View 配置(源自 19 §6.3)

保存到 `.obsidian/graph.json`,4 个预设(新增 Evidence-Chain):

| Filter Group | 显示关系 |
|---|---|
| **Paper-Claim** | paper → claim |
| **Evidence-Claim**(核心知识图谱) | evidence → claim |
| **Evidence-Chain**(新增) | evidence → claim → synthesis 完整链路 |
| **Topic View** | topic → paper → claim |

---

## 7. 质量保障(L0-L3 分层 Lint + 集中 Schema 注册表)

| 层 | 检查内容 | 工具 | 频率 |
|---|---|---|---|
| **L0** | 文件存在性、frontmatter YAML 解析 | `wiki_lint.py` | 每次写入 |
| **L1** | 必填字段完整性、枚举值合法性、jsonschema | `_registry.py validate` + `wiki_check_evidence.py` | 每次写入 |
| **L2** | wikilink 双向存在、反向链接一致性 | `wiki_lint.py` | 每日 |
| **L3** | Grounding grep、数值合理性、claim/evidence slug 唯一性 | `wiki_lint.py --layer L3` | 每周 |

### 7.1 集中 Schema 注册表(新增,源自 EmpiricalWiki `_schemas.py`)

**新增**: `.skill/scripts/schemas/_registry.py` — 所有 schema 的单一真相源(和 scripts 一起,便于 Python import)。

```python
# .skill/scripts/schemas/_registry.py
"""单一真相源:所有节点 schema 定义。lint.py 和 validate.py 共享此文件。"""

SCHEMAS_DIR = Path(__file__).parent  # .skill/scripts/schemas/
ENTITY_DIRS = {
    "paperinfo": "paperinfo", "paper": "papers", "claim": "claims",
    "evidence": "evidence", "topic": "topics", "synthesis": "syntheses", "pending": "00-pending",
}

EDGE_TYPE_SPECS = {
    "supports": {"from": "evidence", "to": "claim", "direction": "directed", "confidence": "required"},
    "contradicts": {"from": "evidence", "to": "claim", "direction": "directed", "confidence": "required"},
    "qualifies": {"from": "evidence", "to": "claim", "direction": "directed", "confidence": "required"},
    "same_claim_as": {"from": "claim", "to": "claim", "direction": "symmetric", "confidence": "required"},
    "extends": {"from": "claim", "to": "claim", "direction": "directed", "confidence": "optional"},
    "refines": {"from": "claim", "to": "claim", "direction": "directed", "confidence": "optional"},
    "cites": {"from": "paper", "to": "paper", "direction": "directed", "confidence": "none"},
}

REQUIRED_FIELDS = {
    "paperinfo": ["type", "citekey", "title", "authors", "year"],
    "paper": ["type", "citekey", "paperinfo", "study_type", "extraction_mode"],
    "claim": ["type", "claim_id", "statement", "claim_type", "atomic", "verification"],
    "evidence": ["type", "evidence_id", "fact_type", "observation", "provenance", "verifies", "supports"],
    "synthesis": ["type", "id", "question", "strength"],
}
```

**好处**: `lint.py` 和 `validate.py` 共享同一份 schema;新增边类型只需改一处;agent 可以 `read _registry.py` 获取所有约束。

### 7.2 LLM 抽取自检清单

1. 每个 CLAIM 都有 1+ EVIDENCE?
2. 数值是否在合理范围(p ≤ 1, n ≥ 1)?
3. 是否区分 empirical_result vs author_interpretation?
4. 关联主题都来自现有 topics/?
5. evidence.supports / contradicts 是否成对?
7. **边的 confidence 是否填写?** (新增:EmpiricalWiki 模式)

---

## 8. 批量处理 — Runner 直调 LLM CLI(pi / codex;2026-09-04 引擎解耦)

> **禁止用 sub-agent / workflowScript 编排批量抽取**(2026-08-27 用户指令:"不要用 subagent,
> 而是直接用 pi cli";2026-09-04 解除"固定 pi":**pi / codex / zcode 三引擎均合法**,但
> sub-agent 编排禁令不变)。并行 = 同一机器上 N 个 `wiki_run_extract.sh` 后台进程,瓜分
> **不重叠**的 citekey 列表。抽取 runner **不需要** worktree(铁律 #15,靠 #12+#13 保护)。

### 8.0 引擎矩阵(选型)

| 引擎 | 形态 | 模型 | 适用 | 备注 |
|---|---|---|---|---|
| **pi**(默认) | `pi -p` 子进程 | `--provider cce-minimax3 --model MiniMax-M3`(批量默认,AGENTS §0.5) | headless 批量 / 交互 | skill 自动发现(`~/.pi/agent/skills/`) |
| **codex** | `codex exec -C <root> --sandbox workspace-write` 子进程 | 默认 `~/.codex/config.toml`(gpt-5.6-terra),`--model` 透传 | headless 批量 / 交互 | 无 skill 自动发现,靠 INVOKE-PREFIX 指示 read SKILL.md;沙箱无网络但抽取全流程本地(不受影响);runner 超时放宽 3600s |
| **zcode** | 会话内(无 headless CLI) | 客户端选择 | 交互单篇 / 小批量 | 用户说「处理 <citekey>」,会话按微 skill 执行 S0-S7;必须自持锁 + 落盘即 commit(铁律 #12/#13) |

三引擎共用:INVOKE-PREFIX 前缀 · S0-S7 流程 · S4 闸门 · 篇级锁 · 幂等续跑。commit message 自动带
`engine=` 标注以便溯源。

### 8.1 单篇流水线(不变)

一篇论文 = 一次独立引擎调用(pi `pi -p` / codex `codex exec`,独立 context,不污染主会话):
T0→T4 五阶段在单次调用内完成,产物写 `00-pending/<citekey>/`,不直接动正式目录。

### 8.2 N-paper 并行 + Checkpoint(当前方式)

```bash
# 3 路并行示例:引擎+模型按 AGENTS.md §0.5 先问用户;列表不重叠
.skill/scripts/wiki_run_extract.sh --engine pi --provider cce-minimax3 ck1  ... ck11 &
.skill/scripts/wiki_run_extract.sh --engine pi --provider cce-minimax3 ck12 ... ck22 &
.skill/scripts/wiki_run_extract.sh --engine codex ck23 ... ck32 &   # 模型走 codex config,--model 可覆盖
wait
```

runner 内置保护(详见 AGENTS.md §8 铁律 #12/#13):
- **落盘即 commit**:每篇完成立即 git commit,产物不停留在 untracked 状态
- **篇级锁**:`.git/wiki-locks/<ck>.<pid>`,同篇并发自动 `[skip-locked]`
- **幂等续跑**:已完成(`00-pending/<ck>/<ck>.md` 已在 HEAD)自动 `[skip-done]`
- **日志**:`/tmp/pi_logs_runner/<ck>.log`(FAIL 时先看这里)

之后仍是人工审阅 → `wiki_promote.py <citekey>`(S7 闸门)→ 正式目录 + git tag checkpoint。

**失败回滚**:单篇质量问题 → 人审不 promote 即可;任何 git 破坏性手术前跑
`wiki_git_guard.sh`(铁律 #13)。

### 8.3 历史注记:Sub-agent Pipeline(2026-08-24 孪生脑批次,已废弃)

2026-08-24 的 49 篇孪生脑批次曾用 "N=5 worker sub-agent + 每worker独立 worktree" 编排
(4 sub-agent 串行:papper-analyst→claim-miner→evidence-mapper→topic-linker)。
该方式**已废弃**:编排复杂、产物曾长时间停留在 untracked 状态(2026-08-26 事故教训,
见 AGENTS.md §8)。`.pi/subagents/`(missions/artifacts)为遗留目录,新批次不再使用,
仅存档勿删。

---

## 9. 迁移策略 — 渐进式

### 9.1 分批迁移(AI 第三次建议 §渐进式)

| 批次 | 论文数 | 任务 |
|---|---|---|
| **Batch 0** | 5 | Gold Set,完整 5 阶段,验证 schema |
| **Batch 1** | 20 | 跑通批量 + checkpoint |
| **Batch 2** | 50 | 验证 stitch-knowledge(去重) |
| **Batch 3** | 100 | 全量 lint |
| **Batch 4** | 197 | 剩余全部 |

**关键**:每一批次 **git tag**,失败回滚。

### 9.2 Schema 版本兼容

- 新字段 **全 optional**:旧节点不破坏
- scripts 自动给旧 claim 补 `verification.confidence: null`、`scope: {}` 等默认值
- 升级命令:`wiki upgrade-plan-final [--dry-run] [--all]`

**迁移详情**:详见 `tasks.md T-W1-007 详情`(原 `MIGRATION_PLAN.md` 已并入)。包含 semantic-slug 重命名算法、paper.md frontmatter 重写、evidence/syntheses 新建、时间表、风险与回滚、验收标准、启动命令。

---

## 10. 实施路线图(4 周)

### Week 1 · 基础设施
| Day | 任务 |
|---|---|
| D1 | 写 AGENTS.md(< 80 行) + plan_final 文档定稿 |
| D2 | 拆 SKILL.md + 8 微 Skill(含 stitch-knowledge) |
| D3 | 写 10 个 Prompt Templates |
| D4 | 写 5 个 Extension(wiki-tools.ts) |
| D5 | 写 3 套 jsonschema + **集中 Schema 注册表**(`_registry.py`) |

### Week 2 · Gold Set + Batch 1(5 + 20 篇)
| Day | 任务 |
|---|---|
| D6-D7 | 5 篇 Gold Set,完整 T0-T4 |
| D8-D9 | 20 篇 Batch 1,跑通 pipeline + checkpoint |
| D10 | 人工审阅 + 迭代 SKILL |

### Week 3 · Batch 2-3(50 + 100 篇)
| Day | 任务 |
|---|---|
| D11-D12 | 50 篇 Batch 2 + stitch-knowledge 验证 |
| D13-D14 | 100 篇 Batch 3 + 全量 lint |
| D15 | 人工批量审阅 |

### Week 4 · Batch 4 + 迁移
| Day | 任务 |
|---|---|
| D16-D17 | 剩余 22 篇 |
| D18 | /lint 全量检查,生成报告 |
| D19 | 修 issues,重新跑 lint |
| D20 | 文档同步更新,发版 |

---

## 11. 与 AI 建议的关系

### 11.1 采纳的(15 项)

| AI 来源 | 建议 | 采纳位置 |
|---|---|---|
| **ChatGPT §1** | 收缩成 4-5 个核心对象 | §2.1 |
| **ChatGPT §3** | Evidence-centric 而非 Toulmin-centric | §1.3 方法论家族 |
| **ChatGPT §4** | CERIC 强推 | §1.3 论文层 |
| **ChatGPT §4** | Warrant 不做独立节点 | §3.5 claim.reasoning |
| **ChatGPT §7** | Claim verification 4 态 + confidence + strength | §3.5 verification |
| **ChatGPT §十一** | Observation + Interpretation 拆分 | §3.4 |
| **ChatGPT §十二** | Provenance 完整对象 | §3.4 provenance |
| **ChatGPT §二十二** | Atomic Claim | §3.5 atomic: true |
| **ChatGPT §二十三** | Claim Scope | §3.5 scope |
| **ChatGPT §二十七** | Synthesis 动态视图 | §2.2 |
| **YuanBao §三** | Toulmin + Cornwell + SciClaim 融合 | §1.3 方法论家族 |
| **DouBao §一** | 3 类方法论(论证/证据/流程) | §1.3 |
| **AI 第三次 §十六** | 4+1 抽取阶段 | §5.1 |
| **AI 第三次 §二十** | LLM→JSON→MD 流水线 | §5.2 |
| **AI 第三次 §二十五** | GRADE 不在 Claim | §3.5 verification 不带 GRADE |
| **AI 第三次 §十九** | 显式路由表 | §4.5 |
| **AI 第三次 §二十一** | Evidence Contract | §3.8 JSON Schema |
| **19 §4.5** | Stitch-knowledge 解决跨论文去重 | §5.4 |
| **19 §6.3** | Graph View Filter 配置 | §6.3 |

### 11.2 与工具包的关系(新增)

| 工具 | 洞察 | 采纳位置 |
|---|---|---|
| **EmpiricalWiki** | 集中 Schema 注册表(`_schemas.py`) | §7.1 `_registry.py` |
| **EmpiricalWiki** | 边类型注册表 + 置信度 | §1.2 #11 + §5.4 |
| **EmpiricalWiki** | `paper_kind` 区分实证/理论 | §3.2 |
| **SciClaim** | 细粒度主张 KG | 已试运行弃用(0/368,2026-08-25) |
| **SciFact** | claim verification 4 态 | §3.5 verification(已有) |
| **PaperJury** | 结构化审阅流程 | §7.2 自检清单 |
| **ScanSci Pi** | 句子级证据锚定 | §3.4 provenance(已有) |
| **MindCite** | Zotero → Obsidian 管线 | §4.4 wiki-zotero-sync |

### 11.3 未采纳的(及理由,合并 19 §11.2 + 21 + 工具包)

| 建议 | 理由 |
|---|---|
| 独立 Warrant 节点 | 90% 的 warrant 是隐含领域共识,降级为字段(GPT §四) |
| 独立 Mechanism / Variable 节点 | 节点数爆炸,吸收进 claim/evidence 正文 |
| 多模型交叉验证 | 成本高,先用单模型 + 代码校验 |
| embedding 去重 | 暂用 LLM 语义判断,Phase 2 再加 |
| GRADE 完整整合到单 claim | 单 claim 层不需要,放在 synthesis 层(AI 第三次 §25) |
| Contradiction Note 独立节点 | 用 claim.verification.contested + synthesis 标注 |
| pgvector / Neo4j | Obsidian Graph View 够用 |
| RAG 验证 | 先用 full.md 搜索 + Grounding grep |
| IMRaD 当骨架 | 只是论文结构,作为抽取辅助即可 |
| Discourse Graph | 太轻,不作骨架 |
| 单文档全文 Transclusion 不折叠 | callout 默认折叠缓解膨胀(用户接受) |
| /extract 不需要 arguments | 用户已习惯 argument-hint,保留 |
| GraphRAG 全量集成 | 太重,Obsidian Graph View 够用 |
| LangExtract 独立使用 | LLM 直接抽取更简单 |
| PaperQA2 RAG 全量 | 先用 full.md 搜索 + Grounding grep |
| ASReview 主动学习 | Phase 2,当前规模不需要 |
| EmpiricalWiki 10 类节点 | 过度特化,我们 5 类核心够用 |

### 11.3 延展优化项(Phase 2 候选,Phase 1 不做)

scout 综合分析发现 14 项次级创新点,均为非阻塞、Phase 2 可选。**记录在此避免遗忘,但本版本不实施**:

| # | 优化项 | 来源 | 影响 | 触发条件 |
|---|---|---|---|---|
| 1 | **D\* Delta 提案机制**(`evolution_type` + `proposed/accepted/parked/revised` 4 态生命周期) | 5-llm §2.4 | 高 | 当 wiki > 50 篇时(stitch-knowledge 执行协议) |
| 2 | Status 扩到 7 态(`pending/candidate/triaged/reading/summarized/approved/rejected/archived`) | 5-llm §2.6 | 中 | 当需要 rejected 留痕时 |
| 3 | Paper 节点 `citation_contexts` 6 类引用意图 | 13-architecture §3.3 | 中 | **已启用(批次4)**:107+ 篇同簇互引,新抽取建议填写(可选字段) |
| 4 | Paper 节点 `**关键概念**` 字段(3-8 关键词 + section 标注) | 6-wiki-extract P0-2 | 中 | 当需要按概念聚类时 |
| 5 | Paper 节点 `**我的判断**` 字段(最有启发/可借鉴/可追问/与研究关联) | 6-wiki-extract P0-3 | 中 | 当需要个人解读沉淀时 |
| 6 | Paper 正文 `**深度阅读**` 5 部分(真问题/背景张力/方法机制/真正洞察/项目定位) | 6-wiki-extract P1-1 | 中 | 当需要批判性阅读深度时 |
| 7 | **图片归档流程**(MinerU → `assets/<paper-id>/` → wikilink 引用) | 6-wiki-extract P1-3 | 中 | 当 wiki 中图文混合时 |
| 8 | **Lineage 技术路线图**(区别于 citation graph,最多 20 篇/lane) | 5-llm §2.7 | 中 | 当需要绘制研究脉络时 |
| 9 | **PUG (Project Understanding Graph)**(Q/C/E/W/L/RL/TL 7 类图节点 + 项目级真值) | 5-llm §2.3 | 中 | 当需要项目级认知时 |
| 10 | Reasoning Problem 标记(causal_overreach/confounding/selection_bias/null_result_overclaim) | 11-integrated L2 | 低 | 当需要质控批判时 |
| 11 | 3-Stage 批量策略(triage/skeleton/deep/audit 四阶段) | 6-wiki-extract P0-5 | 中 | 当 batch 数量 > 100 时 |
| 12 | 分层 vault(个人/项目/共享三层) | 6-wiki-extract P1-5 | 低 | 当需要多 wiki 切换时 |
| 13 | Transclusion 边界 HTML 注释标记(`<!-- CLAIM-EMBEDDING-START/END -->`) | 13-architecture §3.4 | 低 | 当需要自动化抽取嵌入时 |
| 14 | Pi 5 层扩展机制(Intent/Skill/Tool/Extension/Package) | 20_minimax §3.1 | 低 | 当需要分发 wiki 包时 |

**引用**:详细说明见 `ref/backup/` 中的对应早期文件(scout 抽样 5 份:`5-llm-tools-research-pilot-deepdive.md`、`13-architecture-v4-embed-paper.md`、`6-wiki-extract-skill-optimization.md`、`11-integrated-4-layer-architecture.md`、`20_minimax_pi_plan_version_cla.md`)。

---

## 12. 与现有版本的关系

| 维度 | v4(piminimax) | mimo(v16) | 19(mimo_pi_plan) | 21(minimiax_pi) | **plan_final** |
|---|---|---|---|---|---|
| 文件大小 | 114 KB | 34 KB | 35 KB | 37 KB | **~50 KB** |
| 节点数 | 8 类 | 6+2 | 5 类核心 | 5+2 | **5 核心 + 2 辅助** |
| 设计哲学 | 12 铁律 | 4 铁律 | 6 pi 原则 | 4 铁律 | **6 pi 原则 + 11 铁律 + 方法论家族** |
| 铁律数 | 12 | 4 | 13 | 4 | **11**(+Graph Edges Typed) |
| Schema 管理 | 分散 | 分散 | 分散 | 分散 | **集中注册表**(`_registry.py`) |
| 边类型 | 未注册 | 未注册 | 未注册 | 未注册 | **7 种注册类型 + 置信度** |
| Synthesis | 静态 | 静态 | **动态视图** | 未展开 | **动态 + 按需固化** |
| 抽取阶段 | 3 级 | 4 阶段 | 3 级分流 | 4+1 阶段 | **3 模式 × 5 阶段** |
| Pipeline | 3 sub-agent | 4 sub-agent | sub-agent + 断点续跑 | sub-agent + worktree | **sub-agent + worktree + checkpoint** |
| 路由 | LLM 猜 | 显式表 | description-driven | 显式表 + description | **显式表 + description** |
| Transclusion | 全量 | 摘要+折叠+块引用 | 2 级 + `<details>` | 3 级 + callout + `^summary` | **2 级 + callout + 全文嵌入**(用户硬需求) |
| Stitch Knowledge | × | × | **新增** | × | **保留 + 边类型验证** |
| claim 子结构 | 无 | 无 | 无 | 无 | **SciClaim 细粒度**(可选) |
| paper_kind | 无 | 无 | 无 | 无 | **empirical / theory / both** |
| Schema 版本 | v4.1 | v3 | 5.0 | minimiax_pi_v1 | **plan_final_v1** |

**核心差异**:plan_final 不是新设计,而是 **合并 + 收紧 + 加方法论家族 + 全文嵌入 + 集中 Schema 注册表 + 类型化语义图谱**。

---

## 13. 总结

### 核心创新点

1. **Pi 原生架构**:Wiki 的 progressive disclosure 与 pi 的 Skill 系统同构
2. **6 条 pi 原则 + 11 铁律 + 方法论家族**:三层设计哲学,可读可执行
3. **5 类核心节点**:从 8 类收缩,吸收 warrant/mechanism/variable 到字段
4. **Evidence-Centric**:evidence 是中心,claim/topic 都指向 evidence
5. **Synthesis 动态视图**:按需生成,用户确认才固化
6. **3 模式 × 5 阶段 抽取矩阵**:覆盖所有场景
7. **LLM→JSON→MD 三级流水线**:JSON 契约 + MD 表现
8. **全文 Transclusion(callout 折叠)**:用户硬需求,paper.md 看全
9. **Sub-agent + Worktree + Checkpoint**:可靠批量
10. **Grounding Invariant**:数值可验证,幻觉可检测
11. **#11 铁律:Graph Edges Are Typed & Confident**:边类型注册表 + 置信度,防止 LLM 编造关系
12. **集中 Schema 注册表**:单一真相源(`_registry.py`),避免 schema 分散
13. **SciClaim 细粒度**:evidence 内部的 association/factor/magnitude 结构(可选)

### 一句话

> **用 pi 的五件套 + 集中 Schema 注册表 + 类型化语义图谱 + SciClaim 细粒度 + Evidence-Centric 方法论家族 + 3模式×5阶段抽取 + LLM→JSON→MD流水线 + 全文嵌入(callout折叠)+ Sub-agent Pipeline + 分层 Lint,在 Minimax M3 上跑一个 5 类核心节点的 Pi-Native 证据 Wiki。**

### 参考文献

- ChatGPT 2026-08-21: `<external-notes>/参考资料/论文写作/论文整理/ai建议/ChatGPT_2026_08_21__1820.md`
- DeepSeek 2026-08-21: `.../DeepSeek_2026_08_21__1827.md`
- DouBao 2026-08-21: `.../DouBao_2026_08_21__1831.md`
- Gemini 2026-08-21: `.../Gemini_2026_08_21__1823.md`
- YuanBao 2026-08-21: `.../YuanBao_2026_08_21__1827.md`
- 千问 阿里 2026-08-21: `.../千问 阿里_AI_助手.md`
- 智谱清言 2026-08-21: `.../智谱清言.md`
- AI 第三次建议合并: `.skill/ref/ai第三次建议.md`(10 AI 共识)
- 整合来源: `.skill/ref/19mimo_pi_plan.md` + `.skill/ref/21_minimiax_pi_plan.md`
- 工具包(22 个): `<external-notes>/参考资料/论文写作/论文整理/工具包/`
  - **EmpiricalWiki**: Schema 注册表 / 边类型系统 / paper_kind 分流
  - **SciClaim** (EMNLP 2021): 细粒度科学主张 KG
  - **SciFact**: claim verification
  - **PaperJury**: 结构化审阅流程
  - **ScanSci Pi**: 证据优先科研工作台

---

## 14. 文件清单(给实施者)

```
wiki/
├── ARCHITECTURE.md                    # ★ 架构契约(本文,原 plan_final.md,2026-08-25 升格)
├── AGENTS.md                          # < 80 行,宪法 + 路由表
├── index.md                           # 全局索引
├── log/                               # 日志文件夹(2026-08-27)
│   ├── README.md                      # 批次索引 + 建批/并行规范
│   ├── ops.md                         # 全局操作日志(append-only)
│   └── batch-*.md                     # 批次档案(源 CSV 路径 + 逐篇状态,AUTO 区脚本刷新)
│
├── paperinfo/                         # scripts 写
├── papers/                            # LLM 写(审阅后)
├── claims/                            # LLM 写
├── evidence/                          # LLM 写
├── topics/                            # LLM 写(跨论文)
├── syntheses/                         # LLM 动态生成,用户固化
├── 00-pending/                        # LLM 写,人审阅
├── raw/                                # ★ 权威源(MinerU 复制品)
│   ├── <citekey>/                     # 论文目录
│   │   ├── full.md                     # MinerU 输出
│   │   └── images/                     # 论文图片(直接引用,无中间层,T-W4-029)
│
├── .skill/
│   ├── ARCHITECTURE.md                # 纯指针 → 根 ARCHITECTURE.md(单一契约,§0.1)
│   ├── SKILL.md                       # < 100 行,入口
│   ├── skills/                        # 8 微 Skill
│   │   ├── wiki-extract-paper/
│   │   ├── wiki-build-claim/
│   │   ├── wiki-build-evidence/
│   │   ├── wiki-build-topic/
│   │   ├── wiki-query-evidence/
│   │   ├── wiki-stitch-knowledge/     # 跨论文去重 + 边类型验证
│   │   ├── wiki-lint-wiki/
│   │   └── wiki-zotero-sync/
│   ├── scripts/schemas/               # NEW: 集中 schema(和 Python 一起)
│   │   ├── _registry.py               # 单一真相源(EDGE_TYPE_SPECS)
│   │   ├── evidence.schema.json
│   │   ├── claim.schema.json
│   │   └── topic.schema.json
│   ├── scripts/                       # 验证工具
│   └── references/                    # AGENTS.md + templates/
│
└── .pi/
    ├── prompts/                       # 10 个命令模板
    └── extensions/
        └── wiki-tools.ts              # 5 个自定义工具
```

---

> **下一步**:用户确认 plan_final 后，开始重构 wiki 实际数据。
> 重构顺序:Week 1(基础设施，含 `_registry.py`)→ Week 2(Gold Set 5 篇，含 SciClaim 验证)→ Week 3-4(批量 197 篇)。

---

## 15. 测试过程发现的问题与修复(2026-08-24)

> **本节记录从“设计→实施”迁移过程中发现的所有问题、诊断报告与修复记录。后续遇到的问题也会补充到这里。**

### 15.1 诊断报告 (8 项 → 全部修复)

**2026-08-24 执行的诊断**(对照 plan_final  vs 实际实现):

| # | 问题描述 | 严重性 | 修复状态 |
|---|---|---|---|
| **P0-1** | 命名约定矛盾：plan_final §2.3 使用 `CLAIM-NNN_<slug>.md`，但 SKILL.md / 微 Skill 使用语义 slug | P0 | ✅ 已修复（选择保持语义 slug，改 plan_final） |
| **P0-2** | 边类型置信度未落地 schema：supports/contradicts 是扁平字符串数组，丢失 target/confidence/relation 结构 | P0 | ✅ 已修复（改为对象数组 {target, confidence, relation}） |
| **P0-3** | `_registry.py` 缺 EDGE_TYPE_SPECS / ENTITY_DIRS / REQUIRED_FIELDS | P0 | ✅ 已修复（补上 3 个常量 + check_edge 函数） |
| **P1-1** | SKILL.md 260 行超标（plan §4.2 要求 < 80 行） | P1 | ✅ 已修复（精简到 90 行） |
| **P1-2** | schema 目录路径不一致：plan 写 `.skill/schemas/`，实际 `.skill/scripts/schemas/` | P1 | ✅ 已修复（统一为 `.skill/scripts/schemas/`，plan 同步） |
| **P1-3** | `.pi/` 目录不存在 | P1 | ❌ 报告错误（实际已存在：10 prompts + 1 extension） |
| **P2-1** | 缺 paper.schema.json | P2 | ⏸ Phase 2 |
| **P2-2** | claim schema 缺 evidence_quality / reasoning_type | P2 | ⏸ Phase 2 |

### 15.2 抽取 3 篇孪生脑论文时的问题(11 个假 wikilink)

**问题描述**:抽取 Martin 2025 / Cakan 2023 / Boisgontier 2026 三篇论文时，claim 节点的「引用此主张的页面」与 paper 节点的「引用本论文的页面」中出现了指向不存在的节点的 wikilink(broken links)。

**根本原因**:
- 3 篇论文还在 `00-pending/`，未 promote 到 `papers/`
- 5 个主题节点（tvb-platform / digital-twin-brain-development / neural-mass-models / neurodevelopmental-disorders / prader-willi-syndrome）尚未创建
- 手工写反向链接时未验证目标存在性

**L2 语义层 lint 规则**(固化):
- 所有 `[[wikilink]]` 目标必须存在于 wiki 中（根目录 + paperinfo / papers / claims / evidence / topics / syntheses 之一）
- scripts `wiki_check_wikilinks` Extension 会标记 broken link
- LLM 抽取时反向链接必须验证后才能写入

**修复** (2026-08-24, T-W4-009):
- 4 个 claim 节点删除 11 个假 wikilink:
  - `tvb-ontology-enables-reproducibility.md` 删 3 个
  - `neurolib-enables-whole-brain-modeling.md` 删 2 个
  - `pws-infants-show-early-brain-hyperperfusion.md` 删 3 个
  - `early-brain-perfusion-linked-to-feeding-social-function.md` 删 3 个
- 3 个 paper.md 修复 `**引用本论文的页面**`（单行格式，`·` 分隔）:
  - martin_2025: 全部删（只剩 `---` 标题）
  - cakan_2023: 保留 [[whole-brain-modeling]]（真实存在）
  - boisgontier_2026: 全部删（只剩 `---` 标题）

**教训(写入 Prompt)**:
- `.pi/prompts/extract.md` 加步骤: “生成反向链接前调 `wiki_check_wikilinks` Extension 验证目标存在性”
- `.pi/prompts/promote.md`(新建)加: "promote 前确认 L0-L3 全部通过，无 broken link"

**未来预防**:
- 后续 promote 时，scripts `wiki_check_wikilinks.py` Extension 作为 Extension 工具提供可被 pi 调用
- lint 报告包含“broken_wikilink”作为 P0 阻塞项

### 15.3 Raw 层 未建立(已修复 → §15.4 后续防)

**问题描述**:抽取 3 篇论文时，`evidence.provenance.source_text` 需要在 raw full.md 中 grep (Grounding Invariant)。但原始 full.md 在外部 `<zotero-md>/`，wiki 本身未携带原始素材。

**修复**(2026-08-24, T-W4-008):
- 3 个 raw 目录复制到 `wiki/raw/<citekey>/`
- 4 个 evidence 节点添加 `provenance.raw_path` 字段
- 文档：plan_final §2.1 + §5.5 + §14, SKILL.md, AGENTS.md, README.md 全部更新
- `_registry.py` 加 `RAW_PATH_TEMPLATE` + `check_raw_exists()`

### 15.4 后续遇到的问题(动态补充)

> 本节为预留位。后续遇到的问题将按以下格式记录:
> - **问题描述**: 简要说明
> - **发现时间**: YYYY-MM-DD
> - **修复方式**: 详细修复步骤
> - **预防**: 写入哪些 Prompt / Extension / Script 防止复发

#### 15.4.1 paper.md 中的提示文字(已修复,2026-08-24)

- **问题描述**: martin_2025_tvb_ontology/paper.md 的 `## 本论文的 Evidence(完整嵌入)` 段后保留了草稿提示 `> 以下用 \`![[...]]\` 直接嵌入 evidence 节点内容`,在 LLM 抽取的纸面读起来不像节点本来的文本。
- **发现时间**: 2026-08-24(用户审阅反馈)
- **修复方式**: 3 个 paper.md 检查 + 删除提示行(只 martin 有,cakan/boisgontier 没有)
- **预防**: paper.md 模板(plan_final §3.3)删除该提示行
- **状态**: ✅

#### 15.4.2 paper.md 命名与 paperinfo 引用(已修复,2026-08-24)

- **问题描述**: 抽取时 paper.md 命名为通用名 `paper.md`,违反 plan_final §2.3 命名约定(应为 `<BBT-citekey>.md`)。另外 3 个 paper.md 中 `paperinfo: "[[paperinfo/<citekey>]]"` 字段被 wikilink 修复脚本误删,导致 L2 broken link。
- **发现时间**: 2026-08-24(用户反馈 + wikilink lint)
- **根因**:
  - 3 个 paper 节点未 promote,仍在 00-pending/ 草稿状态时用 `paper.md` 临时命名
  - `paperinfo/` 目录未填充 Zotero sync 结果,导致 paperinfo 节点未生成
  - 上轮“删假 wikilink”脚本误删了 paperinfo 引用
- **修复方式**:
  - 重命名 `00-pending/<citekey>/paper.md` → `00-pending/<citekey>/<citekey>.md`
  - 创建 3 个 paperinfo 占位节点(`paperinfo/<citekey>.md`),等 zotero sync 填充真实元数据
  - 恢复 3 个 paper.md 的 `paperinfo: "[[paperinfo/<citekey>]]"` 字段(frontmatter + 元信息段)
  - 合并断行 bug(`- paperinfo: \n[[...]]` → `- paperinfo: [[...]]`)
- **预防**:
  - paper.md 模板明确使用 `<BBT-citekey>.md` 命名(即使在 00-pending/ 中)
  - paperinfo 节点创建作为抽取流程的一部分(不是 zotero sync 才能创建)
  - 抽取脚本同时创建 paperinfo 占位节点(zotero sync 只填充,不创建)
- **状态**: ✅ 0 broken wikilink

#### 15.4.3 paperinfo 节点用占位而非 Zotero 真实数据(已修复,2026-08-24)

- **问题描述**: T-W4-010 创建的 3 个 paperinfo 节点是占位(zotero-key: TODO, 字段全空),不是从 Zotero 库真实抽取的。
- **发现时间**: 2026-08-24(用户反馈“都不是直接 zotero 抽取的”)
- **根因**: 抽取流程未实际查询 Zotero DB,只是手填了占位元数据。
- **修复方式**:
  1. 复制 Zotero SQLite 到 `/tmp/zotero-readonly.db`(避免锁)
  2. 查询 3 个论文的 zotero item:
     - Martin 2025: itemID=66715, zotero-key=7LVJCVTB, 11 作者
     - Cakan 2023: itemID=??, zotero-key=YS3RPZHD, 0 作者(Zotero 只存了 PDF 文件名作为 title)
     - Boisgontier 2026: itemID=??, zotero-key=PXTUVFFA, 15 作者
  3. 填充 paperinfo 节点:
     - Martin + Boisgontier: Zotero 抽取全字段
     - Cakan: Zotero 抽取 zotero-key/link + 从 full.md 补全 title/authors/year/DOI/abstract
- **预防**:
  - 抽取脚本调用 `wiki_zotero_sync.py` 实际查询 Zotero SQLite(不是手填)
  - 如果 Zotero 中元数据不完整,从 full.md 抽取补全(LLM-driven)
  - 抽取报告包含“Zotero 抽取状态: 完整/不完整/需补全”字段
- **状态**: ✅ 3 个 paperinfo 节点含真实 zotero-key + 完整元数据

#### 15.4.4 Cakan 误用 attachment key 而非 paper key(已修复,2026-08-24)

- **问题描述**: 抽取 cakan_2023_neurolib 时使用 `--zotero-key YS3RPZHD`,但该 key 在 Zotero 中是 **PDF attachment 节点**(不是 paper 节点),抽取得到 `title = "cakan_2023_cogn_comput_neurolib A Simulation Framework for Whole-Brain Neural Mass Modeling.pdf"`(PDF 文件名)。
- **发现时间**: 2026-08-24(用户提问“Cakan 是zotero中没有吗?”后调查发现)
- **根因**:
  - Zotero 中有 2 个相关节点:
    - **attachment `YS3RPZHD`** (itemID=66939): PDF 附件, linkMode=2
    - **paper `DW6SBAT5`** (itemID=66727): cakan paper 节点, 3 作者, 完整 DOI/abstract
  - 之前抽取脚本未走 attachment 过滤逻辑,直接调用 `zot.item(YS3RPZHD)`,拿到 attachment 节点的数据。
- **修复**:
  1. 删除错误 paperinfo `paperinfo/cakan_2023_neurolib.md`
  2. 用 paper key `DW6SBAT5` 重跑:`wiki zotero extract --zotero-key DW6SBAT5 --citekey cakan_2023_neurolib --force`
  3. 验证 3 作者 / DOI / publication / abstract 都完整
- **预防**(写入 wiki_zotero.py):
  - `cmd_extract` 加过滤:检测 itemType != 'attachment' / 'note' / 'annotation'
  - 如果是 attachment,自动找 parentItemID 重试
  - 打印警告: "key=XXX is attachment, use parent key=YYY instead"
  - add_argument `--zotero-key` help 加备注: "要的是 paper key,不是 attachment key"
- **状态**: ✅ cakan paperinfo 用 DW6SBAT5 抽取,完整元数据

#### 15.4.5 paperinfo 目录 14657 个文件加载慢(已优化,2026-08-24)

- **问题描述**: `paperinfo/` 目录含 14657 个 .md 文件(90 MB),Obsidian 启动扫描所有文件,打开和加载慢。
- **发现时间**: 2026-08-24(用户反馈“一下子太多笔记,打开和加载都太慢”)
- **根因**:
  - Zotero sync 生成 Zotero 库全部条目(14656+ 论文)的 paperinfo 节点
  - 实际被 wiki 引用的只有 ~15 个(其中 3 个是新论文,其他是历史论文)
  - 14653 个孤立 paperinfo 不被引用,但被 Obsidian 扫描
- **优化方案**:`.obsidianignore` 排除 `paperinfo/` 目录
  - **优势**:零迁移、零风险、立即生效
  - **优势**:wikilink `[[paperinfo/xxx]]` 仍可点击(Obsidian wikilink 解析独立于 ignore 列表)
  - **优势**:需要查看 paperinfo 元数据时,可以从文件浏览器手动添加 `paperinfo/` 目录
- **预防**:
  - future zotero sync 默认不写 paperinfo(只填必要字段)
  - 或者按需 rehydrate(被 wikilink 引用的才写)
- **状态**: ✅ 3 个被引用的 paperinfo 仍可解析,14653 个孤立节点不再被 Obsidian 索引

#### 15.4.8 中文文本中 `-` 替代空格审计(已修复,2026-08-24)

- **问题描述**: 36 处中文内连字符(`神经-行为`、`脑-行为`、`内脊-纹状体`、`模型-数据` 等)违反 plan_final §3.5 §15.4.7 规则
- **根因**: 抽取脚本序列化时误用 `-` 替代真实空格
- **修复**:
  - 36 处 `中文-中文` / `中文-英文` / `英文-中文` 模式全部改为真实空格
  - 核心文件: tasks.md / log.md / 3 个新 paper.md / templates / .skill/ref/plan_final.md / .skill/ref/ai第三次建议.md / .skill/ref/handoff-to-other-ais.md / .skill/ref/design-history.md / .skill/skills/wiki-build-evidence/SKILL.md / .skill/ref/demo-views/README.md / topics/* / .memsearch/memory/*
  - 3 处残留(总览):`文献清单-合并` / `文献清单-终版` / `校验-修正` / `年份-关键词`
- **例外**(保留 `-`):
  - 专业术语:Prader-Willi / insula-temporal / striatum-pallidum / TVB-O / whole-brain / oral-motor / machine-readable
  - 文件名 slug:kebab-case(plan_final §2.3 规定)
  - 字段名:snake_case(`_` 分隔)
- **预防**:
  - scripts `wiki_lint.py` 加 `grep "[一-鿿]+-[一-鿿]+"` 自动检查
  - 抽取 LLM 看到 §15.4.7 规则自动避免
- **状态**: ✅ 145 个核心文件 0 中文内连字符

#### 15.4.6 claim 的 sources target 应指向 papers/ 而非 paperinfo/(已修复,2026-08-24)

- **问题描述**: 4 个 claim 节点的 `sources.target` wikilink 写为 `[[cakan_2023_neurolib]]`(无前缀),Obsidian 全局搜索会找到 `paperinfo/cakan_2023_neurolib.md`(虽然被 .obsidianignore 排除,但仍可能引发问题)。
- **发现时间**: 2026-08-24(用户反馈“应该是直接 cite papers/cakan_2023_neurolib”)
- **根因**: 抽取时未走 plan_final 推荐的“显式 papers/ 前缀”约定
- **修复**:
  - 4 个 claim 的 `sources.target` 加 `papers/` 前缀:
    - `[[cakan_2023_neurolib]]` → `[[papers/cakan_2023_neurolib]]`
    - `[[martin_2025_tvb_ontology]]` → `[[papers/martin_2025_tvb_ontology]]`
    - `[[boisgontier_2026_brain_perfusion]]` → `[[papers/boisgontier_2026_brain_perfusion]]`(× 2 个 claim)
- **预防**(写入 plan_final §3.5 模板):
  - claim frontmatter `sources.target` 模板改为 `[[papers/<citekey>]]`
  - claim `evidence.target` 同样: `[[evidence/<author>-<year>-<slug>]]`
  - 抽取脚本序列化时强制加前缀
- **状态**: ✅ 4 个 claim.sources 显式指向 papers/(同时 .obsidianignore 仍保护 paperinfo/)

#### 15.4.10 claim 表格"来源"列改为 wikilink(已修复,2026-08-24)

- **问题描述**: 4 个 claim 正文表格的"来源"列是纯文本(`Boisgontier 2026` / `Cakan 2023` / `Martin 2025`),不是 wikilink
- **发现时间**: 2026-08-24(用户反馈"这里下边应该是 [[papers/citekey]],所有 claim 的这里都要注意")
- **根因**: 抽取时只设了 frontmatter `sources.target` wikilink,正文表格"来源"列未同步
- **修复**:
  - 4 个 claim 表格"来源"列改为 wikilink:
    - `Boisgontier 2026` → `[[papers/boisgontier_2026_brain_perfusion]]`(× 2)
    - `Cakan 2023` → `[[papers/cakan_2023_neurolib]]`
    - `Martin 2025` → `[[papers/martin_2025_tvb_ontology]]`
- **预防**:
  - 抽取脚本同时同步表格列(不只 frontmatter)
  - 模板示例明确使用 wikilink
- **状态**: ✅ 4 个 claim 表格"来源"列全部为 wikilink

#### 15.4.9 claim/evidence 文件名改为中文 + 真实空格(已优化,2026-08-24)

- **问题描述**: 4 个 claim + 4 个 evidence 文件名用 kebab-case 英文(如 `neurolib-enables-whole-brain-modeling.md`),人类可读性差,且不反映实际内容
- **发现时间**: 2026-08-24(用户反馈"md 的名字没有改变"+"可以是中文的"+"不要用 -")
- **根因**: 沿用 plan_final §2.3 旧约定(只允许 kebab-case 英文)
- **修复**:
  - 4 个 claim 重命名为**中文 + 真实空格**(Obsidian 支持):
    - `neurolib-enables-whole-brain-modeling.md` → `neurolib 启用可扩展的全脑建模.md`
    - `tvb-ontology-enables-reproducibility.md` → `TVB-O 启用可重复脑网络模拟.md`
    - `pws-infants-show-early-brain-hyperperfusion.md` → `PWS 婴儿早期脑高灌注.md`
    - `early-brain-perfusion-linked-to-feeding-social-function.md` → `早期脑灌注与喂养社会功能相关.md`
  - 4 个 evidence 重命名为**中英混合**(`<author>-<year>-<中文 slug>`):
    - `martin-2025-tvb-ontology-semantic-kb.md` → `martin-2025 TVB-O 是统一语义知识库与软件工具.md`
    - `cakan-2023-neurolib-python-framework.md` → `cakan-2023 neurolib 是 Python 全脑建模框架.md`
    - `boisgontier-2026-pws-cbf-increases.md` → `boisgontier-2026 PWS 婴儿 3 脑区 CBF 增高.md`
    - `boisgontier-2026-perfusion-clinical-associations.md` → `boisgontier-2026 PWS 婴儿脑灌注与临床关联.md`
- **更新引用**:48 处 wikilink 引用同步(3 个 paper.md + 4 个 claim + 4 个 evidence 自身,共 48 处)
- **验证**:0 broken wikilink
- **规范更新**(plan_final §2.3 命名约定):
  - 优先用中文 slug(真实空格分隔)
  - 避免用 `-` 替代空格(§15.4.7 / §15.4.8)
  - evidence 仍用 `<author>-<year>-<slug>` 形式(中英混合)
- **状态**: ✅ 8 个 md 文件重命名,48 处引用同步

#### 15.4.11 evidence 废除 raw_path 字段 + 架构文档升格(2026-08-25)

- **问题描述**: 368 个 evidence 全部携带 `raw_path` 指针字段,raw 目录重命名为 BBT citekey 后 95.7%(351/368)悬空失效。evidence 的 provenance 锚本应是**复制进节点的原文**(`prov_source_text`,368/368 已覆盖),raw_path 是可从 `source` citekey 推导的冗余信息,存储即双源、必然漂移。
- **决策**(用户裁定):
  1. **evidence 不存任何 raw 指针字段**,raw_path 从 schema 中废除;
  2. evidence 需要证据时**直接复制原文**进节点(`prov_source_text` + `prov_section`/`prov_page`);
  3. 脚本(Grounding 验真)需要访问 raw 时,按 evidence 的 `source`/`prov_paper` citekey **现场推导** `raw/<citekey>/full.md`,不读存储指针。
- **同日决策**: `plan_final.md` 升格迁至 wiki 根目录为 **`ARCHITECTURE.md`**(数据架构契约),新增 **`.skill/ARCHITECTURE.md`**(工具链架构契约),构成两层架构文档体系(§0.1)。agent 修改 wiki 数据或 `.skill/` 前必读。
- **存量清理**: 368 个 evidence 的 raw_path 字段剥离 + 依赖脚本(`_registry.py`/`wiki_lint.py`/`wiki_check_evidence.py`)改为推导逻辑 → 任务 **T-W5-002**。
- **状态**: ✅ 契约已更新 · ⏳ 存量数据清理待执行(T-W5-002)