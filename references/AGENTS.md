# AGENTS.md — 证据 Wiki 操作规范

> **本文件是整个 Wiki 系统的灵魂。**
> pi 在第一次处理本目录时，应当完整阅读本文件。
> 阅读后，所有页面写入与维护操作都必须遵守本规范。

---

## 0. 角色与边界

你是这个学术证据 Wiki 的**长期维护者**。

- 你的输入：用户提供的论文路径（Zotero PDF 或 MinerU full.md），或用户的提问。
- 你的输出：写入 `papers/`、`topics/`、`claims/`、`syntheses/` 等节点的 Markdown 页面；维护 `index.md` 与 `log.md`。
- 你的能力：抽取结构化笔记、跨节点 wikilink 关联、回答问题、定期 lint。
- 你的禁区：**永不修改原始层**（Zotero 库、MinerU 导出目录）。

---

## 1. 节点模型与目录约定

Wiki 由**四类平等节点** + **两个全局文件**构成。所有节点之间通过 `[[wikilink]]` 自然形成双向链接，不强制层级。

### 1.1 四类节点

| 节点 | 目录 | 何时创建 | 数量预期 |
|---|---|---|---|
| **论文节点** | `papers/` | 摄入每篇论文时 | 多 |
| **主题节点** | `topics/` | 用户提出主题，或某主题首次跨论文出现时 | 中 |
| **主张节点** | `claims/` | 一个主张在 2+ 篇论文中复用时 | 少 |
| **综合节点** | `syntheses/` | 用户问了一个值得固化的问题 | 少 |

### 1.2 目录布局

```
./
├── AGENTS.md            ← 本文件
├── README.md            ← Wiki 入口说明
├── index.md             ← 全局索引
├── log.md               ← 操作日志（append-only）
│
├── 00-pending/          ← 待审阅的新页面（先放这里）
├── paperinfo/           ← Zotero 元数据镜像 (scripts 同步)
├── papers/              ← 论文节点
├── topics/              ← 主题节点
├── claims/              ← 主张节点（懒创建）
├── syntheses/           ← 综合节点（懒创建）
│
├── raw/                 ← 论文原始素材 (full.md + images/, scripts 同步, 不可变)
└── templates/           ← 节点模板（仅参考，不复制到节点）
```

### 1.3 节点命名约定(ARCHITECTURE §2.3 + T-W4-030,优先中文 + 真实空格)

- 论文节点：`papers/<BBT-citekey>.md`(ASCII citekey 形式)
  - 例:`papers/zhang_2021_fnirs.md` / `papers/boisgontier_2026_brain_perfusion.md`
- 主题节点:`topics/<topic-key>.md`(优先中文 + 真实空格)
  - 例:`topics/fNIRS 认知控制.md` / `topics/fnirs-cognitive-control.md`
- 主张节点:`claims/<semantic-slug>.md`(优先中文 + 真实空格,**无编号**)
  - 例:`claims/PWS 婴儿早期脑高灌注.md` / `claims/dlpfc-hbo-age.md`
  - **不**用 CLAIM-001 / CLAIM-007 内部编号
- 证据节点:`evidence/<author>-<year>-<slug>.md`(中英混合 + 真实空格)
  - 例:`evidence/boisgontier-2026 PWS 婴儿 3 脑区 CBF 增高.md`
  - 前缀 `<author>-<year>-` 用 ASCII 避免重名,主体 `<slug>` 可中英混合
- 综合节点:`syntheses/<question-key>.md`(优先中文 + 真实空格)
  - 例:`syntheses/DLPFC 发育与认知控制.md`

**核心规则**:
- **优先中文 + 真实空格**(Obsidian 自动 URL-encode 中文文件名,直接 `[[中文文件名]]` 引用即可)
- **不用 `-` 替代真实空格**(ARCHITECTURE §15.4.7);例外:专业术语 `Prader-Willi` / `TVB-O` / `whole-brain` / `neural-behavioral`
- 中英混合 / kebab-case / snake_case 也允许(多风格并存)

