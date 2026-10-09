#!/usr/bin/env python3
"""
wiki_lint.py — 4 层 lint 校验

L0 结构：文件存在、命名规范、frontmatter 完整、wikilink 解析
L1 证据：数值在 raw 中可 grep、quote 格式、数值范围
L2 语义：CLAIM 有 EVIDENCE、RELATION 正确、双向 wikilink
L3 一致性：数值范围合理、矛盾检测
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "schemas"))
import wiki_common as wc
import _registry
import wiki_check_evidence as wce


# === L0 结构校验 ===

# 节点类型 → 目录映射:单一真相源在 schemas/_registry.py(批次1.1 消灭双源)
NODE_TYPE_TO_DIR = _registry.ENTITY_DIRS
KNOWN_NODE_TYPES = set(NODE_TYPE_TO_DIR.keys())


def lint_l0_structure(wiki_root: Path) -> list[str]:
    """L0: 结构校验（确定性，零 LLM）。"""
    errors = []

    # 必填顶层文件(2026-08-27 起 log 拆为 log/ 文件夹,全局日志在 log/ops.md)
    for name in ("AGENTS.md", "index.md", "log/ops.md", "log/README.md"):
        if not (wiki_root / name).is_file():
            errors.append(f"L0: missing required file: {name}")

    # papers/ 命名规范：<Author>_<Year>_<short>.md (允许 - 和 .)
    # 例: sanz-leon_2015_neuroimage.md / li_2023_visual_informatics.md
    # 允许 8 位 zotero-key 命名作为后备（BBT 解析失败的论文）
    # 例: a__.md / wang__.md / dollomaja__medrxiv_prepr_serv_health_sci.md
    name_re = re.compile(r"^([a-zA-Z][a-zA-Z0-9_.\-]*_\d{4}[a-z]?_[a-zA-Z0-9_.\-]*|[A-Z0-9]{8}|[a-z_][a-z0-9_]*__[a-z0-9_]+|[a-z]+__)\.md$")
    papers = wc.papers_dir(wiki_root)
    if papers.is_dir():
        for f in papers.iterdir():
            if f.is_file() and f.suffix == ".md" and not name_re.match(f.name):
                errors.append(f"L0: papers/{f.name} does not match <Author>_<Year>_<short>.md")

    # claims/ 命名规范：<semantic-slug>.md (ARCHITECTURE §2.3 + T-W4-030)
    # 优先中文 + 真实空格,如 `PWS 婴儿早期脑高灌注.md`
    # 也支持中英混合 / kebab-case / snake_case / PascalCase
    # 例: PWS 婴儿早期脑高灌注.md / dlpfc-hbo-age.md / tvb-multiscale-platform.md
    # 唯一标识 = 文件名,无需 CLAIM-NNN 编号
    # 字符集:中文(CJK) + 日文(假名) + ASCII(字母数字) + 空格 + `-` `_` `.`
    claim_name_re = re.compile(
        r"^[A-Za-z0-9\u4e00-\u9fff\u3040-\u30ff]"
        r"[A-Za-z0-9\u4e00-\u9fff\u3040-\u30ff \-\._]*\.md$"
    )
    claims = wc.claims_dir(wiki_root)
    if claims.is_dir():
        for f in claims.iterdir():
            if f.is_file() and f.suffix == ".md" and not claim_name_re.match(f.name):
                errors.append(f"L0: claims/{f.name} 不符合 <semantic-slug>.md 命名(ARCHITECTURE §2.3,优先中文 + 真实空格,T-W4-030)")

    return errors


# === L0 节点类型一致性(铁律 #4:用 frontmatter type 字段判定节点类型,不用文件名正则) ===

def lint_l0_node_type_consistency(wiki_root: Path) -> list[str]:
    """
    L0 增强(T-W4-028):用 frontmatter type 字段判定节点类型,与目录位置交叉校验。

    铁律 #4 (NO REGEX ON MEANING) 执行:
    - 节点"是什么类型"不靠文件名/路径正则判断,靠 frontmatter `type:` 字段
    - 节点位置(目录)与 type 必须一致(ARCHITECTURE §2.1)

    检查项:
    1. 如果文件有 `type:` 字段,值 ∈ KNOWN_NODE_TYPES
    2. `type:` 对应目录必须与文件所在目录一致

    注意:不强制每个文件必须有 type 字段(避免误报已有的 v4 时期文件),
         但如果有 type 字段,必须一致。
    """
    errors = []

    for type_name, dir_name in NODE_TYPE_TO_DIR.items():
        dir_path = wiki_root / dir_name
        if not dir_path.is_dir():
            continue
        for f in dir_path.iterdir():
            if not f.is_file() or f.suffix != ".md":
                continue
            text = wc.read_text(f)
            fm, _ = wc.parse_frontmatter(text)

            # 没有 type 字段 → 不强制(向后兼容)
            if "type" not in fm:
                continue

            node_type = fm["type"].lower()  # 容忍大写

            # type 必须 ∈ 已知类型
            if node_type not in KNOWN_NODE_TYPES:
                errors.append(
                    f"L0.5: {dir_name}/{f.name} type='{fm['type']}' 不在已知节点类型 {sorted(KNOWN_NODE_TYPES)} 中"
                )
                continue

            # type 必须与所在目录一致(ARCHITECTURE §2.1 节点架构)
            expected_dir = NODE_TYPE_TO_DIR.get(node_type)
            if expected_dir != dir_name:
                errors.append(
                    f"L0.5: {dir_name}/{f.name} type='{node_type}' 应位于 '{expected_dir}/' 而非 '{dir_name}/'(ARCHITECTURE §2.1)"
                )

    return errors


# === L4.6 raw 素材路径校验 ===

def _lint_l0_terms(wiki_root: Path) -> list[str]:
    """L0.7: 术语规范(fNIRS/EEG-fNIRS/VBT 等,详见 wiki_normalize_terms.py 规则表)。"""
    import wiki_normalize_terms as wnt

    errors = []
    for e in wnt.check(wiki_root):
        if e.startswith("L0.7[未启用]"):
            continue  # E-J 未启用规则只提示不计错
        errors.append(e)
    return errors


def lint_l4_raw_path(wiki_root: Path) -> list[str]:
    """L4.6: papers/ 的 csv-source-path 必须指向 raw/ 存在的 full.md。"""
    errors = []
    papers = wc.papers_dir(wiki_root)
    if not papers.is_dir():
        return errors

    csv_path_re = re.compile(r'^csv-source-path:\s*"(.+?)"', re.MULTILINE)
    for f in papers.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        m = csv_path_re.search(text)
        if not m:
            continue
        path = m.group(1)
        # 空路径或外部路径 (zotero_md 原始)
        if not path or "zotero_md" in path:
            errors.append(f"L4.6: papers/{f.name} csv-source-path points to external (zotero_md): {path[:60]}")
            continue
        # 本地路径但文件不存在
        if not Path(path).is_file():
            errors.append(f"L4.6: papers/{f.name} csv-source-path not found: {path[:60]}")
    return errors


# === L1 证据校验 ===

def _iter_frontmatter(wiki_root: Path, dir_name: str):
    """遍历目录下 .md,产出 (文件名, frontmatter dict)。"""
    d = wiki_root / dir_name
    if not d.is_dir():
        return
    for f in sorted(d.iterdir()):
        if f.is_file() and f.suffix == ".md":
            text = wc.read_text(f)
            fm, _ = wc.parse_frontmatter(text)
            yield f.name, fm


def lint_l1_node_schemas(wiki_root: Path) -> list[str]:
    """
    L1.5(批次1.1 新增,2026-08-25 盲区修复):claims/ + evidence/ **以及
    00-pending/&lt;citekey&gt;/{claims,evidence}/** 的 frontmatter 用 jsonschema 校验。
    §4.6 契约"L1 = frontmatter 必填 + enum 合法"的实现。
    扫 00-pending 是 S4 闸门的关键:新抽取在进正式目录前就必须被校验
    (否则 217/249 不过 schema 的新抽取会带着脏值被 promote)。
    报出的失败 = 真实数据问题,不是误报。
    """
    errors = []
    targets: list[tuple[str, str]] = [("claims", "claim"), ("evidence", "evidence")]
    for sub in sorted((wiki_root / "00-pending").glob("*/")):
        for kind_dir, node_type in (("claims", "claim"), ("evidence", "evidence")):
            if (sub / kind_dir).is_dir():
                targets.append((f"00-pending/{sub.name}/{kind_dir}", node_type))
    for dir_name, node_type in targets:
        d = wiki_root / dir_name
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            # 用 yaml.safe_load 解析(2026-08-25 修复:wc.parse_frontmatter 是简易解析器,
            # 所有值返回字符串 → '1' is not integer 假阳性淹没了真脏值)
            import yaml as _yaml
            text = wc.read_text(f)
            m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not m:
                errors.append(f"L1.5: {dir_name}/{f.name} frontmatter 缺失")
                continue
            try:
                fm = _yaml.safe_load(m.group(1)) or {}
            except _yaml.YAMLError as e:
                errors.append(f"L1.5: {dir_name}/{f.name} YAML 解析失败: {str(e)[:80]}")
                continue
            if not isinstance(fm, dict) or not fm:
                errors.append(f"L1.5: {dir_name}/{f.name} frontmatter 解析为空")
                continue
            ok, err = _registry.validate(node_type, fm)
            if not ok:
                msg = (err or "unknown")[:160]
                errors.append(f"L1.5: {dir_name}/{f.name} schema 校验失败: {msg}")
                continue
            # T-W7-001 交叉字段校验(归属/论证链;旧节点无这些字段,天然通过)
            if node_type == "claim":
                attr = fm.get("attribution")
                if attr in ("cited_single", "cited_multi") and not (
                        fm.get("cited_targets") or fm.get("cited_apa")):
                    errors.append(
                        f"L1.5: {dir_name}/{f.name} attribution={attr} 但 cited_targets/cited_apa 均为空(T-W7-001:转述 claim 必须带被引文献)")
                if attr in ("author_own", "field_consensus") and fm.get("cited_apa"):
                    errors.append(
                        f"L1.5: {dir_name}/{f.name} attribution={attr} 不应携带 cited_apa(归属与被引文献矛盾)")
                if fm.get("origin_section") in ("introduction", "discussion", "conclusion", "review") \
                        and not fm.get("argument_role"):
                    errors.append(
                        f"L1.5: {dir_name}/{f.name} origin_section={fm.get('origin_section')} 但缺 argument_role(论证链 claim 必须标注角色)")
                for edge in ("premises",):
                    t = fm.get(f"{edge}_targets")
                    if isinstance(t, list) and t:
                        c = fm.get(f"{edge}_confidences")
                        r = fm.get(f"{edge}_relations")
                        if not isinstance(c, list) or len(c) != len(t):
                            errors.append(
                                f"L1.5: {dir_name}/{f.name} {edge}_confidences 与 targets 不等长(平行数组铁律)")
                        if not isinstance(r, list) or len(r) != len(t):
                            errors.append(
                                f"L1.5: {dir_name}/{f.name} {edge}_relations 与 targets 不等长(平行数组铁律)")
            if node_type == "evidence" and fm.get("fact_type") == "secondary_citation":
                if not (fm.get("cited_targets") or fm.get("cited_apa")):
                    errors.append(
                        f"L1.5: {dir_name}/{f.name} fact_type=secondary_citation 但缺 cited_targets/cited_apa(二手证据必须带一手出处,T-W7-001)")
    return errors


