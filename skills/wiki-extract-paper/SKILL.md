---
name: wiki-extract-paper
description: >-
  EXTRACT one paper's full.md into paper/claim/evidence nodes via the 5-stage
  pipeline (T0 Ingest → T1 Scan → T2 Extract → T3 Evidence → T4 Audit).
  T0/T3 阶段 read `.skill/references/templates/` 下 paper.md + claim.md +
  evidence.md + paper-<modality>.md 和 `paper_stats.md` 作为字段契约;
  body 一律由 `wiki_render_nodes.py` 渲染(§5.0 S3) + `wiki_lint.py` 校验. 3 模式:quick-scan (review/methodology),
  deep-read (empirical core), audit (user question/30 天复检). 写入
  `00-pending/<citekey>/`. **NOT for**: creating single evidence (use
  wiki-build-evidence), cross-paper dedup (use wiki-stitch-knowledge). Use
  when user says "处理 [full.md|pdf]" or "/extract <path>" (PDF 输入先走 S0a 转 md).
---

# Wiki Extract Paper

将一篇论文的 `full.md` 抽取为 paper + claim + evidence 节点。

## 何时使用

| 触发 | 模式 |
|---|---|
| `处理 [full.md]` / `/extract <path>` | 根据论文类型选模式 |
| `处理 [pdf]`(未经 MinerU 的裸 PDF) | **先走 S0a 转 md**,再按论文类型选模式 |
| 用户没指定 | 默认 deep-read |

## S0a PDF→MD(可选步,输入是 PDF 时,ARCHITECTURE §5.0)

用户直接给 PDF(懒得先转 md)时,先机械转换再进 S1——转换本身**不含任何语义抽取**(铁律 3):

```bash
python3 .skill/scripts/wiki_pdf_to_md.py <pdf> [--citekey <ck>] [--lang ch] [--force]
# 或统一入口: wiki pdf2md <pdf> [--citekey <ck>]
```

- **citekey 已知**(canonical = paperinfo 节点名)→ 直转 `raw/<ck>/{full.md, images/}`,S1/S2 即完成
- **citekey 未知** → 暂存 `raw/_incoming/<pdf-stem>/`;S1 用暂存 full.md 的标题/DOI
  匹配或从 Zotero 创建 paperinfo 定 canonical citekey,**S2 把暂存目录整体移到
  `raw/<citekey>/`**(一次命名到位,永不改名,勿在 _incoming/ 里直接抽取)
- 幂等:目标已有 full.md 自动跳过;`--force` 重转
- >200 页警告:云端 API 慢且贵,改用本地 mineru(`conda run -n mineru
  mineru_local_batch.py`,见 <mineru-root>/)
- 暂存产物随 COMMIT AS YOU GO 一起提交,不留在 untracked 状态

## 标准作业顺序 S0-S7(ARCHITECTURE §5.0,不得跳步/调序)

```
S0 输入规范化   CSV(含 md 清单)/直接 md/PDF(PDF 先走 S0a wiki_pdf_to_md.py 转 md)
                → 单篇队列(CSV 解析只提路径,不碰语义)
S1 paperinfo 先 从 CSV 行/md 标题/DOI 匹配或从 Zotero 创建 paperinfo(用 paper key,
                勿用 attachment key);canonical citekey = paperinfo 节点名
S2 raw 复制     md 所在文件夹(zotero_md / raw/_incoming/ 暂存)→ raw/<citekey>/
                (full.md + images/),一次命名到位永不改名
S3 单篇抽取     ★ 本 Skill 主体:一篇论文 = 一次引擎调用(pi/codex 子进程,或 zcode 会话内;
                调用规范 = .skill/INVOKE.md,INVOKE-PREFIX 三引擎共用),只处理这一篇 → 00-pending/<citekey>/
                · **「LLM 只写 frontmatter」仅适用于 claim/evidence 节点**;paper 节点的
                  叙事章节(## 元信息/研究目的/被试/实验设计/…/结论/Code & Data)由 LLM
                  按 templates/paper.md「body 分工」**直接写散文**(含原文 quote 锚点)
                · **body 全部由 `wiki_render_nodes.py` 生成**的部分 = paper 的主张/证据表格 +
                  两大全文嵌入章节 + claim/evidence 的全部 body;S3 末尾跑一次渲染脚本
                · claim 链接已有优先(查 claims/ 索引),新建从严
                · topic 只链接已有,确需新建先查 topics/ 近重复(防碎片化)
                · evidence 原文即证据(prov_source_text,无 raw_path)
S4 机械检查     _registry frontmatter 校验 + lint L0/L0.5/L1/L1.5/L3 + **wiki_audit_pending.py 批次体检** + Grounding grep + wikilink 存在性
                → 任何一项不过退回 S3,不得进 S5
S5 互联         ① `wiki_link_paper.py` 自动补 paper.related_evidence/related_claims(从正向边反推)
                ② `wiki_render_nodes.py paper` 重生成嵌入段 + Backlinks Cache(反向链接段从正向边生成)
                ③ claim↔evidence 边表由渲染器出;完成标准 = 0 broken wikilink + 嵌入段非空
S6 人审         用户审阅 00-pending(清单见下方"用户审阅与 Promote")
S7 Promote      **闸门(wiki_promote.py)**:①L1.5 对该 citekey 0 error ②body 含 banner 且与 frontmatter 重渲染一致
                ③evidence 无 raw_path;过闸才 00-pending → 正式目录;index/log/git;批后 stitch-knowledge
```