### 1.4 节点之间的关系

**所有关系通过 `[[wikilink]]` 表达，不写硬关系字段。**

论文 ↔ 主题：双向 `[[wikilink]]`，多对多
- 论文节点的 `关联主题` 列出主题
- 主题节点的 `涉及论文` 列出论文

论文 → 主张：单向 `[[wikilink]]`
- 论文节点的 `核心主张` 中提及 `[[CLAIM-001]]`
- 主张节点反向链接到论文（在 `引用此主张的页面` 中）

Obsidian Graph View 会自动绘制这张图。

### 1.5 raw 原始素材目录 (Source of Truth)

```
raw/
├── <citekey>/
│   ├── full.md        ← MinerU 导出的论文正文 (LLM 抽取源)
│   ├── images/        ← 相对路径被 full.md 引用
│   └── ...
```

**原则** (RAW IS IMMUTABLE):
- 每个 paper.md 对应一个 `raw/<citekey>/` 目录
- `raw/<citekey>/full.md` 是 LLM 抽取 L2/L3 字段的**唯一来源**
- `csv-source-path` 字段应始终指向 `raw/<citekey>/full.md` (本地副本)
- 不可手动改 raw 内容 (内容必须与 zotero_md 同步)

**同步脚本**: `wiki sync-raw`
- 从 `<zotero-md>/<collection>/<paper>/` 完整复制 (含 images/)
- 增量补全 (已有 full.md 时, 仅补 images/)
- MANUAL_CITKEY_MAP 处理命名不一致 (旧 paper 用 Firstname_Lastname_Year)

**集成**:
- LLM 抽取前, 必须先 `wiki sync-raw` 同步素材
- `wiki zotero pull` 生成 paperinfo, 后续 LLM 从 raw/ 抽取 L2/L3
- 增量同步以 `zotero-lastmod` 为指纹 (不重写未改的)

---

## 2. 字段命名与样式约定

### 2.1 字段标题风格

**使用 `**xxx**` 而非 `#` 标题**。原因：
- MinerU 默认输出就是这种 bold 风格，便于从 full.md 直接复制段落
- Obsidian 中 `**xxx**` 与 `#` 都能在 Outline 面板显示
- 减少层级噪音，让正文更突出

但**页面的顶级标题仍然用 `# Page Title`**（Obsidian 必须有顶级标题才识别为页面）。

### 2.2 节点字段模板

**论文节点字段**（实证研究风格，按需增减）：
```
# {Title}                          ← 页面顶级标题（必填）

**元信息**                          ← 作者/年份/期刊/DOI/类型/领域
**研究目的**
**被试**
**实验设计**
**实验范式**
**刺激材料**                       ← optional
**测量工具**                       ← optional
**数据分析**                       ← 统计/ML 方法
**结果**
**结论**
**核心主张**                       ← CLAIM 列表（实证 + 解读）
**证据条目**                       ← EVIDENCE 列表
**关联主题**                       ← [[topic-xxx]]
**关联主张**                       ← [[CLAIM-XXX]]
**引用本论文的页面**                 ← 反向链接
```

**主题节点字段**：
```
# {Topic Title}

**主题描述**
**涉及论文**                       ← [[paper-id]] 列表
**核心主张**                       ← [[CLAIM-XXX]] 列表
**共识**
**矛盾**
**空白**
**关联主题**                       ← optional
```

**主张节点字段**（懒创建）：
```
# CLAIM-XXX: {陈述}

**主张陈述**
**首次出现**
**支持证据**                       ← [[paper-id]] + 原文 quote
**反对证据**
**限定条件**
**证据强度**
**引用此主张的页面**
```

**综合节点字段**：
```
# {Question}

**问题**
**结论**
**关键证据链**
**证据强度**
**边界**
**涉及页面**
**更新历史**
```

### 2.3 实证字段的填充规则

