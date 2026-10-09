# PAPER 节点模板(frontmatter 契约,2026-08-26 对齐 SKILL S0-S7)

> **本文件 = paper 的结构契约**(通用版)。模态专用字段检查单见 `paper-<modality>.md`(fnirs/eeg/fmri/eye-tracking/ml/multimodal/meta-analysis/review/modeling),统计方法候选见 `paper_stats.md`。建模/代理脑论文的训练-验证-测试协议深读另见 `paper-modeling.md` + skills/wiki-extract-modeling。
> schema:`.skill/scripts/schemas/`(claim/evidence);paper 无独立 jsonschema,以本文件 + 渲染器为准。

## 目录与文件(硬约束)

```
00-pending/<citekey>/            # 目录名 = paperinfo canonical citekey
├── <citekey>.md                 # 唯一顶层 paper md(禁止 paper.md 等第二份)
├── claims/<semantic-slug>.md    # 3-8 个(>20 警告)
└── evidence/<author>-<year>-<slug>.md   # 3-10 个(>30 警告)
```

## frontmatter(LLM 填;related_* 由 S5 脚本反推补全)

```yaml
---
type: paper
schema_version: plan_final_v1
citekey: <canonical citekey>
title: "Full Title"
authors: ["First Last", ...]
first-author: Lastname
year: 2026
publication: journal-name        # 期刊/会议名
DOI: 10.xxxx/xxxxx               # 有则必填(批次查重靠它)
language: en
study_type: empirical_computational_modeling   # 综述=review / 方法=methodology / ...
modality: fnirs                  # fnirs|eeg|fmri|multimodal|ml|...
paperinfo: "[[paperinfo/<BBT-citekey>]]"   # S1 匹配到的 paperinfo(必加)
raw_path: raw/<citekey>/full.md  # S2 复制后的规范位置;禁 zotero_md 绝对路径长期指向
code_urls: [https://github.com/...]  # 全部代码/模型仓库(GitHub/GitLab/Bitbucket/HF/Docker...);无则 []
data_url: "..."                      # 数据/材料存档(Zenodo/OSF/Figshare/Dryad/...);多个写 YAML list
tags: [virtual-brain, ...]
related_evidence:                # [[wikilink]] 格式,禁裸字符串;S5 自动补全
  - "[[<author>-<year>-<slug>]]"
related_claims:
  - "[[<claim slug>]]"
related_topics: []               # topic 只链接已有,单篇不新建
---
```

## body 分工(LLM 只写叙事,机械段归渲染器)

- **LLM 写**:叙事章节(标题可按论文类型取舍,模态检查单见 `paper-<modality>.md`):
  `# {Title}` / `## 元信息` / `## 研究目的` / `## 被试` / `## 实验设计` / `## 实验范式` /
  `## 测量工具` / `## 数据分析` / `## 结果`(嵌原文 quote+统计值) / `## 结论`(含 局限性) /
  `## Code & Data`(必写,契约见下)
  - **禁 CLAIM-001/EVID-NNN 编号**(旧架构;主张/证据用语义 slug wikilink)
  - `## Code & Data`(**必写**,2026-09-03):逐条整理本论文全部代码/数据/材料/模型获取入口 —
    扫 Data/Code Availability 声明 + 脚注 + 致谢 + 附录,GitHub/GitLab/Bitbucket、
    Zenodo/OSF/Figshare/Dryad、Hugging Face、Docker 镜像、数据请求表单/联系邮箱均算;
    每条格式 `- **[代码|数据|材料|模型]** 名称 — 一句话内容说明 → URL`;同步填 frontmatter
    `code_urls`/`data_url`;原文确无任何公开代码/数据时写「原文未提供公开代码/数据
    (数据可用性声明:…)」— 章节永远存在,禁省略;仅在参考文献里引用的他人仓库不算本篇产物
  - 结果段统计值 verbatim 引用原文,标注(§x.y, p.z)
- **渲染器写**(`wiki_render_nodes.py paper`,S5/幂等重生成,LLM 勿手写勿复制):
  `**核心主张**` 表 / `**证据条目**` 表 / `**关联主题**` / `**关联主张**` / `**引用本论文的页面**` /
  `## 本论文的 Evidence(全文)`(`> [!evidence]+ **slug**` + `> ![[slug]]` 逐条嵌入) /
  `## 本论文支持的 Claims(全文)`(`> [!claim]+ **slug**` + `> ![[slug]]`)
  **两大全文嵌入章节必须存在**(无 evidence/claim 也要有空章节占位)——S4 的 B10 检查项。

## 抽取模式差异(SKILL §3 模式)

- quick-scan(综述/方法论):只写 paper(元信息 + 5 字段摘要),不建 claim/evidence
- deep-read(实证核心):paper + 3-8 claim + 3-10 evidence 全量
- audit:校验修正既有节点,不新增