**两处反直觉但必须遵守**:S1 在 S2 之前(raw 名 = canonical citekey,先定名再复制);topic 单篇只链接不新建。

## 3 模式(ARCHITECTURE §5.1)

| 模式 | 适用 | 耗时 | 输出 |
|---|---|---|---|
| **quick-scan** | 批量导入前初筛(只出 paper 不出 claim/evidence) | 30s | paper L1(元信息 + 5 字段摘要)|
| **deep-read** | 核心实证 + **综述/方法论/meta(T-W7-002,必须 deep-read)** | 5-8min | paper L1 + claim/evidence 完整 |
| **audit** | 用户质疑/30 天复检 | 2min | 校验修正 |

## 5 阶段流水线(模板作为字段契约贯穿全程)

```
T0 Ingest   →  读 full.md + 识别论文类型 + 加载模板(30s)
               ├─ read raw/<citekey>/full.md 识别 modality(fnirs/eeg/fmri/ml/multimodal/...)
               └─ read .skill/references/templates/paper.md(结构契约:目录布局/frontmatter/两大嵌入章节)
                  + paper-<modality>.md(模态叙事检查单)  ← 字段白名单契约
T1 Scan     →  对照模板「研究目的/被试/方法/结果/结论」5 字段,确认覆盖度(30s)
T2 Extract  →  按模板字段白名单抽 14 字段 + CLAIM + EVIDENCE(5-8min)
               ├─ claim frontmatter 契约:.skill/references/templates/claim.md(35 字段+平行数组+禁字段)
               ├─ evidence frontmatter 契约:.skill/references/templates/evidence.md
               │  (prov_source_text 散文原句硬规则 + 无 raw_path + verify_* 数值规范)
               ├─ ★ Code & Data 强制捕获(2026-09-03):扫 Availability 声明/脚注/致谢/附录,
               │  GitHub/GitLab/Zenodo/OSF/Figshare/Dryad/HF 等代码·数据·材料·模型链接
               │  一律不漏 → frontmatter code_urls/data_url + 正文 `## Code & Data` 章节
               │  (契约 = templates/paper.md body 分工;缺章节 audit B11 退回)
               **节点数量无硬性限制**(ARCHITECTURE §2.4,T-W4-032):
               - 推荐每篇 3-8 CLAIM + 3-10 EVIDENCE
               - 上限警告:> 20 CLAIM / > 30 EVIDENCE 需 LLM 评估是否过度拆解
               - 质量优先:宁可少而精,不为完整性虚构
               ├─ ★ 深度契约(2026-09-16,契约=templates/claim.md「深度契约」节):
               │  每条 claim 过「深度五问」(方向/条件/机制/边界与 hedging/前人关系),
               │  statement 按五要素构成式写;reasoning=warrant+机制,empirical claim ≥40 字;
               │  新增 6 optional 字段 role_in_paper/polarity/epistemic_stance/qualifier/
               │  boundary/alternative_explanations(无则不写,禁空串)
               ├─ ★ T2b 深度回读段(deep-read only,同一次引擎调用内,非二次调用):
               │  对 role_in_paper=central 的 1-3 条 claim,重读 raw 的 Discussion/Limitations,
               │  补全 qualifier/boundary/alternative_explanations + 连 supports 上位边
               │  (先查 claims/ 索引,链接已有优先)
               ├─ ★ 分节差异化(2026-09-16):Results→数值 evidence(verify_* 全捕);
               │  Discussion→与前人关系(secondary_citation evidence + supports/contradicts 边)
               │  +替代解释+局限→boundary+hedging→qualifier;Methods→操纵 rationale/关键参数
               │  →paper 叙事段;Intro→领域争议与 gap→paper 研究目的段;
               │  负结果默认建 claim(polarity=null_result/negative)
