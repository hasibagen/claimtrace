# Zotero→Paper MD Bridge 设计文档

> **生成时间**: 2026-08-20
> **状态**: 设计确认，待实施
> **核心目标**: 从 Zotero SQLite 自动生成 Evidence Wiki 的 Paper 节点骨架

---

## 1. 问题陈述

### 1.1 现状

- 用户有 **13,850 篇 journalArticle** 存储在 Zotero（`~/Zotero/zotero.sqlite`）
- BBT 已安装，**citationKey 已存在**（15,397 条）
- Evidence Wiki 架构已设计（v4），有详细的模态 schema（fMRI/EEG/fNIRS 等）
- **但目前 Paper 节点的元信息靠手填**，没有自动化管道

### 1.2 目标

1. **自动从 Zotero 生成 Paper 节点骨架**（YAML frontmatter + 可读元信息段 + 正文骨架）
2. **按 Collection 粒度生成**（不是全量，用户选择 Collection）
3. **增量同步**（只处理新增论文，不覆盖已有内容）
4. **Zotero 元数据 immutable**（AI 不可修改 frontmatter）

---

## 2. 数据源分析

### 2.1 Zotero SQLite Schema（关键表）

```
items (itemID, itemTypeID, key, dateAdded, dateModified, libraryID)
  ↓
itemData (itemID, fieldID, valueID)
  ↓
itemDataValues (valueID, value, valueNormalized)
  ↓
fields (fieldID, fieldName)

itemCreators (itemID, creatorID, creatorTypeID, orderIndex)
  ↓
creators (creatorID, firstName, lastName)
  ↓
creatorTypes (creatorTypeID, creatorType)

itemTags (itemID, tagID)
  ↓
tags (tagID, name)

itemAttachments (itemID, parentItemID, contentType, path)
collections (collectionID, collectionName, parentCollectionID)
collectionItems (collectionID, itemID)
```

### 2.2 可用字段覆盖率

| 字段 | 覆盖量 | 覆盖率 |
|---|---|---|
| journalArticle 总量 | 13,850 | 100% |
| BBT citationKey | 15,397 | ~100% |
| DOI | 13,981 | ~100% |
| abstractNote | 13,320 | ~96% |
| PMID | 4,711 | ~34% |

### 2.3 Collection 结构

用户有 **500+ 个 Collection**，按研究主题组织，主要类别：

- 模态类: `fnirs`(1700+), `eeg`(200+), `fmri`(100+), `eeg&fnirs`(408)
- 方法类: `机器学习`(573), `时频分析`(191), `溯源分析`(248), `微状态`(132)
- 主题类: `语言加工`(500+), `注意&认知控制`(394), `静息态`(437)
- 特殊类: `超扫描`(122), `儿童`(151), `孪生脑`(97)

---

## 3. Paper 节点结构设计

### 3.1 YAML Frontmatter（Zotero 元数据，immutable）

```yaml
---
# === Zotero 来源字段（CLI 自动生成，AI 不可修改） ===
id: Smith_2025_fMRI_lang              # = 文件名，唯一标识
citekey: Smith2025                     # BBT citation key
title: "Neural mechanisms of speech processing"
authors:
  - "Smith, J."
  - "Wang, L."
year: 2025
journal: "NeuroImage"
doi: "10.1016/j.neuroimage.2025.12345"
pmid: "39876543"                       # 可选，覆盖率 ~34%
volume: "289"
issue: "2"
pages: "120-135"
item_type: journalArticle
language: "en"
tags:                                  # Zotero 标签
  - fMRI
  - language
zotero_key: "ABCD1234"                 # Zotero item key
zotero_link: "zotero://select/library/items/ABCD1234"
collection: "eeg&fnirs"                # 所属 Collection

# === Wiki 状态 ===
modality: fmri                         # [fmri, eeg, fnirs, multimodal, stats, ml, other]
status: pending                        # [pending, extracted, verified]
created: 2026-08-20
updated: 2026-08-20
---
```

### 3.2 正文结构

```markdown
# Neural mechanisms of speech processing

**元信息**
- **作者**: Smith, J.; Wang, L.
- **年份**: 2025
- **期刊**: NeuroImage | Vol 289(2), pp. 120-135
- **DOI**: [10.1016/...](https://doi.org/10.1016/j.neuroimage.2025.12345)
- **PMID**: 39876543
- **Zotero**: [打开](zotero://select/library/items/ABCD1234)

**研究目的**

**被试**

**实验设计**

**实验范式**

**刺激材料**

**测量工具**

**数据分析**
> ![[paper_fmri]]

**结果**

**结论**

**核心主张**

**证据条目**

**关联主题**

**关联主张**

**引用本论文的页面**
```

### 3.3 字段分工

| 部分 | 来源 | 修改权限 |
|---|---|---|
| YAML frontmatter | Zotero SQLite → CLI 自动生成 | **只读**（AI 不可改） |
| `**元信息**` 正文段 | CLI 从 frontmatter 渲染 | **只读** |
| `**研究目的**` 等正文字段 | AI 从 PDF/MinerU 抽取 | AI 可写 |
| `**数据分析**` 嵌入子模板 | 模板引用，AI 填充实例 | AI 可写 |
| `**核心主张**` / `**证据条目**` | AI 抽取 + 人工审阅 | AI 可写 |

---

## 4. CLI 工具设计

### 4.1 命令接口

