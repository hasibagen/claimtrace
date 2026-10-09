#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本为 v4 时期启发式 L2/L3 填充工具。
新功能请用 wiki-extract-paper Skill(T0-T4 流水线 + LLM 语义抽取)。
仅供历史回填使用。
原 docstring 保留如下:

finalize_extract.py — 最后清理: 把所有 paper.md 的 L2/L3 placeholder 替换成真实内容

策略:
- 读 SQLite (paperinfo 的 metadata: title, publicationTitle, abstractNote, date)
- 基于元数据 + zk 自动生成 L2/L3 字段:
  - research-question: 标题 + abstract
  - hypothesis: 假设/模型
  - sample-size: 摘要里的 n=X
  - study-design: 启发式判断
  - main-findings: 摘要摘要
  - evidence-level: 启发式
- 处理 190 个 papers
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

from pathlib import Path as _P
DB = ("file:" + str(_P.home() / "Zotero" / "zotero.sqlite") + "?mode=ro")
conn = sqlite3.connect(DB, uri=True)
conn.row_factory = sqlite3.Row
c = conn.cursor()


def get_paper_meta(zk: str) -> dict:
    """用 zk 查 SQLite 拿元数据"""
    out = {"title": "", "publication": "", "abstract": "", "date": "", "type": "journalArticle", "doi": ""}
    # title
    c.execute("""SELECT f.fieldName, idv.value FROM items i
                 JOIN itemData id ON i.itemID = id.itemID
                 JOIN fields f ON id.fieldID = f.fieldID
                 JOIN itemDataValues idv ON id.valueID = idv.valueID
                 WHERE i.key = ?""", (zk,))
    for row in c.fetchall():
        f = row['fieldName']
        v = row['value']
        if f == "title": out["title"] = v
        elif f == "publicationTitle": out["publication"] = v
        elif f == "abstractNote": out["abstract"] = v
        elif f == "date": out["date"] = v
        elif f == "DOI": out["doi"] = v
        elif f == "itemType": out["type"] = v
    return out


def extract_abstract_rq(abstract: str) -> str:
    """从 abstract 提研究问题 (找问句)"""
    if not abstract:
        return "(基于论文标题/abstract 推断)"
    # 找问号
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    for s in sentences:
        if "?" in s and len(s.strip()) > 20:
            return s.strip()
    return sentences[0].strip() if sentences else abstract[:200]


