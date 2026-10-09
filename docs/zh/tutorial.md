# 教程 · 从零到第一个 evidence 节点的完整流程

> **目标:** 教程结束时,您将完成一篇论文的摄入、抽取、人工审阅、提升和查询。总耗时 ~20 分钟(加上 LLM 抽取的异步等待)。

**语言版本:** [English](../en/tutorial.md) | [中文](./tutorial.md)

---

## 前置依赖

- Python ≥ 3.10
- 可用的 LLM 端点(Claude / GPT / 任意 pi-coding-agent 模型)
- 可选:安装 [Obsidian](https://obsidian.md/) 用于可视化

---

## 第 0 步 · 安装 skill

```bash
git clone https://github.com/hasibagen/claimtrace.git
cd claimtrace
pip install -e .

# 验证 CLI 可用
./scripts/wiki --help
```

您应该看到子命令列表:`init`、`ingest`、`lint`、`check-evidence`、`search`、`status`、`index`、`archive`、`zotero`、`zotero-csv`。

---

## 第 1 步 · 创建您的 wiki

随便挑一个空目录作为 wiki 根。**不要**在 `claimtrace` 仓库本身里初始化——那里存放 skill 代码,不是您的数据。

```bash
mkdir ~/my-research-wiki
cd ~/my-research-wiki
wiki init
```

这会创建:

```
my-research-wiki/
├── AGENTS.md      # 11 条铁律(pi 自动加载)
├── index.md       # 自动重建的目录
├── log.md         # 仅追加的审计日志
├── paperinfo/     # 书目元数据
├── raw/           # 不可改的原始论文文本(MinerU 输出)
├── 00-pending/    # LLM 抽取后,等待您审阅
├── papers/        # 已发布的"这篇论文声称什么"节点
├── claims/        # 跨论文 claim
├── evidence/      # 具体证据(数字、引文)
├── syntheses/     # 长篇综合文档
└── topics/        # 主题落地页
```

> **铁律 #10 — HUMAN REVIEWS PENDING**。`00-pending/` 是一个缓冲带。LLM 写到这里,人工提升。您不会丢失工作,但也不会让原始 LLM 输出未经审阅就成为"正式"节点。

---

## 第 2 步 · 准备论文

您需要一篇 **Markdown** 形式的论文(MinerU 输出最理想)。本教程假设:

```
my-research-wiki/
└── raw/
    └── smith_2022_neuroimage/
        └── full.md
```

`smith_2022_neuroimage` 是 **citekey** —— 一个唯一的标识符,所有地方都用。命名约定:`<作者>_<年份>_<期刊简称或短标题>.md`。

> **铁律 #1 — RAW IS IMMUTABLE**。一旦 `full.md` 放入 `raw/`,您永远不修改它。所有 wiki 节点通过 `raw/<citekey>/full.md` 引用以提供出处。

如果您还没有论文,可以直接 `wiki ingest path/to/anywhere.md` —— 它会复制到 `raw/<citekey>/` 并创建 citekey。

---

## 第 3 步 · 摄入与抽取

### 3.1 · 初始化 pending 目录

```bash
wiki ingest raw/smith_2022_neuroimage/full.md
```

这会:
- 检测或询问 citekey(`smith_2022_neuroimage`)
- 创建 `00-pending/smith_2022_neuroimage/`
- 生成三个骨架文件:
  - `00-pending/smith_2022_neuroimage/smith_2022_neuroimage.md` (paper.md 骨架)
  - `00-pending/smith_2022_neuroimage/claims/*.md` (claim 骨架)
  - `00-pending/smith_2022_neuroimage/evidence/*.md` (evidence 骨架)

### 3.2 · 跑 LLM 抽取

`wiki` CLI 处理机械化步骤。**LLM 抽取** 最好在交互式 pi-coding-agent 会话里跑:

```
> /extract raw/smith_2022_neuroimage/full.md
```

这会触发 **4 阶段抽取流水线**:

| 阶段 | 做什么 | 耗时 |
|---|---|---|
| T1 · 扫描 | 读论文,识别节(引言/方法/结果/讨论) | ~30s |
| T2 · 抽取 | 每节生成 claim/evidence JSON 骨架 | ~5–8 min |
| T3 · Evidence | 给每条证据编号,加出处(页码、引文) | ~3 min |
| T4 · 审计 | 对抗式审问:LLM 是否捏造了数字? | ~2 min |

LLM 把所有东西写入 `00-pending/smith_2022_neuroimage/`。`papers/`、`claims/`、`evidence/` 都**没碰过**。

---

## 第 4 步 · 人工审阅(最关键的一步)

用编辑器打开 `00-pending/smith_2022_neuroimage/smith_2022_neuroimage.md`。它有 YAML frontmatter 和 Markdown 正文。

### 4.1 · 检查 frontmatter

```yaml
---
type: paper
citekey: smith_2022_neuroimage
title: "Smith et al. (2022). Functional connectivity in resting-state fMRI."
authors: [Smith, J., Doe, A.]
year: 2022
journal: NeuroImage
study_type: empirical_research
modality: fmri
paperinfo: "[[paperinfo/smith_2022_neuroimage]]"
raw_path: "raw/smith_2022_neuroimage/full.md"
claims:
  - "[[smith-2022-default-mode-network]]"
  - "[[smith-2022-test-retest-reliability]]"
related_evidence: []
---
```

核对:
- ✅ `citekey` 与目录名匹配
- ✅ `title`、`authors`、`year`、`journal` 与论文一致
- ✅ `study_type` 是 `empirical_research` / `methodology` / `review` / `meta_analysis` / `empirical_computational_modeling` 之一
- ✅ `modality` 匹配成像方式(fmri / eeg / fnirs / meg / multimodal / behavioral / other)
- ✅ `raw_path` 是从 wiki 根到 `full.md` 的**相对**路径

### 4.2 · 检查 claims

打开 `claims/` 下每个 claim 文件。模板见 [`references/templates/claim.md`](../../references/templates/claim.md)。claim 是**您的综合**,不是论文的结论。它应该是可证伪的。

```yaml
---
type: claim
id: smith-2022-default-mode-network
statement: |
  重度抑郁症患者与健康对照相比,默认网络(DMN)的功能连接降低。
authors: [Smith, J.]
year: 2022
status: pending
related_papers:
  - "[[smith_2022_neuroimage]]"
supports_evidence:
  - "[[smith-2022-dmn-fc-reduction]]"
qualifies_evidence: []
contradicts_evidence: []
---

## Reasoning

42 名患者 vs 38 名对照,DMN 内部连接降低(t = -3.45, p < 0.001),
FDR 校正后仍显著。控制头部运动后效应依然存在(平均 FD < 0.2 mm)。

## Sources

- Smith et al. (2022), NeuroImage, Results §3.2
```

### 4.3 · 检查 evidence

每个 evidence 文件有 **11 个数值校验字段**——样本量、检验方法、统计量、效应量、95% CI、df、p 值等。这是**铁律 #8 — EVERY NUMBER IS VERIFIABLE** 的字段。

例如 `evidence/smith-2022-dmn-fc-reduction.md`:

```yaml
verify_n: 80                # 总样本
verify_test_method: independent_samples_t_test
verify_test_stat_type: t
verify_test_stat_value: -3.45
verify_df: 78
verify_p_value: 0.0009
verify_effect_size_type: cohens_d
verify_effect_size_value: -0.62
verify_ci_95: [-0.95, -0.29]
prov_source_text: "DMN within-network FC was reduced in patients (t₇₈ = -3.45, p = 0.0009, d = -0.62)"
```

`wiki check-evidence` 脚本会在 `raw/smith_2022_neuroimage/full.md` 里 grep `prov_source_text` 并验证存在:

```bash
wiki check-evidence smith_2022_neuroimage
# ✅ smith-2022-dmn-fc-reduction: prov_source_text found verbatim (fuzzy match)
# ✅ 1/1 evidence verified
```

---

## 第 5 步 · 提升为"正式"节点

审阅完 pending 目录后,提升:

```bash
wiki promote smith_2022_neuroimage
```

这会**原子地**:

1. 把 `00-pending/smith_2022_neuroimage/papers/smith_2022_neuroimage.md` → `papers/smith_2022_neuroimage.md`
2. 把每个 claim → `claims/<slug>.md`
3. 把每个 evidence → `evidence/<slug>.md`
4. 自动渲染 body 表格(`## 数值校验` / `## 支持的 Claim`)
5. 更新相关论文的反向链接

`00-pending/` 目录留着空(或您可以删除)。

---

## 第 6 步 · Lint

```bash
wiki lint
```

跑 **4 层 lint**(L0 → L3):

| 层 | 内容 | 机械化? |
|---|---|---|
| L0 Structure | 文件命名、目录布局、frontmatter 必填字段 | ✅ 脚本 |
| L0.5 Type | 所有 `type:` 字段是合法 enum | ✅ 脚本 |
| L1 Evidence | 每条 evidence 有全部 11 个 verify_* 字段(填或 null) | ✅ 脚本 |
| L1.5 Schema | 对 `scripts/schemas/*.json` 的 JSON-Schema 校验 | ✅ 脚本 |
| L2 Semantic | claims 可证伪,evidence → paper 反向链接存在 | ✅ 脚本 + LLM |
| L3 Consistency | frontmatter 里的数字在 `raw/full.md` 中可 grep | ✅ 脚本(grounding) |
| L4.6 Edges | 所有边有类型(`supports`/`contradicts`/`qualifies`) + 置信度 | ✅ 脚本 |

干净的 wiki 应该看到 `0 errors`。

---

## 第 7 步 · 查询

现在您有节点了,可以查:

```bash
wiki search "default mode network depression"
```

或者在 pi-coding-agent 里用 slash-command:

```
> /query evidence for "DMN FC reduction in major depression"
```

返回 `evidence/*.md` 中 `interp_text`、`prov_source_text`、`tags` 匹配的所有文件。

---

## 第 8 步 · 可视化(Obsidian)

把 `my-research-wiki/` 作为 vault 在 Obsidian 打开。

- **graph view** 显示 `paper → claim ← evidence` 链接
- 每个 `[[wikilink]]` 可点击
- `tag:#dm` 或 `tag:#fmri` 按标签分组
- `tag:#needs-review` 显示还在 pending 的内容

---

## 下一步?

| 您想 …… | 用 |
|---|---|
| 跨论文追踪 claim | [`/claim`](./micro-skills.md#claim) |
| 把书目拉进 `paperinfo/` | [`/sync`](./micro-skills.md#sync) |
| 找重复 claim | [`/stitch`](./micro-skills.md#stitch) |
| 对一篇论文做对抗式审阅 | [`/audit`](./micro-skills.md#audit) |
| 搭主题落地页 | [`/topic`](./micro-skills.md#topic) |
| 加自定义成像方式模板 | 编辑 `references/templates/paper-*.md` |
| 用别的模型重抽 | `pi -p "extract this paper, 8 evidence" --provider <x> --model <y>` |

想深入理解,读 **[`architecture.md`](./architecture.md)**。

---

## 常见坑

1. **忘记 grep 数字**。`wiki check-evidence` 不是可选的。如果脚本在 `raw/full.md` 中找不到您的 `prov_source_text`,数字就是未经验证的。
2. **把 claim 当作论文结论的改写**。claim 是*您的*综合,通常跨多篇论文。论文结论在 `papers/<citekey>.md`,不在 `claims/`。
3. **编辑原始 `full.md`**。绝对不行。铁律 #1。如果 MinerU 出错,在 pending paper.md 里留 `note:`。
4. **LLM 直接写到 `papers/`**。铁律 #10。所有东西先进 `00-pending/`。
5. **忘记 commit**。这是 git。每次提升都是值得 commit 的事件。

---

## FAQ

**Q: 不用 Obsidian 能用吗?**
A: 可以。Obsidian 只是渲染器。wiki 是纯 Markdown + YAML。

**Q: 不用 pi-coding-agent 能用吗?**
A: 可以。`wiki` CLI 处理所有机械化步骤。您也可以手动驱动抽取——见 [`scripts/wiki_lint.py`](../../scripts/wiki_lint.py) 了解校验流水线。

**Q: 为什么要 Markdown 而不是 SQLite?**
A: 铁律 #2。Markdown 在 git 里可 diff,在 Obsidian 里可渲染,可到处导出。SQLite 查询快但审计是黑盒。ClaimTrace 优化**可审计性而非速度**。

**Q: wiki 能长多大?**
A: 测试 wiki 有 192 篇论文、870 个 claim、1154 个 evidence 节点,lint < 30s。线性扩展。如果有性能问题,瓶颈通常是 `wiki_render_evidence_body`,会重写每个 evidence 文件——可以收窄到只改变化的文件。

**Q: 能直接从 Zotero 导入吗?**
A: 可以。`wiki zotero list-workspaces` 显示您的 Zotero 库;`wiki zotero sync --collection <name>` 把书目元数据拉进 `paperinfo/`。全文需要单独从 MinerU 来。

**Q: 怎么引用这个 skill?**
A: 见 README 的 Citation 章节。