T3 Evidence →  evidence 提升到 evidence/,建立 evidence × claim matrix(3min)
               ├─ read .skill/references/templates/paper_stats.md  ← 统计字段契约
               ├─ 数值事实按 paper_stats.test_method 候选清单识别检验方法
               ├─ 效应量按 paper_stats.effect_size_type 候选清单标注(d/g/η²/R²/...)
               └─ 多重比较按 paper_stats.p_method 候选清单标注(FWE/FDR/cluster/TFCE/...)
T4 Audit    →  校验 quote/数值/wikilink + verify_* 字段必填(2min)
               ├─ python3 .skill/scripts/wiki_render_nodes.py evidence 00-pending/<citekey>/evidence/  ← body 全渲染(P0-2 修复后就地渲染)
               └─ python3 .skill/scripts/schemas/_registry.py evidence <file.md>  ← schema 校验
```

## LLM→JSON→MD 流水线(ARCHITECTURE §5.2)

```
Stage 1: LLM 输出 JSON(claim/evidence 各一份;字段契约 = templates/claim.md + evidence.md)
Stage 2: scripts/jsonschema 校验(ARCHITECTURE §3.8 Evidence Contract)
Stage 3: frontmatter 写入 00-pending/<citekey>/(dump_frontmatter_safe)
Stage 4: body 由 wiki_render_nodes.py 渲染(LLM 不写任何 body 段)
```

## 节点命名(ARCHITECTURE §2.3 + T-W4-030)

- paper:`papers/<BBT-citekey>.md`(ASCII citekey 形式,如 `zhang_2021_fnirs.md`)
- claim:`claims/<semantic-slug>.md`(优先中文 + 真实空格,无编号)
- evidence:`evidence/<author>-<year>-<slug>.md`(中英混合 + 真实空格,无编号)

## 输出契约硬约束(2026-08-26 孪生脑批次问题谱系固化,违反 = S4 退回)

1. **一个目录一个 paper 文件**:00-pending/<citekey>/ 内**只允许** `<citekey>.md` 一个顶层 md;
   禁止再出现 `paper.md` 等第二份(重复抽取影子文件)。
2. **paper 正文必须有两大全文嵌入章节**(由 S5 渲染器从 frontmatter 生成,LLM 不手写):
   `## 本论文的 Evidence(全文)` 与 `## 本论文支持的 Claims(全文)`;
   无 evidence/claim 时章节也要保留(渲染器输出空段)。前置条件 = frontmatter
   `related_evidence`/`related_claims` 完整且全部 `[[wikilink]]` 格式(裸字符串在
   Obsidian 属性面板不构成链接,S5 由 `wiki_link_paper.py` 语义反推补全)。
3. **evidence 的 prov_source_text 必须是 raw 中可 grep 命中的散文原句**:
   禁止 HTML 表格碎片(`<td>`/`<tr>` 串)、禁止截断开头(如 `lation between…`)、
   禁止 `(待补)` 占位;数值只在表格里时,改锚表格标题/结果段的散文句。
4. **evidence 无 raw_path**(S7 闸门既有条款);raw 唯一权威位置 = `raw/<citekey>/full.md`,
   由 S2 复制,extract 时不得引用 zotero_md 绝对路径作为长期指向。
5. **claim 不携带 prov_paper/prov_source_text 字段**(claim schema 无此二字段;claim 的
   出处走 `sources_targets`(→paper)+ `evidence_targets`(→evidence),证据原文在
   evidence 节点上);禁止 `[[papers/TODO]]`、`(待补)` 之类占位值,statement 禁止退化成标题。
6. **批次级查重先于抽取**:新批次开工前先跑 DOI/raw-md5/标题三元对撞
   (pending ⇄ papers/ 与 pending ⇄ pending),命中即跳过或走 canonical 合并,
   不得对同一论文产生第二个抽取目录。
