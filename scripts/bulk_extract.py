#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本为 v4 时期 legacy 批量抽取,生成 CLAIM-NNN 编号 claim。
ARCHITECTURE §2.3 已废 CLAIM-NNN,新功能请使用 wiki-extract-paper 微 Skill
(T0-T4 流水线 + LLM 语义抽取 + semantic-slug 命名)。
仅供历史回填或一次性 Phase 2 迁移使用。
原 docstring 保留如下:

bulk_extract.py — 批量抽取 L2/L3 + 创建 CLAIM 节点

对 papers/ 里 status: extracted 但 L2/L3 是 placeholder 的论文:
1. 读 raw/<citekey>/full.md
2. 智能抽取 (Abstract / Methods / Results / Conclusion 段)
3. 数值提取 (n=X, p<Y, r=Z)
4. 生成 1-2 CLAIM (从主结论)
5. 创建 claims/CLAIM-XXX.md
6. 更新 paper.md (替换 placeholder)
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc
import wiki_zotero as wz


# 编号游标
CLAIM_COUNTER_START = 34  # CLAIM-001 ~ CLAIM-033 已存在


# === full.md 智能解析 ===

def split_into_sections(text: str) -> dict:
    """按 Markdown 标题 (## / ###) 切分 full.md。"""
    sections = {}
    current_h = "Abstract"
    buf = []
    for line in text.split("\n"):
        if line.startswith("## ") or line.startswith("### "):
            if buf:
                sections[current_h] = "\n".join(buf).strip()
            current_h = line.lstrip("#").strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current_h] = "\n".join(buf).strip()
    return sections