每篇论文至少填以下字段：
- `**元信息**`（必填）
- `**研究目的**`（必填，1-3 句）
- `**被试**`（必填，n=..., 人群, 年龄范围）
- `**实验设计**`（必填，cross-sectional / longitudinal / RCT / within-subject 等）
- `**数据分析**`（必填，统计/ML 方法）
- `**结果**`（必填，原文 quote 嵌入关键统计值）
- `**结论**`（必填，作者总结）

可选字段：
- `**实验范式**`（block design / event-related / resting-state 等）
- `**刺激材料**`（神经影像/EEG/fNIRS 必备）
- `**测量工具**`（仪器/量表）

CLAIM / EVIDENCE 字段：
- 一篇论文**至少**列 1-3 条 CLAIM
- 一条 CLAIM 至少有 1 条 EVIDENCE 支撑

### 2.5 字段定义（嵌入式 schema）

> **本节是 4 类节点字段约束的权威源**。pi 抽取时必读；校验脚本可解析本章节自动生成规则。所有节点模板（`templates/*.md`）的字段约束以本节为准。

#### 2.5.1 论文节点（Paper Node）必填字段

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | string | 格式：`<Author>_<Year>_<short>` | 唯一标识，与文件名一致 |
| `title` | string | 必填 | 论文标题 |
| `year` | integer | 1900-2030 | 发表年份 |
| `modality` | enum | [fmri, eeg, fnirs, eye-tracking, multimodal, meta-analysis, review, stats, ml, other] | 模态/论文类型分类 |
| `research_goal` | string | 1-3 句话 | 研究目的 |
| `participants.n` | integer | >0 | 被试数（综述/meta 用覆盖研究数 + 总 N） |
| `data_analysis.preprocessing.software` | string | 必填（按模态） | 预处理软件 |
| `results` | array | 每条含 `statistic` + `evidence_id` | 关键结果 |

#### 2.5.2 论文节点条件必填（按模态 / 研究类型）

- **fmri**: 必须包含 `preprocessing` / `hrf_model` / `motion_correction` / `glm_design` / `multiple_comparison`
- **eeg**: 必须包含 `montage` / `filter` / `ica` / `epoch`
- **fnirs**: 必须包含 `device` / `channels` / `preprocessing` / `hrf` / `wavelength`
- **eye-tracking**: 必须包含 `sampling_rate` / `fixation_detection` / `aoi` / `pupillometry`(如适用)
- **multimodal**: 涵盖各模态的必填字段
- **meta-analysis**: 必须包含 `search_databases` / `inclusion_criteria` / `effect_size` / `heterogeneity_I2` / `publication_bias` / `software`
- **review**: 必须包含 `review_subtype` / `search_strategy` / `inclusion_criteria` / `synthesis_method` / `evidence_grade`(如适用)

#### 2.5.2.1 模板选择指引

每种研究类型使用对应模板（`evidence-wiki-skill/references/templates/`）：

| 论文类型 | 模板文件 | modality 取值 |
|---|---|---|
| fNIRS 实证 | `paper-fnirs.md` | `fnirs` |
| fMRI 实证 | `paper-fmri.md` | `fmri` |
| EEG 实证 | `paper-eeg.md` | `eeg` |
| 眼动追踪 | `paper-eye-tracking.md` | `eye-tracking` / `multimodal` |
| Meta 分析 | `paper-meta-analysis.md` | `meta-analysis` / `stats` |
| 综述 | `paper-review.md` | `review` |
| 通用实证（其他模态） | `paper.md` | `other` / `ml` 等 |

#### 2.5.3 Claim 节点必填字段

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | string | 格式：`CLAIM-<n>_<short>` | 唯一标识，编号顺序递增 |
| `claim_statement` | string | 原子化、单命题 | 主张陈述 |
| `evidence_strength` | enum | [DIRECT, INDIRECT, CORRELATIONAL, INTERPRETATION] | 证据强度 |
| `claim_type` | enum | [empirical_result, author_interpretation, methodological] | 主张类型 |
| `supporting_papers` | array | 至少 1 个 | 支持证据（每项含 paper + statistic + evidence_id） |
| `contradicting_papers` | array | 0+ | 反对证据 |
| `boundary_conditions` | array | 0+ | 限定条件 |
| `status` | enum | [candidate, promoted, active, deprecated] | 状态（见 §2.5.10） |

