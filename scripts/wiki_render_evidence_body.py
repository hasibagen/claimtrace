"""
wiki_render_evidence_body.py
从 evidence frontmatter + schema $defs 自动生成 body 中的自动渲染段。

T-W4-027 升级:生成 ## 数值校验 表格(11 verify_* 字段 + schema enum 候选)
T-W4-031 升级:同时生成 ## 支持的 Claim / ## 反对的 Claim / ## 限定的 Claim 表格
  (3 类边 × 3 平行数组,ARCHITECTURE §1.2 #11)
  - strength 是 evidence 节点全局属性,在 frontmatter 体现一次,不重复在每条边后
  - 每条边只显示 关系(direct/indirect/partial) + 置信度(high/medium/low)

设计原则(ARCHITECTURE §1.2 #11 + 铁律 #4 NO REGEX ON MEANING):
  - body 表格 **只渲染、不维护** —— 永远从 frontmatter 生成,不允许手工编辑
  - schema enum 是说明列的唯一真相源($defs.test_method_enum 等)
  - 论文未报告的字段(frontmatter 中为 null)→ 表格值列显示 _(论文未报告)_

用法:
  python3 wiki_render_evidence_body.py evidence/<file>.md             # 单文件,直接写
  python3 wiki_render_evidence_body.py evidence/                       # 目录所有 .md
  python3 wiki_render_evidence_body.py --dry-run evidence/<file>.md    # 只输出到 stdout
  python3 wiki_render_evidence_body.py --check evidence/               # 一致性检查(diff 检测)
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SCHEMAS_DIR = SCRIPT_DIR / "schemas"
EVIDENCE_SCHEMA = SCHEMAS_DIR / "evidence.schema.json"

# 11 verify_* 字段与表格列的固定映射(顺序固定,ARCHITECTURE §3.4)
VERIFY_ROWS = [
    ("verify_n",              "样本量 (n)",  "总样本数"),
    ("verify_test_method",    "检验方法",     "paper_stats.md 方法学候选"),
    ("verify_test_stat_type", "统计量类型",    "统计量类型候选"),
    ("verify_test_stat_value","统计量数值",    "论文报告的具体值(null=未报告)"),
    ("verify_effect_size_type", "效应量类型",  "效应量类型候选"),
    ("verify_effect_size_value","效应量数值",  "论文报告的效应量值(null=未报告)"),
    ("verify_ci_95",          "95% 置信区间", "如 [0.18, 0.50](null=未报告)"),
    ("verify_df",             "自由度 (df)",  "统计量对应的自由度(null=未报告)"),
    ("verify_p_value",        "p 值",        "原始 p 值(null=未报告)"),
    ("verify_p_method",       "p 值校正",     "paper_stats.md 多重比较候选"),
    ("verify_note",           "备注",        "上下文或限制说明"),
]

# enum 候选映射(从 schema $defs 字段名 → 表格"说明"列的语义提示)
ENUM_HINT = {
    "verify_test_method":    "$defs.test_method_enum",
    "verify_test_stat_type": "$defs.test_stat_type_enum",
    "verify_effect_size_type": "$defs.effect_size_type_enum",
    "verify_p_method":       "$defs.p_method_enum",
}

# 边类型(ARCHITECTURE §1.2 #11)→ 段标题 + frontmatter 字段前缀
EDGE_TYPES = [
    ("supports",   "## 支持的 Claim"),
    ("contradicts","## 反对的 Claim"),
    ("qualifies",  "## 限定的 Claim"),
]

# 自动渲染段(由脚本生成,不应手工编辑)
AUTO_RENDERED_PATTERNS = [
    r"## 数值校验[\s\S]*?(?=\n## |\n# |\Z)",
    r"## 支持的 Claim[\s\S]*?(?=\n## |\n# |\Z)",
    r"## 反对的 Claim[\s\S]*?(?=\n## |\n# |\Z)",
    r"## 限定的 Claim[\s\S]*?(?=\n## |\n# |\Z)",
]


def load_schema():
    """加载 evidence schema,失败则 raise"""
    if not EVIDENCE_SCHEMA.exists():
        raise FileNotFoundError(f"Schema not found: {EVIDENCE_SCHEMA}")
    return json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))


def extract_sections(content: str):
    """
    把 evidence .md 文件切成 frontmatter + body
    返回 (frontmatter_yaml_str, body_str)
    """
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n([\s\S]*)$', content, re.DOTALL)
    if not m:
        raise ValueError("No frontmatter found (--- ... --- required)")
    return m.group(1), m.group(2)


def parse_frontmatter(yaml_str: str) -> dict:
    """
    YAML 极简解析:支持
    - key: value / key: 'value' / key: "value" / null
    - block list: key 后跟多行 "- item"
    - 不支持嵌套对象(plan_final 扁平化设计不需要)
    """
    data = {}
    lines = yaml_str.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        # 解析 key: value 或 key:
        m = re.match(r'^([\w-]+):\s*(.*)$', stripped)
        if not m:
            i += 1
            continue
        key = m.group(1)
        rest = m.group(2).strip()
        if rest:
            # 单行 value
            if len(rest) >= 2:
                if (rest[0] == '"' and rest[-1] == '"') or \
                   (rest[0] == "'" and rest[-1] == "'"):
                    rest = rest[1:-1]
            if rest.lower() in ('null', '~', ''):
                rest = None
            data[key] = rest
            i += 1
        else:
            # key 后是空 → block list
            i += 1
            items = []
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('- '):
                    item = next_line[2:].strip()
                    # 去掉引号
                    if len(item) >= 2:
                        if (item[0] == '"' and item[-1] == '"') or \
                           (item[0] == "'" and item[-1] == "'"):
                            item = item[1:-1]
                    items.append(item)
                    i += 1
                elif not next_line:
                    # 空行:继续看下一行(可能是 list 续)
                    i += 1
                else:
                    break
            data[key] = items
    return data


def load_enum(schema: dict, def_key: str) -> list:
    """从 schema $defs 提取 enum 候选列表"""
    return schema.get("$defs", {}).get(def_key, {}).get("enum", [])


def render_value_cell(value) -> str:
    """值列:论文未报告(null/空)→ _(论文未报告)_;否则 `value`"""
    if value is None or str(value).strip() == '':
        return '_(论文未报告)_'
    return f"`{value}`"


def render_enum_hint(enum_list: list, max_show: int = 3) -> str:
    """说明列(批次4瘦身):只显示前 3 个候选 + 总数,不再倾倒全量枚举"""
    if not enum_list:
        return ""
    if len(enum_list) > max_show:
        return ", ".join(enum_list[:max_show]) + f" 等(共 {len(enum_list)} 候选,见 paper_stats)"
    return ", ".join(enum_list)


def render_verify_table(fm: dict, schema: dict) -> str:
    """生成 ## 数值校验 11 行 markdown 表格"""
    enum_resolver = {
        "verify_test_method":    load_enum(schema, "test_method_enum"),
        "verify_test_stat_type": load_enum(schema, "test_stat_type_enum"),
        "verify_effect_size_type": load_enum(schema, "effect_size_type_enum"),
        "verify_p_method":       load_enum(schema, "p_method_enum"),
    }
    rows = [
        "| 项目 | 值 | 说明 |",
        "|------|------|------|",
    ]
    for field, label, base_hint in VERIFY_ROWS:
        value = fm.get(field)
        value_cell = render_value_cell(value)
        hint = render_enum_hint(enum_resolver.get(field, [])) if field in enum_resolver else base_hint
        rows.append(f"| {label} | {value_cell} | {hint} |")
    return "\n".join(rows)


