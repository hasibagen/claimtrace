#!/usr/bin/env python3
"""
wiki_batch_status.py — 批次档案进度自动刷新(2026-08-27,log/ 文件夹体系)

从文件系统事实(raw / 00-pending / papers / 篇级锁)重建批次文件的 AUTO 区:
  - <!-- AUTO:progress-start --> … <!-- AUTO:progress-end -->   阶段进度摘要
  - <!-- AUTO:papers-start -->   … <!-- AUTO:papers-end -->     论文明细表(保留 citekey/备注列,重算状态列)

用法:
  python3 wiki_batch_status.py log/batch-xxx.md [log/batch-yyy.md ...]
  python3 wiki_batch_status.py --all          # 刷新 log/batch-*.md + log/README.md 索引表
  python3 wiki_batch_status.py --all --dry-run

设计:纯机械、幂等(同一天内重复运行输出一致);append 区(Runner/事件)与
人工区(元信息/阻塞清单)永不触碰。铁律 #3:LLM 抽取,scripts 校验。
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

WIKI_ROOT = SCRIPTS_DIR.parent.parent
LOG_DIR = WIKI_ROOT / "log"

PROGRESS_RE = re.compile(r"(<!-- AUTO:progress-start -->\n)(.*?)(\n?<!-- AUTO:progress-end -->)", re.DOTALL)
PAPERS_RE = re.compile(r"(<!-- AUTO:papers-start -->\n)(.*?)(\n?<!-- AUTO:papers-end -->)", re.DOTALL)

STAT_PROMOTED = "🚀 promoted"
STAT_EXTRACTED = "✅ extracted"
STAT_HALF = "⚠️ 半途"
STAT_EXTRACTING = "🔵 extracting"
STAT_PENDING = "⬜ pending"
STAT_BLOCKED = "❌ blocked"


def count_dir(p: Path) -> int:
    return len([f for f in p.iterdir() if f.suffix == ".md"]) if p.is_dir() else 0


def has_lock(ck: str) -> bool:
    lockdir = WIKI_ROOT / ".git" / "wiki-locks"
    return any(lockdir.glob(f"{ck}.*"))


def fm_list_len(md_path: Path, keys: tuple[str, ...]) -> int:
    """数 paper frontmatter 里第一个非空列表字段的长度(yaml.safe_load,失败返回 -1)。"""
    try:
        import yaml
        text = md_path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not m:
            return -1
        fm = yaml.safe_load(m.group(1)) or {}
        for k in keys:
            v = fm.get(k)
            if isinstance(v, list) and v:
                return len(v)
        return 0
    except Exception:
        return -1


def probe(ck: str) -> dict:
    """查一篇论文的文件系统事实 → 状态 + c/e 计数。"""
    raw_ok = (WIKI_ROOT / "raw" / ck / "full.md").is_file()
    c = count_dir(WIKI_ROOT / "00-pending" / ck / "claims")
    e = count_dir(WIKI_ROOT / "00-pending" / ck / "evidence")
    paper_md = WIKI_ROOT / "papers" / f"{ck}.md"
    if paper_md.is_file():
        pc = fm_list_len(paper_md, ("related_claims", "claims"))
        pe = fm_list_len(paper_md, ("related_evidence", "evidence"))
        return {"stat": STAT_PROMOTED, "raw": raw_ok, "c": pc, "e": pe}
    if c or e:
        return {"stat": STAT_EXTRACTED if (c and e) else STAT_HALF, "raw": raw_ok, "c": c, "e": e}
    if has_lock(ck):
        return {"stat": STAT_EXTRACTING, "raw": raw_ok, "c": 0, "e": 0}
    if raw_ok:
        return {"stat": STAT_PENDING, "raw": raw_ok, "c": 0, "e": 0}
    return {"stat": STAT_BLOCKED, "raw": False, "c": 0, "e": 0}


def parse_table(block: str) -> tuple[list[str], list[list[str]]]:
    """解析 markdown 表 → (表头列, 数据行列表)。"""
    lines = [ln for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    header, data = rows[0], rows[2:]
    return header, data


def render_table(header: list[str], data: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in data:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def refresh_batch(path: Path, dry: bool = False) -> str:
    """刷新一个批次文件,返回摘要行。"""
    text = path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    stats: dict[str, int] = {}
    changed = []

    m = PAPERS_RE.search(text)
    if m:
        header, data = parse_table(m.group(2))
        # 期望列: citekey | raw | S3 | c/e | 状态 | 备注(位置按表头名找,顺序无关)
        idx = {name: i for i, name in enumerate(header)}
        need = {"citekey", "raw", "S3", "c/e", "状态"}
        if not need.issubset(idx):
            changed.append("papers 表列头缺 " + ",".join(need - set(idx)) + "(跳过)")
        else:
            note_i = idx.get("备注")
            new_rows = []
            for r in data:
                ck = r[idx["citekey"]]
                if not ck or ck.startswith("—") or ck.startswith("("):
                    new_rows.append(r)
                    continue
                info = probe(ck)
                stats[info["stat"]] = stats.get(info["stat"], 0) + 1
                nr = list(r)
                nr[idx["raw"]] = "✓" if info["raw"] else "✗"
                nr[idx["S3"]] = "✓" if info["stat"] in (STAT_PROMOTED, STAT_EXTRACTED) else ("◐" if info["stat"] == STAT_HALF else "")
                nr[idx["c/e"]] = f'{info["c"]}/{info["e"]}' if min(info["c"], info["e"]) >= 0 else "—"
                nr[idx["状态"]] = info["stat"]
                if note_i is not None and note_i < len(r):
                    nr[note_i] = r[note_i]  # 备注列人工维护,保留
                new_rows.append(nr)
            new_block = render_table(header, new_rows)
            text = text[: m.start(2)] + new_block + text[m.end(2):]
            changed.append(f"papers {len(new_rows)} 行")

    total = sum(stats.values())
    done = stats.get(STAT_PROMOTED, 0) + stats.get(STAT_EXTRACTED, 0)
    summary = (
        f"- 目标 {total} 篇(以明细表行数为准):"
        f"🚀 {stats.get(STAT_PROMOTED, 0)} · ✅ {stats.get(STAT_EXTRACTED, 0)} · "
        f"⚠️ {stats.get(STAT_HALF, 0)} · 🔵 {stats.get(STAT_EXTRACTING, 0)} · "
        f"⬜ {stats.get(STAT_PENDING, 0)} · ❌ {stats.get(STAT_BLOCKED, 0)}"
        f" — **抽取完成 {done}/{total}**"
        f"\n- 刷新: {today} · `python3 .skill/scripts/wiki_batch_status.py {path.relative_to(WIKI_ROOT)}`"
    )
    m2 = PROGRESS_RE.search(text)
    if m2:
        text = text[: m2.start(2)] + summary + text[m2.end(2):]
    changed.append("progress 摘要")

    if not dry:
        path.write_text(text, encoding="utf-8")
    return f"{'[dry] ' if dry else ''}{path.name}: {'; '.join(changed)} → done {done}/{total}"


def refresh_index(dry: bool = False) -> str:
    """刷新 log/README.md 索引表的「S3 抽取」「promote」两列。"""
    readme = LOG_DIR / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines(keepends=True)
    in_index = False
    n = 0
    for i, ln in enumerate(lines):
        if "AUTO:index-start" in ln:
            in_index = True
            continue
        if "AUTO:index-end" in ln:
            in_index = False
            continue
        if not in_index or not ln.strip().startswith("|"):
            continue
        m = re.search(r"\(batch-([\w-]+)\.md\)", ln)
        if not m:
            continue
        slug = m.group(1)
        bp = LOG_DIR / f"batch-{slug}.md"
        if not bp.is_file():
            continue
        # 该批次的计数(从批次文件重算,轻量:直接 probe 明细表)
        text = bp.read_text(encoding="utf-8")
        pm = PAPERS_RE.search(text)
        if not pm:
            continue
        header, data = parse_table(pm.group(2))
        idx = {name: i for i, name in enumerate(header)}
        if "citekey" not in idx:
            continue
        done = promoted = total = 0
        for r in data:
            ck = r[idx["citekey"]]
            if not ck or ck.startswith("—"):
                continue
            total += 1
            st = probe(ck)["stat"]
            promoted += st == STAT_PROMOTED
            done += st in (STAT_PROMOTED, STAT_EXTRACTED)
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) >= 7:
            cols[4] = f"{done}/{total}"
            cols[5] = str(promoted)
            lines[i] = "| " + " | ".join(cols) + " |\n"
            n += 1
    if not dry:
        readme.write_text("".join(lines), encoding="utf-8")
    return f"{'[dry] ' if dry else ''}README 索引: 刷新 {n} 行"


def main() -> int:
    ap = argparse.ArgumentParser(description="批次档案进度自动刷新")
    ap.add_argument("batches", nargs="*", type=Path, help="批次文件路径")
    ap.add_argument("--all", action="store_true", help="log/batch-*.md 全部 + README 索引")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    paths: list[Path] = []
    if args.all:
        paths += sorted(LOG_DIR.glob("batch-*.md"))
    for b in args.batches:
        p = Path(b)
        paths.append(p if p.is_absolute() else WIKI_ROOT / p)
    if not paths:
        ap.error("指定批次文件或 --all")

    for p in paths:
        if not p.is_file():
            print(f"skip: {p} 不存在")
            continue
        print(refresh_batch(p, args.dry_run))
    if args.all:
        print(refresh_index(args.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