def extract_hypothesis(abstract: str) -> str:
    """从 abstract 找 'we propose / hypothesize' 句"""
    if not abstract:
        return "(基于论文推断)"
    for pat in [r"we propose that ([^.]+\.)",
                r"we hypothesize that ([^.]+\.)",
                r"we present ([^.]+\.)",
                r"here we (?:propose|present) ([^.]+\.)"]:
        m = re.search(pat, abstract, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return "(基于 abstract 推断)"


def extract_sample_size(abstract: str) -> str:
    """从 abstract 抽 n=X"""
    if not abstract:
        return "n=?"
    patterns = [
        r"n\s*=\s*(\d+)",
        r"N\s*=\s*(\d+)",
        r"(\d+)\s*patients?",
        r"(\d+)\s*participants?",
        r"(\d+)\s*subjects?",
    ]
    for p in patterns:
        m = re.search(p, abstract, re.IGNORECASE)
        if m:
            return f"n={m.group(1)}"
    return "(无明确样本量)"


def extract_study_design(abstract: str, item_type: str) -> str:
    """从 abstract 判断研究类型"""
    if not abstract:
        abstract = ""
    text_lower = abstract.lower()
    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        return "meta-analysis / systematic review"
    if "randomized controlled" in text_lower or "rct" in text_lower:
        return "RCT (randomized controlled trial)"
    if "case-control" in text_lower:
        return "case-control study"
    if "longitudinal" in text_lower and "cohort" in text_lower:
        return "longitudinal cohort study"
    if "cross-sectional" in text_lower:
        return "cross-sectional study"
    if "case study" in text_lower or "case series" in text_lower:
        return "case study / case series"
    if "modeling" in text_lower or "simulation" in text_lower or "computational" in text_lower:
        return "computational modeling / simulation"
    if "review" in text_lower:
        return "review / methodology"
    if "cohort" in text_lower:
        return "cohort study"
    if "methodology" in text_lower or "framework" in text_lower:
        return "methodology / framework"
    return "empirical study (具体设计待 LLM 详细抽取)"


def extract_main_findings(abstract: str) -> str:
    """从 abstract 抽 main findings"""
    if not abstract:
        return "(基于 abstract 推断)"
    # 限制长度
    if len(abstract) > 1500:
        return abstract[:1500] + "..."
    return abstract


def extract_evidence_level(abstract: str, item_type: str) -> str:
    text_lower = abstract.lower() if abstract else ""
    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        return "strong"
    if "rct" in text_lower or "randomized" in text_lower:
        return "strong"
    if "preprint" in item_type.lower() or "biorxiv" in text_lower:
        return "suggestive"
    if "simulation" in text_lower or "modeling" in text_lower:
        return "suggestive"
    if "case" in text_lower:
        return "weak"
    return "moderate"


def extract_modality(abstract: str, item_type: str) -> str:
    if not abstract:
        return "meta"
    text_lower = abstract.lower()
    if ("fmri" in text_lower or "bold" in text_lower) and "eeg" in text_lower:
        return "multimodal"
    if "fmri" in text_lower or "functional magnetic" in text_lower:
        return "fmri"
    if "eeg" in text_lower and ("meg" in text_lower or "fmri" in text_lower):
        return "multimodal"
    if "eeg" in text_lower:
        return "eeg"
    if "meg" in text_lower:
        return "meg"
    if "fnirs" in text_lower or "nirs" in text_lower:
        return "fnirs"
    if "pet" in text_lower:
        return "pet"
    if "dti" in text_lower or "diffusion tensor" in text_lower:
        return "fmri"
    if "machine learning" in text_lower or "deep learning" in text_lower or "neural network" in text_lower:
        return "ml"
    if "modeling" in text_lower or "simulation" in text_lower:
        return "meta"
    if item_type in ("book", "bookSection", "thesis"):
        return "meta"
    return "meta"


def main():
    papers_dir = Path.cwd() / "papers"
    fixed = 0
    errors = 0

    for p in papers_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if "待 LLM 抽取" not in text:
            continue

        m_zk = re.search(r"^zotero-key:\s*(\S+)", text, re.MULTILINE)
        m_ck = re.search(r'^citekey:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        m_title = re.search(r'^title:\s*"(.+?)"', text, re.MULTILINE)
        if not (m_zk and m_title):
            errors += 1
            continue

        zk = m_zk.group(1)
        title = m_title.group(1)
        ck = m_ck.group(1) if m_ck else p.stem

        # 查 Zotero metadata
        meta = get_paper_meta(zk)
        if not meta["title"]:
            meta["title"] = title
        abstract = meta["abstract"]

        # 抽取
        research_q = extract_abstract_rq(abstract)
        hypothesis = extract_hypothesis(abstract)
        sample_size = extract_sample_size(abstract)
        study_design = extract_study_design(abstract, meta["type"])
        main_findings = extract_main_findings(abstract)
        evidence_level = extract_evidence_level(abstract, meta["type"])
        modality = extract_modality(abstract, meta["type"])

        # 找到所有 "key: |\n  占位符" 段
        lines = text.split("\n")
        new_lines = []
        i = 0
        fields = {
            "modality": [modality, False],
            "research-question": [research_q, True],
            "hypothesis": [hypothesis, True],
            "sample-size": [sample_size, True],
            "study-design": [study_design, True],
            "main-findings": [main_findings, True],
            "limitations": ["(待 LLM 抽取 — 从 Discussion/Conclusion 段)", True],
            "evidence-level": [evidence_level, False],
        }
        while i < len(lines):
            line = lines[i]
            m = re.match(r'^([a-z][a-z\-]*):\s*(.*)$', line)
            if m and not line.startswith(" "):
                key = m.group(1)
                value = m.group(2)
                if key in fields and (value == "|" or value == "|-" or "(待 LLM 抽取" in str(value)):
                    new_value = fields[key][0]
                    multiline = fields[key][1]
                    if multiline and (value == "|" or value == "|-"):
                        new_lines.append(f"{key}: |")
                        for v in new_value.split("\n"):
                            new_lines.append(f"  {v}")
                        i += 1
                        while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                            i += 1
                        continue
                    else:
                        new_lines.append(f"{key}: {new_value}")
                        i += 1
                        continue
            new_lines.append(line)
            i += 1

        p.write_text("\n".join(new_lines), encoding="utf-8")
        fixed += 1

    print(f"=== finalize_extract 结果 ===")
    print(f"  ✓ 修复: {fixed}")
    print(f"  ✗ 错误: {errors}")
    # 验证
    placeholder = sum(1 for p in papers_dir.glob("*.md")
                      if "(待 LLM 抽取 — 从 Abstract" in p.read_text(encoding="utf-8"))
    print(f"  含 placeholder: {placeholder}")


if __name__ == "__main__":
    main()
