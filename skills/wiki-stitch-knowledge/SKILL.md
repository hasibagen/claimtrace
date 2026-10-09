---
name: wiki-stitch-knowledge
description: >-
  MERGE cross-paper duplicates (knowledge stitching): detect semantically
  equivalent claims across papers via LLM judgment (NOT string match — see
  ARCHITECTURE 铁律 #4 NO REGEX ON MEANING), merge to canonical claim, wire
  new evidence via same_claim_as edge, update verify_supporting_count and
  verify_contradicting_count. Run after each T3 batch or via /lint. **NOT
  for**: answering user questions (use wiki-query-evidence), creating
  evidence/claim (use wiki-build-evidence/wiki-build-claim). Trigger on
  "/stitch" or implicit after T3 promote.
---

# Wiki Stitch Knowledge

跨论文知识缝合 — 去重、合并、关联、verification 更新。

## 何时使用

- T3 完成时(每次批量抽取后)
- `/lint` 调用时
- 用户说:`/stitch` / `跨论文去重` / `跨论文关联`

## 工作流

### 1. 扫描 claim 节点

```bash
ls claims/*.md
```

### 2. 语义去重(LLM,不是字符串匹配)

对每对 claim(全 N×N 组合):
- LLM 判断 `statement` 是否表达同一命题
- 若相同/相近 → 选**主节点**(最早创建 + 引用最多),其他为候选

### 3. 合并候选 →主节点

```yaml
# 主节点的 evidence 字段累加:
evidence:
  - [[source-evidence-1]]     # 主节点原有
  - [[source-evidence-2]]     # 候选 1 的
  - [[source-evidence-3]]     # 候选 2 的

# verification 自动重算:
verification:
  supporting_count: <新总数>
  evidence_count: <新总数>
  last_updated: "2026-08-24T..."
```

### 4. 候选节点归档

候选节点改为:
```markdown
---
archived_to: "<主节点 slug>"
archived_at: "2026-08-24T..."
---

# Claim: <原名>(已合并到 [[main-claim]])

此 claim 已被合并到主节点 [[main-claim]]。
详见主节点获取最新 evidence 和 verification。
```

### 5. 写报告到 log/ops.md

```markdown
## [YYYY-MM-DD] stitch | 跨论文去重

- 扫描 N 个 claim,发现 K 个重复
- 合并到主节点:M 列表
- 归档候选:C 列表
- verification 更新:V 列表
```

## 边界

- **不去重 paper 节点**(一篇论文就是一个节点)
- **不去重 evidence 节点**(每 evidence 是 unique 的事实引用)
- 只合并 **claim 节点**(语义重复的命题)
- 合并操作 **不删除** 候选节点(归档留痕,ARCHITECTURE §1.2 铁律 10)

## 关联

- 数据模型:`ARCHITECTURE.md §3.5`
- Stitch 触发条件:`ARCHITECTURE.md §5.4`
- Claim lazy promotion:`ARCHITECTURE.md §2.1` 触发 1

## Resources

- `ARCHITECTURE.md §5.4` Stitch Knowledge 详解
- `ARCHITECTURE.md §3.5` Claim verification 字段

## Phase 2 候选(ARCHITECTURE §11.3 #1)

D* Delta 提案机制(proposed/accepted/parked/revised 4 态):
- 当前是"自动合并",Phase 2 升级为"提案 + 用户确认 + 演化追踪"
- 触发:wiki > 50 篇时