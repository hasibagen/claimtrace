"""
批次1 最小测试集 — 闸门核心逻辑的安全网(ARCHITECTURE §4.6 技术债 #3)。

覆盖:
  1. _registry.check_edge(边规格 + 端点校验)
  2. _registry.validate(claim/evidence schema:必填 + enum)
  3. wiki_check_evidence.verify_in_source(三态 grounding)
  4. wiki_check_evidence.normalize_text(Unicode 归一化)
  5. wiki_lint._citekey_from_wikilink(宽容 citekey 解析)
"""
import _registry
import wiki_check_evidence as wce
import wiki_lint as wl


# ---------- 1. check_edge ----------

def test_check_edge_valid_supports():
    ok, err = _registry.check_edge("supports", {"target": "[[x]]", "confidence": "high", "relation": "direct"})
    assert ok, err


def test_check_edge_invalid_confidence():
    ok, _ = _registry.check_edge("supports", {"target": "[[x]]", "confidence": "very_sure"})
    assert not ok


def test_check_edge_missing_confidence_required():
    ok, _ = _registry.check_edge("supports", {"target": "[[x]]"})
    assert not ok


def test_check_edge_endpoint_mismatch():
    # supports 只允许 evidence/claim → claim;paper 作为 from 违规
    ok, _ = _registry.check_edge("supports", {"target": "[[x]]", "confidence": "high"}, from_kind="paper")
    assert not ok


def test_check_edge_endpoint_ok_evidence():
    ok, err = _registry.check_edge("supports", {"target": "[[x]]", "confidence": "high"}, from_kind="evidence")
    assert ok, err


def test_check_edge_supersedes_removed():
    assert "supersedes" not in _registry.EDGE_TYPE_SPECS
    assert "cites" in _registry.EDGE_TYPE_SPECS


# ---------- 2. schema validate ----------

VALID_CLAIM = {
    "type": "claim", "statement": "这是一个测试主张,长度足够。", "claim_type": "methodological",
    "verify_status": "supported",
}

VALID_EVIDENCE = {
    "type": "evidence", "fact_type": "empirical_result",
    "observation": "x"*20, "interp_origin": "author", "interp_text": "解释文本,长度足够通过 minLength 5",
    "prov_paper": "[[papers/p1]]", "prov_section": "Results", "prov_source_text": "y"*10,
    "verify_n": 30, "verify_test_method": "t_test_paired",
}


def test_validate_claim_ok():
    ok, err = _registry.validate("claim", VALID_CLAIM)
    assert ok, err


def test_validate_claim_bad_enum():
    bad = dict(VALID_CLAIM, claim_type="critical_distinction")
    ok, _ = _registry.validate("claim", bad)
    assert not ok


def test_validate_evidence_na_stat_type():
    ok, err = _registry.validate("evidence", dict(VALID_EVIDENCE, verify_test_stat_type="na"))
    assert ok, err


def test_validate_evidence_bad_p_method():
    bad = dict(VALID_EVIDENCE, verify_p_method="bonferroni-not-applied")
    ok, _ = _registry.validate("evidence", bad)
    assert not ok


# ---------- 3. verify_in_source 三态 ----------

RAW = 'In the study of "visual cortex" activation — the r\u00a0=\u00a00.42 value was reported (p < 0.001, n = 120).'


def test_verify_exact():
    assert wce.verify_in_source("n = 120", RAW) == "exact"


def test_verify_normalized_curly_quotes_and_dashes():
    # 弯引号 + em-dash 变体 → 归一化后命中
    q = "\u201cvisual cortex\u201d activation \u2014 the"
    assert wce.verify_in_source(q, RAW) == "exact"


def test_verify_fuzzy_paraphrase():
    # 词覆盖率 ≥0.75 的改写
    q = "the r = 0.42 value was reported activation"
    assert wce.verify_in_source(q, RAW) == "fuzzy"


def test_verify_none():
    assert wce.verify_in_source("completely unrelated words zzz qq", RAW) == "none"


# ---------- 4. normalize_text ----------

def test_normalize_nfkc_and_punct():
    s = wce.normalize_text("\u201cquote\u201d\u2014dash\u00a0space")
    assert s == '"quote"-dash space'


# ---------- 5. citekey 解析 ----------

def test_citekey_variants():
    assert wl._citekey_from_wikilink("[[papers/cakan_2023]]") == "cakan_2023"
    assert wl._citekey_from_wikilink("cakan_2023") == "cakan_2023"
    assert wl._citekey_from_wikilink(["[papers/aerts_2018]"]) == "aerts_2018"
    assert wl._citekey_from_wikilink("[[papers/x|显示名]]") == "x"