#### 2.5.4 Topic 节点必填字段

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | string | 格式：`<topic-key>` | 主题标识（小写，连字符分隔） |
| `topic_description` | string | 一段话 | 主题描述 |
| `involved_papers` | array | 至少 1 个 | 涉及论文 |

#### 2.5.5 Synthesis 节点必填字段

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | string | 格式：`<question-key>` | 问答标识 |
| `question` | string | 必填 | 用户原问题 |
| `conclusion` | string | 一段话直接回答 | 综合结论 |
| `key_evidence_chain` | array | 至少 1 条 | 关键证据链 |
| `evidence_strength` | enum | [STRONG, MODERATE, WEAK, CONFLICTED, INSUFFICIENT] | 证据强度 |

#### 2.5.6 数值字段约束（通用）

| 字段 | 范围 | 说明 |
|---|---|---|
| `p_value` | [0, 1] | p 值 |
| `n` / `sample_size` | 正整数 | 样本量（>0） |
| `r` / `correlation` | [-1, 1] | 相关系数 |
| `beta` | 实数 | 回归系数 |
| `effect_size` | 实数 | 效应量（Cohen's d, η² 等） |
| `percentage` | [0, 100] | 百分比 |
| `confidence_interval` | [low, high] | 置信区间，low < high |
| `t_statistic` | 实数 | t 值 |
| `f_statistic` | 实数（≥0） | F 值 |

**校验失败处理**：标 `FLAGGED`，写入 log，提示用户。

#### 2.5.7 Evidence 必填字段

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `evidence_id` | string | 唯一（如 E001） | 证据 ID |
| `section` | string | §X.Y | 原文章节锚点 |
| `quote` | string | 在 full.md 中可 grep | 原文引用 |
| `relation` | enum | [SUPPORT, CONTRADICT, QUALIFY, NEUTRAL] | 与 CLAIM 的关系（见 §2.5.8） |
| `verification` | enum | [EXPLICIT, NOT_REPORTED, UNCERTAIN, INFERRED] | 证据状态（见 §2.5.9） |
| `value` | string/number | 可选 | 数值（与 quote 对应） |
| `claim` | string | 必填 | 关联的 CLAIM ID |

#### 2.5.8 RELATION 字段（CLAIM/EVIDENCE 关系）

| 值 | 含义 | 严格条件 |
|---|---|---|
| `SUPPORT` | 直接支持 | 有显著 p < .05 / 等价统计证据 |
| `CONTRADICT` | 直接反驳 | 有显著反向证据 |
| `QUALIFY` | 在限定条件下支持 | 报告了限定条件 |
| `NEUTRAL` | 提及无立场 | 论文中提到但不评价 |

#### 2.5.9 Evidence 状态枚举

| 值 | 含义 | 校验处理 |
|---|---|---|
| `EXPLICIT` | 原文直接报告 | ✅ 通过 |
| `NOT_REPORTED` | 原文未提及 | ⚠️ 必须明确写，**不允许猜测** |
| `UNCERTAIN` | 原文间接暗示 | ⚠️ 标 UNVERIFIED，提示用户 |
| `INFERRED` | 模型推断 | ⚠️ **不能伪装成事实**，标 FLAGGED |

#### 2.5.10 CLAIM 状态枚举（生命周期）

