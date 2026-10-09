---
name: wiki-audit-paper
description: >-
  AUDIT one paper or node with critical-question checklist (CERIC 的 Critique 要素,
  补 T4 机械校验之外的语义审问). 8-10 固定批判问题 + paper 可选 **我的判断** 段.
  Use when user says "审阅这篇" / "/audit <node>" / 质疑某论文抽取质量 / 30 天复检.
  NOT for: 机械 lint (use wiki-lint-wiki), 重新抽取 (use wiki-extract-paper).
---

# Wiki Audit Paper · 批判性审问(CERIC-C)

> T4 的机械校验(quote/数值/wikilink)抓不住**语义级问题**("不显著被抄成显著"、
> "claim 宽而证据窄")。本 Skill 用固定批判提问清单审问,产出写进 paper 的
> `**我的判断**` 段(可选)与 audit 记录。

## 流程

1. 读目标 `papers/<citekey>.md` + 其 claim/evidence(用渲染后的 body)
2. 跑机械底座:`wiki_lint.py --layer L3` + `wiki_stat_sanity.py`(先排数值雷)
3. 逐条审问下方清单,**每条给 verdict**(✓ 通过 / ⚠ 疑点 / ✗ 问题)+ 一句话证据
4. 产出:
   - paper 正文追加 `**我的判断**` 段(最有启发/可借鉴/可追问/与研究关联/风险)
   - 发现的抽取错误 → 修 frontmatter 后**重跑渲染器**
   - log/ops.md 记录 audit 结论

## 批判性提问清单(固定 10 问,6 个 AI 共识 + Walton 模式)

1. **方法配得上问题吗?** 研究设计能回答它声称的问题?(横断≠因果;仿真≠实证)
2. **claim 宽而证据窄?** statement 的 scope 是否超出证据覆盖(population/modality/task)?
3. **方向核对**:evidence 的 prov_source_text 里"显著/不显著、升/降"与 claim statement 方向一致?
4. **混杂与对照**:有关键混杂未控制?对照组合理?(临床尤其)
5. **样本与效力**:N 是否支撑结论强度?verify_strength 与 N 匹配?
6. **多重比较**:p_method 是否如实反映校正?未校正的批量大扫描被当单结论?
7. **二手引文**:Intro/Discussion 转述的他人结果是否被标 secondary_citation 而非本文实证?
8. **循环论证/数据泄漏**:方法(如拟合指标)是否与评价指标同源?
9. **利益与偏倚**:预注册?选择性报告?(能从文中判断多少)
10. **可复现**:参数/代码/数据可得性(与 claim 的 methodological 主张一致?)

## 边界

- 审问≠重抽:发现抽取错误修 frontmatter(渲染器出 body),语义分歧报告用户裁决
- **我的判断**段是个人观点层,与 evidence(原文事实)严格分开,不混入数值字段
