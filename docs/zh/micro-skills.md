# 9 个 Micro-Skills

> 每个 micro-skill 都是一个专业化的 wiki 操作子例程。在 pi-coding-agent 里通过 slash-command 调用。

**语言版本:** [English](../en/micro-skills.md) | [中文](./micro-skills.md)

---

## 1. `wiki-extract-paper` · `/extract`

**做什么:** 在一篇 `full.md` 上跑 5 阶段抽取流水线。

**何时用:**
- 有新论文要摄入
- 很久以前抽取过一篇,想深度重抽
- 用户说:"处理这篇论文"、"/extract full.md"、"extract this paper"

**模式:**

| 模式 | 适用 | 耗时 |
|---|---|---|
| `quick-scan` | 综述论文 / 方法学论文 | ~1–2 min |
| `deep-read` | 需要引用的实证论文 | ~5–10 min |
| `audit` | 重新审视旧抽取 | ~3–5 min |

**示例:**

```
> /extract raw/zhang_2021_fnirs/full.md --mode deep-read
```

**不适用:** 创建单条 evidence(用 `wiki-build-evidence`),搜索 wiki(用 `wiki-query-evidence`)。

---

## 2. `wiki-build-claim` · `/claim`

**做什么:** 创建一个 claim(原子命题),可能跨多篇论文。

**何时用:**
- 您发现同一发现出现在 3 篇论文里,想要一个规范 claim
- 用户说:"建一个 claim"、"/claim"、"this is a cross-paper finding"

**输出:** `claims/<semantic-slug>.md`(无内部编号,优先中文 + 真实空格)。

**Frontmatter 锚点:**

```yaml
type: claim
statement: |
  <一个可证伪的命题>
claim_type: empirical_result
atomic: true
scope_species: human
scope_n: 80
scope_age_mean: 35
scope_condition: major_depressive_disorder
reasoning: <为什么这个 claim 可辩护>
reasoning_type: cross_paper_synthesis
related_papers: [[paper1]], [[paper2]]
supports_evidence: [[ev1]], [[ev2]]
qualifies_evidence: [[ev3]]
contradicts_evidence: []
```

**不适用:** 读/回答问题(用 `wiki-query-evidence`),跨论文合并已有 claims(用 `wiki-stitch-knowledge`)。

---

## 3. `wiki-build-evidence` · `/evidence`

**做什么:** 把论文里一个具体的引文/数字提升为类型化 evidence 节点。

**何时用:**
- 找到一个值得追踪的数字/引文
- 用户说:"这是事实"、"/evidence"、"promote this to evidence"

**输出:** `evidence/<author>-<year>-<slug>.md`

