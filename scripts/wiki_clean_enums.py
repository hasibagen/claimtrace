#!/usr/bin/env python3
"""
wiki_clean_enums.py — enum/类型脏值清洗(批次修复 4,2026-08-25)

范围:00-pending/*/claims/*.md + 00-pending/*/evidence/*.md(新抽取批次)。
正式目录 claims/ evidence/ 的存量清洗归批次 3.1,本脚本支持 --scope formal 时再跑。

原则(铁律 #3 LLM EXTRACTS, SCRIPTS VALIDATE 的推论):
  - 映射表由 LLM(人)审定,显式列出、可审计;脚本只机械执行
  - 多值字符串不丢弃:原值挪进 verify_note,数值字段置 null
  - frontmatter 用 dump_frontmatter_safe 写回(L-002 教训)
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "schemas"))
import wiki_common as wc
import _registry

# ---------- 审定映射表(2026-08-25,依据 ARCHITECTURE §3.4/§3.5 enum) ----------

REASONING_TYPE_MAP = {
    # → empirical_inference
    "empirical_inference": None, "empirical_comparison": "empirical_inference",
    "empirical_observations": "empirical_inference", "correlational_inference": "empirical_inference",
    "design_argument_empirical_check": "empirical_inference",
    "design_argument_with_quantitative_support": "empirical_inference",
    "inductive_from_benchmark": "empirical_inference", "statistical_inference": "empirical_inference",
    "empirical_replication": "empirical_inference", "empirical_validation": "empirical_inference",
    "corroborative_comparison": "empirical_inference",
    # → theoretical_assumption
    "theoretical_assumption": None, "deductive": "theoretical_assumption",
    "analytical_derivation": "theoretical_assumption", "mathematical_derivation": "theoretical_assumption",
    "theoretical_model_based": "theoretical_assumption", "simulation_based_argument": "theoretical_assumption",
    # → methodological_design
    "methodological_design": None, "algorithmic_complexity": "methodological_design",
    "platform_specification": "methodological_design", "architecture_design": "methodological_design",
    "engineering_tradeoff": "methodological_design", "benchmark_comparison": "methodological_design",
    "design_argument": "methodological_design", "specification_compliance": "methodological_design",
}

VERIFY_CONSENSUS_MAP = {
    "established": None, "emerging": None, "fringe": None,
    "high": "established", "consensus": "established", "corroborating": "established",
    "consistent_with_literature": "established", "strong": "established",
    "single_study": "emerging", "moderate": "emerging", "preliminary": "emerging",
    "partial": "emerging", "mixed": "emerging", "isolated": "emerging",
    "low": "fringe", "controversial": "fringe", "contradicted": "fringe",
}

VERIFY_STATUS_MAP = {  # claim 层误用/近义词
    "verified": "supported", "partially_verified": "partial",
    "pending": "no_evidence", "unverified": "no_evidence",
    "supported": None, "partial": None, "contradicted": None, "no_evidence": None,
}

ORIGIN_MAP = {"paper": "extracted", "papers": "extracted", "author": None,
              "extracted": None, "normalized": None, "synthesized": None}
VERIFY_STRENGTH_MAP = {"high": "strong", "very_strong": "strong", "good": "moderate",
                       "medium": "moderate", "low": "weak", "very_weak": "weak",
                       "strong": None, "moderate": None, "weak": None, "inconclusive": None}

CLAIM_TYPE_MAP = {
    "methodological_result": "methodological", "methodological_claim": "methodological",
    "methodology": "methodological", "methodological": None,
    "empirical": "empirical_result", "empirical_observation": "empirical_result",
    "theoretical": "theoretical_interpretation", "critical_distinction": "theoretical_interpretation",
    "application_proposal": "methodological", "meta_analytic": None,
    "empirical_result": None, "empirical_generalization": None, "theoretical_interpretation": None,
}

EFFECT_SIZE_MAP = {  # 独立表(2026-08-25 修 P1-5:stat 表的 R2 在 effect 枚举里不存在)
    "r2": "R_squared", "r_squared": None, "R_squared": None, "rp2": "R_squared",
    "eta2": "eta_squared", "eta_squared": None, "partial_eta2": "partial_eta_squared",
    "partial_eta_squared": None, "cohens_d": "cohen_d", "cohen_d": None,
    "hedges_g": None, "cramers_v": None, "bayes_factor": None,
    "r": None, "rho": None, "beta": None, "or": "OR", "rr": "RR", "phi": None, "na": None,
}

STAT_TYPE_MAP = {
    "pearson_correlation": "r", "correlation": "r", "pearson_r": "r",
    "r_squared": "R2", "rp2": "R2", "r2": "R2",
    "f_statistic": "F", "t_statistic": "t", "chi_square": "chi2",
    "cohens_d": "d", "z_score": "z", "p_value": "na", "n/a": "na", "none": "na",
    "rmse": "na", "accuracy": "na", "f1_score": "na", "auc": "na",
}

CONFIDENCE_MAP = {"moderate": "medium", "med": "medium", "high": None, "medium": None, "low": None,
                  "very_high": "high", "very_low": "low", "0.9": "high", "0.95": "high", "0.8": "high"}

RELATION_MAP = {"directly_supports": "direct", "primary_support": "direct",
                "quantitatively_supports": "direct", "support_via_heterogeneity_robustness": "indirect",
                "contextualizes": "partial", "primary_source": "direct",
                "elaborates": "indirect", "corroborating": "direct", "supports": "direct",
                "direct": None, "indirect": None, "partial": None}

EV_VERIFY_STATUS_MAP = {"pending": "unverified", "verified": None, "unverified": None, "flagged": None}

TEST_METHOD_KEYWORD = [  # (关键词, 候选)
    ("paired_t", "t_test_paired"), ("t_test", "t_test_independent"), ("t-test", "t_test_independent"),
    ("anova_glm", "anova_multi_factor"), ("rm_anova", "anova_rm"), ("repeated", "anova_rm"),
    ("anova", "anova_one_way"), ("linear_regression", "regression_linear"),
    ("logistic", "regression_logistic"), ("multiple_regression", "regression_multiple"),
    ("pearson", "correlation_pearson"), ("spearman", "correlation_spearman"),
    ("kendall", "correlation_kendall"), ("mann", "mann_whitney"), ("wilcoxon", "wilcoxon"),
    ("kruskal", "kruskal_wallis"), ("friedman", "friedman"), ("permutation", "permutation_test"),
    ("spin", "spin_test"), ("lmm", "mixed_effects_lmm"), ("mixed_effect", "mixed_effects_lmm"),
    ("bayes", "bayesian_hierarchical"), ("nested_cv", "nested_cv"), ("loso", "loso"), ("louo", "louo"),
]


def _audit(fm, field, old, new):
    """enum 改写留痕(P1-6):记入 frontmatter `_cleanup_log` 数组,可审计可回溯。"""
    log = fm.setdefault("_cleanup_log", [])
    log.append(f"{field}: {old} → {new}")


def canon(s):
    return str(s).strip().strip('"\'').lower()


def map_enum(value, table, fallback):
    v = canon(value)
    if v in table:
        return table[v]  # None = 已合法
    return fallback


def map_test_method(value, valid):
    v = canon(value)
    if v in valid:
        return v if str(value) != v else None   # 大小写不符也回写规范形式(P1-7)
    for kw, cand in TEST_METHOD_KEYWORD:
        if kw in v and cand in valid:
            return cand
    # 方法学/架构/软件/综述类 → methodology;其余定性 → descriptive
    if any(k in v for k in ("architect", "design", "platform", "framework", "ontology",
                            "software", "survey", "review", "complexity", "specificat",
                            "benchmark", "simulation_protocol", "pipeline", "implementation",
                            "ablation", "convergent", "cross_valid", "descriptive_stat")):
        return "methodology"
    return "descriptive"


def map_stat_type(value, valid):
    v = canon(value)
    if v in valid:
        return None
    if v in STAT_TYPE_MAP:
        return STAT_TYPE_MAP[v]
    return "na"


def clean_number_field(fm, field):
    v0 = fm.get(field)
    if isinstance(v0, str) and v0.strip().lower() in ("n/a", "na", "none", "-"):
        fm[field] = None
        return True
    """多值/带单位字符串 → null + 原值挪 verify_note。纯数字字符串 → float。"""
    v = fm.get(field)
    if v is None or isinstance(v, (int, float)):
        return False
    s = str(v).strip()
    try:
        fm[field] = float(s) if "." in s else int(s)
        return True
    except ValueError:
        pass
    note = str(fm.get("verify_note") or "").strip()
    extra = f"[{field} 原值: {s}]"
    fm["verify_note"] = (note + "; " + extra) if note else extra
    fm[field] = None
    return True


def _norm_dates(fm):
    """yaml 把无引号日期解析成 date 对象 → 转 isoformat 字符串(54 个假 schema 错)。"""
    import datetime
    for k, v in fm.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            fm[k] = v.isoformat()


def _norm_arrays(fm):
    """confidences/relations 数组内的别名归一(L-008)。"""
    for k in list(fm.keys()):
        if not isinstance(fm[k], list):
            continue
        if k.endswith("_confidences"):
            # 2026-08-25 修乒乓 bug:映射表合法值为 None 表示"不变",dict.get 会把 None
            # 当结果返回导致 [medium]→[null]→[medium] 死循环;显式三分支处理
            def _conf(x):
                if x is None or str(x).strip() == "":
                    return "medium"
                v = CONFIDENCE_MAP.get(canon(x))
                if v:
                    return v
                return canon(x) if canon(x) in ("high", "medium", "low") else "medium"
            fm[k] = [_conf(x) for x in fm[k]]
        elif k.endswith("_relations"):
            def _rel(x):
                if x is None or str(x).strip() == "":
                    return "direct"
                v = RELATION_MAP.get(canon(x))
                if v:
                    return v
                return canon(x) if canon(x) in ("direct", "indirect", "partial") else "direct"
            fm[k] = [_rel(x) for x in fm[k]]
        elif k.endswith("_targets"):
            # targets 的 None 空槽 → 空字符串占位(后续渲染过滤)
            fm[k] = [("" if x is None else str(x)) for x in fm[k]]


def process(files, kind, claim_valid, ev_valid):
    changed = 0
    for f in files:
        p = Path(f)
        content = p.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?([\s\S]*)$", content, re.DOTALL)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            print(f"⚠️  YAML 解析失败跳过: {f}")
            continue
        if not isinstance(fm, dict):
            continue
        orig_yaml = m.group(1)
        orig = dict(fm)

        _norm_dates(fm)
        _norm_arrays(fm)
        # schema_version 历史四种混用 → 统一
        if fm.get("schema_version") != "plan_final_v1":
            fm["schema_version"] = "plan_final_v1"
        if kind == "evidence" and "verify_status" in fm:
            v = canon(fm["verify_status"])
            if v not in ("verified", "unverified", "flagged"):
                fm["verify_status"] = EV_VERIFY_STATUS_MAP.get(v, "unverified")

        if kind == "claim":
            if "reasoning_type" in fm:
                nv = map_enum(fm["reasoning_type"], REASONING_TYPE_MAP, "methodological_design")
                if nv:
                    fm["reasoning_type"] = nv
            if "verify_consensus" in fm:
                nv = map_enum(fm["verify_consensus"], VERIFY_CONSENSUS_MAP, "emerging")
                if nv:
                    fm["verify_consensus"] = nv
            if "origin" in fm:
                v = canon(fm["origin"])
                if v not in ("extracted", "author", "normalized", "synthesized"):
                    fm["origin"] = ORIGIN_MAP.get(v, "extracted")
            if "verify_strength" in fm:
                v = canon(fm["verify_strength"])
                if v not in ("strong", "moderate", "weak", "inconclusive"):
                    fm["verify_strength"] = VERIFY_STRENGTH_MAP.get(v, "moderate")
            if "claim_type" in fm:
                v = canon(fm["claim_type"])
                if v not in ("empirical_result", "empirical_generalization",
                             "theoretical_interpretation", "methodological", "meta_analytic"):
                    fm["claim_type"] = CLAIM_TYPE_MAP.get(v, "methodological")
            if "verify_status" in fm:
                nv = map_enum(fm["verify_status"], VERIFY_STATUS_MAP, None)
                if nv:
                    fm["verify_status"] = nv
            else:
                fm["verify_status"] = "supported" if (fm.get("evidence_targets") or []) else "no_evidence"
        else:
            if "verify_test_method" in fm:
                old = fm["verify_test_method"]
                nv = map_test_method(old, ev_valid["test_method"])
                if nv:
                    _audit(fm, "verify_test_method", old, nv)
                    fm["verify_test_method"] = nv
            if "verify_test_stat_type" in fm:
                old = fm["verify_test_stat_type"]
                nv = map_stat_type(old, ev_valid["stat_type"]) if old is not None else "na"
                if nv:
                    _audit(fm, "verify_test_stat_type", old, nv)
                    fm["verify_test_stat_type"] = nv
            if "verify_p_method" in fm:
                old = fm["verify_p_method"]
                v = canon(old)
                if v in ev_valid["p_method"]:
                    if str(old) != v:
                        _audit(fm, "verify_p_method", old, v)
                        fm["verify_p_method"] = v
                else:
                    nv = ("uncorrected" if "uncorrect" in v else
                          "fdr_bh" if "fdr" in v else
                          "bonferroni" if "bonferroni" in v else
                          "cluster_based" if ("cluster" in v or "tfce" in v) else
                          "fwe" if ("fwe" in v or "maxt" in v) else
                          "holm_bonferroni" if "holm" in v else "na")
                    _audit(fm, "verify_p_method", old, nv)
                    fm["verify_p_method"] = nv
            if "verify_effect_size_type" in fm:
                old = fm["verify_effect_size_type"]
                v = canon(old)
                if v in ev_valid["effect_size"]:
                    if str(old) != v:
                        _audit(fm, "verify_effect_size_type", old, v)
                        fm["verify_effect_size_type"] = v
                else:
                    nv = EFFECT_SIZE_MAP.get(v, "na")
                    _audit(fm, "verify_effect_size_type", old, nv)
                    fm["verify_effect_size_type"] = nv
            for fld in ("verify_test_stat_value", "verify_effect_size_value",
                        "verify_p_value", "verify_n", "verify_df", "verify_ci_95", "prov_page"):
                clean_number_field(fm, fld)
            if fm.get("prov_paper") is None and fm.get("source"):
                fm["prov_paper"] = fm["source"]

        if fm != orig:
            p.write_text(wc.dump_frontmatter_safe(fm, m.group(2).lstrip("\n")), encoding="utf-8")
            changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["pending", "formal"], default="pending")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ev_schema = _registry.load_schema("evidence")["$defs"]
    ev_valid = {
        "test_method": set(ev_schema["test_method_enum"]["enum"]),
        "stat_type": set(ev_schema["test_stat_type_enum"]["enum"]),
        "p_method": set(ev_schema["p_method_enum"]["enum"]),
        "effect_size": set(ev_schema["effect_size_type_enum"]["enum"]),
    }
    claim_schema = _registry.load_schema("claim")
    claim_valid = set()

    if args.scope == "pending":
        claim_files = glob.glob("00-pending/*/claims/*.md")
        ev_files = glob.glob("00-pending/*/evidence/*.md")
    else:
        claim_files = glob.glob("claims/*.md")
        ev_files = glob.glob("evidence/*.md")

    c1 = process(claim_files, "claim", claim_valid, ev_valid)
    c2 = process(ev_files, "evidence", claim_valid, ev_valid)
    print(f"清洗完成: claims {c1}/{len(claim_files)}, evidence {c2}/{len(ev_files)}"
          + ("(dry-run 未写)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
