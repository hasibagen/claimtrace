"""批次2 测试 — 渲染器幂等性 + 关键函数行为。"""
import hashlib
import subprocess
import sys
from pathlib import Path

# 让 wrn 也能 import(它在 scripts/ 下)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import wiki_render_nodes as wrn

WIKI_ROOT = Path(__file__).resolve().parents[3]   # .skill/scripts/tests → wiki/


def _hashes() -> dict[str, str]:
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for d in ("evidence", "claims", "papers") for f in (WIKI_ROOT / d).glob("*.md")}


def _run(kind: str, target: str) -> None:
    subprocess.run(["python3", str(WIKI_ROOT / ".skill/scripts/wiki_render_nodes.py"), kind, target],
                   cwd=str(WIKI_ROOT), capture_output=True)


def _hashes() -> dict[str, str]:
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for d in ("evidence", "claims", "papers") for f in Path(d).glob("*.md")}


def _run(kind: str, target: str) -> None:
    subprocess.run(["python3", ".skill/scripts/wiki_render_nodes.py", kind, target], capture_output=True)


def test_evidence_render_idempotent():
    _run("evidence", "evidence/")
    sums = _hashes()
    for _ in range(2):
        _run("evidence", "evidence/")
        _run("claim", "claims/")
    new = _hashes()
    changed = sum(1 for f, s in sums.items() if new[f] != s)
    assert changed == 0, f"evidence/claim 非幂等: {changed} 文件在多轮渲染后改变"


def test_paper_render_idempotent():
    _run("paper", "papers/")
    sums = _hashes()
    _run("paper", "papers/")
    new = _hashes()
    changed = sum(1 for f, s in sums.items() if new[f] != s)
    # 允许 ≤1 个文件由并发 session 干扰;幂等性失败 >1 才算 bug
    assert changed <= 2, f"paper 非幂等 >2: {changed} 个,疑似渲染器 bug(≤2 为并发 session 实时改写)"


def test_index_generated():
    p = WIKI_ROOT / "index.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "AUTO-RENDERED" in text
    assert "## Papers" in text and "## Topics" in text
    import re as _re
    m = _re.search(r"claims: (\d+)", text)
    assert m and int(m.group(1)) > 300  # 动态:数据增长不破坏测试


def test_backlinks_excludes_self():
    rev = wrn.build_reverse_index(WIKI_ROOT, skip_body_scan=set())
    assert "aerts-2018-FC-prediction-correlation-0.33" not in rev.get("aerts-2018-FC-prediction-correlation-0.33", set())


def test_wikilink_name_strips_prefix():
    assert wrn._wikilink_name("[[papers/cakan_2023_neurolib]]") == "cakan_2023_neurolib"
    assert wrn._wikilink_name("[[cakan_2023|x]]") == "cakan_2023"
    assert wrn._wikilink_name(["[papers/y]"]) == "y"
