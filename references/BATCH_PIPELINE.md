# Batch Pipeline · 批量抽取工作流(ARCHITECTURE §8)

> **本文件是 Week 2-4 批量抽取的执行手册**(方法文档,位于 `.skill/references/`,2026-08-24 从 wiki 根目录迁移过来)。
>
> **关联 plan**:`ARCHITECTURE.md §8`(Sub-agent Pipeline)+ `§10`(Week 2-4)
> **关联 tasks**:`tasks.md` T-W2-001 ~ T-W4-003

---

## 1. Pipeline 总览

```
EXTRACT_QUEUE.md(论文列表)
   ↓
sub-agent pipeline(每篇独立 worktree)
   ↓
00-pending/<citekey>/(LLM 抽取产物)
   ↓
用户审阅 + wiki_promote
   ↓
papers/claims/evidence/(正式目录)
   ↓
git tag checkpoint(每批次)
```

## 2. 4 个 Sub-agent(ARCHITECTURE §8.1)

每个 sub-agent 处理一篇论文,串行执行:

| 阶段 | sub-agent | 任务 |
|---|---|---|
| **T1 Scan** | paper-analyst | 读 full.md,识别论文类型,5 字段摘要 |
| **T2 Extract** | claim-miner | 抽 claim 列表(语义理解,不用正则) |
| **T3 Evidence** | evidence-mapper | 抽 evidence 列表,建立 evidence × claim matrix |
| **T4 Audit** | topic-linker | 关联 topic + 反向链接 + L0-L3 自检 |

每个 sub-agent:
- 独立 context(不污染主会话)
- 独立 worktree(不互相干扰)
- 写入 `00-pending/<citekey>/`

## 3. N-paper 并行

```bash
# /batch N
# 并发启动 N 个 pipeline(每篇独立 worktree)
```

N 推荐值:
- **Gold Set**:N=1(逐步验证)
- **Batch 1**:N=3(并行 3 篇,看稳定性)
- **Batch 2-3**:N=5
- **Batch 4**:N=10

## 4. Checkpoint

每篇完成时:
```bash
wiki_snapshot "paper-<citekey>" "完成 <title>"
```

失败时:
```bash
jj undo  # 回到上一个 snapshot
```

## 5. 模式选择(ARCHITECTURE §5.1)

| 论文类型 | 模式 | 适用 |
|---|---|---|
| `empirical` + 模态(EEG/fMRI/fNIRS) | **deep-read** | 5-8 分钟,完整抽取 |
| `review` / `theoretical` | **quick-scan** | 30s,5 字段摘要 |
| `methodology` / `meta_analysis` | **quick-scan** | 30s |
| 用户质疑 / 30 天复检 | **audit** | 2min,校验修正 |

自动判断逻辑:
1. 检查 `study_type` field(由 paper-analyst 设置)
2. `empirical` → deep-read
3. 其他 → quick-scan
4. 用户可显式覆盖

## 6. 用户审阅流程

每篇 paper 完成抽取后:
1. **读 `00-pending/<citekey>/`** 中的 paper + claim + evidence 节点
2. **检查**:
   - 字段完整性
   - claim 是否原子化
   - evidence 是否可定位到 raw
   - wikilink 双向存在
3. **通过** → `/promote <citekey>`(脚本移到正式目录)
4. **不通过** → 注释修改 + 重新抽取

## 7. Lint(每次 T3 后)

```bash
# L0 Structure
python3 -m py_compile .skill/scripts/_registry.py  # 注册表语法
ls claims/*.md | wc -l

# L1 Evidence(用 jsonschema)
python3 -c "
from .skill.scripts.schemas._registry import validate_file
import os
for f in os.listdir('claims'):
    if f.endswith('.md'):
        ok, err = validate_file('claim', f'claims/{f}')
        if not ok: print(f'{f}: {err}')
"

# L2 Semantic(LLM 主导)
# LLM 检查 claim-evidence 关系

# L3 Consistency(Grounding grep)
for num in $(grep -oP '\d+\.\d+' claims/*.md evidence/*.md); do
  grep -q "$num" raw/*/full.md || echo "FLAGGED: $num"
done
```

## 8. 失败模式与防御

| 失败 | 防御 |
|---|---|
| LLM 漏 frontmatter | scripts 强制校验 |
| claim 编号冲突 | CLAIM-NNN 已弃,用 slug 唯一 |
| Transclusion 让 paper.md 膨胀 | 接受,callout 默认折叠缓解 |
| Zotero 改动覆盖 paperinfo | sync 只写 paperinfo/,不动 papers/ |
| Sub-agent 互相串改文件 | worktree 隔离 |
| 跨论文重复 claim | stitch-knowledge 自动合并 |

## 9. Phase 2 候选(ARCHITECTURE §11.3)

- D* Delta 提案机制(wiki > 50 篇时启用)
- Lineage 技术路线图
- 图片归档流程
- Reasoning Problem 标记

---

## 命令速查

| 用户说 | 触发 | 见 |
|---|---|---|
| `/extract <full.md>` | 抽取一篇 | T-W1-004 prompt |
| `/batch N` | 批量 N 篇 | T-W1-004 prompt + 本文件 §3 |
| `/lint` | 4 层检查 | T-W1-004 prompt |
| `/promote <citekey>` | 移到正式目录 | T-W1-007 MIGRATION |
| `/sync` | Zotero 同步 | T-W1-004 prompt |