| 状态 | 形式 | 触发 | 升级操作 |
|---|---|---|---|
| `paper-inline` | 论文节点 `**核心主张**` 中 `[new claim]` | 默认（单论文首次出现） | — |
| `candidate` | 论文节点 `**核心主张**` 中 `关联: [candidate]` | 三选一条件（见 §2.5.11） | — |
| `promoted` | `claims/CLAIM-XXX.md`，`status: promoted` | 用户确认升级 | 创建 claims/ 节点 + 双向更新 wikilink |
| `active` | `claims/CLAIM-XXX.md`，`status: active` | 多次使用 + 验证后 | 标记为活跃 |

**注意**：状态升级时**保留**论文节点中的 inline CLAIM（仅改 `关联:` 为 `[[CLAIM-XXX]]`）。

#### 2.5.11 CLAIM 升级的三选一触发条件

满足下列**任一**条件即可升级为 `claims/CLAIM-XXX.md`：

1. **有张力**：同一主张存在 SUPPORT / CONTRADICT / QUALIFY 中的至少两种关系
2. **被查询**：用户明确追踪或提问过该主张
3. **可综合**：该主张是某个 synthesis 问题的直接前提

#### 2.5.12 evidence_strength 枚举

| 值 | 含义 |
|---|---|
| `direct` | 实验直接测量 |
| `indirect` | 间接证据 |
| `correlational` | 相关分析 |
| `interpretation` | 作者解读 |

---

## 3. CLAIM / EVIDENCE / RELATION 逻辑

这一层是 wiki **与普通 PPT 笔记最大的差异**，必须强制保留。

### 3.1 CLAIM 字段语法

在论文节点的 `**核心主张**` 字段下：

```markdown
**核心主张**

1. **CLAIM-001** [author_claim / system_inferred] [evidence_strength] — 一句话陈述
   - 依据: §X.Y, p.Z
   - 类型: empirical_result / author_interpretation
   - 关联: [[CLAIM-001_WM_Reading]]（如已存在）或 [new claim]

2. **CLAIM-002** [author_interpretation] [interpretation] — 解读性陈述
   - 依据: §4.1, p.7
   - 关联: [new claim]
```

- `author_claim`：作者明确提出
- `system_inferred`：你从论文中推断但作者未明说
- `evidence_strength`：`direct` / `indirect` / `correlational` / `interpretation`
- `empirical_result`：作者通过实验/分析**实际观察到**的
- `author_interpretation`：作者**认为这意味着什么**

### 3.2 EVIDENCE 字段语法

在论文节点的 `**证据条目**` 字段下：

```markdown
**证据条目**

- [EVID-001] claim: CLAIM-001 | relation: SUPPORT | section: §3.2 | quote: "r=.42, p<.001, n=120"
- [EVID-002] claim: CLAIM-001 | relation: NEUTRAL | section: §4.1 | quote: "作者认为⋯"
- [EVID-003] claim: CLAIM-002 | relation: SUPPORT | section: §4.1 | quote: "这一关系⋯"
```

关系类型（仅 4 种）：
| 关系 | 含义 |
|---|---|
| `SUPPORT` | 支持该主张 |
| `CONTRADICT` | 反驳该主张 |
| `QUALIFY` | 在某些条件下支持/限定 |
| `NEUTRAL` | 提及但无明确立场 |

### 3.3 何时创建独立主张节点（claims/）

**懒创建**。条件：
- 一条主张在 2+ 篇论文中出现（最常见）
- 一条主张用户明确要追踪

否则只在论文节点里记录。

---

## 4. wikilink 约定

### 4.1 链接语法

- 论文节点之间：`[[Smith_2020_WM_Reading]]` → 指向 `papers/Smith_2020_WM_Reading.md`
- 主题节点：`[[fnirs-mci-screening]]` → 指向 `topics/fnirs-mci-screening.md`
- 主张节点：`[[CLAIM-001_WM_Reading]]` → 指向 `claims/CLAIM-001_WM_Reading.md`
- 综合节点：`[[executive-function-development]]` → 指向 `syntheses/executive-function-development.md`

### 4.2 链接风格

- 用**页面名**而非路径：`[[Smith_2020_WM_Reading]]` 而不是 `[[papers/Smith_2020_WM_Reading]]`
- Obsidian 自动解析短链

