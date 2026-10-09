# 2026-10-08 zcode CLI 引擎接线 plan

> 背景:用户配置好了 zcode CLI 的 headless 能力,指令"后面提取可以用 zcode cli 做"。
> 勘察结论:`zcode -p "<prompt>" --cwd <path>` 冒烟通过(0.16.9,`-p` 默认 yolo 模式可写),
> 与 pi/codex 子进程形态同构 → zcode 从"仅会话内"升级为"可被 runner 拉起的第三引擎"。

## 改动清单(本次)

| 文件 | 改动 | 状态 |
|---|---|---|
| `AGENTS.md` §0.5 | zcode 条目:headless 可用(`zcode -p --cwd`,runner `--engine zcode`);模型=客户端配置,首选 GLM-5.3-Flash(2026-09-17 用户指令);会话内模式保留 | ✅ |
| `.skill/INVOKE.md` | 唤起路径表拆"zcode cli(headless)"+"zcode 会话(交互)"两行;标准模板引擎 3 换成真实命令;runner 示例加 `--engine zcode` | ✅ |
| `.skill/scripts/wiki_run_extract.sh` | 删 zcode 报错分支;`--engine zcode` 走 `timeout 3600 zcode -p "<PREFIX> 处理 <ck>(自持锁注记)" --cwd <wiki-root>`;--provider/--model 对 zcode 忽略并提示;COMMIT_TAG `engine=zcode(model=client-config)` | ✅ |
| `log/ops.md` | append 一条施工记录 | ✅ |

## 验证(2026-10-08 实测全绿)

| 测试 | 输入 | 期望/实测 |
|---|---|---|
| T1 | `--engine zcode AnZongHui_2019_`(HEAD 已有) | `[skip-done]` ✅ |
| T2 | `--engine zcode petitto_2012_brain_lang`(字节级从 raw/ 派生的 ck,有 `.zcodeidle` 锁) | `[skip-locked]` ✅ |
| T3 | `--engine zcode --model foo --provider bar AnZongHui_2019_`(**flag 乱序**) | 两条 engine-note + `[skip-done]` ✅(修复后;修复前 `--provider` 被当 citekey) |
| T4 | `--engine bogus someck` | `[engine-error]` exit 1 ✅ |
| T5 | 无参 | 用法 + exit 1 ✅ |
| T6 | `-- --provider AnZongHui_2019_` | `[ck-invalid]` ×2 + 正常 `[skip-done]` ✅ |

另:`bash -n` 语法通过;`zcode -p --cwd /tmp` 冒烟通过(0.16.9)。

## 计划外:两个 runner bug 修复 + 误触发事故记录(同日)

1. **flag 解析顺序敏感**(存量 bug,本次暴露):旧版单遍 if 依次匹配 `--engine→--provider→--model`,`--model X --provider Y` 顺序会使 `--provider` 漏配、被当 citekey **发动真实垃圾抽取**(实测发生,已当场终止)。修复:while/case 循环,顺序无关。
2. **citekey 守卫缺失**:新增 `[ck-invalid]`(`-*`/空参拦截)+ `[ck-warn]`(raw 缺失警告,不拦截以保留引擎登记缺陷流程)。
3. **事故坦白**:测试者手误把 `petitto_2012_brain_lang` 多打一个 t(`pettito`),锁检查正确判无锁 → 发动了一次约 10 分钟的 headless 空转抽取(typo 拼写无 raw/paperinfo),已 kill 三进程 + 清 typo 锁,**零产物残留**。教训:citekey 一律从文件系统派生/字节级核对,近似姓氏(Petitto/Petitto 类)肉眼不可分,`od -c` 验真。

## 挂起项(不属本次)

- **`.skill/ARCHITECTURE.md` §8.0 引擎矩阵 zcode 行**(现仍写"无 headless CLI"):该文件有 2026-09-04 遗留的 1750 行未提交改动(根 `ARCHITECTURE.md` 同步被删未提交,疑似契约文件搬迁未收尾)。为避免把半成品卷进提交,本次不动;**搬迁由用户决断落定后**,把 §8.0 zcode 行同步为 headless 表述。
- 真实单篇抽取试点(需用户提供 citekey;批量启动前按 §0.5 与用户确认引擎+模型)。