**必填 frontmatter(铁律 #8 — EVERY NUMBER IS VERIFIABLE):**

```yaml
fact_type: empirical_result   # 或 observation / methodology
observation: |
  <verbatim 引文,≥20 字符>
interp_text: |
  <用平实语言您的解读>
prov_paper: "[[smith_2022_neuroimage]]"
prov_section: "Results §3.2"
prov_page: 6
prov_source_text: "DMN FC was reduced (t₇₈ = -3.45, p = 0.0009, d = -0.62)"
verify_n: 80
verify_test_method: independent_samples_t_test
verify_test_stat_type: t
verify_test_stat_value: -3.45
verify_df: 78
verify_p_value: 0.0009
verify_effect_size_type: cohens_d
verify_effect_size_value: -0.62
verify_ci_95: [-0.95, -0.29]
verify_p_method: frequentist
```

**验证:**

```bash
wiki check-evidence smith-2022-dmn-fc-reduction
# ✅ prov_source_text found verbatim in raw/smith_2022_neuroimage/full.md (fuzzy match)
```

---

## 4. `wiki-build-topic` · `/topic`

**做什么:** 创建主题落地页(内容地图),聚合相关 claims。

**何时用:**
- 2+ 篇论文共享一个主题
- 用户说:"建主题"、"/topic default mode network"、"tag this with #dm"

**懒创建规则:** 不到 ≥2 个相关 claim 时不要创建主题。主题是*聚合视图*,不是数据节点——它们只组织引用。

**输出:** `topics/<topic-slug>.md`

**Frontmatter:**

```yaml
type: topic
name: "默认网络(Default Mode Network)"
tags: [fmri, depression, dm]
related_claims:
  - "[[smith-2022-dmn-fc-reduction]]"
  - "[[doe-2020-dmn-altered-connection]]"
related_evidence: []
related_papers:
  - "[[smith_2022_neuroimage]]"
  - "[[doe_2020_jneurosci]]"
```

**不适用:** 单论文组织(用 `paper.md` 里的主题相关字段),创建 claims/evidence。

---

## 5. `wiki-query-evidence` · `/query`

**做什么:** 通过读已有 claim + evidence + topic + synthesis 节点来回答研究问题。

**何时用:**
- "X 的证据?" / "What evidence for X?"
- "DMN 在抑郁里怎么变?"
- 用户说:"/query"、"/ask"

**流水线:**

1. 读 `index.md` 找候选节点
2. 读候选的 `evidence/*.md` 和 `claims/*.md`
3. 构建 Evidence × Claim 矩阵
4. 生成综合答案
5. 可选地持久化为 `syntheses/<question-slug>.md`

**示例:**

```
> /query "DMN functional connectivity reduction in major depression"
```

输出:
```
找到 3 篇论文 / 5 条 evidence / 2 个 claims / 1 个 topic 匹配。

Evidence:
  ✅ smith-2022-dmn-fc-reduction (Smith 2022, NeuroImage): t=-3.45, d=-0.62, n=80
  ✅ doe-2020-dmn-altered (Doe 2020, J Neurosci): β=-0.31, p<0.001, n=120
  ⚠️  chen-2018-dmn-review (Chen 2018, meta): 叙事综述,无效应量

Claims:
  ✅ smith-2022-default-mode-network: "DMN FC reduced in MDD vs HC"
  ⚠️  doe-2020-dmn-heterogeneity: "DMN effect varies by depression subtype"

Topics: topic/dm-network.md (默认网络)
```

**不适用:** 创建新节点。

---

## 6. `wiki-lint-wiki` · `/lint`

**做什么:** 跑 4 层 lint 检查,不写入。

**何时用:**
- 提升一篇论文后
- commit 之前
- 用户说:"/lint"、"检查 wiki"、"lint"

**各层:**

| 层 | 内容 | 机械化? |
|---|---|---|
| L0 | 文件命名 + 目录布局 | ✅ |
| L0.5 | `type:` enum | ✅ |
| L1 | Evidence 11 个 verify_* 字段 | ✅ |
| L1.5 | JSON-Schema | ✅ |
| L2 | 语义关系 + LLM 判定 | 混合 |
| L3 | Grounding grep 到 `raw/` | ✅ |
| L4.6 | 类型化边 + 置信度 | ✅ |

**示例:**

```bash
wiki lint
# L0: 0 errors
# L0.5: 0 errors
# L1.5: 0 errors
# L2: 0 errors
# L3: 332 errors (all: raw/<filename> missing — needs MinerU re-extraction)
# L4.6: 0 errors
```

**按层过滤:**

```bash
wiki lint --layer L3
wiki lint --layer L0.5,L1.5
```

---

## 7. `wiki-zotero-sync` · `/sync`

**做什么:** 把 Zotero 库同步到 wiki 的 `paperinfo/` 目录。

**何时用:**
- 您在 Zotero 里加了论文,想拉进 wiki
- 用户说:"/sync"、"zotero 同步"、"pull new papers"

**流水线:**

1. 读 `~/Zotero/zotero.sqlite`(不走网络)
2. 匹配 citekeys(Zotero item key → wiki citekey)
3. 新论文创建 `paperinfo/<citekey>.md`
4. 已有的,用 `zotero-lastmod` 指纹增量更新
5. 标记冲突供人工审阅

**示例:**

```
> /sync collection="twin-brain"
```

输出:
```
在 Zotero collection "twin-brain" 找到 158 篇论文
  - 142 已在 wiki(未变)
  -  11 新建(创建了 paperinfo/*.md)
  -   5 更新(lastmod 比 wiki 新)
  -   0 冲突
```

---

## 8. `wiki-stitch-knowledge` · `/stitch`

**做什么:** 找并合并跨论文重复的 claims。

**何时用:**
- 一批抽取之后
- 怀疑两个 claim 说的是同一件事
- 用户说:"/stitch"、"去重"、"merge similar claims"

**流水线:**

1. 给所有 `claims/*.md` 做 embedding(语义向量)
2. 找余弦相似度 > 0.85 的簇
3. LLM 判断每对是否*语义等价*(不只是相似)
4. 合并:挑规范 claim, 通过 `same_claim_as` 边连接 evidence
5. 更新 `verify_supporting_count` / `verify_contradicting_count`

**关键:** 用 **LLM 判断**,不用字符串匹配。"DMN reduced in depression" 和 "Depression shows lower DMN connectivity" 即使文字不同也能被检测为重复(铁律 #4 — NO REGEX ON MEANING)。

---

## 9. `wiki-audit-paper` · `/audit`

**做什么:** 对一篇论文/节点做批判性对抗式审阅。超出 L4.6 机械 lint。

**何时用:**
- 想挑战某论文的 claims
- 30 天复检
- 用户说:"/audit"、"审阅"、"challenge this"

**流水线:**

1. 加载论文 + 它所有 claims + evidence
2. 跑 8–10 个固定对抗式问题:
   - claims **可证伪**吗?
   - 每个数字在 raw 中能 **grep** 吗?
   - **边类型**正确吗?(应该是 `qualifies` 的 `contradicts`?)
   - **scope** 一致吗?(说"人类"的 claim,但 evidence 来自"大鼠"?)
   - LLM 抽取是否**遗漏**了不同意的发现?
   - **provenance 页码**正确吗?
   - **样本量**在 claim 和 evidence 间一致吗?
   - **论文结论**是否漏到 claim 节点?(铁律 #9)
3. 把答案 + 可选的 **我的判断** 段写到 `audit_report.md`

**示例:**

```
> /audit papers/zhang_2021_fnirs.md
```

输出:
```
审计报告: zhang_2021_fnirs.md
  ✅ Claims 可证伪
  ✅ 所有数字在 raw 中可 grep 验证
  ⚠️  E3 的 verify_df=null 但论文报告 F(2,38)=4.51(df 未抽取)
  ⚠️  C2 把"统计显著性"等同于"实际显著性"
  ✅ 无论文结论泄漏
  → 审计文件: 00-pending/zhang_2021_fnirs/audit.md
```

---

## 速查表

| Skill | Slash | 写入? | LLM? | 耗时 |
|---|---|---|---|---|
| `wiki-extract-paper` | `/extract` | 是 | 是 | 5–10 min |
| `wiki-build-claim` | `/claim` | 是 | 是 | ~30s |
| `wiki-build-evidence` | `/evidence` | 是 | 是 | ~30s |
| `wiki-build-topic` | `/topic` | 是 | 是 | ~30s |
| `wiki-query-evidence` | `/query` | 可选 | 是 | ~1 min |
| `wiki-lint-wiki` | `/lint` | 否 | 部分 | < 30s |
| `wiki-zotero-sync` | `/sync` | 是 | 否 | ~5s |
| `wiki-stitch-knowledge` | `/stitch` | 是 | 是 | ~2 min |
| `wiki-audit-paper` | `/audit` | 是 | 是 | ~2 min |
## 10 · `wiki-extract-modeling` — `/modeling` · 建模拆解

**触发:** `建模拆解 [论文]` / `/modeling <citekey>` —— 面向建模类论文(训练-验证-测试协议重要时)。

**做什么:** 深读*训练-验证-测试协议*:数据划分、泄漏控制、评估指标、基线。在 paper
节点产出 `## 建模拆解` 章节(mermaid 流水线图 + 三层讲解 + 红旗),并落对应
claims/evidence。

**何时用:** 仅建模类论文(关键词 + 排除式筛选,如排除协议平凡的纯解码论文)。
建模论文登记表满 5 篇后形成主题。