def lint_l1_evidence(wiki_root: Path) -> list[str]:
    """L1: 证据校验（确定性，调用 wiki_check_evidence）。"""
    errors = []

    papers = wc.papers_dir(wiki_root)
    if not papers.is_dir():
        return errors

    for paper_file in papers.iterdir():
        if paper_file.suffix != ".md":
            continue

        paper_id = paper_file.stem
        raw_file = wiki_root / "raw" / paper_id / "full.md"
        if not raw_file.is_file():
            raw_file = wiki_root / "raw" / f"{paper_id}.md"
        if not raw_file.is_file():
            errors.append(f"L1: {paper_id}: raw full.md missing")
            continue

        paper_text = wc.read_text(paper_file)
        source_text = wc.read_text(raw_file)

        # 只校验 DOI 后缀数字（避免 p-value / 统计值误报）
        for doi_match in re.finditer(r"10[.]\d{4,5}/[\w.\-]+", paper_text):
            doi = doi_match.group(0)
            if doi not in source_text and doi.replace("-", "") not in source_text.replace("-", ""):
                errors.append(f"L1: {paper_id}: DOI '{doi}' not found in raw")

    return errors


# === L2 语义校验（确定性部分） ===

def lint_l2_semantic(wiki_root: Path) -> list[str]:
    """L2: 语义校验（部分确定性 + 部分 LLM）。"""
    errors = []

    papers = wc.papers_dir(wiki_root)
    if not papers.is_dir():
        return errors

    for paper_file in papers.iterdir():
        if paper_file.suffix != ".md":
            continue

        paper_id = paper_file.stem
        text = wc.read_text(paper_file)

        # CLAIM 必须有 EVIDENCE 支撑(ARCHITECTURE §3 扁平化:wikilink 形式)
        # 旧版用 **CLAIM-NNN** 和 - [EVID-NNN] 文本标记;新版本用 [[claims/<slug>]]
        # 和 [[evidence/<slug>]] wikilink,通过 frontmatter 校验(见 _registry.py)
        claim_wikilinks = re.findall(r"\[\[claims/[^\]]+\]\]", text)
        evidence_wikilinks = re.findall(r"\[\[(?:evidence|paperinfo)/[^\]]+\]\]", text)
        if claim_wikilinks and not evidence_wikilinks:
            errors.append(f"L2: {paper_id}: has CLAIM wikilinks but no EVIDENCE wikilinks (ARCHITECTURE §3.4)")

        # RELATION 必须是 ARCHITECTURE §1.2 #11 边类型之一(批次1.1:从 _registry 派生,消灭双源)
        valid_relations = set(_registry.EDGE_TYPE_SPECS.keys())
        edge_keys = "|".join(sorted(valid_relations))
        for m in re.finditer(rf"(?:{edge_keys})_(?:targets|relations)\s*:\s*\[([^\]]*)\]", text):
            relation_list = [x.strip().strip('"\'') for x in m.group(1).split(",") if x.strip()]
            for rel in relation_list:
                if rel and rel not in valid_relations:
                    errors.append(f"L2: {paper_id}: invalid relation '{rel}' (must be one of {sorted(valid_relations)})")

    return errors


