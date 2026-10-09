#!/usr/bin/env python3
"""wiki_audit_pending.py — 00-pending 批次体检(S4 机械检查固化,2026-08-26)

检查项(按 2026-08-26 孪生脑批次问题谱系):
  A1 canonical paper md 缺失          A2 多余顶层 md(如 paper.md)
  A3 意外子目录                      A4/A5 claims//evidence/ 缺失或空
  B1/B4 frontmatter 无 related_*     B2/B5 related_* 非 [[wikilink]] 格式
  B3/B6 related_* 指向不存在的节点(本地+正式区都不存在才算)
  B7/B8 本地 evidence/claim 未被 paper 引用(frontmatter+正文)
  B9 paper raw_path 不存在(相对路径按 wiki 根解析)
  B10 paper 正文缺 "## 本论文的 Evidence(全文)" / "## 本论文支持的 Claims(全文)"
  B11 raw 命中代码/数据平台链接(github/zenodo/osf/...)但 paper 无 "## Code & Data";
      或 frontmatter 有 code_urls/data_url 而正文 Code & Data 未列出这些 URL
  C1 evidence prov_source_text 缺失/占位
  C3 evidence prov_source_text HTML 表格碎片
  C5 evidence prov_source_text 截断开头(小写字母起头且非常见虚词)
  C6 claim 残留占位字段 prov_paper=TODO / prov_source_text=待补(claim 契约无此二字段)
  C7 evidence 带 raw_path(违反 S7 闸门"evidence 无 raw_path")
  C8 raw/<citekey>/full.md 缺失(S2 未走)
  C9 claim statement 缺失/占位(空壳残体,2026-09-09);C1 扩展 'test' 占位

用法: python3 .skill/scripts/wiki_audit_pending.py [00-pending 目录] [--summary]
"""
from __future__ import annotations
import os, re, sys, glob, yaml, unicodedata
from pathlib import Path

WIKI = Path(__file__).resolve().parent.parent.parent
if "--help" in sys.argv or "-h" in sys.argv:
    print(__doc__)
    print("用法: python3 wiki_audit_pending.py [00-pending 目录] [--summary]")
    sys.exit(0)
PEND = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else WIKI / "00-pending"
SUMMARY = "--summary" in sys.argv

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)

def load(path: Path):
    try:
        t = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"__error__": "read_fail"}, ""
    m = FM_RE.match(t)
    if not m:
        return {"__error__": "no_fm"}, t
    try:
        return yaml.safe_load(m.group(1)) or {}, t[m.end():]
    except yaml.YAMLError as e:
        return {"__error__": f"yaml: {str(e).splitlines()[0]}"}, ""

def unwrap(v):
    if isinstance(v, list):  # 容错:嵌套 list(如 [['x']])拍平为字符串,按非 wikilink 报告而非崩溃
        return ", ".join(unwrap(x) for x in v)
    if not isinstance(v, str):
        return str(v)
    m = re.fullmatch(r"\[\[(.+?)\]\]", v.strip())
    return (m.group(1) if m else v.strip()).split("/")[-1].removesuffix(".md").strip() if (m or "/" in v or v.strip().endswith(".md")) else (m.group(1) if m else v.strip())

def is_wikilink(v):
    return isinstance(v, str) and bool(re.fullmatch(r"\[\[(.+?)\]\]", v.strip()))

FORMAL_CLAIMS = {f.stem for f in (WIKI / "claims").glob("*.md")} if (WIKI / "claims").is_dir() else set()
FORMAL_EVID = {f.stem for f in (WIKI / "evidence").glob("*.md")} if (WIKI / "evidence").is_dir() else set()

