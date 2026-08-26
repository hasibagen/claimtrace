# LESSONS · 过程问题与经验沉淀

> **定位**:记录执行过程中的工具/流程/数据陷阱教训,**供后续优化**。与 ARCHITECTURE §15(数据问题修复史)互补:§15 记"改了什么数据",本文件记"为什么会踩坑 + 以后怎么防"。
> **维护规则**:每次返工/事故/用户纠偏,完成后**必须**在此追加一条(append-only,带日期)。agent 优化 skill 前先读本文件。

---

## L-001 · skill 从未被真正调用(2026-08-25,🔴 最高教训)

- **现象**:pi cli 被脚本调用时自己重写 prompt(硬编码"抽 14 字段+写 2-3 个 claim"),不读 `.skill/` 的 SKILL.md/templates;8 个 pi session log 中 `.skill/` Read 次数 = 0;Claude 会话中 `/skills` 也看不到。12 篇重抽全部字段可能不完整。
- **根因**:pi 是 npm 全局包,只读 `~/.pi/agent/`(skills/prompts/extensions),**不读项目目录的 `.skill/`**;Claude 的 skills 在 `~/.claude/skills/`。两边都没注册。
- **修复**:① `~/.pi/agent/skills/evidence-wiki` → symlink 到 wiki/.skill(已验证 pi 能发现);② `~/.claude/skills/evidence-wiki` 同款 symlink;③ 建 `.skill/INVOKE.md` + `INVOKE-PREFIX.txt` 标准调用前缀,所有 subprocess 调 pi 必须逐字使用。
- **预防**:批量脚本 prompt 禁止硬编码字段描述;新会话开工先验证 `pi -p "skills 里有 evidence-wiki 吗"`。

## L-002 · YAML round-trip 损坏 wikilink(2026-08-25,🔴)

- **现象**:51 个 papers 的 `paperinfo: "[[x]]"` 变成 `[['x']]` 嵌套列表、三层嵌套、括号不平衡;行内注释全丢。
- **根因**:用 `yaml.safe_load → dump/手拼` 重写 frontmatter——`[[x]]` 不带引号时被 YAML 解析成嵌套数组;含 `#` 的注释被当注释丢弃。
- **修复**:`wiki_common.dump_frontmatter_safe`(拍平嵌套 + wikilink/中文/含特殊字符值强制双引号);一次性规范化 69 个 papers。
- **预防**:**任何脚本要写 frontmatter,一律用 `dump_frontmatter_safe`,禁止手拼、禁止 yaml.dump 原样回写**。渲染器保持"frontmatter 字节级不动"原则。

## L-003 · 手写正则改 frontmatter 出乱子(2026-08-25,来自用户另一会话经验)