# === L3 一致性校验（确定性部分） ===

def _citekey_from_wikilink(link) -> str:
    """
    宽容解析 prov_paper/source 的真实数据格式(批次1.1 修正):
    '[[papers/cakan_2023]]' / 'cakan_2023' / ['[papers/cakan_2023]'] → 'cakan_2023'
    """
    if isinstance(link, list):
        link = link[0] if link else ""
    s = str(link).strip()
    s = s.strip("[]").strip()          # 剥 wikilink 括号
    s = s.split("|")[0].strip()        # 剥别名
    if s.endswith("/paper"):           # 旧架构 '<citekey>/paper' 残留,citekey 在首段
        s = s.rsplit("/", 1)[0].strip()
    return s.split("/")[-1].strip()    # 剥路径前缀


def lint_l3_grounding(wiki_root: Path) -> list[str]:
    """
    L3 Grounding(批次1.1 新增):evidence 的 prov_source_text 必须能在
    raw/<citekey>/full.md 中命中(exact/fuzzy 三态,§5.3 Grounding Invariant)。
    raw 路径按 prov_paper citekey 现场推导(§15.4.11,不存指针)。
    """
    errors = []
    raw_cache: dict[str, str] = {}   # citekey → raw text(避免重复读大文件)
    checked = 0
    for fname, fm in _iter_frontmatter(wiki_root, "evidence"):
        quote = fm.get("prov_source_text") or ""
        if not quote or not isinstance(quote, str):
            continue
        prov = fm.get("prov_paper", fm.get("source", ""))
        if prov in ("", None, [], "{}"):
            continue
        citekey = _citekey_from_wikilink(prov)
        if not citekey:
            continue
        checked += 1
        if citekey not in raw_cache:
            raw_file = wiki_root / "raw" / citekey / "full.md"
            raw_cache[citekey] = wc.read_text(raw_file) if raw_file.is_file() else ""
        raw_text = raw_cache[citekey]
        if not raw_text:
            errors.append(f"L3: evidence/{fname} raw missing for citekey '{citekey}'(Grounding 不可执行)")
            continue
        status = wce.verify_in_source(quote, raw_text)
        if status == "none":
            errors.append(f"L3: evidence/{fname} prov_source_text 未在 raw/{citekey}/full.md 中命中(疑似幻觉/转引,§5.3)")
    wc.eprint(f"  (grounding checked {checked} evidence quotes)")
    return errors