7. **YAML 写回一律 `dump_frontmatter_safe`**:浮点 e 记数法自动补小数点
   (`1e-20`→`1.0e-20`,YAML 1.1 无点读回为 str),浅层 dict 用 flow 映射
   (`field_status: {mode: reported}`),控制字符必须先清洗。
8. **`## Code & Data` 章节必备(2026-09-03)**:paper 正文必须有该章节 — 本论文的代码/数据/
   材料/模型链接(GitHub/GitLab/Zenodo/OSF/Figshare/Dryad/HF/数据请求表单…)逐条列出
   +一句话内容说明,并同步 frontmatter `code_urls`/`data_url`;确无则写明「原文未提供
   公开代码/数据」;仅在参考文献中引用的他人仓库不算。缺章节 = audit B11 退回;
   frontmatter 有 URL 而正文未整理同样退回。

9. **schema 枚举速查与引句铁律(2026-09-04/06 批次实测坑固化,源自 _tmp_zc_spec_lib)**:
   - **verify_test_method 无** `bootstrap`(→`permutation_test`)、无 ROC 类(→`descriptive`);
     **verify_effect_size_type 无** `odds_ratio`/`auc`(→`OR`/`na` + verify_note 记数值);
     **verify_p_method** 校正 `fdr`→`fdr_bh`;**verify_test_stat_type** 无 `p`(按检验选 F/t);
     **claim_type 无** `methodology_result`(→`methodological`)。
   - **引句铁律**:prov_source_text 避开含 LaTeX/`\mathsf`/`\mathrm`/统计式/HTML sup 标签的句子
     (MinerU 会转成 `$\mathsf{F}(2,14)=9.69$` 形态,复制极易 grounding-MISS)——
     选纯散文段,数值放 observation 与 verify_* 字段。
   - **OCR 控制字符**:连字丢失可能表现为 `\x1f` 控制符或字面 `|`(NFKC 不消控制符)——
     引句必须逐字节核对,含控制符的句子绕开。
   - **claim slug 禁 `/`**(会生成子目录路径)。
   - **modality 等 schema 枚举字段的值不做术语大小写替换**(`modality: fnirs` 是合法枚举,
     术语规则 A 只作用于散文正文;normalize_terms 已加枚举字段保护)。

S4 体检命令:`python3 .skill/scripts/wiki_audit_pending.py`(检查 A1-A6/B1-B10/C0-C8,
含 B10 两大章节存在性;退出非 0 即有残留,逐条修复后复跑至 0)。

**⚠️ Claim 文件名禁例(2026-08-25 lint 修复)**:
- **禁数学符号**:`+` `=` `[` `]` `(` `)` `^` `%` `,` — 这些**公式应写在 `statement` 字段或 body 代码块**,**不**在文件名
- **禁附加标记**:`(paula 2015 抽取)`、`(author 抽取)`、`(2024 重抽)` 等抽取元信息**不**写在文件名 — 文件名是**语义 slug**,**不**是抽取日志
- **字符集**:中文(CJK) / 日文(假名) / ASCII 字母数字 / 空格 / `-` `_` `.`(wiki_lint 字符白名单)
- **长度**:建议 ≤ 30 字,过长截取核心语义
- **正确 vs 错误**:
 - ✓ `BNM 通过三层耦合支持双尺度空间.md`
 - ✗ `BNM 通过三层耦合 ν0 ν1 ν2 支持双尺度空间 (paula 2015 抽取).md`
 - ✓ `TVB 集成八套神经质量模型与四类前向模型.md`
 - ✗ `TVB 集成 8 套神经质量模型与 4 类多模态前向模型于同一神经活动源 (paula 2015 抽取).md`
 - ✓ `BVEP 100 准确反演 84 脑区空间癫痫源性.md`
 - ✗ `BVEP 100% 准确反演 84 脑区空间癫痫源性.md`
 - ✓ `z3 全局潜状态作为虚拟药物干预靶点.md`
 - ✗ `z(3) 全局潜状态作为虚拟药物干预靶点.md`

## 边界

- 写入 `00-pending/`,**不**直接写 `papers/` / `claims/` / `evidence/`
- 用户审阅后才移到正式目录
- scripts 只做机械校验(YAML / jsonschema / wikilink 存在性)
- LLM 负责**所有**语义抽取
- **不用正则**抽取任何字段(ARCHITECTURE §1.2 铁律 4)

