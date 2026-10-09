---
description: 批量抽取(批次文件在 log/,runner 直调 LLM cli:pi/codex 按 --engine 切换)
argument-hint: "<batch-slug 或 citekey 列表>"
---

请执行批量抽取: $1

## 步骤(2026-09-04 版,禁用 sub-agent 编排;引擎 pi/codex 可选,见 ARCHITECTURE §8.0)

1. 读 `log/README.md` 批次索引,定位批次文件 `log/batch-<slug>.md`
2. 在批次文件「Runner 运行记录」追加认领行(时间 / runner / 引擎+模型 / 认领 citekey 列表)
3. 用 `.skill/scripts/wiki_run_extract.sh --engine <pi|codex> [--provider <p>] [--model <m>] ck1 ck2 ...` 逐篇抽取
   - 引擎按 AGENTS.md §0.5 先与用户确认(pi 默认 cce-minimax3/MiniMax-M3;codex 默认走其 config 模型)
   - N 路并行 = N 个 runner 后台进程瓜分**不重叠**列表
   - 每篇落盘即 commit(铁律 #12);篇级锁自动跳过他人认领的论文
4. 全部完成后跑 `python3 .skill/scripts/wiki_batch_status.py log/batch-<slug>.md` 刷新批次进度
5. 人工审阅 00-pending → `wiki_promote.py --check/--execute <citekey>`(S7 闸门)

## 失败处理

- 单篇失败只重跑该篇:看 `/tmp/pi_logs_runner/<ck>.log`
- 结果(含 FAIL)如实追加到批次文件「Runner 运行记录」

## 约束

- 抽取 runner 不需要 worktree(铁律 #15,靠 #12+#13 保护)
- LLM 抽取,scripts 校验
- 批次事件写批次文件;全局事件(infra/promote)才写 `log/ops.md`