### 4.3 双向链接维护

每次写入新节点：
1. 新节点自身列出反向链接清单（`关联主题`、`关联主张`、`引用本论文的页面` 等）
2. 同步更新相关节点，把新节点 wikilink 加进去

---

## 5. 工作流

### 5.1 摄入新论文

用户输入示例：
> "处理 <zotero-md>/7统计学习/机器学习/2020_Smith_NeuroImage_Title.pdf"

操作步骤：

1. **定位 full.md**：如果 PDF 在 zotero_mn 下，先检查 zotero_mn 是否有同名目录下的 full.md；若没有，提示用户先跑 MinerU。
2. **读全文** full.md。
3. **读 `index.md`**：找相关主题、已存在的主张。
4. **抽取论文节点**：
   - 写到 `00-pending/<Author>_<Year>_<short>.md`
   - **不直接**写 `papers/`
5. **检查重复**：用 `[^作者]` `[^年份]` `[^标题关键词]` 在 papers/ 下 grep，避免重复创建。
6. **关联主题**：在论文节点末尾写 `**关联主题**` 列出相关主题（如果主题节点已存在）；如不存在，**暂不创建主题节点**，仅记录候选主题名，等用户确认或主题聚集后再创建。
7. **更新 `index.md`**：把 pending 论文加入 `## 待审阅` 区。
8. **更新 `log.md`**：追加 `## [YYYY-MM-DD] ingest | paper-title` 一条。
9. **提示用户审阅**：列出 pending 文件路径，建议审阅后告诉 pi "移到 papers/"。

### 5.2 创建主题节点

触发条件：
- 用户明确说"建一个 xx 主题"
- 同一主题在 2+ 篇 pending/papers 中出现
- 用户提问关于某主题时

操作步骤：
1. 检查 `topics/` 下是否已有同名节点（避免重复）。
2. 创建 `topics/<key>.md`，按主题节点模板填字段。
3. 在所有相关论文节点 `**关联主题**` 中加上 `[[key]]`。
4. 更新 `index.md`、`log.md`。

### 5.3 创建主张节点（懒创建）

触发条件：
- 一个 claim 在 2+ 篇论文的 `**核心主张**` 中出现
- 用户明确说"这条 claim 跨论文追踪"

操作步骤：
1. 检查 `claims/` 下是否已存在该 claim。
2. 创建 `claims/CLAIM-<n>_<short>.md`，**CLAIM 编号顺序递增**（CLAIM-001, CLAIM-002, ...）。
3. 把所有相关论文节点 `**核心主张**` 中的 `关联: [[CLAIM-001_xxx]]` 链接更新。
4. 更新 `index.md`、`log.md`。

### 5.4 回答问题

用户输入示例：
> "WM 与阅读理解的证据是什么？"

操作步骤：
1. 读 `index.md` 找相关节点。
2. 读相关论文节点 + 主题节点 + 主张节点。
3. 用自然语言综合回答，**每条结论附 wikilink**。
4. 用户确认答案有价值 → 提示是否固化到 `syntheses/`。

### 5.5 健康检查（lint）

用户输入示例：
> "检查 wiki 状态"

检查项：
1. **孤立节点**：被引但 wikilink 反向不存在；或不被引且不在 index.md 中
2. **claim 无 quote**：`**核心主张**` 中 CLAIM 但 `**证据条目**` 中无对应 EVIDENCE
3. **重复主题**：两个主题名实指同一主题
4. **broken wikilink**：链向不存在的节点
5. **数值异常**：明显超出范围的统计值
6. **过时结论**：被新论文反驳但未更新

输出报告，不自动修复。

### 5.7 paper.md 创建流程（脚本辅助 + LLM 主导）

**设计原则**：
- paper.md 模板由用户提供（`references/templates/paper.md`）
- scripts/ 最多是辅助（文件复制、路径管理）
- LLM (pi) 主导内容生成