```bash
# 列出所有 Collection（带论文数）
zotero-md collections

# 按 Collection 生成 Paper 骨架
zotero-md generate --collection "eeg&fnirs" --output ./wiki/papers/

# 增量同步（只处理新增论文）
zotero-md sync --collection "eeg&fnirs"

# 全量重建（覆盖已有文件）
zotero-md rebuild --collection "eeg&fnirs"

# 指定 modality（覆盖自动检测）
zotero-md generate --collection "fnirs" --modality fnirs

# 干跑模式（只显示将生成的文件，不实际写入）
zotero-md generate --collection "eeg&fnirs" --dry-run
```

### 4.2 文件命名规则

```
papers/<FirstAuthor>_<Year>_<short-keyword>.md
```

- `FirstAuthor`: 第一作者姓氏（英文小写，中文保留汉字）
  - 英文: `Smith` → `smith`
  - 中文: `张克亮` → `张克亮`
- `Year`: 发表年份
- `short-keyword`: 从标题提取的 2-4 个**名词/动词**，下划线连接，全小写
  - 提取规则: 去除停用词（the, of, and, in, a, an, for, with, to, on），取剩余实义词前 4 个
  - 英文示例: "Neural mechanisms of speech processing" → `neural_mechanisms_speech_processing`
  - 中文示例: "基于本体的语义相似度计算研究" → `本体_语义相似度_计算`
- 完整示例: `smith_2025_neural_mechanisms_speech.md`

**冲突处理**: 如果文件已存在，跳过（sync 模式）或覆盖（rebuild 模式）

### 4.3 Modality 自动检测

从 Collection 名称和 Zotero 标签推断 modality，**优先级从高到低**：

| 优先级 | 规则 | modality |
|---|---|---|
| 1 | 用户显式指定 `--modality` 参数 | 用户指定值 |
| 2 | Collection 名含 `fmri`（不区分大小写） | fmri |
| 3 | Collection 名含 `eeg` | eeg |
| 4 | Collection 名含 `fnirs` | fnirs |
| 5 | Collection 名含 `ml` 或 `机器学习` | ml |
| 6 | Collection 名含 `stats` 或 `统计` | stats |
| 7 | Zotero 标签含 `fMRI` / `EEG` / `fNIRS` | 对应 modality |
| 8 | 以上都不匹配 | other |

**冲突处理**: Collection 名优先于标签（Collection 是用户主动分类，更可靠）

---

## 5. 技术栈

| 组件 | 技术选择 | 理由 |
|---|---|---|
| 数据源 | 直读 `zotero.sqlite` | 无需 BBT 导出配置，实时 |
| 语言 | Python 3 | 标准库 sqlite3，无需额外依赖 |
| 模板引擎 | Jinja2 | 灵活的模板渲染 |
| CLI 框架 | argparse | 简单，无额外依赖 |
| 配置 | YAML | 与 Wiki 系统一致 |

---

## 6. 数据流

```
~/Zotero/zotero.sqlite
    │
    │ Python sqlite3 读取
    ↓
zotero-md CLI
    │
    │ 解析 items + itemData + creators + tags
    │ 渲染 Jinja2 模板
    ↓
wiki/papers/Smith_2025_fMRI_lang.md
    │
    │ YAML frontmatter (immutable)
    │ + 可读元信息段 (auto-generated)
    │ + 正文骨架 (待 AI 填充)
    ↓
后续 AI Agent 填充研究字段
```

---

## 7. 目录结构

```
evidence-wiki-skill/
├── scripts/
│   ├── wiki                    # 现有统一入口
│   ├── wiki_zotero_md.py       # 新增：Zotero→Paper 桥接
│   └── ...
└── references/
    └── templates/
        └── paper_skeleton.j2   # 新增：Paper 骨架 Jinja2 模板
```

---

## 8. 边界与约束

### 8.1 做什么

- 从 Zotero SQLite 读取元数据
- 生成 Paper 节点骨架（YAML frontmatter + 可读元信息 + 正文骨架）
- 按 Collection 粒度生成
- 增量同步（不覆盖已有内容）

### 8.2 不做什么

- **不修改 Zotero 数据库**（只读）
- **不调用 LLM**（元数据生成是纯机械操作）
- **不自动填充研究字段**（那是后续 AI Agent 的工作）
- **不处理 PDF 附件**（仅生成 zotero_link 链接）
- **不做全量自动同步**（用户手动触发）

### 8.3 与现有系统的关系

- **互补**: 现有 `wiki_ingest.py` 处理 AI 抽取阶段，本工具处理元数据灌入阶段
- **顺序**: 先 `zotero-md generate` 生成骨架 → 再 AI Agent 填充研究字段
- **不冲突**: frontmatter 由 CLI 管理，正文由 AI 管理

---

## 9. 成功标准

1. 能从 Zotero SQLite 正确读取 13,850 篇 journalArticle 的元数据
2. 能按 Collection 粒度生成 Paper 骨架
3. 生成的 YAML frontmatter 包含完整元数据（title/authors/year/journal/doi/citekey）
4. 生成的正文包含可读的 `**元信息**` 段落
5. 增量同步不覆盖已有内容
6. modality 自动检测准确率 > 90%

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| Zotero 运行时数据库锁定 | 无法读取 | 复制到临时文件再读取 |
| SQLite schema 变化（Zotero 升级） | 解析失败 | 版本检测 + 错误提示 |
| 中文作者名处理 | 文件名乱码 | 拼音转换或保留中文 |
| Collection 名含特殊字符 | 路径问题 | 清理特殊字符 |
| 大 Collection 生成慢 | 用户体验 | 进度条 + 并行处理 |
