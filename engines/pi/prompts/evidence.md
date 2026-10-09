---
description: 把一条事实固化为 evidence 节点
argument-hint: "<quote text or paper citation>"
---

请创建一条 evidence 节点: $1

## 步骤

1. read `.skill/skills/wiki-build-evidence/SKILL.md` 获取字段定义(T-W4-026 升级:11 verify_* 平铺)
2. **observation 必须是原文 verbatim**(从 raw full.md 复制,20+ 字符)
3. 必填:provenance(扁平化为 prov_paper / prov_section / prov_page / prov_source_text / extract_*)
4. **数值校验**(顶层平铺,11 字段):
   - `verify_n`(必填,样本量)
   - `verify_test_method`(必填,enum 候选见 schema $defs.test_method_enum,37 个)
   - `verify_test_stat_type`(枚举:20 候选)
   - `verify_test_stat_value`(数值,null=未报告)
   - `verify_effect_size_type`(枚举:16 候选)
   - `verify_effect_size_value`(数值,null=未报告)
   - `verify_ci_95`(字符串,如 `"[0.18, 0.50]"`,null=未报告)
   - `verify_df`(整数,null=未报告)
   - `verify_p_value`(数值,[0,1],null=未报告)
   - `verify_p_method`(枚举:11 候选)
   - `verify_note`(字符串,未报告字段说明)
5. 关系(扁平化为 3 平行数组):`supports_targets` / `supports_confidences` / `supports_relations`(同 contradicts_*/qualifies_*)
6. 命名:`<author>-<year>-<short-keyword>.md`(**优先中文 + 真实空格**,如 `boisgontier-2026 PWS 婴儿 3 脑区 CBF 增高`;中英混合 / kebab-case 也允许;不用 `-` 替代真实空格,plan_final §2.3 + T-W4-030)
7. write 到 `00-pending/<slug>.md`
8. 跑 `python3 .skill/scripts/wiki_render_evidence_body.py <file>.md` 自动渲染 `## 数值校验` 表格(body 只渲染不维护)

## 约束

- Grounding Invariant:每个数字必须在 raw 中可 grep(plan_final §5.3)
- prov_source_text(扁平化字段)必须**可定位**到 raw full.md
- 不直接写 `evidence/`,先放 `00-pending/`