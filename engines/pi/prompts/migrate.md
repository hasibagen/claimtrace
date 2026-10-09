---
description: 数据迁移脚本入口(渐进式,plan_final §9)
argument-hint: ""
---

请执行数据迁移

## 步骤

1. read `plan_final.md §9` 渐进式迁移策略
2. 决定迁移批次(从 `log/README.md` 批次索引读取)
3. 对每批次:
   - LLM 抽取 → `00-pending/<citekey>/`
   - 用户审阅 → `papers/` / `claims/` / `evidence/`
   - git tag checkpoint
4. 失败回滚:`jj undo` 到上一个 snapshot

## 渐进式策略(plan_final §9.1)

| 批次 | 论文数 | 任务 |
|---|---|---|
| Batch 0 | 5 | Gold Set,完整 5 阶段,验证 schema |
| Batch 1 | 20 | 跑通批量 + checkpoint |
| Batch 2 | 50 | 验证 stitch-knowledge(去重) |
| Batch 3 | 100 | 全量 lint |
| Batch 4 | 197 | 剩余全部 |

## 约束

- 每批次 git tag,失败可回滚
- 渐进式,不一次性
- scripts 不抽取语义