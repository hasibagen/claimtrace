# Markdown 风格约束 (Markdown Style Constraints)

> **目的**: 减少 `**` 在 Wiki 节点中的滥用, 避免 Obsidian 渲染错乱 + LLM 抽取歧义
> **优先级**: ⭐⭐⭐ (高 — 所有 LLM 抽取任务必须遵循)
> **适用范围**: papers/, claims/, topics/, syntheses/, paperinfo/ 5 类节点

---

## 1. 背景

`**bold**` 是 Markdown 标准粗体语法, 但在以下场景会出问题:

| 场景 | 问题 | 后果 |
|---|---|---|
| YAML 多行字符串块 (`\|` / `>`) | `**` 与后续中文混排, 视觉杂乱 | LLM 后续抽取时易混淆 |
| 表格行内 | 跟 markdown 表格语法 `\|...\|` 冲突 | 渲染时部分粗体化 |
| wikilink `[[...]]` 周围 | `[[**paper**/xx]]` Obsidian 解析失败 | 反向链接断裂 |
| 列表项内 | `**Foo** [bar]` 跨多行解析错位 | 字段错位 |

**根本原则**: 粗体强调只在**单行**里用, 多行结构化字段用**子标题 / 列表 / 引用块**。

---

## 2. ** 允许/禁止矩阵

### ✓ 允许 (单行)

```markdown
**元信息**              ← 章节标题 (单行)
- **作者**: Smith et al.       ← 表格行单行
- **年份**: 2024
**首次出现**            ← 章节标题
**支持证据**
- 引用: `paper.md` §3.2     ← 行内行首单行
```

### ✗ 禁止 (多行/嵌入)

```yaml
# YAML 多行字符串块 (research-question, hypothesis, abstract 等)
research-question: |
  通过把连接组 (connectome) 作为**模型先验 (prior) 的参数**纳入  ← ❌
  摊销推断 (amortized inference) 框架, 配合**跨编码器 (cross-coder)**    ← ❌
  生成**群体级连接组先验**, 可实现: - 训练阶段匿名          ← ❌
```

```markdown
| 字段 | 值 |                          ← ❌ 表格行内
| 摘要 | 本研究**首次**证明 ... |
```

```markdown
[[**paperinfo/smith_2024**]]        ← ❌ wikilink 内
```

---

## 3. 替代方案

### 3.1 强调术语 → 用 `_斜体_`

```yaml
research-question: |
  通过把连接组 (connectome) 作为 _模型先验 (prior) 的参数_ 纳入
  _摊销推断 (amortized inference)_ 框架, 配合 _跨编码器 (cross-coder)_
  生成 _群体级连接组先验_, 可实现:
  - 训练阶段匿名 (只用群体均值+协方差)
  - 推断阶段个性化 (每位受试者生成特定 connectome)
```

**理由**: `_xxx_` 在 YAML 多行字符串里是字面量, Obsidian 渲染为斜体, 视觉清晰且不破坏 YAML。

### 3.2 强调重要词 → 用括号注释

```yaml
abstract: |
  本文提出 _cohort-amortized personalization_ (CAP, 群体摊销个性化) 框架.
  解决 VBT 临床转化的两个核心障碍: (a) 隐私 / (b) 计算.
```

**理由**: 首次出现的术语给中英对照, 后续直接使用。

### 3.3 段落强调 → 用空行 + 列表

```yaml
main-findings: |
  ## 关键结果 (用空行分段)
  
  CAP 在 21 例癫疖患者中:
  - 个体化 regional variability 预测发作起始与传播
  - F1 = 0.56
  
  CAP 在 832 例 1000BRAINS 受试者中:
  - structural disconnection 解释 modified resting state
  - predicted age r = 0.44
```

**理由**: YAML 字符串里支持 `#` (注释, 但会丢失), 用空行 + `-` 列表结构化。

### 3.4 引用原文 → 用 `>` 块引用

```yaml
quote: >-
  "We introduce cohort-amortized personalization (CAP), which replaces
  data sharing with model sharing: a neural density estimator is trained
  on simulations from a mechanistic whole-brain model under a low-rank
  cohort prior."
```

**理由**: 块引用是 YAML/双链都尊重的语法, Obsidian 渲染清晰。

### 3.5 表格内 → 用换行或子列表

```markdown
**元信息**

- 作者: Smith et al.
- 年份: 2024
- DOI: [10.xxxx](https://doi.org/10.xxxx)
  - 重要: 这是 _首次_ 验证 X
```

