---
description: 创建一个主题节点(MOC)
argument-hint: "<topic name>"
---

请创建 topic 节点: $1

## 步骤

1. read `.skill/skills/wiki-build-topic/SKILL.md` 获取模板
2. 命名:`topics/<topic-key>.md`(**优先中文 + 真实空格**,如 `fNIRS 认知控制`;中英混合 / kebab-case 也允许;不用 `-` 替代真实空格,plan_final §2.3 + T-W4-030)
3. 必填:涉及论文 + 核心主张 + 关键证据(可标 DRAFT 等用户填)
4. 灵魂字段:共识 / 矛盾 / 空白
5. write 到 `00-pending/<topic-key>.md`

## 约束

- topic 是辅助节点,只在跨论文时才创建(plan_final §2.1)
- 不替代 paper(那是原始研究)
- 不替代 synthesis(那是问题驱动的综合)