def lint_l3_consistency(wiki_root: Path) -> list[str]:
    """L3: 一致性校验（确定性部分）。"""
    errors = []

    papers = wc.papers_dir(wiki_root)
    if not papers.is_dir():
        return errors

    for paper_file in papers.iterdir():
        if paper_file.suffix != ".md":
            continue

        paper_id = paper_file.stem
        text = wc.read_text(paper_file)

        # 数值范围检查(批次1.1 修幂次误报;2026-09-02 修回溯误报:
        # 旧正则在 "p=4.885e-04" 前瞻失败后回溯把数字截成 4.88 报出)
        # 现把指数并入捕获值(p=4.885e-04 → 0.0004885 合法),
        # 并排除 ×10^n / 10^n / 10⁻ⁿ 上标形态;(?![\d.]) 禁止数字中途截断
        # p ∈ [0, 1]
        for m in re.finditer(
            r"\bp\s*[<>=]\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
            r"(?![\d.])(?!\s*[×x^⁻])(?!\s*[-−]\s*\d)(?![⁰¹²³⁴⁵⁶⁷⁸⁹])",
            text,
        ):
            try:
                p = float(m.group(1))
                if p < 0 or p > 1:
                    errors.append(f"L3: {paper_id}: p-value {p} out of [0, 1]")
            except ValueError:
                pass

        # r ∈ [-1, 1](排除 r² / R2 / r2 等上标形式)
        for m in re.finditer(r"(?<![\w²])r\s*=\s*(-?\d+\.?\d*)(?!\s*[\^×eE][-−\d])(?![²2])", text):
            try:
                r = float(m.group(1))
                if r < -1 or r > 1:
                    errors.append(f"L3: {paper_id}: r-value {r} out of [-1, 1]")
            except ValueError:
                pass

    # Grounding grep(§4.6:L3 = 数值区间 + Grounding)
    errors.extend(lint_l3_grounding(wiki_root))

    return errors