**理由**: 表格行改用 `-` 列表, 每字段独占一行。

---

## 4. LLM 抽取时的心智模型

LLM 在抽取 L2/L3 字段时, 应按以下心智模型:

```
1. 字段是 YAML 多行字符串块 (|) → 全文不用 **
2. 字段是单行 → 可用 **字段名**:
3. 章节标题 → 单行用 **
4. 表格行 → 不在 | ... | 表格里写多行
5. 引文 → 用 > 块引用
```

### 反例 → 正例对照

❌ 反例 (YAML 块内滥用 `**`):
```yaml
hypothesis: |
  通过 **cohort-amortized personalization (CAP)** 框架:
  (1) **CrossCoder**: 跨 20 种 atlas ...
```

✓ 正例:
```yaml
hypothesis: |
  通过 _cohort-amortized personalization (CAP)_ 框架:
  (1) _CrossCoder_: 跨 20 种 atlas ...
```

❌ 反例 (表格行):
```markdown
| 摘要 | 本研究**首次**证明 X |
```

✓ 正例:
```markdown
## 摘要

本研究 _首次_ 证明 X (见 §3.2)
```

---

## 5. AGENTS.md 集成规则

在 `references/AGENTS.md` §2 字段规范中, 增加一条:

```
### 2.x Markdown 风格约束

所有 Wiki 节点必须遵循 `references/markdown-style.md` 定义的格式约束:

- YAML 多行字符串块 (`|`) 内禁止 `**` 加粗 → 用 `_斜体_`
- 表格行内 (`|...|`) 禁止 `**` → 用列表结构
- wikilink `[[...]]` 内部禁止 `**` → 反向链接会断裂
- 章节标题 (单行) 允许 `**` → `**元信息**` 风格
- 元信息表格行 (`- **字段**: 值`) 允许 `**` → 单行格式
```

---

## 6. 检测与 lint 脚本

未来可在 `wiki lint` 中加 L4.5 (markdown 风格) 检查:

```python
# 伪代码
for md_file in wiki_root.glob("papers/*.md"):
    text = read_text(md_file)
    # 找 YAML 多行字符串块 (| 或 |-) 中的 **bold**
    in_yaml_block = False
    for line in text.split("\n"):
        if line.startswith(("research-question:", "hypothesis:", "abstract:", "main-findings:")):
            in_yaml_block = True
        elif in_yaml_block and line.startswith("---"):
            in_yaml_block = False
        elif in_yaml_block and "**" in line:
            warn(f"YAML block 中使用 **bold**: {line}")
```

---

## 7. 改造清单

按本约束需要改造的文件:

| 文件 | 问题 | 改造 |
|---|---|---|
| `baldy_2026_lect_notes_comput_sci.md` | YAML 块内 14 处 `**` | `_xxx_` 替换 |
| `esmaeili_2026.md` | YAML 块内 28 处 `**` | `_xxx_` 替换 |
| `falcon_2016_curr_opin_neurol.md` | YAML 块内 10 处 `**` | `_xxx_` 替换 |
| `10 个 CLAIM-XXX_*.md` | 主张陈述行内 `**` | 部分替换 |
| `references/templates/paper.md` | 模板示例含 `**` | 改用 `_xxx_` |
| `references/templates/claim.md` | 模板示例含 `**` | 改用 `_xxx_` |
| `wiki zotero.py` PAPER_TEMPLATE | `**` 字段内字面量 | 改 `_xxx_` |

**保持 `**` 的场景** (合规):
- 单行章节标题: `**元信息**`, `**研究目的**`
- 单行元信息: `- **作者**: Smith`
- 单行表格头: `| 字段 | 值 |`

---

## 8. 总结

| 之前 | 之后 |
|---|---|
| `**模型先验 (prior) 的参数**` (YAML 块) | `_模型先验 (prior) 的参数_` |
| `**首位字母大写**` (中文长句) | `_首位字母大写_` |
| 表格内 `\| 摘要 \| 本研究**首次** ... \|` | 列表 `## 摘要\n\n本研究 _首次_ ...` |
| wikilink `[[**paper**/x]]` | `[[paper/x]]` 或 `[[paper/_x_]]` |

**统一原则**: 多行结构 → 用 `_xxx_` 斜体; 单行表格/标题 → 可用 `**xxx**` 粗体。
