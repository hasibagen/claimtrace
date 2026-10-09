---
description: Zotero 增量同步
argument-hint: "<collection name>"
---

请同步 Zotero collection: $1

## 步骤

1. read `.skill/skills/wiki-zotero-sync/SKILL.md` 获取完整流程
2. 调用脚本:
   ```bash
   # 增量同步(默认)
   python3 .skill/scripts/wiki_zotero.py sync --collection "$1"
   ```
3. 报告:新增 / 更新 / 不动 数量
4. 写 `log/ops.md`

## 约束

- 只写 `paperinfo/`,**不**碰 `papers/` / `claims/` / `evidence/`
- scripts 用 Zotero local SQLite,不联网
- paperinfo 是论文身份信息的 Source of Truth(plan_final §3.1)