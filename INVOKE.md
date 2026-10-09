# INVOKE · skill 标准调用规范(2026-08-25 统一;2026-09-04 三引擎解耦;2026-10-08 zcode headless 解禁)

> **问题背景**:LLM CLI(pi / codex / zcode)被调用时经常绕过本 skill 自己重写 prompt(硬编码 14 字段描述、不读 templates、不跑渲染器),导致字段不完整、格式漂移。本文件是**唯一合法的调用方式**,所有批量脚本 / subprocess / 人工指令必须照此。
>
> **引擎原则(2026-09-04 用户指令)**:抽取不固定 pi — **pi / codex / zcode 三引擎均合法**,按 AGENTS.md §0.5 选型;但无论哪个引擎,prompt 前缀、S0-S7 流程、S4 闸门完全一致。

## 四条唤起路径(已全部注册)

| 环境 | 方式 | 验证 |
|---|---|---|
| **pi cli(headless/批量)** | skill 已注册到 `~/.pi/agent/skills/evidence-wiki`(symlink → 本目录),pi 启动自动发现;不放心可显式 `--skill <wiki-root>/.skill` | `pi -p "你加载的 skills 里有 evidence-wiki 吗"` |
| **pi 交互会话(在 wiki 目录)** | `/extract <citekey>` 等 10 个命令(`.pi/prompts/`)+ skill 自动发现 | `/skills` 列表可见 evidence-wiki |
| **codex cli(headless/批量)** | `codex exec -C <wiki-root> ...`(见下方模板);codex 无 skill 自动发现,靠 INVOKE-PREFIX 指示 read SKILL.md;根 `AGENTS.md` 宪法由 codex 按 cwd 自动加载 | 日志出现对 `.skill/skills/wiki-extract-paper/SKILL.md` 的 read |
| **zcode cli(headless/批量;2026-10-08 起可用)** | `zcode -p "<INVOKE-PREFIX> 处理 <citekey>" --cwd <wiki-root>`;cwd 下 AGENTS.md 自动加载,`~/.zcode/skills/` 微 skill 自动发现;`-p` 默认 yolo 模式(可写) | 日志出现对 `.skill/skills/wiki-extract-paper/SKILL.md` 的 read |
| **zcode 会话(交互)** | 微 skill 已注册 `~/.zcode/skills/`(symlink → `.skill/skills/`);在 wiki 工作区会话中直接说「处理 <citekey>」 | 会话 Skill 列表可见 wiki-extract-paper |
| **Claude 会话** | 已注册 `~/.claude/skills/evidence-wiki`(symlink → 本目录) | `/skills` 列表可见 |

## 标准调用模板(subprocess 必须逐字使用)

任何脚本调用 LLM 引擎抽取论文时,prompt **必须以本前缀开头**(禁止改写、禁止省略):

```bash
# 引擎 1:pi(模型按 AGENTS.md §0.5,批量默认 cce-minimax3 / MiniMax-M3)
pi -p "$(cat <wiki-root>/.skill/INVOKE-PREFIX.txt) 处理 <citekey>" \
   --provider cce-minimax3 --model "MiniMax-M3"

# 引擎 2:codex(模型默认走 ~/.codex/config.toml,-m 可覆盖)
codex exec -C <wiki-root> --sandbox workspace-write \
   "$(cat <wiki-root>/.skill/INVOKE-PREFIX.txt) 处理 <citekey>"

# 引擎 3:zcode(2026-10-08 起 headless 可用;模型=客户端当前配置,CLI 无 --model 透传)
zcode -p "$(cat <wiki-root>/.skill/INVOKE-PREFIX.txt) 处理 <citekey>" \
   --cwd <wiki-root>
#   会话内模式依旧合法:用户在 ZCode 会话说「处理 <citekey>」→ 会话加载 wiki-extract-paper 微 skill,
#   自身按 S0-S7 执行;必须自持篇级锁(.git/wiki-locks/<ck>.<pid>)+ 落盘即 commit(铁律 #12)

# 批量一律走 runner(自动加锁/提交/幂等续跑;引擎由 --engine 切换):
.skill/scripts/wiki_run_extract.sh --engine pi    --provider cce-minimax3 --model MiniMax-M3 ck1 ck2 ...
.skill/scripts/wiki_run_extract.sh --engine codex [-m 由 --model 透传,缺省用 codex config] ck1 ck2 ...
.skill/scripts/wiki_run_extract.sh --engine zcode [模型走 zcode 客户端配置(首选 GLM-5.3-Flash,2026-09-17 用户指令);--provider/--model 被忽略] ck1 ck2 ...
```

## 禁例(违反 = 返工)

1. ❌ prompt 里硬编码字段描述("抽 14 字段 + 写 2-3 个 claim"之类)——字段契约只在 `.skill/references/templates/` 与 ARCHITECTURE §3
2. ❌ 不带 INVOKE 前缀直接 `pi -p "你是论文抽取助手..."` / `codex exec "你是论文抽取助手..."`
3. ❌ 抽完不跑渲染器(body 手写)——S3 规定 body 由 `wiki_render_nodes.py` 生成
4. ❌ 不跑 S4 检查就写入完成(`wiki_lint.py --layer L1.5` 必须对该 citekey 0 error)

## 一键自检

```bash
# 抽取后(单篇)应有的完整闭环:
python3 .skill/scripts/wiki_render_nodes.py evidence 00-pending/<citekey>/evidence/  # 就地渲染
python3 .skill/scripts/wiki_render_nodes.py claim 00-pending/<citekey>/claims/
python3 .skill/scripts/wiki_lint.py --wiki-root . --layer L1.5   # S4 闸门(含 pending)
python3 .skill/scripts/wiki_promote.py <citekey> --check          # S7 闸门预检
```
