---
description: 运行 4 层健康检查(L0-L3)
argument-hint: ""
---

请运行 wiki 健康检查

## 步骤

1. read `.skill/skills/wiki-lint-wiki/SKILL.md` 获取完整流程
2. 依次执行 L0 / L1 / L2 / L3:
   - **L0 Structure**:`Extension wiki_check_wikilinks`
   - **L1 Evidence**:3 套 jsonschema 校验
   - **L2 Semantic**:scripts 配对 + LLM 校验(claim-evidence 关系)
   - **L3 Consistency**:Grounding grep + 数值区间 + slug 引用计数
3. 输出报告到控制台 + `log/ops.md`
4. **不自动修复**(plan_final §13 失败模式)

## 报告格式

```markdown
# Wiki Lint 报告 · YYYY-MM-DD HH:MM

## 总结
- L0: X 问题 / L1: X / L2: X / L3: X

## 详细
<每层的具体问题清单>

## 建议修复
<按优先级排序>
```