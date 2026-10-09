#!/usr/bin/env python3
"""
wiki_normalize_terms.py — 术语规范常驻关卡(2026-08-26)

目的:终结"每批新 paper 落库后再手动批量修术语"的循环。
三件套之一(另两处挂钩):
  - wiki_lint.py    → L0.7 术语层(本脚本 check)
  - wiki_promote.py → 闸门④(00-pending 含违规术语不许 promote)
  - 本脚本 --fix     → 幂等修复

规则表 = wiki_unify_terms.py(2026-08-26 批次)沉淀,显式可审计(铁律 #4 推论:
regex 只做大小写/写法归一,不抽取语义)。E-J(eeg/fmri/bold/tdcs/rtms/tacs)
等用户点头后才把 enabled 改 True。

用法:
  python3 wiki_normalize_terms.py                # check:列出违规(退出码 1)
  python3 wiki_normalize_terms.py --fix          # 修复已启用规则(幂等)
  python3 wiki_normalize_terms.py --fix-links    # wikilink slug 大小写对齐真实文件名
  python3 wiki_normalize_terms.py --pending-only # 只查 00-pending(promote 前用)

原则:
  - 不碰 raw/(铁律 #1)
  - 不改文件名(slug 是 wikilink key;大小写错 slug 用 --fix-links 对齐磁盘真名)
  - URL / 行内代码 / wikilink 目标路径段不做大小写替换
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 规则表(顺序敏感:长模式优先)
# enabled=False 的规则 check 时以 [未启用] 提示,--fix 跳过
# ============================================================
RULES: list[dict] = [
    # --- C1: EEG-fNIRS 写法归一(先于 fnirs 大小写跑) ---
    {"id": "C1", "re": re.compile(r"\bfNIRS\s*[-–—]\s*EEG\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\bfNIRS\s+EEG\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\bEEG\s+fNIRS\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\bEEG\s*[-–—]\s*fNIRS\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\b(?:FNIRS|fnirs|Fnirs|fNIRS)[\s–—-][Ee][Ee][Gg]\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\b[Ee][Ee][Gg][\s–—-](?:FNIRS|fnirs|Fnirs|fNIRS)\b"), "to": "EEG-fNIRS", "enabled": True},
    {"id": "C1", "re": re.compile(r"\beeg\s+fnirs\b", re.IGNORECASE), "to": "EEG-fNIRS", "enabled": True},
    # --- A: fnirs 大小写(前后均排除连字符复合词:slug 自引用如 fnirs-GLM / motor-fnirs;
    #     代价是 fnirs-based 这类复合词不修,宁漏勿错) ---
    {"id": "A", "re": re.compile(r"(?<![\w-])(fnirs|FNIRS|Fnirs|FNirs|FNiRS)(?![\w-])"), "to": "fNIRS", "enabled": True},
    # --- D4: VBTs 复数归一 ---
    {"id": "D4", "re": re.compile(r"\bVBTs\b"), "to": "VBT", "enabled": True},
    # --- E-J: 纯大小写(用户点头后把 enabled 改 True;同样排除 slug 连字符词) ---
    {"id": "E", "re": re.compile(r"(?<![\w-])eeg\b"), "to": "EEG", "enabled": False},
    {"id": "F", "re": re.compile(r"(?<![\w-])fmri\b"), "to": "fMRI", "enabled": False},
    {"id": "G", "re": re.compile(r"(?<![\w-])bold\b"), "to": "BOLD", "enabled": False},
    {"id": "H", "re": re.compile(r"(?<![\w-])tdcs\b"), "to": "tDCS", "enabled": False},
    {"id": "I", "re": re.compile(r"(?<![\w-])rtms\b"), "to": "rTMS", "enabled": False},
    {"id": "J", "re": re.compile(r"(?<![\w-])tacs\b"), "to": "tACS", "enabled": False},
]

WIKI_DIRS = ["papers", "claims", "evidence", "topics", "syntheses", "00-pending"]
URL_RE = re.compile(r"https?://\S+|\[[^\]]*\]\(\S*?\)|`[^`]*`")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(#[^\]|]*)?(?:\|[^\]]*)?\]\]")


# frontmatter 中由 schema enum 约束的字段:其值受契约管控(如 modality: fnirs 是
# 合法 enum,而术语规则 A 会把它"纠正"为 fNIRS,造成 S7 promote 闸门冲突,
# 2026-09-02 homae 会话实撞)。这些字段的值一律不做术语替换。
ENUM_FM_KEYS = frozenset([
    "modality", "study_type", "claim_type", "fact_type", "verify_status",
    "verify_test_method", "verify_p_method", "verify_effect_size_type",
    "verify_test_stat_type", "strength", "interp_origin", "reasoning_type",
    "claim_origin", "origin", "extraction_mode", "verify_confidence",
    "verify_consensus", "verify_evidence_quality", "language", "attribution",
    "sources_relations", "supports_relations", "contradicts_relations",
    "qualifies_relations", "evidence_relations", "premises_relations",
    "sources_confidences", "supports_confidences", "contradicts_confidences",
    "qualifies_confidences", "evidence_confidences", "study_design",
])
_ENUM_LINE_RE = re.compile(
    r"^(" + "|".join(sorted(ENUM_FM_KEYS)) + r"):(\s*)(.+)$", re.M)


def _protected_spans(text: str) -> list[tuple[int, int]]:
    """URL / 行内代码 / wikilink 目标段 / fm 枚举字段值 的 (start, end) 列表——不做替换。"""
    spans: list[tuple[int, int]] = []
    for m in URL_RE.finditer(text):
        spans.append(m.span())
    for m in WIKILINK_RE.finditer(text):
        spans.append(m.span(1))  # 只保护目标段,锚点/别名文本仍可修
    # fm 枚举字段值:仅在前两个 '---' 定界之间生效
    fm_end = text.find("\n---", 3)
    if text.startswith("---") and fm_end > 0:
        head = text[:fm_end]
        off = fm_end - len(head)
        for m in _ENUM_LINE_RE.finditer(head):
            spans.append((m.start(3), m.end(3)))
    return spans


def _split_segments(text: str) -> list[tuple[bool, str]]:
    """切成 [(is_protected, chunk), ...];替换只作用于非保护段,边界恒定。"""
    spans = _protected_spans(text)
    segs, pos = [], 0
    for s, e in sorted(spans):
        if s > pos:
            segs.append((False, text[pos:s]))
        segs.append((True, text[s:e]))
        pos = e
    if pos < len(text):
        segs.append((False, text[pos:]))
    return segs


def apply_rules(text: str, *, include_disabled: bool = False):
    """返回 (new_text, hits:list[(rule_id, count)])。保护段(URL/代码/wikilink 目标)原样保留。"""
    segs = [[is_prot, chunk] for is_prot, chunk in _split_segments(text)]
    hits: list[tuple[str, int]] = []
    for r in RULES:
        if not r["enabled"] and not include_disabled:
            continue
        count = 0
        for seg in segs:
            if not seg[0]:

                def _repl(m, _to=r["to"]):
                    nonlocal count
                    if m.group(0) != _to:
                        count += 1
                    return _to

                seg[1] = r["re"].sub(_repl, seg[1])
        if count:
            hits.append((r["id"], count))
    return "".join(c for _, c in segs), hits


def iter_md_files(wiki_root: Path, pending_only: bool = False, only_dir: Path | None = None):
    if only_dir is not None:
        yield from sorted(only_dir.rglob("*.md"))
        return
    dirs = ["00-pending"] if pending_only else WIKI_DIRS
    for d in dirs:
        p = wiki_root / d
        if p.is_dir():
            yield from sorted(p.rglob("*.md"))


# 损坏代码链接:`[[X]]`X]]`fNIRS-X]]` … → `[[X]]`(嵌套替换事故残留,机械可修)
# 垃圾段必须由"无反引号且以 ]] 结尾"的片段构成,避免吞掉相邻正常代码 span
MANGLED_CODELINK_RE = re.compile(r"`(\[\[[^\]`\n]+\]\])`(?:[^\]`\n]*\]\])+`")


def fix_mangled(wiki_root: Path) -> int:
    changed = 0
    for f in iter_md_files(wiki_root):
        text = f.read_text(encoding="utf-8")
        # 嵌套多层时逐层收敛到不动点
        for _ in range(5):
            new = MANGLED_CODELINK_RE.sub(r"`\1`", text)
            if new == text:
                break
            text = new
        if text != f.read_text(encoding="utf-8"):
            f.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def check(wiki_root: Path, pending_only=False, only_dir=None) -> list[str]:
    errors = []
    for f in iter_md_files(wiki_root, pending_only, only_dir):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        _, hits = apply_rules(text)
        _, hits_off = apply_rules(text, include_disabled=True)
        off_ids = {rid for rid, _ in hits_off} - {rid for rid, _ in hits}
        rel = f.relative_to(wiki_root)
        for rid, n in hits:
            errors.append(f"L0.7: {rel}: 违反术语规则 {rid} ×{n}(跑 wiki_normalize_terms.py --fix)")
        if off_ids:
            errors.append(f"L0.7[未启用]: {rel}: 存在 E-J 大小写问题 {sorted(off_ids)}(需用户点头后启用)")
    return errors


def fix(wiki_root: Path, pending_only=False, only_dir: Path | None = None):
    changed = 0
    for f in iter_md_files(wiki_root, pending_only):
        text = f.read_text(encoding="utf-8")
        new, hits = apply_rules(text)
        if hits:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def fix_links(wiki_root: Path) -> int:
    """wikilink slug 大小写对齐磁盘真实文件名(解决 fNIRS/fnirs 双 slug 误植)。"""
    # 建 case-insensitive 索引:basename(去 .md) -> 真名(含相对目录)
    index: dict[str, Path] = {}
    for d in WIKI_DIRS:
        p = wiki_root / d
        if not p.is_dir():
            continue
        for f in p.rglob("*.md"):
            index.setdefault(f.name.lower(), f.relative_to(wiki_root))
    changed = 0
    for f in iter_md_files(wiki_root):
        text = f.read_text(encoding="utf-8")
        n_rew = 0

        def _rew(m):
            nonlocal n_rew
            target = m.group(1)
            key = target if target.endswith(".md") else target + ".md"
            real = index.get(key.lower())
            if not real:
                return m.group(0)
            real_posix = real.as_posix()
            # 只修"纯大小写差异",不改链接形式(裸名/带路径/带不带 .md 均保持原样)
            if "/" in target:
                fixed = real_posix if target.endswith(".md") else real_posix[: -len(".md")]
            else:
                fixed = real.name if target.endswith(".md") else real.stem
            if fixed != target:
                n_rew += 1
                return m.group(0).replace(target, fixed, 1)
            return m.group(0)

        new = WIKILINK_RE.sub(_rew, text)
        if n_rew:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def fix_filenames(wiki_root: Path) -> tuple[int, list[str]]:
    """claims/evidence/topics/syntheses/pending 文件名里的旧术语写法归一(N2 类操作):
    改名 + 全库 wikilink 同步;改名后若产生大小写碰撞(同名不同写),报告不自动合并。
    """
    renames: list[tuple[Path, Path]] = []
    for d in ["claims", "evidence", "topics", "syntheses"]:
        p = wiki_root / d
        if not p.is_dir():
            continue
        for f in sorted(p.rglob("*.md")):
            new_stem, hits = apply_rules(f.stem)
            if hits and new_stem != f.stem and "/" not in new_stem:
                renames.append((f, f.with_name(new_stem + ".md")))
    # 00-pending 子目录里的 claims/evidence 同样处理
    for sub in sorted((wiki_root / "00-pending").glob("*/")):
        for d in ["claims", "evidence"]:
            p = sub / d
            if not p.is_dir():
                continue
            for f in sorted(p.rglob("*.md")):
                new_stem, hits = apply_rules(f.stem)
                if hits and new_stem != f.stem and "/" not in new_stem:
                    renames.append((f, f.with_name(new_stem + ".md")))

    collisions: list[str] = []
    done: list[tuple[str, str]] = []
    for old, new in renames:
        if new.exists() and new.resolve() != old.resolve():
            collisions.append(f"{old.relative_to(wiki_root)} ↔ {new.relative_to(wiki_root)}(大小写碰撞,疑似重复文件,走 /dedup 人工合并)")
            continue
        if not new.exists():
            old.rename(new)
            done.append((old.stem, new.stem))
    # 全库 wikilink:旧 stem → 新 stem(保留链接形式)
    if done:
        mapping = {o.lower(): n for o, n in done}
        for f in iter_md_files(wiki_root):
            text = f.read_text(encoding="utf-8")

            def _rw(m):
                target = m.group(1)
                core = target[: -len(".md")] if target.endswith(".md") else target
                fixed = mapping.get(core.lower())
                if not fixed:
                    return m.group(0)
                repl = (fixed + ".md") if target.endswith(".md") else fixed
                return m.group(0).replace(target, repl, 1)

            new_text = WIKILINK_RE.sub(_rw, text)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
    return len(done), collisions


def main() -> int:
    ap = argparse.ArgumentParser(description="术语规范常驻关卡(check/fix)")
    ap.add_argument("--wiki-root", type=Path, default=None)
    ap.add_argument("--fix", action="store_true", help="修复已启用规则")
    ap.add_argument("--fix-links", action="store_true", help="wikilink slug 对齐真实文件名")
    ap.add_argument("--fix-filenames", action="store_true", help="claims/evidence 等文件名术语归一(改名+全库链接同步;碰撞只报告)")
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--dir", type=Path, default=None,
                    help="只检查/修复单个目录(00-pending/<citekey> 或正式区目录);避免全库扫描被个别损坏目录绊倒")
    args = ap.parse_args()
    import wiki_common as wc
    wiki_root = args.wiki_root or wc.find_wiki_root()
    if args.dir and not args.dir.is_absolute():
        args.dir = (wiki_root / args.dir).resolve()

    if args.fix:
        n = fix(wiki_root, args.pending_only, only_dir=args.dir)
        wc.ok(f"fix: {n} 个文件已归一(幂等,可重复跑)")
        n = fix_mangled(wiki_root)
        wc.ok(f"fix-mangled: {n} 个文件损坏代码链接已修复")
    if args.fix_links:
        n = fix_links(wiki_root)
        wc.ok(f"fix-links: {n} 个文件 wikilink 已对齐真名")
    if args.fix_filenames:
        n, collisions = fix_filenames(wiki_root)
        wc.ok(f"fix-filenames: {n} 个文件已改名并同步全库 wikilink")
        for c in collisions:
            wc.eprint(f"  ⚠ 碰撞: {c}")
    if not args.fix and not args.fix_links and not args.fix_filenames:
        errors = check(wiki_root, args.pending_only, only_dir=args.dir)
        hard = [e for e in errors if not e.startswith("L0.7[未启用]")]
        for e in errors:
            wc.eprint(f"  ✗ {e}" if not e.startswith("L0.7[未启用]") else f"  · {e}")
        wc.eprint(f"\n术语检查: {len(hard)} 处违规(硬)/{len(errors)-len(hard)} 处未启用提示")
        return 1 if hard else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
