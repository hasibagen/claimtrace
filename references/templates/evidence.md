# EVIDENCE 节点模板(frontmatter 契约,2026-08-26 新建,对齐 evidence.schema.json)

> **本文件 = evidence 的字段契约**(此前缺失,2026-08-26 补建)。schema 权威版:`.skill/scripts/schemas/evidence.schema.json`。
> **LLM 只写 frontmatter,body 全部由 `wiki_render_nodes.py evidence` 渲染**——不写 观察/原文引用/解释/出处/数值校验 等任何 body 段。

## 文件与命名

- 路径:`00-pending/<citekey>/evidence/<author>-<year>-<slug>.md`(promote 后 → `evidence/`)
- 命名:`<author 姓小写>-<year>-<语义 slug>`,中英混合 + 真实空格,禁编号、禁数学符号
- 例:`aerts-2018-fc-prediction-improved-by-individual-tuning.md`

## frontmatter 字段(必填 ★ / 枚举 ∷)

```yaml
---
type: evidence                   # ★ 固定
schema_version: plan_final_v1
evidence_id: <citekey>-E<n>-<slug>
fact_type: empirical_result      # ★ ∷ empirical_result|observation|methodology|secondary_citation
source: '[[<本论文 citekey>]]'    # 源论文 wikilink
observation: >-                  # ★ 客观观察(英文原句可,数值 verbatim);可附 [原文锚点] "..."
interp_origin: author            # ★ ∷ author|reviewer|system(解释出自谁)
interp_text: 中文解读,与 observation 的数字严格一致
prov_paper: '[[<本论文 citekey>]]'   # ★ 出处块 4 件套
prov_section: Results §1; Fig. 2     # ★ 章节/图表定位
prov_page: 7
prov_paragraph: 2
prov_source_text: >-             # ★★ 原文 verbatim 引用(见下方硬规则)
  After tuning the model parameters, the link-wise Pearson correlation was on
  average 0.33 across subjects (SD=0.09) ...
extract_model: MiniMax-M3        # 抽取溯源 5 件套
extract_timestamp: '2026-08-26'
extract_method: llm_semantic     # ∷ llm_semantic
extract_temperature: 0.2
verify_status: verified          # ∷ verified|unverified|flagged
verify_verifier: LLM
verify_n: 36                     # ★ 样本量(数值,非字符串)
verify_test_method: anova_one_way   # ★ 候选清单见 paper_stats.md
verify_test_stat_type: F         # F|t|χ²|r|z|W|...
verify_test_stat_value: 6.34     # 统计量数值(真数字)
verify_effect_size_type: eta_squared   # d|g|η²|R²|...(paper_stats.md 候选)
verify_effect_size_value: null
verify_ci_95: null               # 如 0.45-0.65;无则 null
verify_df: 140                   # 自由度(纯数值;逗号串如 '2,58' 必须拆成数字)
verify_p_value: 0.0005           # 科学计数法必须 1.0e-20 式带点
verify_p_method: uncorrected     # FWE|FDR|cluster|TFCE|uncorrected|na|not_applicable
verify_note: >-                  # 多重比较/事后检验/CI 解读备注
supports_targets: ['[[<claim slug>]]']   # 支持的 claim([[wikilink]] 列表)
supports_confidences: [high]     # 平行等长 ∷ high|medium|low
supports_relations: [direct]     # ∷ direct|indirect|partial
contradicts_targets: []
contradicts_confidences: []
contradicts_relations: []
qualifies_targets: []
qualifies_confidences: []
qualifies_relations: []
strength: strong                 # ∷ strong|moderate|weak
extraction_confidence: 0.95      # LLM 自评 0-1
field_status: {mode: reported}   # reported|derived|estimated;flow 单行映射
scope_region: whole_brain
---
```

## prov_source_text 硬规则(2026-08-26 批次教训固化)

1. **raw full.md 中可 grep 命中的 verbatim 散文原句**(归一化后子串匹配;铁律 7/8)。
2. **禁止**:
   - HTML 表格碎片(`<td>`/`<tr>`/`<table>` 串)——数值只在表格时,改锚**表格标题/结果段散文句**,或 caption 句
   - 截断开头(如 `lation between …` 从词中间起头)——从句子边界起
   - `(待补)` / 空值占位
   - 转述改写(LLM 自己的话)——必须是原文
3. 长度 ≥ 20 字符,建议 ≤ 600;含全部关键数值最佳。
4. **无 raw_path 字段**(S7 闸门条款):raw 唯一权威位置 = `raw/<citekey>/full.md`,由 S2 复制;evidence 节点不携带任何 raw 路径。

## verify_* 数值规范

- 全部真数字(`verify_df: 140` ✓ / `'2,58'` ✗ / `140` 字符串 ✗);科学计数法带小数点
- 无报告值用 `null`,禁写描述串(如 `p=ns`、`>0.05` → 拆到 verify_note)
- `verify_test_method` / `effect_size_type` / `p_method` 用 paper_stats.md 候选清单里的标准词