report: dict[str, list] = {}
for d in sorted(p for p in os.listdir(PEND) if (PEND / p).is_dir()):
    dp = PEND / d
    iss = []

    top_mds = sorted(f.name for f in dp.iterdir() if f.is_file() and f.suffix == ".md")
    if f"{d}.md" not in top_mds:
        iss.append(f"A1: 缺 canonical paper md;顶层={top_mds}")
    for f in top_mds:
        if f != f"{d}.md":
            iss.append(f"A2: 多余顶层 md: {f}")
    for sd in sorted(x.name for x in dp.iterdir() if x.is_dir()):
        if sd not in ("claims", "evidence"):
            iss.append(f"A3: 意外子目录: {sd}/")
    claims_f = sorted(glob.glob(str(dp / "claims/*.md")))
    evid_f = sorted(glob.glob(str(dp / "evidence/*.md")))
    if not claims_f: iss.append("A4: claims/ 缺失或为空")
    if not evid_f: iss.append("A5: evidence/ 缺失或为空")
    ev_names = {Path(x).stem for x in evid_f}
    cl_names = {Path(x).stem for x in claims_f}

    pmd = dp / f"{d}.md"
    if pmd.exists():
        fm, body = load(pmd)
        if "__error__" in fm:
            iss.append(f"A6: paper YAML 损坏: {fm['__error__']}")
        else:
            for key, names, formal, tag in (("related_evidence", ev_names, FORMAL_EVID, "ev"),
                                            ("related_claims", cl_names, FORMAL_CLAIMS, "cl")):
                vals = fm.get(key)
                code = "B1" if key == "related_evidence" else "B4"
                if not vals:
                    iss.append(f"{code}: frontmatter 无 {key}")
                else:
                    if isinstance(vals, str): vals = [vals]
                    for e in vals:
                        nm = unwrap(e)
                        if not is_wikilink(e):
                            iss.append(f"{'B2' if tag=='ev' else 'B5'}: {key} 非 wikilink: {str(e)[:50]}")
                        if nm not in names and nm not in formal:
                            iss.append(f"{'B3' if tag=='ev' else 'B6'}: {key} 指向不存在节点: {nm[:50]}")
            for n in sorted(ev_names):
                if n not in (body or ""):
                    iss.append(f"B7: evidence 未被 paper 引用: {n[:50]}")
            for n in sorted(cl_names):
                if n not in (body or ""):
                    iss.append(f"B8: claim 未被 paper 引用: {n[:50]}")
            rp = fm.get("raw_path")
            if isinstance(rp, str) and rp.strip():
                p = Path(rp) if rp.startswith("/") else WIKI / rp
                if not p.exists():
                    iss.append(f"B9: raw_path 不存在: {rp[:70]}")
            if "## 本论文的 Evidence(全文)" not in (body or ""):
                iss.append("B10: 正文缺『## 本论文的 Evidence(全文)』章节")
            if "## 本论文支持的 Claims(全文)" not in (body or ""):
                iss.append("B10: 正文缺『## 本论文支持的 Claims(全文)』章节")
            # B11 Code & Data(2026-09-03):链接必须落到正文章节,raw 有信号而未捕获即退回
            cb = body or ""
            _cu = fm.get("code_urls")
            _du = fm.get("data_url")
            fm_urls = [v.strip() for v in (_cu if isinstance(_cu, list) else [_cu]) +
                       (_du if isinstance(_du, list) else [_du])
                       if isinstance(v, str) and v.strip()]
            if "## Code & Data" not in cb:
                if fm_urls:
                    iss.append(f"B11: 正文缺『## Code & Data』章节,frontmatter 已有 {len(fm_urls)} 个 URL 未整理")
                else:
                    rawp = WIKI / "raw" / d / "full.md"
                    if rawp.exists():
                        try:
                            _m = re.search(r"(github\.com|gitlab\.com|bitbucket\.org|zenodo\.org|osf\.io|figshare\.com|dryad\.|huggingface\.co)",
                                           rawp.read_text(encoding="utf-8", errors="replace"), re.I)
                            if _m:
                                iss.append(f"B11: raw 命中代码/数据平台链接({_m.group(1)})但正文无『## Code & Data』章节"
                                           " — 核实后整理;若仅为参考文献引用他人仓库,在该章节注明即可")
                        except Exception:
                            pass
            elif fm_urls and not any(u in cb for u in fm_urls):
                iss.append(f"B11: frontmatter 有 {len(fm_urls)} 个代码/数据 URL 但正文『## Code & Data』未列出")
    if not (WIKI / "raw" / d / "full.md").exists():
        iss.append("C8: raw/<citekey>/full.md 缺失")

    def check(files, kind):
        for fp in files:
            fn = Path(fp).name
            fm, _ = load(Path(fp))
            if "__error__" in fm:
                iss.append(f"C0: {kind}/{fn[:46]} YAML 损坏: {str(fm['__error__'])[:50]}")
                continue
            if kind == "ev":
                pst = fm.get("prov_source_text")
                s = str(pst or "").strip()
                if not s or s in ("(待补)", "待补", "TODO", "test"):
                    iss.append(f"C1: {kind}/{fn[:46]} prov_source_text 缺失/占位")
                elif re.search(r"</?t[dr]>|<tr>|</?table", s):
                    iss.append(f"C3: {kind}/{fn[:46]} prov_source_text=HTML 碎片")
                elif re.match(r"^[a-z]{3,}", s) and not re.match(r"^(the|a|an|in|on|for|and|but|with|from|this|that|these|we|our|it|is|was|to|of|as|at|by|or|if|no|not|both|whereas)\b", s):
                    iss.append(f"C5: {kind}/{fn[:46]} prov_source_text 截断开头")
                if "raw_path" in fm:
                    iss.append(f"C7: {kind}/{fn[:46]} 带 raw_path(违反 S7)")
            else:
                pp = str(fm.get("prov_paper") or "")
                if "TODO" in pp:
                    iss.append(f"C6: {kind}/{fn[:46]} prov_paper=TODO 占位")
                st_stmt = str(fm.get("statement") or "").strip()
                if st_stmt in ("", "(未填写)", "test", "TODO"):
                    iss.append(f"C9: {kind}/{fn[:46]} statement 缺失/占位(空壳残体)")
                ps = str(fm.get("prov_source_text") or "").strip()
                if ps in ("(待补)", "待补", "TODO", "test"):
                    iss.append(f"C6: {kind}/{fn[:46]} prov_source_text=待补 占位")
    check(evid_f, "ev")
    check(claims_f, "cl")

    if iss:
        report[d] = iss

from collections import Counter
cnt = Counter(i.split(":")[0] for iss in report.values() for i in iss)
total_dirs = len([p for p in os.listdir(PEND) if (PEND / p).is_dir()])
print(f"== 00-pending 体检: 目录 {total_dirs}, 有问题 {len(report)} ==")
for k in sorted(cnt):
    print(f"  {k}: {cnt[k]}")
if not SUMMARY:
    print()
    for d, iss in report.items():
        print(f"### {d}")
        for i in iss:
            print(f"  - {i}")
