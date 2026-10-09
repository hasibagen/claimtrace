#!/usr/bin/env python3
"""
wiki_stat_sanity.py — 数值双检 + 冲突清单(批次4,kimi Q5 L3/L4 + deepseek)

纯确定性数学,无 LLM:
  A. stat_sanity:evidence frontmatter 数值内部一致性
     - r + n → 反推 95% CI(≈ r ± 1.96/√(n-3),Fisher z),与 verify_ci_95 比对
     - t + df → 反推 p(双尾正态近似),与 verify_p_value 数量级比对(>1 个数量级差报警)
     - 效应量方向 vs 统计量符号
  B. CONFLICTING:同一 claim 同含 supports 与 contradicts 非空边 → 列入冲突清单
     (deepseek:"发现矛盾是杀手级价值"——矛盾应触发 synthesis 解释,不该被静默平均)

用法:python3 wiki_stat_sanity.py [--json]
输出:STAT_MISMATCH 清单 + CONFLICTING 清单(exit 1 表示有冲突需人审)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def load_fm(p: Path) -> dict:
    m = FM_RE.match(p.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_ci(s):
    if not s:
        return None
    m = re.findall(r"(-?\d+\.?\d*)", str(s))
    return (float(m[0]), float(m[1])) if len(m) >= 2 else None


def stat_sanity(wiki_root: Path) -> list[str]:
    issues = []
    for f in sorted((wiki_root / "evidence").glob("*.md")):
        fm = load_fm(f)
        n = _num(fm.get("verify_n"))
        r = None
        # r 可能在 stat 或 effect 里
        tst = str(fm.get("verify_test_stat_type") or "").lower()
        est = str(fm.get("verify_effect_size_type") or "").lower()
        if tst == "r":
            r = _num(fm.get("verify_test_stat_value"))
        elif est in ("r", "rho"):
            r = _num(fm.get("verify_effect_size_value"))
        ci = _parse_ci(fm.get("verify_ci_95"))

        # r∈[-1,1] 基本域
        if r is not None and not (-1 <= r <= 1):
            issues.append(f"STAT[{f.name}] r={r} 超出 [-1,1](抽取错误,如 12±4 被拼成 124)")

        # r+n → CI 反推(Fisher z 近似)
        if r is not None and n and n > 4 and ci and -1 < r < 1:
            try:
                z = 0.5 * math.log((1 + r) / (1 - r))
                se = 1 / math.sqrt(n - 3)
                lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
                if not (lo * 0.5 <= ci[0] and ci[1] <= hi * 1.5 + 0.05):
                    issues.append(f"STAT[{f.name}] r={r},n={n} 反推 CI≈[{lo:.2f},{hi:.2f}] 与报告 {ci} 偏差过大")
            except (ValueError, ZeroDivisionError):
                pass

        # t+df → p 数量级(双尾正态近似)
        t = _num(fm.get("verify_test_stat_value")) if tst == "t" else None
        df = _num(fm.get("verify_df"))
        p = _num(fm.get("verify_p_value"))
        if t is not None and df and p is not None and p > 0:
            try:
                from statistics import NormalDist
                p_est = 2 * (1 - NormalDist().cdf(abs(t)))
                if p > 0 and (p / max(p_est, 1e-12) > 30 or p_est / max(p, 1e-12) > 30):
                    issues.append(f"STAT[{f.name}] t={t},df={df} 反推 p≈{p_est:.2g} 与报告 p={p} 差 >1.5 个数量级")
            except Exception:
                pass
    return issues


def conflicting(wiki_root: Path) -> list[str]:
    out = []
    for f in sorted((wiki_root / "claims").glob("*.md")):
        fm = load_fm(f)
        sup = [x for x in (fm.get("supports_targets") or []) if str(x).strip().strip("[]")]
        con = [x for x in (fm.get("contradicts_targets") or []) if str(x).strip().strip("[]")]
        if sup and con:
            out.append(f"CONFLICT[{f.stem}] supports {len(sup)} 条 vs contradicts {len(con)} 条 → 应建 synthesis 解释矛盾来源(样本?方法?效力?)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent.parent

    stats = stat_sanity(root)
    confs = conflicting(root)

    if args.json:
        print(json.dumps({"stat_sanity": stats, "conflicting": confs}, ensure_ascii=False, indent=2))
    else:
        print(f"== STAT_SANTITY({len(stats)} 项数值不一致)")
        for s in stats:
            print("  ✗", s)
        print(f"\n== CONFLICTING({len(confs)} 个 claim 存在支持/反对并存)")
        for c in confs:
            print("  ⚡", c)
        if confs:
            print("\n→ 矛盾是知识:逐个建 synthesis 解释冲突来源,不要静默平均(AI 共识)")
    return 1 if (stats or confs) else 0


if __name__ == "__main__":
    sys.exit(main())