def extract_abstract(text: str) -> str:
    """从 full.md 抽 Abstract 段 (去掉空行)"""
    # 优先找 "## Abstract" 或 "## ABSTRACT"
    m = re.search(r"^## (?:Abstract|ABSTRACT|Abstract\W.*?)\s*\n(.+?)(?=\n## |\Z)",
                  text, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip()
    # fallback: 找第一段 (After title/author)
    lines = text.split("\n")
    in_abstract = False
    buf = []
    for line in lines:
        if "## Abstract" in line or "## ABSTRACT" in line:
            in_abstract = True
            continue
        if in_abstract:
            if line.startswith("## ") and "Abstract" not in line:
                break
            if line.strip():
                buf.append(line)
    return "\n".join(buf).strip()


def extract_sample_size(text: str) -> str:
    """正则提取样本量: n=NN / N=NN / participants: NN 等"""
    patterns = [
        r"[nN]\s*=\s*(\d+)",
        r"(\d+)\s*participants?",
        r"(\d+)\s*patients?",
        r"sample\s*size\s*of\s*(\d+)",
        r"N\s*=\s*(\d+)",
    ]
    matches = set()
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            matches.add(m.group(1))
    if not matches:
        return "(无明确样本量)"
    # 取最大的 (通常是总样本)
    n = max(int(x) for x in matches)
    return f"n={n}"


def extract_study_design(text: str, title: str = "") -> str:
    """从方法学关键词判断研究类型"""
    text_lower = text.lower()
    # 优先级: meta-analysis > RCT > review > empirical
    if any(w in text_lower for w in ["meta-analysis", "systematic review", "scoping review"]):
        return "meta-analysis / systematic review"
    if "randomized controlled trial" in text_lower or "rct" in text_lower or "randomized" in text_lower:
        return "RCT (randomized controlled trial)"
    if "review" in text_lower and ("narrative" in text_lower or "scoping" in text_lower):
        return "narrative / scoping review"
    if "cross-sectional" in text_lower or "cross sectional" in text_lower:
        return "cross-sectional study"
    if "longitudinal" in text_lower and "cohort" in text_lower:
        return "longitudinal cohort study"
    if "case-control" in text_lower or "case control" in text_lower:
        return "case-control study"
    if "case study" in text_lower or "case series" in text_lower:
        return "case study / case series"
    if "modeling" in text_lower or "simulation" in text_lower or "computational" in text_lower:
        return "computational modeling / simulation"
    if "method" in text_lower or "methodology" in text_lower:
        return "methodology / methods paper"
    if "cohort" in text_lower:
        return "cohort study"
    return "empirical study (具体设计待 LLM 详细抽取)"


def extract_main_findings(text: str) -> str:
    """从 Results / Findings 段抽主要发现"""
    sections = split_into_sections(text)
    # 找 Results / Findings / Outcomes 段
    for key in ["Results", "Findings", "Main Findings", "Results and Discussion"]:
        if key in sections:
            content = sections[key]
            # 限制长度
            if len(content) > 2000:
                content = content[:2000] + "..."
            return content
    # fallback: 找 Conclusion 之前的所有内容
    for key in ["Conclusion", "Discussion", "Conclusion and Discussion"]:
        if key in sections:
            idx = text.find(sections[key])
            return text[max(0, idx - 2000):idx].strip()[:2000]
    return "(待 LLM 抽取)"


def extract_limitations(text: str) -> str:
    """从 Discussion 或 Conclusion 找 limitations"""
    for key in ["Limitations", "Discussion", "Conclusion"]:
        sections = split_into_sections(text)
        if key in sections:
            content = sections[key]
            # 找 "limitation" 关键词
            sentences = re.split(r'[.!?]\s+', content)
            for s in sentences:
                if 'limitation' in s.lower() or 'caveat' in s.lower() or 'future work' in s.lower():
                    return s.strip() + "."
    return "(待 LLM 抽取 — 从 Discussion/Conclusion 段)"


def extract_research_question(text: str, title: str) -> str:
    """从 Introduction 找研究问题"""
    sections = split_into_sections(text)
    intro = sections.get("Introduction", "")
    # 找问句
    for line in intro.split("\n")[:50]:
        if "?" in line and len(line) > 20:
            return line.strip()
    return f"基于论文标题 ({title}) 推断的具体研究问题待 LLM 抽取"


def extract_hypothesis(text: str, title: str) -> str:
    """从 Abstract 找 hypothesis / propose"""
    abstract = extract_abstract(text)
    # 找 "we propose" / "we hypothesize" / "hypothesis"
    for pat in [r"we propose that ([^.]+\.)",
                r"we hypothesize that ([^.]+\.)",
                r"hypothesis\s*:?\s*([^.]+\.)",
                r"here we propose ([^.]+\.)"]:
    # Continue from here, rest defined below
                pass
    return "(待 LLM 抽取 — 从 Abstract 找 'we propose / hypothesize')"


def extract_evidence_level(text: str) -> str:
    """从 abstract 推断证据等级"""
    text_lower = text.lower()
    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        return "strong"
    if "rct" in text_lower or "randomized controlled" in text_lower:
        return "strong"
    if "randomized" in text_lower or "double-blind" in text_lower:
        return "moderate"
    if "case study" in text_lower or "case series" in text_lower:
        return "weak"
    if "simulation" in text_lower or "modeling" in text_lower:
        return "suggestive"
    if "preprint" in text_lower or "biorxiv" in text_lower:
        return "suggestive"
    if "review" in text_lower:
        return "moderate"
    return "moderate"


def extract_numerical_results(text: str) -> list:
    """提取关键统计数字"""
    patterns = [
        r"n\s*=\s*(\d+)",
        r"p\s*<\s*(0\.\d+)",
        r"p\s*=\s*(0\.\d+)",
        r"r\s*=\s*(-?\d*\.?\d+)",
        r"F\s*=\s*(\d*\.?\d+)",
        r"t\s*=\s*(-?\d*\.?\d+)",
    ]
    found = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            v = m.group(1)
            if v and v not in [x[1] for x in found]:
                found.append((p.split("\\")[0], v))
            if len(found) >= 10:
                break
    return found


def extract_main_claim(text: str) -> str:
    """从 Abstract 找主要 claim (一句陈述)"""
    abstract = extract_abstract(text)
    # 找 "we [verb] that ..." 句式
    m = re.search(
        r"\b(we|this study|these results|our results?|our findings?)\s+"
        r"(show|demonstrate|suggest|propose|indicate|reveal|find|argue|conclude)\s+"
        r"that\s+([^.]+\.)",
        abstract, re.IGNORECASE
    )
    if m:
        return f"{m.group(0).strip()}"
    # fallback: 找句号 + 30 词以上
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', abstract) if len(s.strip()) > 40]
    if sentences:
        return sentences[0]
    return "(待 LLM 抽取)"


def extract_modality(text: str, it_type: str) -> str:
    """从全文推断 modality"""
    text_lower = text.lower()
    if "fmri" in text_lower or "functional magnetic" in text_lower or "bold" in text_lower:
        if "eeg" in text_lower or "meg" in text_lower or "fnirs" in text_lower:
            return "multimodal"
        return "fmri"
    if "eeg" in text_lower and ("meg" in text_lower or "fmri" in text_lower):
        return "multimodal"
    if "fnirs" in text_lower and ("fmri" in text_lower or "eeg" in text_lower):
        return "multimodal"
    if "eeg" in text_lower:
        return "eeg"
    if "meg" in text_lower:
        return "meg"
    if "fnirs" in text_lower:
        return "fnirs"
    if "pet" in text_lower:
        return "pet"
    if "mri" in text_lower and "connectome" in text_lower:
        return "fmri"
    if "connectome" in text_lower or "brain network" in text_lower or "graph theory" in text_lower:
        return "connectomics"
    if "machine learning" in text_lower or "deep learning" in text_lower or "neural network" in text_lower:
        return "ml"
    if "dti" in text_lower or "diffusion tensor" in text_lower:
        return "fmri"
    if "modeling" in text_lower or "simulation" in text_lower:
        return "meta"
    if it_type in ("review", "review-article"):
        return "meta"
    if it_type in ("preprint",):
        return "meta"
    return "meta"


# === 抽取器 ===

def extract_paper(paper_md: Path) -> dict | None:
    """对单篇 paper.md 做完整抽取 (L2/L3 + CLAIM 列表)."""
    text = paper_md.read_text(encoding="utf-8")
    m_zk = re.search(r"^zotero-key:\s*(\S+)", text, re.MULTILINE)
    m_ck = re.search(r"^citekey:\s*(\S+)", text, re.MULTILINE)
    m_title = re.search(r'^title:\s*"(.+?)"', text, re.MULTILINE)
    m_csv = re.search(r'^csv-source-path:\s*"(.+?)"', text, re.MULTILINE)
    m_need_extract = "(待 LLM 抽取" in text

    if not (m_zk and m_ck and m_title):
        return None

    citekey = m_ck.group(1)
    zk = m_zk.group(1)
    title = m_title.group(1)
    csv_path = m_csv.group(1) if m_csv else ""

    # 读 full.md - 优先级: csv-source-path > wiki/raw/<citekey>/ > wiki/raw/<zotero_key>/
    candidates = []
    if csv_path and Path(csv_path).is_file():
        candidates.append(Path(csv_path))
    candidates.append(Path(f"raw/{citekey}/full.md"))
    candidates.append(Path(f"raw/{zk}/full.md"))

    full_text = None
    for c in candidates:
        if c.is_file():
            full_text = c.read_text(encoding="utf-8")
            csv_path = str(c)
            break

    if full_text is None:
        # 尝试从 zotero_md 自动找
        try:
            import sync_papers
            zotero_md = sync_papers.DEFAULT_ZOTERO_MD
            src = sync_papers.find_zotero_paper_dir_simple(zotero_md, citekey, zk)
            if src:
                full_text = src.joinpath("full.md").read_text(encoding="utf-8")
                csv_path = str(src.joinpath("full.md"))
        except Exception:
            pass

    if full_text is None:
        return None

    # 抽取
    abstract = extract_abstract(full_text)
    research_q = extract_research_question(full_text, title)
    hypothesis = extract_hypothesis(full_text, title)
    sample_size = extract_sample_size(full_text)
    study_design = extract_study_design(full_text, title)
    main_findings = extract_main_findings(full_text)
    limitations = extract_limitations(full_text)
    evidence_level = extract_evidence_level(full_text)
    main_claim = extract_main_claim(full_text)
    num_results = extract_numerical_results(full_text)

    # 推断 modality (需要 zotero itemType)
    try:
        it = wz.get_zotero_local().item(zk)
        it_type = (it.get("data") or {}).get("itemType", "journalArticle")
    except Exception:
        it_type = "journalArticle"
    modality = extract_modality(full_text, it_type)

    # CLAIM 列表 (从 main_claim + 数值提取)
    claims = []
    if main_claim and "待 LLM" not in main_claim:
        claims.append({
            "text": main_claim,
            "support": "main_results",
        })
    # 从 abstract 找附加 claim (找 "we also" / "additionally")
    for s in re.split(r'(?<=[.!?])\s+', abstract):
        if re.search(r"\b(we also|additionally|furthermore|moreover|importantly)\b", s, re.IGNORECASE):
            if len(s.strip()) > 40 and "we propose" not in s and "we hypothesize" not in s:
                claims.append({"text": s.strip(), "support": "additional"})

    # 限制 CLAIM 数量
    claims = claims[:3]

    return {
        "citekey": citekey,
        "zk": zk,
        "title": title,
        "modality": modality,
        "research_question": research_q,
        "hypothesis": hypothesis,
        "sample_size": sample_size,
        "study_design": study_design,
        "main_findings": main_findings,
        "limitations": limitations,
        "evidence_level": evidence_level,
        "main_claim": main_claim,
        "num_results": num_results,
        "claims": claims,
        "csv_path": csv_path,
    }


# === 更新 paper.md ===

def update_paper_md(p: Path, data: dict) -> None:
    """更新 paper.md 的 L2/L3 字段 - 逐行处理避免 regex 复杂性。"""
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 字段映射: key → (value_lines, multiline)
    # multiline=True 表示 key: | 之后是多行值
    fields = {
        "modality": (data.get("modality", "meta"), False),
        "research-question": (data["research_question"], True),
        "hypothesis": (data["hypothesis"], True),
        "sample-size": (data["sample_size"], True),
        "study-design": (data["study_design"], True),
        "main-findings": (data["main_findings"], True),
        "limitations": (data["limitations"], True),
        "evidence-level": (data["evidence_level"], False),
    }

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 找顶层字段 (不以空格开头)
        m = re.match(r'^([a-z][a-z\-]*):\s*(.*)$', line)
        if m and not line.startswith(" "):
            key = m.group(1)
            value = m.group(2)
            if key in fields:
                new_value, multiline = fields[key]
                if multiline and (value == "|" or value == "|-"):
                    # 消耗所有缩进行 (子级)
                    new_lines.append(f"{key}: |")
                    for v in new_value.split("\n"):
                        new_lines.append(f"  {v}")
                    i += 1
                    # 跳过多行值 (缩进行)
                    while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                        i += 1
                    continue
                else:
                    new_lines.append(f"{key}: {new_value}")
                    i += 1
                    continue
        new_lines.append(line)
        i += 1

    # CLAIM 列表
    if data.get("claims"):
        claim_names = []
        for i_c, c in enumerate(data["claims"], 1):
            ck = f"CLAIM-{CLAIM_COUNTER_START + data.get('claim_offset', 0) + i_c - 1:03d}_{slug_from_text(c['text'])}"
            claim_names.append(f'"[[{ck}]]"')
        claim_block = "claims:\n  - " + "\n  - ".join(claim_names)

        # 替换 claims: 行
        new_lines2 = []
        i = 0
        while i < len(new_lines):
            if new_lines[i].startswith("claims:"):
                new_lines2.append(claim_block)
                i += 1
            else:
                new_lines2.append(new_lines[i])
                i += 1
        new_lines = new_lines2

    p.write_text("\n".join(new_lines), encoding="utf-8")


def slug_from_text(text: str, max_len: int = 40) -> str:
    """从 claim text 抽出 slug"""
    words = re.findall(r'\b[a-zA-Z]+\b', text)[:5]
    s = "_".join(words).lower()[:max_len]
    return s.rstrip("_") or "claim"


# === 主函数 ===

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wiki-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    wiki = args.wiki_root
    papers_dir = wiki / "papers"
    claims_dir = wiki / "claims"

    if not papers_dir.is_dir():
        wc.die(f"找不到 {papers_dir}")

    # 找所有 status: extracted 但 L2/L3 是占位符的 paper
    candidates = []
    for p in papers_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if "status: extracted" in text and "(待 LLM 抽取" in text:
            candidates.append(p)

    print(f"=== 待抽取 paper.md ===")
    print(f"  候选: {len(candidates)}")

    if args.limit:
        candidates = candidates[:args.limit]
        print(f"  限制: {args.limit}")

    extracted = 0
    errors = 0
    # 找当前已用的最大 CLAIM 编号
    claim_counter = CLAIM_COUNTER_START
    if claims_dir.is_dir():
        import re as re2
        existing = []
        for cf in claims_dir.glob("CLAIM-*.md"):
            m = re2.match(r'CLAIM-(\d+)_', cf.name)
            if m:
                existing.append(int(m.group(1)))
        if existing:
            claim_counter = max(existing) + 1

    print(f"  Starting CLAIM counter: CLAIM-{claim_counter:03d}")

    for i, p in enumerate(candidates, 1):
        try:
            data = extract_paper(p)
            if data is None:
                errors += 1
                continue

            data["claim_offset"] = claim_counter - CLAIM_COUNTER_START

            if not args.dry_run:
                update_paper_md(p, data)

                # 创建 CLAIM 节点文件
                for j, c in enumerate(data["claims"], 1):
                    claim_num = claim_counter + j - 1
                    slug = slug_from_text(c["text"])
                    claim_filename = f"CLAIM-{claim_num:03d}_{slug}.md"
                    claim_path = claims_dir / claim_filename
                    if claim_path.exists():
                        # 避免重号 - 加 -v2 后缀
                        v = 2
                        while (claims_dir / claim_filename.replace(f"CLAIM-{claim_num:03d}_", f"CLAIM-{claim_num+1000:03d}_")).exists():
                            v += 1
                        # 简单方法: 用 v2 后缀
                        if not (claims_dir / f"CLAIM-{claim_num:03d}_{slug}-v{v}.md").exists():
                            claim_filename = f"CLAIM-{claim_num:03d}_{slug}-v{v}.md"
                            claim_path = claims_dir / claim_filename
                    if not claim_path.exists():
                        # 写 CLAIM 节点
                        claim_md = f"""# CLAIM-{claim_num:03d}: {c['text'][:60]}{'...' if len(c['text']) > 60 else ''}

**主张陈述**

{c['text']}

**首次出现**

- [[{data['citekey']}]]

**支持证据**

- [[{data['citekey']}]] (main {c['support']})
  - > (待具体 quote 抽取)

**反对证据**

（暂无已识别）

**限定条件**

{('基于样本: ' + data['sample_size']) if data['sample_size'] else '(待 LLM 抽取)'}

**证据强度**

- DIRECT 实验证据: 1 篇 ({data['citekey']})
- **综合**: {data['evidence_level']}

**引用此主张的页面**

- [[{data['citekey']}]] (首次提出)
- (其他相关反向链接, 由后续维护自动填充)
"""
                        claim_path.write_text(claim_md, encoding="utf-8")

                claim_counter += len(data["claims"])

            extracted += 1
            if i % 10 == 0:
                print(f"  进度: {i}/{len(candidates)} (extracted: {extracted}, claims: {claim_counter - CLAIM_COUNTER_START})")

        except Exception as e:
            errors += 1
            print(f"  ✗ {p.name}: {e}", file=__import__('sys').stderr)

    print(f"\n=== 结果 ===")
    print(f"  ✓ 抽取: {extracted}")
    print(f"  ✗ 错误: {errors}")
    print(f"  CLAIM 创建: {claim_counter - CLAIM_COUNTER_START} (CLAIM-{CLAIM_COUNTER_START:03d} ~ CLAIM-{claim_counter-1:03d})")
    if args.dry_run:
        print(f"  (DRY-RUN)")


if __name__ == "__main__":
    main()
