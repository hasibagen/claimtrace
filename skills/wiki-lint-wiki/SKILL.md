---
name: wiki-lint-wiki
description: >-
  RUN 5-layer lint on the wiki (no writes, only reports errors). L0 Structure
  (file exists, naming convention `<semantic-slug>.md` 优先中文 + 真实空格,
  frontmatter, wikilinks), L1 Evidence (jsonschema validation against
  `.skill/scripts/schemas/` + numeric range), L2 Semantic (claim-evidence
  relations, edge type, LLM judges), L3 Consistency (Grounding grep into raw/,
  claim/evidence slug uniqueness), L4.6 raw path (csv-source-path 必须指向
  wiki/raw/ 存在). Run via /lint or `python3 .skill/scripts/wiki_lint.py
  --layer <L0|L0.5|L1|L2|L3|L4.6|all>`. **NOT for**: fixing errors (reports
  only); cross-paper dedup (use wiki-stitch-knowledge).
---

# Wiki Lint Wiki

4 层健康检查(L0-L3)。

## 何时使用

- 用户说:`/lint` / `检查 wiki` / `检查状态`
- 每次 T3 完成后(批量)
- 写入节点后(单次,自动)
- 每周一次(全量)

## 4 层(ARCHITECTURE §7)

| 层 | 谁做 | 工具 | 检查 |
|---|---|---|---|
| **L0 Structure** | scripts | `Extension: wiki_check_wikilinks` | 文件存在、命名、frontmatter YAML |
| **L1 Evidence** | scripts | jsonschema | 必填字段、枚举值、jsonschema |
| **L2 Semantic** | LLM | 人工 + scripts 配对 | CLAIM-EVIDENCE 关系、stitch 去重 |
| **L3 Consistency** | scripts | grep | Grounding、数值区间、claim/evidence slug 引用计数 |

## 实施

### L0 Structure(scripts 自动)

```bash
# 文件存在
for f in paperinfo/*.md papers/*.md claims/*.md evidence/*.md; do
  [ -f "$f" ] || echo "MISSING: $f"
done

# frontmatter YAML 解析
python3 -c "import yaml; yaml.safe_load(open('claims/<slug>.md'))"

# wikilink 目标存在
python3 scripts/wiki_check_wikilinks.py
```

### L1 Evidence(scripts + jsonschema)

```bash
# 3 套 jsonschema 校验
python3 -c "
import jsonschema, json
schema = json.load(open('.skill/scripts/schemas/evidence.schema.json'))
data = yaml.safe_load(open('evidence/<slug>.md'))
jsonschema.validate(data, schema)
"
```

### L2 Semantic(LLM 主导)

- scripts 输出"待 LLM 校验"清单
- LLM 校验:CLAIM 是否原子化 / RELATION 是否合理 / EVIDENCE 是否支持 CLAIM

### L3 Consistency(scripts + Grounding grep)

```bash
# Grounding: paper.md 的每个数字必须在 raw 中可 grep
for num in $(grep -oP '\d+\.\d+' papers/<slug>.md); do
  grep -q "$num" raw/<slug>/full.md || echo "FLAGGED: $num"
done

# 数值区间
python3 -c "
for f in claims/*.md:
    data = yaml.safe_load(open(f))
    v = data.get('verification', {}).get('confidence', None)
    if v is not None and not (0 <= v <= 1):
        print(f'OUT_OF_RANGE: {f}')
"
```

## 输出格式

```markdown
# Wiki Lint 报告 · YYYY-MM-DD HH:MM

## 总结
- 节点总数:N
- L0 问题:L0_count
- L1 问题:L1_count
- L2 问题:L2_count
- L3 问题:L3_count
- 严重错误:severe_count

## L0 Structure
- ❌ MISSING: paperinfo/<slug>.md
- ❌ BAD_FRONTMATTER: claims/<slug>.md

## L1 Evidence
- ❌ MISSING_FIELD: evidence/<slug>.md → observation
- ❌ BAD_ENUM: claims/<slug>.md → verification.status=foo

## L2 Semantic
- ❌ ORPHAN_CLAIM: claims/<slug>.md 无 evidence
- ❌ BROKEN_RELATION: claim A supports non-existent claim B

## L3 Consistency
- ❌ UNGROUNDED: papers/<slug>.md 中 β=0.34 在 raw 中找不到
- ❌ OUT_OF_RANGE: claims/<slug>.md confidence=1.5

## Grounding Invariant 验证
∀ quantitative_fact f ∈ evidence.md:
    ∃ quote q ∈ raw full.md:
        numeric_value(f) ∈ numeric_values(q)

## 建议修复(优先级排序)
1. **P0 阻塞**:X 个严重错误(必须修复才能继续)
2. **P1 重要**:Y 个中等问题(影响可用性)
3. **P2 优化**:Z 个建议(可选)

## 趋势对比(对比上次 lint)
| 项 | 上次 | 本次 | 变化 |
|---|---|---|---|
| 节点总数 | N | M | +X |
| L0 问题 | N | M | -X |
| L1 问题 | N | M | -X |
| L2 问题 | N | M | -X |
| L3 问题 | N | M | -X |
| **总问题** | **N** | **M** | **-X** |

## 下一步
- [ ] 修复 P0 阻塞问题
- [ ] 修复 P1 重要问题(可选)
- [ ] git commit lint 报告
- [ ] 重新跑 lint 验证
```

## 边界

- **不自动修复**(ARCHITECTURE §1.2 铁律 10 + §13 失败模式)
- LLM 主导的 L2 校验输出"建议",不修改
- 报告写到 `log/ops.md`,不写到 `00-pending/`

## 关联

- 验证机制:`ARCHITECTURE.md §7`
- Grounding Invariant:`ARCHITECTURE.md §5.3`

## Resources

- `ARCHITECTURE.md §7` 质量保障完整章节
- `.skill/scripts/schemas/*.schema.json` 3 套 schema
- `.pi/extensions/wiki-tools.ts` Extension 工具