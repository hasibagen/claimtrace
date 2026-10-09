"""批次2 测试 — 渲染器幂等性 + 关键函数行为。

Portable edition: runs against the repo's `demo/` vault instead of a live
research vault, so `pytest scripts/tests` passes anywhere (CI included).
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # scripts/tests → repo root
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "schemas"))
import wiki_render_nodes as wrn  # noqa: E402

WIKI_ROOT = REPO / "demo"


def _hashes() -> dict[str, str]:
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for d in ("evidence", "claims", "papers")
            for f in (WIKI_ROOT / d).glob("*.md")}


def _run(kind: str, target: str) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPTS / "wiki_render_nodes.py"), kind,
         str(WIKI_ROOT / target), "--wiki-root", str(WIKI_ROOT)],
        capture_output=True, cwd=str(REPO))


def test_evidence_render_idempotent():
    _run("evidence", "evidence")
    sums = _hashes()
    _run("evidence", "evidence")
    new = _hashes()
    changed = sum(1 for f, s in sums.items() if new[f] != s)
    assert changed == 0, f"evidence 非幂等: {changed} 文件在多轮渲染后改变"


def test_claim_render_idempotent():
    _run("claim", "claims")
    sums = _hashes()
    _run("claim", "claims")
    new = _hashes()
    changed = sum(1 for f, s in sums.items() if new[f] != s)
    assert changed == 0, f"claim 非幂等: {changed} 文件在多轮渲染后改变"


def test_paper_render_idempotent():
    _run("paper", "papers")
    sums = _hashes()
    _run("paper", "papers")
    new = _hashes()
    changed = sum(1 for f, s in sums.items() if new[f] != s)
    assert changed == 0, f"paper 非幂等: {changed} 文件在多轮渲染后改变"


def test_index_generated():
    _run("index", "")
    p = WIKI_ROOT / "index.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "AUTO-RENDERED" in text
    assert "## Papers" in text and "## Topics" in text
    m = re.search(r"claims: (\d+)", text)
    assert m and int(m.group(1)) > 0  # demo vault has claims; live vaults have more


def test_backlinks_excludes_self():
    rev = wrn.build_reverse_index(WIKI_ROOT, skip_body_scan=set())
    # an evidence node never appears among its own backlink sources
    assert "dias-2023-null-rested-wm" not in rev.get("dias-2023-null-rested-wm", set())


def test_wikilink_name_strips_prefix():
    assert wrn._wikilink_name("[[papers/cakan_2023_neurolib]]") == "cakan_2023_neurolib"
    assert wrn._wikilink_name("[[cakan_2023|x]]") == "cakan_2023"
    assert wrn._wikilink_name(["[papers/y]"]) == "y"
