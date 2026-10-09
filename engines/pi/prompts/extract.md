---
description: 把一篇论文抽取为 paper/claim/evidence 节点(按 S0-S7 标准流程,只写 frontmatter,body 由渲染器生成)
argument-hint: "<full.md | pdf | citekey | CSV row>"
---

请执行 wiki 抽取流程,目标: $1

## 首先阅读

1. read `.skill/skills/wiki-extract-paper/SKILL.md` 获取**标准作业顺序 S0-S7**(权威定义见 `ARCHITECTURE.md §5.0`)
2. 若 $1 是 CSV/清单 → 从 S0 开始(解析出 md 路径,逐篇走流程)
3. 若 $1 是 **PDF** → 先走 **S0a**:`python3 .skill/scripts/wiki_pdf_to_md.py $1 [--citekey <ck>]`(citekey 已知直转 raw/<ck>/,未知暂存 raw/_incoming/),再从 S1 开始
4. 若 $1 是 md 路径 → 从 S1 开始;若是 citekey(S1/S2 已完成)→ 直接从 S3 开始

## S0-S7 步骤(不得跳步/调序)

- **S1 paperinfo 先行**:匹配或创建 paperinfo(用 paper key,勿用 attachment key);canonical citekey = paperinfo 节点名
- **S2 raw 复制**:md 所在文件夹 → `raw/<citekey>/`,一次命名到位永不改名
- **S3 单篇抽取**:本 cli 只处理这一篇 → `00-pending/<citekey>/`;**LLM 只写 frontmatter**:
  - claim: statement / claim_type / origin / atomic / scope_* / verify_* / reasoning / reasoning_type / sources_targets / supports_targets / evidence_targets(扁平 3 平行数组)
  - evidence: fact_type / observation / interp_origin / interp_text / prov_paper / prov_section / prov_source_text(原文 verbatim ≥20 字符) / verify_n / verify_test_method 等
  - paper: citekey / paperinfo / study_type / modality / related_topics / research_purpose 等 + **叙事段**(研究目的/被试/实验设计/.../结论)
  - **不写任何 body 段**(## 观察/## 解释/## 数值校验/边表/反向链接),S3 末尾跑渲染(逐命令,就地渲染 pending 目录):`python3 .skill/scripts/wiki_render_nodes.py evidence 00-pending/<citekey>/evidence/` 和 `... claim 00-pending/<citekey>/claims/`
  - claim 链接已有优先;**topic 只链接已有**,确需新建先查 topics/ 近重复
  - evidence 原文即证据(prov_source_text,无 raw_path)
- **S4 机械检查**:`_registry.py validate` + `wiki_lint.py` L0/L0.5/L1/L1.5/L3 + Grounding(quote 在 raw 命中);**不过则退回 S3 修,不得进 S5**
- **S5 互联**:`wiki_link_paper.py`(从正向边反推 paper.related_evidence/claims)→ `wiki_render_nodes.py paper` 重生成嵌入段 + Backlinks Cache;完成标准 = 0 broken wikilink + 嵌入段非空
- **S6 人审**:报告已写入节点路径 + 待审阅项,**不要**自动移到 `papers/`
- **S7 promote**:等用户确认后才执行

## 约束

- 载体是 md,严禁 scripts 抽取语义字段(ARCHITECTURE §1.2 铁律 4)
- LLM→JSON→jsonschema 校验→frontmatter;**渲染脚本 = 唯一 body 维护者**
- 节点命名用语义 slug,不用 CLAIM-NNN / EVID-NNN 编号;claim 文件名禁数学符号与抽取标记
- claim 表字段用 enum 精确值(verify_status / claim_type / reasoning_type / verify_p_method 等)