- **现象**:evidence 文件原文引用重复多次、frontmatter 内容混进正文、引用不完整。
- **根因**:用 Python 正则处理 YAML 多行格式(`prov_source_text: >-\n  ...`),正则无法可靠解析 YAML。
- **预防**:**改 frontmatter 用 PyYAML 读 + dump_frontmatter_safe 写;改正文用渲染器**。永远不要用正则改语义内容(铁律 #4 的推论)。

## L-004 · paperinfo citekey 错位(2026-08-25,来自用户另一会话经验)

- **现象**:`raw/zhao_2022_eur_j_neurosci/` 实际是 Cerebral Cortex 论文,paperinfo 却指向另一篇 EJN 论文。
- **根因**:Zotero 同步时 citekey 冲突,pi 的 citekey 推断自动匹配了错误的 paperinfo。
- **修复**:重命名 raw 目录为正确 citekey + 更新全部引用。
- **预防**:**S1 执行时必须验证 `raw/<citekey>/full.md` 的标题与 paperinfo.title 匹配**(已写入 ARCHITECTURE §5.0 S1 检查项)。

## L-005 · pi cli 必须显式指定模型(2026-08-25,来自用户另一会话经验)

- **现象**:`[1214][modelCode:不存在]` API 错误。
- **根因**:pi 默认模型配置缺失/不正确。
- **预防**:统一 `--model "MiniMax-M3[1m]"`(已写入 INVOKE.md 标准模板);建议在 `.pirc` 配默认模型。

## L-006 · 双层手写漂移(2026-08-25)

- **现象**:AI 抽取常只写 frontmatter 或只写正文一半("这三篇 evidence 里都没有原文")。
- **根因**:frontmatter 与 body 两层都靠 LLM 并行手写 = 双写必漂移。
- **修复**:批次2 生成式视图——frontmatter 唯一维护面,body 全部 `wiki_render_nodes.py` 渲染。
- **预防**:新抽取走 S3 新流程(LLM 只写 frontmatter);**渲染后检查 body 含 AUTO-RENDERED-BODY banner**。

## L-007 · 并发 session 干扰(2026-08-25)

- **现象**:暂存区改动被并发 session 卷进它们的提交;渲染好的文件被另一 session 用不同格式(如 `(全文嵌入)` vs `(全文)`)实时覆写;detached HEAD 反复出现。
- **预防**:改完**立即 commit**;开工先 `git branch --show-current` 确认 main;格式冲突以 ARCHITECTURE 契约为准(渲染器输出 = 唯一标准)。

## L-008 · 新抽取 enum 自造值(2026-08-25)

- **现象**:新抽取 217/249 不过 schema(`verify_consensus: single_study/high`、`reasoning_type: platform_specification` 等自造值)。
- **根因**:S4 闸门(L1.5)原来只扫正式目录,00-pending 是盲区;LLM 不知道 enum 候选就编。
- **修复**:L1.5 扩扫 `00-pending/*/claims|evidence`;enum 清洗映射表。
- **预防**:抽取 prompt(INVOKE-PREFIX)已声明"禁止自行编造 enum 值";L1.5 在 promote 前拦截。

## L-009 · 中英文分工约定(2026-08-25,来自用户另一会话经验)

- **约定**:**论文原文引用用英文(verbatim),其余描述/解释用中文**。结果部分=中文总结+英文原文引用。已写入抽取约定。

## L-010 · PPT/外部资料整合(2026-08-25,来自用户另一会话经验)

- **现象**:pi 只读 full.md,不整合 PPT 中的补充信息(研究背景/被试详况)。
- **约定**:PPT 属外部资料,在 S6 人审阶段手动补充到 paper 叙事段(研究意义/被试特征),**不混入 evidence**(evidence 只能来自 raw full.md,Grounding 铁律)。

## L-011 · dict.get 与"None=合法值"映射表的语义冲突(2026-08-25)

- **现象**:清洗器每遍都报"修改 461/555",`[medium]`↔`[null]` 无限乒乓;lint None 计数随每次清洗波动,一度误判为并发干扰。
- **根因**:`CONFIDENCE_MAP = {"medium": None, ...}` 用 None 表示"已合法不变",但 `dict.get(key, default)` 把**键存在且值为 None** 也返回 None → 数组元素被写成 None → dump 成 null → 下遍又填回 medium。
- **预防**:映射表语义"None=不变"必须显式三分支(`v = m.get(k); if v: return v; ...`),**永远不要把 None 塞进 dict.get 的值域**;清洗类脚本必须做"第二遍 0 修改"幂等断言(已写入 test)。

## L-012 · 学位论文/非期刊文献的 paperinfo 判别(2026-08-25)

- **现象**:处理硕士论文版时,会话想新建 `LiuWenZheng_2022_thesis` paperinfo——实际上 `LiuWenZheng_2022`(DOI 10.27360/d.cnki)就是硕士论文,期刊版是另一个 key。险些造成同一论文双节点。
- **根因**:没有先查已有 paperinfo(按标题/DOI),直接按"文献类型"猜新 citekey。
- **预防**:**S1 匹配 paperinfo 必须按标题/DOI 查,不能按"我觉得需要新键"新建**;学位论文 DOI 特征 `10.27360/d.cnki`(CNKI)可直接判别;Zotero 条目 itemType=thesis。
- **配套修复**:`wiki_zotero.py` 的 sqlite fallback 改为"原库 ro 失败→复制临时副本(带 WAL)再读",Zotero 客户端运行时不再 database is locked;CNKI 导入常缺 creators → 按 §15.4.3 从 full.md 封面补(LiuWenZheng_2022 已补)。