def render_verify_section(fm: dict, schema: dict) -> str:
    """生成 ## 数值校验 段(含标题 + 表格)"""
    return f"## 数值校验\n\n{render_verify_table(fm, schema)}\n"


def _filter_nonempty(items: list) -> list:
    """过滤空字符串/None"""
    return [x for x in (items or []) if x is not None and str(x).strip() != '']


def render_relation_table(fm: dict, edge_type: str) -> str:
    """
    渲染单类边(3 平行数组对齐)的表格:
    edge_type ∈ {'supports', 'contradicts', 'qualifies'}
    读取 fm[f'{edge_type}_targets'] / fm[f'{edge_type}_confidences'] / fm[f'{edge_type}_relations']

    返回 "" 表示无此类边(不渲染段)。
    注意:每条边只显示 关系(direct/indirect/partial) + 置信度(high/medium/low),
    不显示 strength(它是 evidence 节点全局属性,在 frontmatter `strength` 字段体现一次)
    """
    targets = _filter_nonempty(fm.get(f"{edge_type}_targets", []))
    confidences = _filter_nonempty(fm.get(f"{edge_type}_confidences", []))
    relations = _filter_nonempty(fm.get(f"{edge_type}_relations", []))

    if not targets:
        return ""  # 没有此类边,不渲染段

    n = len(targets)
    rows = [
        "| Claim wikilink | 关系 | 置信度 |",
        "|----------------|------|--------|",
    ]
    for i in range(n):
        target = targets[i]
        confidence = confidences[i] if i < len(confidences) else "—"
        relation = relations[i] if i < len(relations) else "—"
        rows.append(f"| {target} | {relation} | {confidence} |")

    title = next(t for et, t in EDGE_TYPES if et == edge_type)
    table = "\n".join(rows)
    return f"{title}\n\n{table}\n"


