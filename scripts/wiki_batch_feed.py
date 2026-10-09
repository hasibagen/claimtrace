#!/usr/bin/env python3
"""wiki_batch_feed.py — 文献清单 CSV 批次喂入器(包装 wiki_run_extract.sh)。

循环:扫描 CSV 中「raw/<ck>/full.md 已就绪 且 00-pending 未提交 且 未 promote 且无锁」
的 citekey(按 relevance 降序,partition 分片保证多 feeder 不重叠)→ 逐篇调
wiki_run_extract.sh(引擎可 --engine pi|codex;pi 默认 cce-minimax3/MiniMax-M3,
codex 默认走 ~/.codex/config.toml 模型,--model 可覆盖)→ runner 内部落盘即提交。
runner 结束后跑 S5 兜底修复(related_evidence/claims 正向边反推 + 重渲染)再提交一次。
全部完成或仅剩阻塞(raw 缺失且 MinerU 队列已结束)时退出。

用法:
  nohup python3 .skill/scripts/wiki_batch_feed.py <csv> --partition I --total N \
      [--engine pi|codex] [--model M] \
      > /tmp/pi_logs_runner/feeder_I.log 2>&1 &
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc

WIKI_ROOT = Path(__file__).resolve().parent.parent.parent
RUNNER = WIKI_ROOT / ".skill" / "scripts" / "wiki_run_extract.sh"
RENDER = WIKI_ROOT / ".skill" / "scripts" / "wiki_render_nodes.py"
MINERU_STATE = Path("/tmp/mineru_batch/state.json")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def committed(ck: str) -> bool:
    r = subprocess.run(["git", "cat-file", "-e", f"HEAD:00-pending/{ck}/{ck}.md"],
                       cwd=WIKI_ROOT, capture_output=True)
    return r.returncode == 0


def has_lock(ck: str) -> bool:
    return any((WIKI_ROOT / ".git" / "wiki-locks").glob(f"{ck}.*"))


_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)

def load_fm_yaml(path: Path) -> tuple[dict, str]:
    """yaml.safe_load 解析 frontmatter(2026-09-03 修复:wc.parse_frontmatter 是 naive
    逐行解析器,读不懂 block scalar/block list,且要求结尾 --- 后必须有换行——
    LLM 落盘的 evidence/claim 大量使用 >- 多行与换行列表,s5_fix 反推会全部失配)。"""
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        import yaml
        y = yaml.safe_load(m.group(1)) or {}
        return (y if isinstance(y, dict) else {}), text[m.end():]
    except yaml.YAMLError:
        return {}, ""


def s5_fix(ck: str) -> bool:
    """正向边反推补 related_evidence/claims + 重渲染(pending)。返回是否有改动。"""
    pdir = WIKI_ROOT / "00-pending" / ck
    paper = pdir / f"{ck}.md"
    if not paper.is_file():
        return False
    text = paper.read_text(encoding="utf-8")
    fm, body = load_fm_yaml(paper)
    evs, cls = set(), set()
    edir, cdir = pdir / "evidence", pdir / "claims"
    if edir.is_dir():
        for f in edir.glob("*.md"):
            efm, _ = load_fm_yaml(f)
            src = str(efm.get("prov_paper") or "")
            if src and ck[:12] in src.replace("papers/", ""):
                evs.add(f.stem)
    if cdir.is_dir():
        for f in cdir.glob("*.md"):
            cfm, _ = load_fm_yaml(f)
            if any(ck[:12] in str(s).replace("papers/", "") for s in (cfm.get("sources_targets") or [])):
                cls.add(f.stem)
    old = (fm.get("related_evidence") or [], fm.get("related_claims") or [])
    fm["related_evidence"] = sorted({x for x in old[0]} | {f"[[{x}]]" for x in evs})
    fm["related_claims"] = sorted({x for x in old[1]} | {f"[[{x}]]" for x in cls})
    changed = (fm["related_evidence"], fm["related_claims"]) != tuple(old)
    if changed:
        paper.write_text(wc.dump_frontmatter_safe(fm, body), encoding="utf-8")
    subprocess.run([sys.executable, str(RENDER), "paper", str(pdir) + "/"],
                   cwd=WIKI_ROOT, capture_output=True, timeout=300)
    return changed


def commit_path(ck: str, msg: str) -> None:
    subprocess.run(["git", "add", f"00-pending/{ck}", f"raw/{ck}"], cwd=WIKI_ROOT)
    subprocess.run(["git", "commit", "-q", "-m", msg, "--", f"00-pending/{ck}", f"raw/{ck}"],
                   cwd=WIKI_ROOT, capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--partition", type=int, default=0)
    ap.add_argument("--total", type=int, default=1)
    ap.add_argument("--max-rounds", type=int, default=500)
    ap.add_argument("--idle-wait", type=int, default=90)
    ap.add_argument("--engine", choices=["pi", "codex"], default="pi",
                    help="抽取引擎(2026-09-04 解耦);zcode 为会话内模式不经过 feeder")
    ap.add_argument("--model", default=None,
                    help="透传给 runner 的 --model;缺省 pi=cce 默认链,codex=config.toml 模型")
    args = ap.parse_args()

    rows = sorted(csv.DictReader(open(args.csv, encoding="utf-8")),
                  key=lambda r: -int(r.get("relevance_score") or 0))
    mine = [r["citation_key"] for r in rows
            if int(hashlib.md5(r["citation_key"].encode()).hexdigest(), 16) % args.total == args.partition]
    log(f"feeder {args.partition}/{args.total}: {len(mine)} 篇候选(按 relevance)")

    done_ct, fail_ct = 0, 0
    idle_rounds = 0
    blocked: dict[str, int] = {}   # 连续失败黑名单
    for _ in range(args.max_rounds):
        target = None
        for ck in mine:
            if (WIKI_ROOT / "papers" / f"{ck}.md").is_file():
                continue
            if committed(ck):
                continue
            if not (WIKI_ROOT / "raw" / ck / "full.md").is_file():
                continue
            if has_lock(ck):
                continue
            if blocked.get(ck, 0) >= 3:
                continue
            target = ck
            break
        if target is None:
            remaining = [ck for ck in mine if not committed(ck)
                         and not (WIKI_ROOT / "papers" / f"{ck}.md").is_file()
                         and blocked.get(ck, 0) < 3]
            if not remaining:
                dead = [ck for ck in mine if blocked.get(ck, 0) >= 3
                        and not committed(ck)
                        and not (WIKI_ROOT / "papers" / f"{ck}.md").is_file()]
                log(f"全部完成 ✅(黑名单 {len(dead)} 篇: {' '.join(dead[:10])}{'…' if len(dead) > 10 else ''})")
                return 0
            no_raw = [ck for ck in remaining if not (WIKI_ROOT / "raw" / ck / "full.md").is_file()]
            if no_raw and len(no_raw) == len(remaining):
                idle_rounds += 1
                if idle_rounds >= 10:  # ~15 分钟无新 raw → MinerU 队列应已结束
                    log(f"仅剩无 raw 的 {len(remaining)} 篇(MinerU 队列应已结束),退出")
                    return 0
                log(f"无就绪目标,剩 {len(remaining)} 篇(其中 {len(no_raw)} 篇无 raw),等待 {args.idle_wait}s …")
                time.sleep(args.idle_wait)
                continue
            idle_rounds = 0
            time.sleep(args.idle_wait)
            continue

        idle_rounds = 0
        log(f"→ runner[{args.engine}]: {target}")
        cmd = ["bash", str(RUNNER), "--engine", args.engine]
        if args.engine == "pi":
            cmd += ["--provider", "cce-minimax3", "--model", args.model or "MiniMax-M3"]
        elif args.model:
            cmd += ["--model", args.model]
        cmd.append(target)
        # runner 内部超时 pi=1800 / codex=3600,feeder 外层留足余量
        feed_timeout = 2100 if args.engine == "pi" else 3900
        subprocess.run(cmd, cwd=WIKI_ROOT, timeout=feed_timeout, capture_output=True)
        if (WIKI_ROOT / "00-pending" / target / f"{target}.md").is_file():
            blocked.pop(target, None)
            if s5_fix(target):
                commit_path(target, f"fix(auto): {target} S5 互联补 related + 重渲染 (feeder)")
                log(f"✅ {target} 完成(S5 兜底修复)")
            else:
                log(f"✅ {target} 完成")
            done_ct += 1
        else:
            fail_ct += 1
            blocked[target] = blocked.get(target, 0) + 1
            pilog = Path(f"/tmp/pi_logs_runner/{target}.log")
            rate_hit = False
            if pilog.is_file():
                tail = pilog.read_text(encoding="utf-8", errors="ignore")[-2000:]
                rate_hit = ("429" in tail or "rate_limit" in tail or "用量上限" in tail)
            if rate_hit:
                # 配额类故障:全局限流,换篇也会失败 → 长退避后重试本篇(不计黑名单)
                blocked.pop(target, None)
                log(f"⏸ {target} 遇 API 配额限制(429),退避 1800s 等配额恢复 …")
                time.sleep(1800)
            else:
                log(f"❌ {target} FAIL({blocked[target]}/3),见 /tmp/pi_logs_runner/{target}.log")
    log(f"到达最大轮次: done={done_ct} fail={fail_ct}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
