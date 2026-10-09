> Wiki AGENTS · 项目契约

> LLM 会话(pi / codex / zcode)启动时无条件加载。违反铁律,所有后续操作都可能错。
> **本文件已被 `tasks.md T-W1-001` 重写(原 637 行 → 现 < 80 行)**;老设计见 `.skill/ref/backup/`,新设计见 `plan_final.md`。

## 0. 角色

你是学术证据 wiki 的长期维护者。输入:论文路径 / 用户提问;输出:markdown 节点 + wikilink。**不修改 Zotero / MinerU 原始层**。

## 0.5 LLM 引擎调用规则(2026-09-04 三引擎解耦,替代旧"pi CLI 调用规则")

- **抽取不固定 pi**(2026-09-04 用户指令):**pi / codex / zcode 三引擎均合法**;批量启动前先与用户确认引擎 + 模型。调用规范唯一入口 = `.skill/INVOKE.md`(INVOKE-PREFIX 前缀三引擎共用)。
- **pi**(`pi -p`,subprocess/交互均可):批量默认 `--provider cce-minimax3 --model MiniMax-M3`(2026-08-27 用户指令:不再用 glm 系列,zhipu 5h 共享限流反复打断批次);`--provider zhipu` 默认但受限;openai/anthropic 需用户提供 key。写文件脚本的 pi prompt 务必简洁(否则 pi 倾向输出"会话状态"而不是执行抽取)。
- **codex**(`codex exec -C <wiki-root> --sandbox workspace-write`,subprocess 批量):模型默认走 `~/.codex/config.toml`(当前 gpt-5.6-terra),`--model` 可透传覆盖;沙箱 workspace-write 对本地抽取足够(全流程无网络需求)。经 runner:`wiki_run_extract.sh --engine codex`。
- **zcode**(2026-10-08 起 headless 可用,用户指令"后面提取用 zcode cli"):`zcode -p "<prompt>" --cwd <wiki-root>` 子进程/交互均可,`-p` 默认 yolo 模式(可写);经 runner `wiki_run_extract.sh --engine zcode`。模型 = 客户端当前配置(CLI 无 --model 透传;2026-09-17 用户指令首选 GLM-5.3-Flash)。会话内模式依旧合法(说「处理 <citekey>」,按 wiki-extract-paper 微 skill 执行 S0-S7);**必须自持篇级锁 + 落盘即 commit**(铁律 #12/#13 同样约束 headless 与会话内抽取)。

## 1. 铁律(11 条,plan_final §1.2)

1. RAW IS IMMUTABLE — Zotero / MinerU 永不修改
2. MARKDOWN IS THE SOURCE OF TRUTH — 不引数据库,JSON 仅作临时
3. LLM EXTRACTS, SCRIPTS VALIDATE — 语义靠 LLM,机械靠 scripts
4. **NO REGEX ON MEANING** — 不写正则抽取任何语义字段
5. PROGRESSIVE DISCLOSURE — frontmatter 可见,正文按需 Transclusion
6. CONTEXT OPTIMIZATION — 最小化上下文,按需 read
7. EVERY FACT HAS PROVENANCE — 重要事实可定位原文 quote
8. EVERY NUMBER IS VERIFIABLE — 数值可 grep 到 full.md
9. CLAIM ≠ PAPER CONCLUSION — claim 与作者结论分开
10. HUMAN REVIEWS PENDING — LLM 写 `00-pending/`,人审阅才进正式目录
11. GRAPH EDGES ARE TYPED & CONFIDENT — 边有类型(supports/contradicts/...)+置信度

## 2. 路由表(意图 → 微 Skill)

| 用户说 | 调用 |
|---|---|
| `处理 [full.md/pdf]` / `/extract | wiki-extract-paper(PDF 先走 S0a `wiki_pdf_to_md.py` 转 md) |
| `跨论文追踪` / `/claim` | wiki-build-claim |
| `这是事实` / `/evidence` | wiki-build-evidence |
| `建主题` / `/topic` | wiki-build-topic |
| `X 的证据` / `/query` | wiki-query-evidence |
| `检查 wiki` / `/lint` | wiki-lint-wiki |
| `zotero 同步` / `/sync` | wiki-zotero-sync |
| `跨论文去重` / `/stitch` | wiki-stitch-knowledge |
| **去重 00-pending + raw** / `/dedup` | **wiki-dedup-papers** |
| `审阅` / `/audit` | **wiki-audit-paper**(批判审问,T4 升级) |
| `建模拆解 [论文]` / `/modeling` | **wiki-extract-modeling**(训练-验证-测试协议深读+mermaid) |

完整 10 个微 Skill + 10 个 Prompt 见 `.skill/SKILL.md §0`。

## 3. 节点架构(5 核心 + 2 辅助 + raw 层,plan_final §2)

核心:paperinfo · paper · claim · evidence · synthesis。辅助:topic(跨论文才创建)· `00-pending/`(审阅缓冲带)。**raw 层**:`raw/<citekey>/full.md`(权威源,见铁律 #1)。

**节点数量无硬性限制**(plan_final §2.4 + T-W4-032):CLAIM 推荐 3-8/paper, EVIDENCE 推荐 3-10/paper;上限警告 > 20 CLAIM / > 30 EVIDENCE,需评估过度拆解。质量优先于完整。

**命名约定**(**无内部编号**):
- 论文:`<BBT-citekey>.md`
- claim:`<semantic-slug>.md`(如 `dlpfc-hbo-age.md`)
- evidence:`<author>-<year>-<slug>.md`(如 `zhang-2021-dlpfc-hbo-age.md`)
- topic/synthesis:`<topic/question-key>.md`
- raw:`raw/<BBT-citekey>/full.md`(从 MinerU 复制,Grounding grep 都在这里)

**`00-pending/` 与 `raw/` 的目录名 = paperinfo 节点名(canonical citekey)**:
- zotero 同步同一论文可能产生多个 raw full.md(大小写/后缀变体),如 `..._The_virtual_brain_on_EBRAINS` / `..._The_Virtual_Brain_on_EBRAINS` / `..._The_Virtual_Brain_on_EBRAINS_2`
- **同一论文只 1 个 00-pending 目录 + 1 个 raw 目录**(以 paperinfo canonical 为准)
- 去重工具:`wiki_dedup_papers.py --rename --execute`(自动增量合并)
- 增量更新:只补缺失内容,不重建已有
- 不创建多个 paper.md / 多个空目录
- 同一论文不同版本(如 arxiv 2025 vs LNCS 2026)以 paperinfo 节点名为准;若 paperinfo 缺失,在合并前补充 paperinfo 节点

## 4. 方法论家族(Evidence-Centric,9 层,plan_final §1.3)

顶层 Scientific Evidence & Argument Mining → 数据 Evidence-centric KG → 论文 CERIC → 论证 Toulmin(降级为字段)→ 验证 SciFact → 强度 GRADE 简化版(放 synthesis)→ 流程 Keshav + Cornwell → 叙事 ABT → 筛选 PRISMA / PICO(可选)。

## 5. Pi 扩展机制(5 件套)

- **AGENTS.md**(本文件):宪法,启动无条件加载
- **SKILL.md** (`.skill/SKILL.md`):入口,含 §0 架构全景
- **Prompt** (`.pi/prompts/`):10 个命令(`/extract` 等)
- **Extension** (`.pi/extensions/`):自定义工具(5 个)
- **微 Skill** (`.skill/skills/*/SKILL.md`):按 description 路由,按需 read

## 6. 抽取流程(T0-T4)与验证(L0-L3)

抽取:T0 Ingest(30s) → T1 Scan(30s) → T2 Extract(5-8min) → T3 Evidence(3m) → T4 Audit(2min)。流水线:**LLM → JSON → scripts 校验 → MD → `00-pending/`**。

验证:**L0 Structure**(scripts)· **L1 Evidence**(scripts)· **L2 Semantic**(LLM)· **L3 Consistency**(scripts,含 Grounding grep)。

## 7. 去重工具

| 工具 | 用途 |
|---|---|
| `wiki_dedup_papers.py --scan` | 扫描 00-pending/raw 重复 |
| `wiki_dedup_papers.py --rename --execute` | 重命名为 paperinfo canonical(自动增量合并) |
| `wiki_dedup_papers.py --canonical <ck> <dirs>` | 手动指定 canonical 合并 |
| `wiki_dedup_papers.py --dry-run` | 仅打印,不修改 |
| `wiki-stitch-knowledge` 微 Skill | 跨论文 claim 去重(LLM 语义判断)|

## 8. 并发安全铁律(2026-08-26 事故后新增,多 AI 会话必须遵守)

12. **COMMIT AS YOU GO** — 批量抽取一律用 `.skill/scripts/wiki_run_extract.sh`:每篇落盘**立即 commit**,绝不让产物停留在 untracked 状态(untracked + 并发 reset = 必丢)
13. **GUARD BEFORE SURGERY** — `reset --hard` / `stash -u` / `git clean` / cherry-pick 冲突手术前,必须先跑 `.skill/scripts/wiki_git_guard.sh`(有活跃锁或别人在途工作则等待;等不及加 `--wip` 先替它 commit 再手术)
13a. **自持锁直接执行**(2026-08-28 M3 锁拒抽事故固化):看到 `.git/wiki-locks/<ck>.<pid>` 时,**如果锁文件名后缀就是本引擎调用(pi/codex/zcode)的 PID**(或本 runner 派生的 PID),直接执行 S3 抽取;**不要等待、不要询问 A/B/C**。这是同会话自持锁(在途并发保护由 #12+#13 互锁负责),不是冲突铁律 #13 适用范围。**冲突铁律 #13 仅适用 git 历史手术(`reset --hard`/`stash -u`/`git clean`/cherry-pick)前,不是 S3 抽取前**。
14. **NO STASH, USE WIP BRANCH** — 多会话环境禁用 stash(黑洞);保存现场用 `git checkout -b wip-x && git add -A && git commit`,可浏览、可部分恢复、reflog 可查
15. **WORKTREE FOR SURGERY ONLY** — git 历史手术类会话(reset/rebase/cherry-pick)用独立 worktree(`git worktree add ../wiki-x main`,用完 `git worktree remove` 归还);抽取 runner(pi/codex)**不需要** worktree,靠 #12+#13 保护即可
