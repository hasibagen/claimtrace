---
name: wiki-build-topic
description: >-
  CREATE a topic node (MOC, Map of Content) for cross-paper aggregation.
  Lazy creation: only when 2+ papers share a theme. Topic is a **聚合视图
  not a data node** — 它只组织引用,不存储 claim/evidence 内容 (避免重复事实).
  Writes to topics/<topic-slug>.md (优先中文 + 真实空格, ARCHITECTURE §2.3
  + T-W4-030). **NOT for**: single-paper organization (use paper.md 关联主题字段),
  creating claims/evidence (use wiki-build-claim/wiki-build-evidence). Use when
  user says "/topic <name>" or "建一个主题 xxx".
---

# Wiki Build Topic

创建 topic 节点(MOC = Map of Content),用于跨论文聚合。

## 何时使用

- 用户说:`/topic <name>` 或 "建一个主题 xxx"
- 同一主题在 2+ 篇 paper 中出现(自动触发,见 ARCHITECTURE §2.1 辅助 A)

**懒创建**:topic 是辅助节点,只在跨论文时才创建(ARCHITECTURE §2.1)。

## 字段(ARCHITECTURE §3.6)

```yaml
---
type: topic
schema_version: "plan_final_v1"
id: <topic-key>
---

# <Topic Title>

## 主题描述
<description — 用 1-2 句说明这个主题的范围>

## 涉及论文
- [[paper-citekey-1]]
- [[paper-citekey-2]]
- ...

## 核心主张
- [[claim-slug-1]] — 一句话陈述
- [[claim-slug-2]] — 一句话陈述

## 关键证据
- [[evidence-slug-1]] — 描述
- [[evidence-slug-2]]

## 共识
<3+ 项研究支持的观点>

## 矛盾
<观点冲突,保留为知识>

## 空白
<未解决问题,推动下一步研究>

## 关联主题
- [[related-topic]]
```

## 命名

**文件**:`topics/<topic-key>.md`(ARCHITECTURE §2.3 + T-W4-030)
- **优先中文 + 真实空格**(如 `topics/fNIRS 认知控制.md`)
- 中英混合 / kebab-case 也允许(如 `topics/fnirs-cognitive-control.md`)
- **不用 `-` 替代真实空格**(ARCHITECTURE §15.4.7)

## 边界

- topic 不替代 paper — 是聚合视图
- topic 不替代 synthesis — synthesis 是问题驱动的综合
- "共识/矛盾/空白" 是 topic 的灵魂(ARCHITECTURE §11 主题节点模板)

## 关联

- 节点模型:`ARCHITECTURE.md §2.1`
- 主题模板:`ARCHITECTURE.md §3.6`

## 模板

```markdown
# <Topic Title>

## 主题描述
<1-2 句>

## 涉及论文
- [[papers/<author>_<year>_<short>]]
- [[papers/<BBT-citekey>]]

## 核心主张
- [[claim-1]] — 一句话
- [[claim-2]] — 一句话

## 关键证据
- [[evidence-1]] — 描述
- [[evidence-2]] — 描述

## 争议点
<观点冲突>

## 待解决问题
- [ ] <研究空白>

## 关联主题
- [[related-topic]]
```

## Resources

- `ARCHITECTURE.md §3.6` Topic 节点完整 schema
- `ARCHITECTURE.md §2.1` 节点模型(topic 是辅助)