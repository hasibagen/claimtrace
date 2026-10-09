#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本为 v4 时期 legacy quote 填充工具,针对 CLAIM-NNN 编号节点。
ARCHITECTURE §2.3 已废 CLAIM-NNN,且 observation 字段已升级为扁平化
verify_* 11 字段(T-W4-026)。新功能请用 wiki-build-evidence Skill。
仅供历史回填使用。
原 docstring 保留如下:

finalize_quotes.py — 解决 252 个 CLAIM 的 quote placeholder + 85 个 limitations placeholder

1. CLAIM quote 填充:
   - 读每个 CLAIM 文件
   - 找 [[citekey]] 链接的 paper
   - 读 paper 对应的 full.md (在 wiki/raw/citekey/full.md)
   - 从 claim text 找关键词, 在 full.md 里找相关句子
   - 替换 "> (待具体 quote 抽取)" 为实际 quote

2. limitations 字段填充:
   - 读 paper.md 的 abstract
   - 用最后 1-2 句作 limitations
   - 替换 placeholder
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc


WIKI_ROOT = Path.cwd()
PAPERS = WIKI_ROOT / "papers"
CLAIMS = WIKI_ROOT / "claims"
RAW = WIKI_ROOT / "raw"


# === CLAIM quote 填充 ===

def find_quote_in_fulltext(claim_text: str, full_text: str, max_quotes: int = 3) -> list[str]:
    """从 full_text 找跟 claim_text 相关的句子。"""
    # claim 关键词 (取名词 + 动词)
    claim_keywords = re.findall(r'\b[a-zA-Z]{4,}\b', claim_text.lower())
    # 保留 top 5 关键词
    claim_keywords = list(set(claim_keywords))[:5]
    if not claim_keywords:
        return []

    # 把 full_text 拆成句子
    # 用简单 split (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    scored = []
    for s in sentences:
        s_lower = s.lower()
        score = sum(1 for kw in claim_keywords if kw in s_lower)
        if score > 0 and len(s.strip()) > 40 and len(s.strip()) < 500:
            scored.append((score, s.strip()))

    # 按 score 排序
    scored.sort(key=lambda x: -x[0])

    return [s for _, s in scored[:max_quotes]]


def update_claim_quotes():
    """更新所有 CLAIM 的 quote 字段。"""
    import_re = re.compile(r"-\s*\[\[([^\]]+)\]\][^\n]*\n\s*-\s*>\s*\"?\(待具体 quote 抽取\)\"?")

    updated = 0
    skipped = 0
    for claim_file in CLAIMS.glob("CLAIM-*.md"):
        text = claim_file.read_text(encoding="utf-8")
        if "(待具体 quote 抽取)" not in text:
            skipped += 1
            continue

        # 找 citekey 链接
        m = re.search(r'\[\[([^\]|]+)', text)
        if not m:
            continue
        citekey = m.group(1).strip()
        # 注意: citekey 在 CLAIM 里可能是 citekey 名 (sanz-leon_2015_neuroimage)
        # 或 zk 名 (PL3HTD4P)
        # 找 paper.md
        paper_path = None
        for p in PAPERS.glob("*.md"):
            text_p = p.read_text(encoding="utf-8")
            m_ck = re.search(r'^citekey:\s*"?([^"\n]+)"?', text_p, re.MULTILINE)
            m_zk = re.search(r"^zotero-key:\s*(\S+)", text_p, re.MULTILINE)
            m_zk2 = re.search(r'^zotero_key:\s*"([^"]+)"', text_p, re.MULTILINE)
            m_tt = re.search(r'^title:\s*"([^"]+)"', text_p, re.MULTILINE)
            ck = m_ck.group(1).strip() if m_ck else ""
            zk = m_zk.group(1) if m_zk else (m_zk2.group(1) if m_zk2 else "")
            p_title = (m_tt.group(1).lower() if m_tt else "")
            ck_low = citekey.lower().replace("_", "").replace(" ", "")
            pt_low = p_title.replace("_", "").replace(" ", "")
            match = (citekey == ck or citekey == zk or citekey == p.stem or
                     (pt_low and (ck_low[:30] in pt_low or pt_low[:30] in ck_low)))
            if match:
                paper_path = p
                break

        if not paper_path:
            continue

        # 找 paper 的 full.md
        # 优先: csv-source-path
        text_p = paper_path.read_text(encoding="utf-8")
        m_csv = re.search(r'^csv-source-path:\s*"(.+?)"', text_p, re.MULTILINE)
        full_md_path = None
        if m_csv and Path(m_csv.group(1)).is_file():
            full_md_path = Path(m_csv.group(1))
        else:
            # 试 wiki/raw/<citekey>/full.md 或 <zk>/full.md
            m_ck_p = re.search(r'^citekey:\s*"?([^"\n]+)"?', text_p, re.MULTILINE)
            m_zk_p = re.search(r"^zotero-key:\s*(\S+)", text_p, re.MULTILINE)
            ck_p = m_ck_p.group(1).strip() if m_ck_p else paper_path.stem
            zk_p = m_zk_p.group(1) if m_zk_p else ""
            for c in [ck_p, zk_p, paper_path.stem]:
                p = RAW / c / "full.md"
                if p.is_file():
                    full_md_path = p
                    break

        if not full_md_path:
            continue

        full_text = full_md_path.read_text(encoding="utf-8")

        # 抽 claim text
        m_main = re.search(r'\*\*主张陈述\*\*\n\n(.+?)(?=\n\n)', text, re.DOTALL)
        if not m_main:
            continue
        claim_text = m_main.group(1).strip()

        # 找相关 quote
        quotes = find_quote_in_fulltext(claim_text, full_text, max_quotes=2)
        if not quotes:
            continue

        # 更新 CLAIM 文件的 quote
        new_text = text
        # 用引号包裹每条 quote
        for i, q in enumerate(quotes):
            quoted = f'  - > "{q[:300]}"'
            # 替换第一个 "(待具体 quote 抽取)"
            # 兼容两种 placeholder 格式 (带引号 / 不带引号)
            for ph in ['  - > "(待具体 quote 抽取)"', '  - > (待具体 quote 抽取)']:
                if ph in new_text:
                    new_text = new_text.replace(ph, quoted, 1)
                    break
        claim_file.write_text(new_text, encoding="utf-8")
        updated += 1

    print(f"=== CLAIM quote 更新 ===")
    print(f"  ✓ 更新: {updated}")
    print(f"  ⚠ 跳过 (没 placeholder): {skipped}")