def render_relations_section(fm: dict) -> str:
    """组合渲染 3 类边表格段(按 supports → contradicts → qualifies 顺序)"""
    sections = []
    for edge_type, _ in EDGE_TYPES:
        s = render_relation_table(fm, edge_type)
        if s:
            sections.append(s)
    return "\n".join(sections)


def render_all_auto_sections(fm: dict, schema: dict) -> str:
    """组合所有自动渲染段(relations + 数值校验),用于一次性重生成"""
    parts = []
    relations = render_relations_section(fm)
    if relations:
        parts.append(relations)
    verify = render_verify_section(fm, schema)
    if verify:
        parts.append(verify)
    return "\n".join(parts)


def remove_auto_rendered_sections(body: str) -> str:
    """删除 body 中所有自动渲染段(防止残留)"""
    for pattern in AUTO_RENDERED_PATTERNS:
        body = re.sub(pattern + r'[\s\S]*?(?=\n## |\n# |\Z)', '', body, count=1)
    # 清理连续空行(超过 2 个换行 → 2 个)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body


def insert_auto_sections(body: str, auto_content: str) -> str:
    """
    把自动渲染内容插入到 body 中合适位置。
    插入点:`**出处**` 段结束后(在 `## 数值校验` 等自动渲染段之前)。
    """
    if not auto_content:
        return body

    # 尝试找到 "**出处**" 段结尾(下一个 ## 标题前或文件末尾)
    m = re.search(r'(\*\*出处\*\*[\s\S]*?)(?=\n## |\n# |\Z)', body)
    if m:
        insertion_point = m.end()
        # 确保插入点前有空行
        prefix = "\n\n" if not body[insertion_point-1:insertion_point+1].startswith("\n\n") else ""
        return body[:insertion_point] + prefix + auto_content + "\n\n" + body[insertion_point:]

    # 兜底:在 "# Evidence:" 标题段后插入
    m = re.match(r'(# [^\n]+\n(?:[^\n]*\n)*)', body)
    if m:
        return body[:m.end()] + "\n" + auto_content + "\n\n" + body[m.end():]

    # 最后兜底:插入开头
    return auto_content + "\n" + body


def process_file(path: Path, schema: dict) -> str:
    """处理单个 evidence 文件,返回新完整内容"""
    content = path.read_text(encoding="utf-8")
    yaml_str, body = extract_sections(content)
    fm = parse_frontmatter(yaml_str)

    auto_content = render_all_auto_sections(fm, schema)

    # 1. 删除所有旧自动渲染段
    new_body = remove_auto_rendered_sections(body)

    # 2. 插入新自动渲染内容到 **出处** 之后
    new_body = insert_auto_sections(new_body, auto_content)

    return f"---\n{yaml_str}\n---\n{new_body}"


def main():
    parser = argparse.ArgumentParser(
        description="从 evidence frontmatter + schema $defs 重生成 body 中的自动渲染段(## 数值校验 / ## 支持的 Claim / ## 反对的 Claim / ## 限定的 Claim)"
    )
    parser.add_argument("target", help="evidence .md 文件路径 或 evidence 目录")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印新内容到 stdout,不写文件")
    parser.add_argument("--check", action="store_true",
                        help="检查模式:不写文件,只比对 diff (有差异 exit 1)")
    args = parser.parse_args()

    schema = load_schema()
    target = Path(args.target)

    if target.is_dir():
        files = sorted(target.glob("*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"❌ Target not found: {target}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"⚠️  No .md files in {target}", file=sys.stderr)
        sys.exit(0)

    changed = 0
    unchanged = 0
    for f in files:
        content = f.read_text(encoding="utf-8")
        new_content = process_file(f, schema)
        if args.dry_run:
            print(f"\n{'='*70}")
            print(f"📄 {f.name}")
            print(f"{'='*70}")
            # 输出所有自动渲染段
            body = new_content.split('---\n', 2)[2]
            for pattern in AUTO_RENDERED_PATTERNS:
                m = re.search(pattern, body)
                if m:
                    print(m.group(0))
                    print()
        elif args.check:
            if new_content != content:
                print(f"❌ {f.name} 与渲染结果不一致(需重生成)")
                changed += 1
            else:
                print(f"✅ {f.name} 一致")
                unchanged += 1
        else:
            if new_content != content:
                f.write_text(new_content, encoding="utf-8")
                print(f"✅ {f.name} 已更新")
                changed += 1
            else:
                print(f"⏭  {f.name} 无变化")
                unchanged += 1

    if args.dry_run:
        return
    print(f"\n汇总: 变更 {changed} / 未变 {unchanged} / 总计 {changed + unchanged}")


if __name__ == "__main__":
    main()