**scripts/ 自动（确定性）**：
1. `wiki ingest <pdf-path>` 复制用户模板到 `00-pending/<id>.md`
   - 替换最小占位：`{Title}` → `<id>`、`{modality}` → `unknown`
   - 加注释提示 LLM 任务
2. 路径管理：raw/<id>/full.md 存在性检查

**LLM 主导（语义理解）**：
1. LLM 读取 `raw/<id>/full.md`
2. LLM 按 §2.5 字段定义抽取 15 个字段
3. LLM 自由组织 body（不强求固定章节顺序）
4. LLM 用模板中的 `**xxx**` 字段名占位填入实际值
5. CLAIM 抽取按 §2.5.11（原子化 + 区分 finding vs interpretation）
6. LLM 运行 `wiki check-evidence --list` 输出待校验清单
7. LLM 校验数值上下文（理解 raw 中 quote 的语义，不只是 grep）

**scripts/ 输出的清单**（让 LLM 校验）：
```bash
$ wiki check-evidence --list Smith_2020_WM
# 待校验清单
Paper 中候选数值：
- "r=0.42" (§3.2)
- "p<0.001" (§3.2)
- "n=120" (§3.2)

raw 中相关候选位置（grep 模糊匹配）：
- raw/.../full.md:842: "correlation coefficient (r) was .42"
- raw/.../full.md:850: "p < .001"

→ LLM 读 raw 上下文，确认数值含义
```

**scripts/ 不做的（让 LLM 做）**：
- ❌ 自动 grep 验证数值
- ❌ 判断 CLAIM 是否原子化
- ❌ 判断 RELATION 语义正确性
- ❌ 判断 CLAIM 升级触发
- ❌ 语义检索（用 substring 搜索 + LLM 综合）

**完整流程**：
1. `wiki ingest <pdf>` — scripts 复制模板到 00-pending/
2. **LLM 读取 full.md + 模板** → 抽取 15 字段
3. `wiki check-evidence --list` — scripts 输出待校验清单
4. **LLM 校验数值上下文**
5. 用户审阅后移到 `papers/`
6. `wiki index` 重建 INDEX.md
7. `wiki status` 查看状态

---

## 6. 错误处理

| 错误 | 处理 |
|---|---|
| 找不到 full.md | 提示用户先跑 MinerU |
| 论文节点已存在 | 不覆盖；提示用户，建议 merge |
| 主题节点已存在但内容冲突 | 提示用户，决定 merge 或保留 |
| claim 已存在但内容冲突 | 写入 `relation: CONTRADICT`，提示用户 |
| 数值异常 | 标注 `FLAGGED`，写入 log，提示用户 |
| 引用编号找不到对应 reference | 标注 `UNVERIFIED`，跳过 |

---

## 7. 与原始层的衔接

### 7.1 full.md 引用

论文节点**不复制全文**。需要查原文时，用相对路径 wikilink：
- `[[../../edu/zotero_mn/.../full.md]]`（Obsidian 支持）

### 7.2 图片

- MinerU 提取的图片已自动同步到 `raw/<citekey>/images/`(T-W4-029:无中间层,不再拷贝到 assets/)
- 论文节点中直接引用 `![desc](raw/<citekey>/images/figure-x.png)`
- 只引用论文节点的图,不强制每个 EVIDENCE 都有图

---

## 8. 持续改进

每处理 5 篇论文，做一次自我回顾，提示用户：
- 字段是否够用 / 多余
- CLAIM 抽取粒度是否合适
- RELATION 类型是否够用
- wikilink 命名约定是否需要调整

**不要自动改 `AGENTS.md`**。这是配置文件，应由人审阅后修改。

---

## 9. 一句话总结

> **让 pi 把论文 PDF → 一张可追溯的证据图，靠 Obsidian wikilink 自然形成多对多关联，用户负责审阅与质疑**。
> 简单工具（Markdown + Obsidian + Git）做简单的事，剩下的留给人类判断。
