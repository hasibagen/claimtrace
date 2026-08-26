#!/usr/bin/env python3
"""
wiki_render_nodes.py — 生成式视图统一渲染器(五批次优化·批次2,ARCHITECTURE §3 批次2 注记)

核心原则:**frontmatter 是唯一维护面,body 全部脚本渲染**(§3.4 T-W4-027 "body 只渲染、
不维护" 推广到全节点)。LLM 抽取只写 frontmatter;本脚本负责:

  evidence <目标>  — 整体重生成 evidence body(观察/原文引用/解释/出处/边表/数值校验/反向链接)
  claim <目标>     — 整体重生成 claim body(主张陈述/推理桥/支持证据/限定条件/证据强度/反向链接)
  paper <目标>     — 重生成 paper 的自动段(核心主张表/证据条目表/transclusion 嵌入段/引用本论文行)
  index            — 生成根 index.md

设计:
  - frontmatter 原样保留(字节级不动,含行内注释——批次3 再清洗);只读解析用 PyYAML
  - 生成的 body 以 <!-- AUTO-RENDERED-BODY --> 注释开头;重跑=整体覆盖,天然幂等
  - 反向链接段从全库正向边推导(Backlinks Cache,gpt5.6sol §十四):
    claims.evidence_targets / evidence.supports_targets / papers.related_* / topics 正文 wikilink
  - paper 的叙事段(元信息/研究目的/被试/…/结论)不在此脚本管辖,保留 LLM 手写

用法:
  python3 wiki_render_nodes.py evidence evidence/            # 目录全部
  python3 wiki_render_nodes.py evidence <file>.md --dry-run
  python3 wiki_render_nodes.py claim claims/
  python3 wiki_render_nodes.py paper papers/
  python3 wiki_render_nodes.py index
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
import wiki_render_evidence_body as wrb   # 复用:数值校验表 + 边表渲染

AUTO_BANNER = "<!-- AUTO-RENDERED-BODY 由 wiki_render_nodes.py 生成;frontmatter 是唯一维护面,勿手编(批次2) -->"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


# ---------- 基础工具 ----------

def split_file(content: str) -> tuple[str, str]:
    """返回 (frontmatter 原文含---定界, body)。无 frontmatter 则 ("", content)。"""
    m = FM_RE.match(content)
    if not m:
        return "", content
    return content[: m.end()], content[m.end():]


def load_fm(content: str) -> dict:
    m = FM_RE.match(content)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _wikilink_name(link) -> str:
    """'[[papers/x|显示]]' / 'x' / ['[x]'] → 'x'"""
    if isinstance(link, list):
        link = link[0] if link else ""
    s = str(link).strip().strip("[]").split("|")[0].strip()
    return s.split("/")[-1].strip()


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    return [s] if s else []


def _md_escape_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ") if s is not None else ""


# ---------- 反向链接索引(Backlinks Cache) ----------

def build_reverse_index(wiki_root: Path, skip_body_scan: set[str] | None = None) -> dict[str, set[str]]:
    """
    node 名 → 指向它的来源页面名集合。

    skip_body_scan(批次2 幂等性修复):渲染 evidence 时不扫描 evidence 正文,
    否则反向索引读到"## 使用此证据的页面"中的 wikilink,backlinks 段随之变化,
    下次渲染又读到变化后的 backlinks,死循环。
    """
    skip_body_scan = skip_body_scan or set()
    rev: dict[str, set[str]] = {}

    def add(target: str, src: str):
        name = _wikilink_name(target)
        if name and name != src:
            rev.setdefault(name, set()).add(src)

    for d in ("claims", "evidence", "papers"):
        p = wiki_root / d
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.md")):
            fm = load_fm(f.read_text(encoding="utf-8"))
            src = f.stem
            for key in (
                "evidence_targets", "supports_targets", "contradicts_targets", "qualifies_targets",
                "sources_targets", "related_claims", "related_evidence", "related_topics", "cited_by",
                "source", "prov_paper",
            ):
                for t in _as_list(fm.get(key)):
                    add(t, src)

    # 正文扫描只用于"不含 frontmatter 反向链接"的目标(topics/syntheses)
    # 且不扫描 skip_body_scan 里的目录
    for d in ("topics", "syntheses"):
        if d in skip_body_scan:
            continue
        p = wiki_root / d
        if not p.is_dir():
            continue
        for f in p.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            for t in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]", text):
                add(t, f.stem)

    # 渲染 evidence/claim 时,**反向索引也跳过当前目录的 body**——
    # 只用 frontmatter 的正向边(=数据真值)推 backlinks。
    # 同时:渲染 evidence 不扫 evidence body(避免循环);渲染 claim 时同样
    #   claim 反向边由 evidence_targets/supports_targets 给出(frontmatter 已收),无需 body 扫描。
    return rev


def render_backlinks_section(node_name: str, rev: dict[str, set[str]], title: str) -> str:
    pages = sorted(rev.get(node_name, set()))
    if not pages:
        return f"## {title}\n\n_(暂无——由脚本从正向边生成,勿手加)_\n"
    lines = "\n".join(f"- [[{p}]]" for p in pages)
    return f"## {title}\n\n{lines}\n"


# ---------- evidence body ----------

def render_evidence_body(fm: dict, node_name: str, rev: dict[str, set[str]], schema: dict) -> str:
    observation = str(fm.get("observation") or fm.get("prov_source_text") or "").strip()
    quote = str(fm.get("prov_source_text") or "").strip()
    section = str(fm.get("prov_section") or "").strip()
    page = fm.get("prov_page")
    interp = str(fm.get("interp_text") or "").strip()
    interp_origin = str(fm.get("interp_origin") or "").strip()
    source = _as_list(fm.get("source") or fm.get("prov_paper"))
    source_link = source[0] if source else ""

    parts = [AUTO_BANNER, "", f"# {node_name}", ""]

    parts.append("## 观察(Observation)\n")
    parts.append(observation or "_(未填写)_")
    parts.append("")

    parts.append("## 原文引用\n")
    if quote:
        src_label = section or "原文"
        if page not in (None, "", "null"):
            src_label += f",p.{page}"
        q_lines = quote.split("\n")
        parts.append(f'> [!quote]+ **来源**: {src_label}')
        for ln in q_lines:
            parts.append(f"> {ln}")
    else:
        parts.append("_(prov_source_text 缺失)_")
    parts.append("")

    parts.append("## 解释(Interpretation)\n")
    if interp:
        if interp_origin:
            parts.append(f"- 解释来源: {interp_origin}")
        parts.append(f"- {interp}")
    else:
        parts.append("_(未填写)_")
    parts.append("")

    parts.append("## 出处(Provenance)\n")
    parts.append(f"- 论文: {source_link or '_(缺失)_'}")
    parts.append(f"- 章节: {section or '—'}")
    if page not in (None, "", "null"):
        parts.append(f"- 页码: {page}")
    parts.append(f"- 原文: {quote[:120]}{'…' if len(quote) > 120 else ''}")
    parts.append("")

    # 边表(复用 wrb)
    rel = wrb.render_relations_section(fm)
    if rel:
        parts.append(rel.rstrip())
        parts.append("")

    verify = wrb.render_verify_section(fm, schema)
    parts.append(verify.rstrip())
    parts.append("")

    parts.append(render_backlinks_section(node_name, rev, "使用此证据的页面").rstrip())
    parts.append("")
    return "\n".join(parts)


# ---------- claim body ----------

def _edge_table(targets: list, confidences: list, relations: list, header: str) -> str:
    if not targets:
        return ""
    rows = [f"| {header} | 关系 | 置信度 |", "|------|------|--------|"]
    for i, t in enumerate(targets):
        c = confidences[i] if i < len(confidences) else "—"
        r = relations[i] if i < len(relations) else "—"
        rows.append(f"| {_md_escape_cell(t)} | {r} | {c} |")
    return "\n".join(rows)


def render_claim_body(fm: dict, node_name: str, rev: dict[str, set[str]]) -> str:
    statement = str(fm.get("statement") or "").strip()
    reasoning = str(fm.get("reasoning") or "").strip()
    rtype = str(fm.get("reasoning_type") or "").strip()
    sources = _as_list(fm.get("sources_targets"))

    parts = [AUTO_BANNER, "", f"# {node_name}", ""]

    parts.append("## 主张陈述\n")
    parts.append(statement or "_(未填写)_")
    parts.append("")

    parts.append("## 推理桥\n")
    if reasoning:
        parts.append(reasoning)
        if rtype:
            parts.append(f"\n- 推理类型: `{rtype}`")
    else:
        parts.append("_(未填写)_")
    parts.append("")

    if sources:
        srcs = " ".join(f"[[{_wikilink_name(s)}]]" for s in sources)
        parts.append("## 来源论文\n")
        parts.append(srcs)
        parts.append("")

    t = _edge_table(_as_list(fm.get("evidence_targets")),
                    _as_list(fm.get("evidence_confidences")),
                    _as_list(fm.get("evidence_relations")), "证据")
    if t:
        parts.append("## 支持证据\n")
        parts.append(t)
        parts.append("")

    t = _edge_table(_as_list(fm.get("contradicts_targets")),
                    _as_list(fm.get("contradicts_confidences")),
                    _as_list(fm.get("contradicts_relations")), "证据")
    if t:
        parts.append("## 反对证据\n")
        parts.append(t)
        parts.append("")

    scopes = [(k, v) for k, v in (
        ("人群", fm.get("scope_population")), ("模态", fm.get("scope_modality")),
        ("任务", fm.get("scope_task")), ("脑区", fm.get("scope_region")),
        ("设计", fm.get("scope_study_design")),
    ) if v not in (None, "", "null")]
    parts.append("## 限定条件\n")
    parts.append("\n".join(f"- {k}: {v}" for k, v in scopes) if scopes else "_(无限定记录)_")
    parts.append("")

    parts.append("## 证据强度\n")
    parts.append(f"- 验证状态: `{fm.get('verify_status', '—')}`"
                 f"  · 强度: `{fm.get('verify_strength', '—')}`"
                 f"  · 共识: `{fm.get('verify_consensus', '—')}`")
    parts.append(f"- 证据计数: {fm.get('verify_evidence_count', '—')}"
                 f"(支持 {fm.get('verify_supporting_count', '—')}"
                 f" / 反对 {fm.get('verify_contradicting_count', '—')})")
    parts.append("")

    parts.append(render_backlinks_section(node_name, rev, "引用此主张的页面").rstrip())
    parts.append("")
    return "\n".join(parts)


# ---------- paper 自动段(混合渲染:叙事段保留) ----------

PAPER_AUTO_PATTERNS = [
    r"<!-- AUTO-RENDERED 由 wiki_render_nodes\.py 生成\(批次2\);[^>]*-->\n",
    r"\*\*核心主张\*\*[\s\S]*?(?=\n\*\*|\n## |\n# |\Z)",
    r"\*\*证据条目\*\*[\s\S]*?(?=\n\*\*|\n## |\n# |\Z)",
    r"\*\*关联主题\*\*[\s\S]*?(?=\n\*\*|\n## |\n# |\Z)",
    r"\*\*关联主张\*\*[\s\S]*?(?=\n\*\*|\n## |\n# |\Z)",
    r"\*\*引用本论文的页面\*\*[\s\S]*?(?=\n\*\*|\n## |\n# |\Z)",
    r"## 本论文的 Evidence[\s\S]*?(?=\n## |\n# |\Z)",
    r"## 本论文支持的 Claims?[\s\S]*?(?=\n## |\n# |\Z)",
]


def _claim_statement_map(wiki_root: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    p = wiki_root / "claims"
    if p.is_dir():
        for f in p.glob("*.md"):
            fm = load_fm(f.read_text(encoding="utf-8"))
            s = str(fm.get("statement") or "").strip()
            if s:
                m[f.stem] = s
    return m


def load_schema_for_promote():
    """给 wiki_promote.py 用:加载 evidence schema(wrb.load_schema 的稳定别名)。"""
    return wrb.load_schema()


def _evidence_map(wiki_root: Path) -> dict[str, dict]:
    """evidence 名 → frontmatter(供 paper 证据表查 fact_type/关键数值/关联 claim)。"""
    m: dict[str, dict] = {}
    p = wiki_root / "evidence"
    if p.is_dir():
        for f in p.glob("*.md"):
            m[f.stem] = load_fm(f.read_text(encoding="utf-8"))
    return m


def _evidence_key_numbers(fm: dict) -> str:
    """从 evidence frontmatter 拼关键数值摘要(统计量/效应量/p)。"""
    bits = []
    for t, v in (("stat", "verify_test_stat_value"), ("eff", "verify_effect_size_value"),
                 ("p", "verify_p_value"), ("n", "verify_n")):
        val = fm.get(v)
        if val not in (None, "", "null"):
            bits.append(f"{t}={val}")
    return ", ".join(bits) if bits else "—"


def render_paper_auto(fm: dict, node_name: str, rev: dict[str, set[str]],
                      claim_stmt: dict[str, str], ev_map: dict[str, dict] | None = None) -> str:
    """paper 的自动段(不含叙事):返回待插入的 markdown 块。"""
    ev_map = ev_map or {}
    claims = [_wikilink_name(x) for x in _as_list(fm.get("related_claims"))]
    evidences = [_wikilink_name(x) for x in _as_list(fm.get("related_evidence"))]

    parts = []
    parts.append(f"<!-- AUTO-RENDERED 由 wiki_render_nodes.py 生成(批次2);叙事段(研究目的/结果等)为 LLM 维护 -->\n")

    parts.append("**核心主张**\n")
    if claims:
        parts.append("| # | claim | 一句话 |")
        parts.append("|---|---|---|")
        for i, c in enumerate(claims, 1):
            stmt = _md_escape_cell(claim_stmt.get(c, "—"))
            parts.append(f"| {i} | [[{c}]] | {stmt} |")
    else:
        parts.append("_(无)_")
    parts.append("")

    parts.append("**证据条目**\n")
    if evidences:
        parts.append("| # | evidence | fact_type | 关键数值 | 关联 claim |")
        parts.append("|---|---|---|---|---|")
        for i, e in enumerate(evidences, 1):
            efm = ev_map.get(e, {})
            ftype = _md_escape_cell(str(efm.get("fact_type", "—")))
            nums = _md_escape_cell(_evidence_key_numbers(efm))
            sup = " ".join(_as_list(efm.get("supports_targets"))[:3])
            sup_names = " ".join(f"[[{_wikilink_name(s)}]]" for s in sup.split(" ") if s) if sup else "—"
            parts.append(f"| {i} | [[{e}]] | {ftype} | {nums} | {sup_names} |")
    else:
        parts.append("_(无)_")
    parts.append("")

    topic_links = fm.get("related_topics")
    if topic_links not in (None, "", []):
        tl = _as_list(topic_links)
        parts.append("**关联主题**  " + " ".join(f"[[{_wikilink_name(x)}]]" for x in tl) + "\n")
    if claims:
        parts.append("**关联主张**  " + " ".join(f"[[{c}]]" for c in claims) + "\n")

    pages = sorted(rev.get(node_name, set()))
    parts.append("**引用本论文的页面**  " +
                 (" ".join(f"[[{p}]]" for p in pages) if pages else "—") + "\n")

    parts.append("## 本论文的 Evidence(全文)\n")
    for e in evidences:
        parts.append(f'> [!evidence]+ **{e}**')
        parts.append(f"> ![[{e}]]")
        parts.append(">")
        parts.append("")

    parts.append("## 本论文支持的 Claims(全文)\n")
    for c in claims:
        parts.append(f'> [!claim]+ **{c}**')
        parts.append(f"> ![[{c}]]")
        parts.append(">")
        parts.append("")

    return "\n".join(parts)


def process_paper(path: Path, wiki_root: Path, rev: dict[str, set[str]],
                  claim_stmt: dict[str, str], ev_map: dict[str, dict] | None = None) -> str:
    content = path.read_text(encoding="utf-8")
    fm_raw, body = split_file(content)
    fm = load_fm(content)
    auto = render_paper_auto(fm, path.stem, rev, claim_stmt, ev_map or {})

    new_body = body
    for pat in PAPER_AUTO_PATTERNS:
        new_body = re.sub(pat, "", new_body, count=1)
    new_body = re.sub(r"\n{3,}", "\n\n", new_body).rstrip() + "\n"

    # 插入点:第一个 "## " 前的叙事块之后 → 简化:追加到 body 末尾(paper 正文以叙事开头)
    # 若 body 已有 "---" 分隔(模板习惯),插到第一个 \n---\n 之前
    m = re.search(r"\n---\s*\n", new_body)
    if m:
        new_body = new_body[: m.start()] + "\n" + auto + "\n---\n" + new_body[m.end():]
    else:
        new_body = new_body.rstrip() + "\n\n" + auto

    return (fm_raw if fm_raw else "---\ntype: paper\n---\n") + new_body


# ---------- index.md ----------

def render_index(wiki_root: Path) -> str:
    def count(d: str) -> int:
        p = wiki_root / d
        return len(list(p.glob("*.md"))) if p.is_dir() else 0

    def listing(d: str) -> str:
        p = wiki_root / d
        if not p.is_dir():
            return "_(空)_"
        names = sorted(f.stem for f in p.glob("*.md"))
        return "\n".join(f"- [[{n}]]" for n in names) if names else "_(空)_"

    lines = [
        "<!-- AUTO-RENDERED 由 wiki_render_nodes.py index 生成(批次2);勿手编 -->",
        "",
        "# Wiki 索引",
        "",
        f"- papers: {count('papers')} · claims: {count('claims')} · evidence: {count('evidence')}"
        f" · topics: {count('topics')} · syntheses: {count('syntheses')}",
        "",
        "## Papers",
        "",
        listing("papers"),
        "",
        "## Topics",
        "",
        listing("topics"),
        "",
        "## Syntheses",
        "",
        listing("syntheses"),
        "",
    ]
    return "\n".join(lines)


# ---------- 主流程 ----------

def process_nodes(kind: str, target: Path, wiki_root: Path, rev: dict[str, set[str]],
                  claim_stmt: dict[str, str], schema: dict) -> tuple[int, int]:
    if target.is_dir():
        files = sorted(target.glob("*.md"))
    else:
        files = [target]
    changed = unchanged = 0
    for f in files:
        content = f.read_text(encoding="utf-8")
        fm_raw, _ = split_file(content)
        fm = load_fm(content)
        if kind == "evidence":
            new_body = render_evidence_body(fm, f.stem, rev, schema)
        else:
            new_body = render_claim_body(fm, f.stem, rev)
        # fm_raw 末尾 '---\n' + body 末尾 '\n',中间不再额外加换行
        new_content = fm_raw + new_body.lstrip("\n")
        if new_content != content:
            f.write_text(new_content, encoding="utf-8")
            changed += 1
        else:
            unchanged += 1
    return changed, unchanged


def main() -> int:
    ap = argparse.ArgumentParser(description="生成式视图统一渲染器(批次2)")
    ap.add_argument("kind", choices=["evidence", "claim", "paper", "index"])
    ap.add_argument("target", nargs="?", help="目标文件或目录(index 不需要)")
    ap.add_argument("--wiki-root", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wiki_root = args.wiki_root or Path(__file__).resolve().parent.parent.parent
    dirmap = {"evidence": "evidence", "claim": "claims"}
    # 渲染 evidence/claim 时不扫同目录 body,避免反向链接循环(批次2 幂等性)
    skip = {dirmap.get(args.kind, "")} if args.kind in dirmap else set()
    rev = build_reverse_index(wiki_root, skip_body_scan=skip)
    claim_stmt = _claim_statement_map(wiki_root)
    ev_map = _evidence_map(wiki_root)
    schema = wrb.load_schema()

    if args.kind == "index":
        out = render_index(wiki_root)
        (wiki_root / "index.md").write_text(out, encoding="utf-8")
        print("✅ index.md 已生成")
        return 0

    if not args.target:
        print("❌ 需要 target 参数", file=sys.stderr)
        return 1
    target = Path(args.target)
    if not target.exists():
        print(f"❌ target 不存在: {target}", file=sys.stderr)
        return 1

    if args.kind == "paper":
        files = sorted(target.glob("*.md")) if target.is_dir() else [target]
        changed = unchanged = 0
        for f in files:
            content = f.read_text(encoding="utf-8")
            new_content = process_paper(f, wiki_root, rev, claim_stmt, ev_map)
            if new_content != content:
                if not args.dry_run:
                    f.write_text(new_content, encoding="utf-8")
                changed += 1
            else:
                unchanged += 1
        print(f"paper: 变更 {changed} / 未变 {unchanged}")
        return 0

    # P0-2 修复(2026-08-25):目标存在(文件/目录)就就地渲染,绝不重定向——
    # 显式传 00-pending/<ck>/evidence/ 时必须就地渲染,否则新抽取永远没 banner。
    # 仅当传入裸名(evidence/claims,相对 cwd 不存在)时才解析到 wiki 根的正式目录。
    if not target.exists():
        target = wiki_root / dirmap[args.kind]
        if not target.exists():
            print(f"❌ target 不存在: {args.target}", file=sys.stderr)
            return 1
    changed, unchanged = process_nodes(args.kind, target, wiki_root, rev, claim_stmt, schema)
    print(f"{args.kind}: 变更 {changed} / 未变 {unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