# === 主入口 ===

def main() -> int:
    parser = argparse.ArgumentParser(description="4-layer lint for Evidence Wiki")
    parser.add_argument("--wiki-root", type=Path, default=None, help="Wiki root")
    parser.add_argument(
        "--layer",
        choices=["L0", "L0.5", "L0.7", "L1", "L1.5", "L2", "L3", "L4.6", "all"],
        default="all",
        help="Which layer to run (default: all). L0.5 = type↔目录;L1.5 = claims/evidence jsonschema(批次1)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()
    wiki_root = args.wiki_root or wc.find_wiki_root()

    layers = {
        "L0": lint_l0_structure,
        "L0.5": lint_l0_node_type_consistency,
        "L0.7": _lint_l0_terms,
        "L1": lint_l1_evidence,
        "L1.5": lint_l1_node_schemas,
        "L2": lint_l2_semantic,
        "L3": lint_l3_consistency,
        "L4.6": lint_l4_raw_path,
    }

    if args.layer == "all":
        runs = layers.items()
    else:
        runs = [(args.layer, layers[args.layer])]

    all_errors: list[str] = []
    per_layer: dict[str, list[str]] = {}
    for name, fn in runs:
        errors = fn(wiki_root) or []
        per_layer[name] = errors
        if errors:
            wc.eprint(f"\n[{name}] {len(errors)} error(s):")
            for e in errors:
                wc.eprint(f"  ✗ {e}")
        else:
            wc.ok(f"[{name}] clean")
        all_errors.extend(errors)

    if args.json:
        print(json.dumps(
            {"layers": {k: len(v) for k, v in per_layer.items()},
             "errors": per_layer},
            ensure_ascii=False, indent=1))

    if all_errors:
        wc.eprint(f"\n✗ Total {len(all_errors)} error(s) across {len(runs)} layer(s)")
        return 1
    wc.ok(f"\n✓ All {len(runs)} layer(s) clean")
    return 0


def run(args: list[str]) -> int:
    sys.argv = ["wiki_lint"] + args
    return main()


if __name__ == "__main__":
    sys.exit(main())