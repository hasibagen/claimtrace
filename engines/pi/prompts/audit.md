---
description: 审阅指定节点(T4 Audit 模式)
argument-hint: "<node path or citekey>"
---

请审阅指定节点: $1

## 步骤

1. read `.skill/skills/wiki-extract-paper/SKILL.md` 的 T4 Audit 章节
2. 校验:
   - **frontmatter**:必填字段 + 枚举值
   - **quote 定位**:observation / source_text 在 raw 中可 grep
   - **数值区间**:p∈[0,1], n≥1, r∈[-1,1], confidence∈[0,1]
   - **wikilink 双向**:所有 `[[xxx]]` 目标存在
3. 修改原节点(若需要)
4. 写记录到 `log/ops.md`

## 触发

- 用户质疑某节点
- 30 天后复检
- `/lint` L2/L3 严重错误时