# === limitations 字段填充 ===

def fill_limitations():
    """用 abstract 末句填 limitations 字段。"""
    updated = 0
    for p in PAPERS.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if "(待 LLM 抽取 — 从 Discussion/Conclusion 段)" not in text:
            continue

        # 找 csv-source-path / zk 拿 abstract
        m_csv = re.search(r'^csv-source-path:\s*"(.+?)"', text, re.MULTILINE)
        m_zk = re.search(r"^zotero-key:\s*(\S+)", text, re.MULTILINE)
        abstract = ""

        # 从 zk 查 SQLite
        if m_zk:
            try:
                import sqlite3
                conn = sqlite3.connect(("file:" + str(Path.home() / "Zotero" / "zotero.sqlite") + "?mode=ro"), uri=True)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""SELECT idv.value FROM items i
                             JOIN itemData id ON i.itemID = id.itemID
                             JOIN fields f ON id.fieldID = f.fieldID
                             JOIN itemDataValues idv ON id.valueID = idv.valueID
                             WHERE i.key = ? AND f.fieldName = 'abstractNote'""", (m_zk.group(1),))
                row = c.fetchone()
                if row:
                    abstract = row['value']
                conn.close()
            except Exception:
                pass

        # 用 abstract 最后 2 句
        if abstract:
            sentences = re.split(r'(?<=[.!?])\s+', abstract)
            # 找含 "limitation" "caution" "however" "future" 等的句
            limitation_keywords = [
                "limitation", "caution", "however", "future", "caveat",
                "extending", "while ", "although", "yet ", "remain", "scope",
                "generaliz", "valid", "constrained", "depends on"
            ]
            lim_sentences = []
            for s in sentences:
                s_lower = s.lower()
                if any(kw in s_lower for kw in limitation_keywords):
                    lim_sentences.append(s.strip())
                if len(lim_sentences) >= 2:
                    break
            if lim_sentences:
                new_lim = "limitations:\n  " + "\n  ".join(lim_sentences)
            else:
                # 通用兜底
                new_lim = "limitations:\n  - 基于 abstract 推断, 需 LLM 详细补充"
        else:
            new_lim = "limitations:\n  - 无 abstract, 需 LLM 详细补充"

        # 替换 limitations 段 (兼容 | 或无 |)
        new_text = re.sub(
            r'^limitations:\s*\|?\n?(.*?)(?=\n[a-z\-]+:|\n---|\Z)',
            new_lim,
            text,
            count=1,
            flags=re.MULTILINE | re.DOTALL,
        )
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            updated += 1

    print(f"\n=== limitations 更新 ===")
    print(f"  ✓ 更新: {updated}")
    print(f"  剩余 placeholder: {sum(1 for p in PAPERS.glob('*.md') if '(待 LLM 抽取 — 从 Discussion' in p.read_text(encoding='utf-8'))}")


def main():
    update_claim_quotes()
    fill_limitations()


if __name__ == "__main__":
    main()