## 关联

- 数据模型:`ARCHITECTURE.md §3`
- 模板:`.skill/references/templates/paper.md`(结构)+ `claim.md`/`evidence.md`(字段契约)+ `paper-<modality>.md`(模态检查单)
- 路由表:`wiki/AGENTS.md §2`

## 关联 Skill

- 完成后调 `wiki-stitch-knowledge`(合并跨论文重复)
- 审阅时调 `wiki-lint-wiki`(L0-L3 校验)

## 用户审阅与 Promote

抽取完成后,用户必须审阅后才移到正式目录。

### 审阅清单

- [ ] **paper.md** 元信息完整(作者、年份、DOI、模态)
- [ ] **paper.md** 14 字段填全
- [ ] **paper.md** 核心主张表格列出 CLAIM(语义 slug wikilink)
- [ ] **paper.md** 证据条目表格列出 EVIDENCE(语义 slug wikilink)
- [ ] **paper.md** 正文含 `## 本论文的 Evidence(全文)` 章节(`> [!evidence]+` + `![[slug]]` 嵌入)
- [ ] **paper.md** 正文含 `## 本论文支持的 Claims(全文)` 章节(`> [!claim]+` + `![[slug]]` 嵌入)
- [ ] **paper.md** 含 `## Code & Data` 章节(代码/数据链接逐条整理;确无则写明未提供)
- [ ] **claims/<slug>.md** 字段完整 + verification 正确(无 prov_paper/prov_source_text 残留)
- [ ] **evidence/<slug>.md** provenance 可定位到 raw(prov_source_text 为散文原句,无 raw_path)

### Promote 命令

```bash
# 单篇 promote(从 00-pending/  移到正式目录)
python3 .skill/scripts/wiki_promote.py <citekey>   # S7 闸门脚本(过闸才 promote)

# 批量 promote
for citekey in <list>; do
  python3 .skill/scripts/wiki_promote.py $citekey
done
```

### Promote 后动作(脚本自动化)

```bash
# 触发 stitch-knowledge
# 批后跨论文去重:按 wiki-stitch-knowledge 微 Skill 的 LLM 流程执行(输出提案 → 人审)

# 触发 lint
python3 .skill/scripts/wiki_lint.py

# 写 log/ops.md(promote 记录 wiki_promote.py --execute 会自动追加;手动补记用此命令)
echo "## [$(date +%Y-%m-%d)] promote | <citekey>" >> log/ops.md

# git tag
git tag -a "wiki-paper-<citekey>" -m "<citekey> promoted to formal"
```

### 失败回滚

```bash
jj undo                                  # 回滚单个 promote
# 或
git reset --hard wiki-paper-<citekey>~1  # git 硬回滚
```

### 批次完成检查(20/50/100/197)

每批次完成后:

- [ ] 全部 promoted
- [ ] L0-L3 lint 全通过
- [ ] git tag checkpoint 已创建
- [ ] log/ops.md 已记录;所属批次文件(log/batch-*.md)状态已刷新(`wiki_batch_status.py`)
- [ ] index.md 已重建
- [ ] 同步 `tasks.md`(状态变更)
- [ ] 同步 `ARCHITECTURE.md`(如有架构变)

## Resources

- `ARCHITECTURE.md §5` 抽取工作流
- `ARCHITECTURE.md §3.8` Evidence Contract (JSON Schema)
- `.skill/references/templates/` 节点模板(paper/claim/evidence/paper-<modality>/paper_stats)
- `.skill/scripts/schemas/evidence.schema.json`
- 批量/并行编排:**直接 LLM cli(pi / codex,`--engine` 切换)或 zcode 会话内,禁用 sub-agent 编排**
  (2026-08-27 用户指令禁 sub-agent;2026-09-04 解除"固定 pi",三引擎等价)。批量一律用
  `.skill/scripts/wiki_run_extract.sh`(一篇=一次引擎调用,落盘即 commit+篇级锁;zcode 会话内
  抽取须自持锁 + 落盘即 commit,同受铁律 #12/#13 约束),N 路并行 = N 个 runner 后台进程瓜分
  不重叠列表,见 `ARCHITECTURE.md §8`;
  历史迁移已完成(MIGRATION_PLAN 并入 tasks.md T-W1-007)