"""
集中 Schema 注册表 · plan_final §1.2 #11 + §7.1 + T-W1-006

所有 jsonschema 在 .skill/scripts/schemas/ 下,本文件统一引用。
LLM 抽取输出 JSON 后,scripts 用 jsonschema 库校验,失败 reject 重写。

提供三个常量供 lint / stitch-knowledge 使用:
  - EDGE_TYPE_SPECS:7 类边的类型 + confidence + relation 枚举
  - ENTITY_DIRS:node_type → wiki 子目录映射
  - REQUIRED_FIELDS:每类节点的必填字段集合

用法:
    from _registry import SCHEMAS, EDGE_TYPE_SPECS, validate
    validate("claim", data)
    edge_ok = check_edge("supports", edge_data)
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Schema 目录(.skill/scripts/schemas/,和 Python 一起,plan §7.1)
SCHEMAS_DIR = Path(__file__).parent

# 集中注册:node_type → schema filename
SCHEMAS: dict[str, str] = {
    "claim": "claim.schema.json",
    "evidence": "evidence.schema.json",
    "topic": "topic.schema.json",
    # "paper": "paper.schema.json",  # Phase 2 加
    # "synthesis": "synthesis.schema.json",  # Phase 2 加
    # "paperinfo": "paperinfo.schema.json",  # scripts 维护
}

# 节点类型 → wiki 子目录(plan_final §2.1 5 核心 + 2 辅助)
ENTITY_DIRS: dict[str, str] = {
    "paperinfo": "paperinfo",
    "paper": "papers",
    "claim": "claims",
    "evidence": "evidence",
    "topic": "topics",
    "synthesis": "syntheses",
    "pending": "00-pending",
    "raw": "raw",   # ★ 权威源(MinerU 复制品,Grounding 引用都从这里)
}

# Raw 路径模板(plan_final §2.1 表格新加)
RAW_PATH_TEMPLATE = "raw/{citekey}/full.md"   # 每个论文一个目录

# Raw 完整性校验(plan_final §5.5 scripts 白名单)
def check_raw_exists(citekey: str) -> bool:
    """
    校验 raw 目录是否存在。
    wiki 引用与 Grounding grep 都依赖 raw 存在。
    """
    import os
    from pathlib import Path
    raw_dir = Path(__file__).parent.parent.parent / "raw" / citekey
    full_md = raw_dir / "full.md"
    return full_md.exists() and full_md.is_file()

# 边类型规格(ARCHITECTURE §1.2 #11 + §7.1,2026-08-25 批次1对齐)
# 7 类边:supports / contradicts / qualifies / same_claim_as / extends / refines / cites
# - supersedes 已删除(数据 0 使用,§7.1 无此边)
# - cites 取代 supersedes(paper→paper,confidence: none)
# - from/to 为允许端点集合(端点校验用,数据现实:claim 也用 supports 指向 claim)
EDGE_TYPE_SPECS: dict[str, dict[str, Any]] = {
    "supports": {
        "description": "Evidence supports claim(或 claim A supports claim B)",
        "from": ("evidence", "claim"), "to": ("claim",),
        "direction": "directed", "confidence": "required",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect", "partial"],
        "required": ["target", "confidence"],
        "optional": ["relation"],
    },
    "contradicts": {
        "description": "Evidence contradicts claim",
        "from": ("evidence", "claim"), "to": ("claim",),
        "direction": "directed", "confidence": "required",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect", "partial"],
        "required": ["target", "confidence"],
        "optional": ["relation"],
    },
    "qualifies": {
        "description": "Evidence qualifies claim(限定条件)",
        "from": ("evidence", "claim"), "to": ("claim",),
        "direction": "directed", "confidence": "required",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect", "partial"],
        "required": ["target", "confidence"],
        "optional": ["relation"],
    },
    "same_claim_as": {
        "description": "两个 claim 表达同一命题(stitch-knowledge 使用)",
        "from": ("claim",), "to": ("claim",),
        "direction": "symmetric", "confidence": "required",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect"],
        "required": ["target", "confidence"],
        "optional": [],
    },
    "extends": {
        "description": "claim A 扩展了 claim B(包含更多边界条件)",
        "from": ("claim",), "to": ("claim",),
        "direction": "directed", "confidence": "optional",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect"],
        "required": ["target"],
        "optional": ["confidence"],
    },
    "refines": {
        "description": "claim A 细化 claim B(更精确的描述)",
        "from": ("claim",), "to": ("claim",),
        "direction": "directed", "confidence": "optional",
        "confidence_enum": ["high", "medium", "low"],
        "relation_enum": ["direct", "indirect"],
        "required": ["target"],
        "optional": ["confidence"],
    },
    "cites": {
        "description": "paper A 引用 paper B(引用关系,无置信度)",
        "from": ("paper",), "to": ("paper",),
        "direction": "directed", "confidence": "none",
        "confidence_enum": [],
        "relation_enum": ["direct"],
        "required": ["target"],
        "optional": [],
    },
}

# 必填字段(ARCHITECTURE §3 各节点 schema 必填字段汇总,2026-08-25 批次1对齐扁平化现实)
# claim 已扁平化:verify_status 替代嵌套 verification
REQUIRED_FIELDS: dict[str, list[str]] = {
    "claim": ["type", "statement", "claim_type", "verify_status"],
    "evidence": [
        "type", "fact_type", "observation",
        "interp_origin", "interp_text",
        "prov_paper", "prov_section", "prov_source_text",
        "verify_n", "verify_test_method",
    ],
    "topic": ["type", "id"],
    "paper": ["type", "citekey", "paperinfo"],  # Phase 2
    "synthesis": ["type", "question", "generated_by"],  # Phase 2
}


def load_schema(node_type: str) -> dict:
    """加载指定 node_type 的 jsonschema"""
    if node_type not in SCHEMAS:
        raise ValueError(f"Unknown node type: {node_type}. Available: {list(SCHEMAS.keys())}")
    schema_path = SCHEMAS_DIR / SCHEMAS[node_type]
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(node_type: str, data: dict) -> tuple[bool, str | None]:
    """
    校验节点数据是否符合 schema。
    返回: (是否通过, 错误信息)
    """
    if jsonschema is None:
        return False, "jsonschema library not installed. Run: pip install jsonschema"

    schema = load_schema(node_type)
    try:
        jsonschema.validate(data, schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, f"{e.message} at {list(e.absolute_path)}"


def validate_file(node_type: str, file_path: str | os.PathLike) -> tuple[bool, str | None]:
    """
    校验 .md 文件的 frontmatter。
    期望文件格式:
        ---
        type: claim
        ...其他字段
        ---
        正文(忽略)
    """
    import re

    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"

    content = path.read_text(encoding="utf-8")

    # 提取 frontmatter(--- 之间)
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return False, "No YAML frontmatter found"

    # 简易 YAML 解析(避免依赖 PyYAML;实际生产用 PyYAML)
    try:
        import yaml
        data = yaml.safe_load(match.group(1))
    except ImportError:
        return False, "PyYAML not installed. Run: pip install pyyaml"

    return validate(node_type, data)


def check_edge(edge_type: str, edge_data: dict, from_kind: str | None = None, to_kind: str | None = None) -> tuple[bool, str | None]:
    """
    校验边对象是否符合 EDGE_TYPE_SPECS。
    edge_data 格式: {"target": "[[xxx]]", "confidence": "high", "relation": "direct"}
    from_kind/to_kind(可选):边所在节点的类型,用于端点校验(EmpiricalWiki 模式,批次1)
        例:evidence 文件里的 supports 边 → check_edge("supports", edge, from_kind="evidence")
    返回: (是否通过, 错误信息)
    """
    if edge_type not in EDGE_TYPE_SPECS:
        return False, f"Unknown edge type: {edge_type}. Available: {list(EDGE_TYPE_SPECS.keys())}"

    spec = EDGE_TYPE_SPECS[edge_type]
    for field in spec["required"]:
        if field not in edge_data:
            return False, f"Missing required field: {field}"

    if "confidence" in edge_data and spec["confidence_enum"]:
        if edge_data["confidence"] not in spec["confidence_enum"]:
            return False, f"Invalid confidence: {edge_data['confidence']}. Must be one of {spec['confidence_enum']}"

    if "relation" in edge_data:
        if edge_data["relation"] not in spec["relation_enum"]:
            return False, f"Invalid relation: {edge_data['relation']}. Must be one of {spec['relation_enum']}"

    if "target" in edge_data:
        import re
        if not re.match(r"^\[\[[^\]]+\]\]$", edge_data["target"]):
            return False, f"Invalid target format: {edge_data['target']}. Must be a wikilink like [[xxx]]"

    # 端点校验(§7.1:supports 只能 evidence→claim 等;省略时跳过)
    if from_kind is not None and from_kind not in spec["from"]:
        return False, f"Endpoint mismatch: '{edge_type}' allows from {spec['from']}, got '{from_kind}'"
    if to_kind is not None and to_kind not in spec["to"]:
        return False, f"Endpoint mismatch: '{edge_type}' allows to {spec['to']}, got '{to_kind}'"

    return True, None


# CLI 入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python _registry.py <node_type> <file.md>")
        print(f"Available node types: {list(SCHEMAS.keys())}")
        print(f"Available edge types: {list(EDGE_TYPE_SPECS.keys())}")
        sys.exit(1)

    node_type = sys.argv[1]
    file_path = sys.argv[2]

    ok, error = validate_file(node_type, file_path)
    if ok:
        print(f"✅ {file_path} 校验通过({node_type})")
        sys.exit(0)
    else:
        print(f"❌ {file_path} 校验失败: {error}")
        sys.exit(1)