# INVOKE · skill 标准调用规范(2026-08-25 统一)

> **问题背景**:pi cli / Claude 被调用时经常绕过本 skill 自己重写 prompt(硬编码 14 字段描述、不读 templates、不跑渲染器),导致字段不完整、格式漂移。本文件是**唯一合法的调用方式**,所有批量脚本 / subprocess / 人工指令必须照此。

## 三条唤起路径(已全部注册)

| 环境 | 方式 | 验证 |
|---|---|---|
| **pi cli(headless/批量)** | skill 已注册到 `~/.pi/agent/skills/evidence-wiki`(symlink → 本目录),pi 启动自动发现;不放心可显式 `--skill /home/mind/nut/edu/wiki/.skill` | `pi -p "你加载的 skills 里有 evidence-wiki 吗"` |
| **pi 交互会话(在 wiki 目录)** | `/extract <citekey>` 等 10 个命令(`.pi/prompts/`)+ skill 自动发现 | `/skills` 列表可见 evidence-wiki |
| **Claude 会话** | 已注册 `~/.claude/skills/evidence-wiki`(symlink → 本目录) | `/skills` 列表可见 |

## 标准调用模板(subprocess 必须逐字使用)

任何脚本调用 pi 抽取论文时,prompt **必须以本前缀开头**(禁止改写、禁止省略):

```bash
pi -p "$(cat /home/mind/nut/edu/wiki/.skill/INVOKE-PREFIX.txt) 处理 <citekey>" \
   --model "MiniMax-M3[1m]"
```

## 禁例(违反 = 返工)

1. ❌ prompt 里硬编码字段描述("抽 14 字段 + 写 2-3 个 claim"之类)——字段契约只在 `.skill/references/templates/` 与 ARCHITECTURE §3
2. ❌ 不带 INVOKE 前缀直接 `pi -p "你是论文抽取助手..."`
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
