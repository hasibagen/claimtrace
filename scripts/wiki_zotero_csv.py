#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本为 Phase 1 孪生脑论文 CSV 批量导入工具。
wiki 当前用 wiki_zotero_sync 微 Skill 增量同步(走 Zotero SQLite)。
新批量导入场景请用 wiki-zotero-sync Skill 替代。
原 docstring 保留如下:

wiki_zotero_csv.py — 从 CSV 批量导入 paperinfo + paper.md 骨架

设计:
- 输入: 一个 CSV (含 DOI / title / full.md 路径 等)
- 输出: 缺失的 paperinfo + 全部 paper.md 骨架
- scripts 只做辅助 (匹配 + 写 frontmatter + 骨架 body)
- LLM (pi) 负责填 L2/L3 字段 + claim/evidence

子命令:
  csv-import <csv>  从 CSV 导入强/弱相关论文
  csv-status <csv>  显示 CSV 论文在 wiki 里的覆盖情况
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc
import wiki_zotero as wz


# ──────────────────────────────────────────────────────────────────────
# Topic 映射 (CSV screen_reason → topic slug)
# ──────────────────────────────────────────────────────────────────────

TOPIC_MAP = {
    "数字孪生脑":   "digital-twin-brain",
    "TVB平台":      "virtual-brain-tvb",
    "虚拟脑孪生":    "virtual-brain-twin",
    "神经血管耦合":   "neurovascular-coupling",
    "神经形态孪生":   "neuromorphic-twin",
    "代理脑":       "surrogate-brain",
    "全脑模型":     "whole-brain-model",
    "脑发育/进化":   "brain-development-evolution",
    "脑数字孪生":    "brain-digital-twin",
    "数字孪生+医学":  "digital-twin-medicine",
    "连接组学":      "connectomics",
    "脑模拟":       "brain-simulation",
    "Neurotwins+tDCS": "neuromodulation-twin",
    "个性化脑":     "personalized-brain",
    "数字孪生+脑":   "digital-brain",
    "神经质量/场模型": "neural-mass-field-model",
    "虚拟癫痫患者":   "virtual-epileptic-patient",
    "个性化脑模型":   "personalized-brain-model",
    "经颅刺激建模":   "tms-modeling",
    "全脑":        "whole-brain",
    "神经退行模型":   "neurodegeneration-model",
    "全脑模拟":     "whole-brain-simulation",
    "多尺度脑模型":   "multiscale-brain-model",
    "经颅刺激+AD剂量": "tms-ad-dosing",
    "神经影像+疾病进展": "neuroimaging-disease-progression",
    "个性化脑动力学":  "personalized-brain-dynamics",
    "数字孪生认知":   "digital-twin-cognition",
    "连接组模型":    "connectome-model",
    "脑电+模型":    "eeg-model",
    "fNIRS+脑":  "fnirs-brain",
    "卡尔曼滤波+神经": "kalman-neural",
    "术前规划+肿瘤切除": "presurgical-planning",
}


def screen_reason_to_topic(sr: str) -> str:
    """CSV screen_reason → topic slug. 未在 TOPIC_MAP 里返回 'misc'."""
    return TOPIC_MAP.get(sr, "misc")


# ──────────────────────────────────────────────────────────────────────
# CSV 读 + 筛
# ──────────────────────────────────────────────────────────────────────

def read_csv(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def filter_target(rows: list[dict]) -> list[dict]:
    """筛 category_new in ('强相关', '弱相关')"""
    return [r for r in rows if r.get("category_new") in ("强相关", "弱相关")]


def parse_doi(doi_str: str) -> str:
    """DOI 列可能含 | 分隔多版本, 取第一个非空的"""
    if not doi_str:
        return ""
    for d in doi_str.split("|"):
        d = d.strip()
        if d:
            return d
    return ""


# ──────────────────────────────────────────────────────────────────────
# Zotero 匹配 (按 DOI / title)
# ──────────────────────────────────────────────────────────────────────

class ZoteroIndex:
    """内存索引: DOI -> item, title-prefix -> item, zotero-key -> item"""

    def __init__(self, zot):
        self.zot = zot
        self.by_doi: dict[str, dict] = {}
        self.by_title: dict[str, dict] = {}
        self.by_ck: dict[str, dict] = {}
        self.by_zk: dict[str, dict] = {}
        self._build()

    def _build(self):
        # 用 all_top 拉所有顶层 items
        items = self.zot.all_top()
        for it in items:
            d = it["data"]
            doi = (d.get("DOI") or "").strip().lower()
            if doi:
                self.by_doi[doi] = it
            title = (d.get("title") or "").lower()[:50]
            if title:
                self.by_title.setdefault(title, it)
            ck = (d.get("citationKey") or "").strip()
            if ck:
                self.by_ck[ck] = it
            zk = d.get("key", "")
            if zk:
                self.by_zk[zk] = it

    def find(self, doi: str, title: str) -> dict | None:
        """按 DOI 或 title prefix 匹配"""
        doi_norm = doi.strip().lower() if doi else ""
        if doi_norm and doi_norm in self.by_doi:
            return self.by_doi[doi_norm]
        t = title.strip().lower()[:50] if title else ""
        if t and t in self.by_title:
            return self.by_title[t]
        return None


# ──────────────────────────────────────────────────────────────────────
# paper.md 骨架模板 (LLM 后填 L2/L3)
# ──────────────────────────────────────────────────────────────────────
# Markdown 风格约束 (references/markdown-style.md):
# - YAML 多行字符串块 (|) 内禁止 **bold** → 用 _italic_ 替代
# - 单行章节标题 (##, **) 保留, 单行表格头 (- **field**:) 保留
# - LLM 抽取 L2/L3 字段时, 只输出 _xxx_ 形式强调

PAPER_TEMPLATE = """---
# === 身份 (scripts 维护, 不要手动改) ===
use-case: paper-template
status: pending                # pending / extracted / verified / stale
relevance-score: {relevance_score}
category-new: {category_new}
screen-reason: {screen_reason}
rank-in-csv: {rank_in_csv}

citekey: {citekey}
zotero-key: {zotero_key}
zotero-link: {zotero_link}
zotero-lastmod: {zotero_lastmod}
paperinfo: "[[paperinfo/{citekey}]]"

# === L1 元数据 (从 Zotero / CSV 同步) ===
title: "{title}"
year: {year}
journal: {journal}
doi: {doi}
authors-csv: "{authors_csv}"
csv-source-path: "{md_path}"

# === L2/L3 LLM 抽取 (scripts 不写, 由 LLM 从 full.md 抽取) ===
modality: ""
research-question: ""
hypothesis: ""
sample-size: ""
study-design: ""
main-findings: ""
limitations: ""
evidence-level: ""
analysis-template: ""

# === claim / evidence 反向链接 (LLM 抽取后填) ===
claims: []
evidence: []
---

# {title}

> **状态**: ⏳ pending (待 LLM 从 full.md 抽取 L2/L3 字段)
> **原始素材**: {md_path_link}
> **paperinfo**: [[paperinfo/{citekey}]]

**元信息**

- **作者**: {authors_csv}
- **年份**: {year}
- **期刊**: {journal}
- **DOI**: [{doi}](https://doi.org/{doi})
- **类型**: [待 LLM 抽取]
- **领域**: {screen_reason}
- **相关性**: {category_new} (relevance_score={relevance_score})

**研究目的**

（待 LLM 抽取 — 从 Abstract + Introduction 推断）

**被试**

（待 LLM 抽取）

**实验设计**

（待 LLM 抽取）

**实验范式**

（待 LLM 抽取）

**刺激材料**

（待 LLM 抽取 — 计算建模研究标注"不适用"）

**测量工具**

（待 LLM 抽取）

**数据分析**

（待 LLM 抽取 — 抽取方法细节，对应 templates/paper_*.md 子模板）

**结果**

（待 LLM 抽取 — 原文 quote + section 锚点）

**结论**

（待 LLM 抽取）

**核心主张**

（待 LLM 抽取 — 每个 CLAIM 配 origin paper section）

**证据条目**

（待 LLM 抽取 — 每个 EVIDENCE 配 quote 锚点）

**关联主题**

- [[{screen_reason_topic}]]（如已创建）
- [[topic-xxx]]（其他相关）

**关联主张**

- （LLM 抽取 claim 后加 [[CLAIM-XXX_xxx]]）

**引用本论文的页面**

（反向链接，由后续维护自动填充）
"""


def render_paper_md(n: dict, csv_row: dict) -> str:
    """生成 paper.md 骨架"""
    primary = n["primary_authors"]
    authors_csv = csv_row.get("author", "").strip()
    if authors_csv.startswith('"') and authors_csv.endswith('"'):
        authors_csv = authors_csv[1:-1]

    title = csv_row.get("title", "").strip()
    if title.startswith('"') and title.endswith('"'):
        title = title[1:-1]
    # CSV 的 title 列含双 title: "A|B" 取第一个
    title = title.split("|")[0].strip()

    journal = csv_row.get("journal", "").strip()
    if journal.startswith('"') and journal.endswith('"'):
        journal = journal[1:-1]
    journal = journal.split("|")[0].strip()

    doi = parse_doi(csv_row.get("DOI", ""))
    year = csv_row.get("year", "").strip()

    md_path = csv_row.get("md_path", "").strip()
    md_path_link = f"`{md_path}`" if md_path else "_无 full.md — 待 MinerU 处理_"

    relevance_score = csv_row.get("relevance_score", "").strip()
    category_new = csv_row.get("category_new", "").strip()
    screen_reason = csv_row.get("screen_reason", "").strip()
    rank_in_csv = csv_row.get("rank_in_csv", "").strip()

    # screen_reason -> topic slug
    screen_reason_topic = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', screen_reason).strip('-')

    citekey = n["citation_key"] or ""
    zk = n["indexed_key"] or ""
    zotero_link = f"zotero://select/library/items/{zk}"
    zotero_lastmod = n["date_modified"] or ""

    return PAPER_TEMPLATE.format(
        relevance_score=relevance_score or "?",
        category_new=category_new,
        screen_reason=screen_reason,
        rank_in_csv=rank_in_csv or "?",
        citekey=citekey,
        zotero_key=zk,
        zotero_link=zotero_link,
        zotero_lastmod=zotero_lastmod,
        title=title,
        year=year or "",
        journal=journal or "",
        doi=doi or "",
        authors_csv=authors_csv,
        md_path=md_path,
        md_path_link=md_path_link,
        screen_reason_topic=screen_reason_topic,
    )


# ──────────────────────────────────────────────────────────────────────
# 子命令 1: csv-import
# ──────────────────────────────────────────────────────────────────────

def cmd_csv_import(args, wiki_root: Path) -> int:
    csv_path = Path(args.csv)
    if not csv_path.is_file():
        wc.die(f"找不到 CSV: {csv_path}")

    zot = wz.get_zotero_local()
    pi_dir = wiki_root / "paperinfo"
    papers_dir = wiki_root / "papers"
    pending_dir = wiki_root / "00-pending"
    pi_dir.mkdir(parents=True, exist_ok=True)
    papers_dir.mkdir(parents=True, exist_ok=True)
    pending_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== 读取 CSV: {csv_path} ===")
    rows = read_csv(csv_path)
    target = filter_target(rows)
    print(f"  总行: {len(rows)}, 强/弱相关: {len(target)}")

    print(f"\n=== 构建 Zotero 索引 (DOI / title / citekey) ===")
    zidx = ZoteroIndex(zot)
    print(f"  Zotero items: {len(zidx.by_doi)} DOI + {len(zidx.by_title)} title")

    # 已有的 paperinfo / paper 文件名
    existing_pi = {f.stem for f in pi_dir.glob("*.md")}
    existing_papers = {f.stem for f in papers_dir.glob("*.md")}

    stats = {
        "pi_existed": 0,
        "pi_created": 0,
        "paper_existed": 0,
        "paper_created": 0,
        "no_zotero_match": 0,
        "skipped": 0,
    }

    for i, r in enumerate(target, 1):
        try:
            doi = parse_doi(r.get("DOI", ""))
            title = r.get("title", "")
            title = title.split("|")[0].strip()
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]

            # 找 Zotero item
            item = zidx.find(doi, title)
            if not item:
                stats["no_zotero_match"] += 1
                if args.verbose:
                    wc.eprint(f"  [{i:3d}] ✗ Zotero 未找到: {title[:50]}")
                continue

            # 规范化,渲染 paperinfo
            n = wz.normalize_item(item, zot)
            ck = n["citation_key"] or ""
            if not ck:
                stats["skipped"] += 1
                wc.eprint(f"  [{i:3d}] ✗ 无 BBT citekey: {title[:50]}")
                continue

            pi_filename = wz.safe_filename(ck)
            pi_path = pi_dir / pi_filename

            # 1. 写 paperinfo (若不存在)
            if pi_path.exists():
                stats["pi_existed"] += 1
            else:
                content = wz.render_paperinfo(n)
                if not args.dry_run:
                    pi_path.write_text(content, encoding="utf-8")
                stats["pi_created"] += 1
                if args.verbose:
                    print(f"  [{i:3d}] + paperinfo/{pi_filename}")

            # 2. 写 paper.md (若不存在)
            paper_path = papers_dir / pi_filename
            if paper_path.exists():
                stats["paper_existed"] += 1
            else:
                content = render_paper_md(n, r)
                # 默认放 00-pending/ 让 LLM 审阅后再移 papers/
                target_path = pending_dir / pi_filename
                if not args.dry_run:
                    target_path.write_text(content, encoding="utf-8")
                stats["paper_created"] += 1
                if args.verbose:
                    print(f"  [{i:3d}] + 00-pending/{pi_filename} (paper.md 骨架)")

        except Exception as e:
            wc.eprint(f"  [{i:3d}] ✗ 错误: {e}", file=__import__('sys').stderr)
            stats["skipped"] += 1

    print(f"\n=== 统计 ===")
    print(f"  paperinfo 已存在: {stats['pi_existed']}")
    print(f"  paperinfo 新建:   {stats['pi_created']}")
    print(f"  paper 已存在:    {stats['paper_existed']}")
    print(f"  paper 新建:      {stats['paper_created']}")
    print(f"  Zotero 未匹配:   {stats['no_zotero_match']}")
    print(f"  跳过:           {stats['skipped']}")
    print(f"\n  输出:")
    print(f"    paperinfo/: {pi_dir}")
    print(f"    00-pending/: {pending_dir}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# 子命令 2: csv-status
# ──────────────────────────────────────────────────────────────────────

def cmd_csv_status(args, wiki_root: Path) -> int:
    csv_path = Path(args.csv)
    if not csv_path.is_file():
        wc.die(f"找不到 CSV: {csv_path}")

    rows = read_csv(csv_path)
    target = filter_target(rows)

    pi_dir = wiki_root / "paperinfo"
    papers_dir = wiki_root / "papers"

    # 加载 paperinfo DOI / citekey
    pi_by_doi = {}
    pi_by_ck = {}
    for p in pi_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^DOI:\s*(\S+)", text, re.MULTILINE)
        if m:
            pi_by_doi[m.group(1).strip().lower()] = p
        m = re.search(r"^citekey:\s*(\S+)", text, re.MULTILINE)
        if m:
            pi_by_ck[m.group(1).strip()] = p

    existing_papers = {f.stem for f in papers_dir.glob("*.md")}

    print(f"=== CSV 覆盖状态 ===")
    print(f"  CSV 总行: {len(rows)}")
    print(f"  强/弱相关: {len(target)}")
    print(f"  wiki/paperinfo/: {len(list(pi_dir.glob('*.md')))} 篇")
    print(f"  wiki/papers/: {len(list(papers_dir.glob('*.md')))} 篇")

    has_pi = 0
    no_pi = 0
    no_paper = 0
    examples = []

    for r in target:
        doi = parse_doi(r.get("DOI", "")).lower()
        ck = ""
        # 用 CSV title 找 paperinfo (fallback)
        pi_match = pi_by_doi.get(doi) if doi else None
        if not pi_match:
            title = r.get("title", "")
            # CSV title 可能含 | 分隔多个变体, 取第一个并去末尾句号 + 引号 + 小写
            title = title.split("|")[0].strip().strip('"').rstrip('.').lower()[:50]
            for stem, p in [(f.stem, f) for f in pi_dir.glob("*.md")]:
                t = p.read_text(encoding="utf-8")
                m = re.search(r'^title:\s*"([^"]+)"', t, re.MULTILINE)
                if m and m.group(1).lower().rstrip('.')[:50] == title:
                    pi_match = p
                    m_ck = re.search(r"^citekey:\s*(\S+)", t, re.MULTILINE)
                    if m_ck:
                        ck = m_ck.group(1)
                    break
        else:
            t = pi_match.read_text(encoding="utf-8")
            m_ck = re.search(r"^citekey:\s*(\S+)", t, re.MULTILINE)
            if m_ck:
                ck = m_ck.group(1)

        if pi_match:
            has_pi += 1
            if ck and ck not in existing_papers:
                no_paper += 1
                if len(examples) < 5:
                    examples.append((r["title"][:50], ck))
        else:
            no_pi += 1

    print(f"\n  paperinfo 覆盖: {has_pi}/{len(target)}")
    print(f"  paper 覆盖: {len(target) - no_paper}/{len(target)}")
    print(f"  缺 paperinfo: {no_pi}")
    print(f"  缺 paper.md: {no_paper}")
    if examples:
        print(f"\n  缺 paper.md 示例:")
        for t, ck in examples:
            print(f"    - {t} (paperinfo: {ck})")
    return 0


# ──────────────────────────────────────────────────────────────────────
# Topic 节点生成
# ──────────────────────────────────────────────────────────────────────

TOPIC_TEMPLATE = """# {topic_title}

**主题描述**

{topic_description}

**领域**: {category_new_zh}
**论文数**: {paper_count}

**涉及论文** ({paper_count} 篇):

{papers_list}

**引用本主题的页面**

（反向链接，由后续维护自动填充）
"""


# 主题描述预定义 (按主分类)
TOPIC_DESCRIPTION = {
    "digital-twin-brain": "数字孪生脑（Digital Twin Brain, DTB）是大脑科学在多模态大数据驱动下兴起的**计算建模范式**。构建能够模拟大脑自发活动、病理状态、认知过程的个体化、可计算脑模型。",
    "virtual-brain-tvb": "The Virtual Brain (TVB) 是 Jirsa 团队主导的数字孪生脑平台, 提供多尺度神经动力学建模与个体化仿真能力。",
    "virtual-brain-twin": "虚拟脑孪生（Virtual Brain Twin）面向精准医学, 通过个体化脑模型模拟特定患者/受试者的脑动力学与病理状态。",
    "neurovascular-coupling": "神经血管耦合（Neurovascular Coupling）研究神经活动与脑血流之间的耦合机制, 是 fMRI/BOLD 信号建模的基础。",
    "neuromorphic-twin": "神经形态孪生（Neuromorphic Twin）使用神经形态计算架构模拟脑动力学, 面向类脑计算与个体化建模。",
    "surrogate-brain": "代理脑（Surrogate Brain）作为脑动力学的可计算替代物, 用于研究扰动、预测、机制理解。",
    "whole-brain-model": "全脑模型（Whole-Brain Model）用连接组+神经质量模型刻画大脑活动, 涵盖大规模脑动力学。",
    "brain-development-evolution": "脑发育与进化, 涵盖从胚胎到成年的脑动力学建模与跨物种比较。",
    "brain-digital-twin": "面向临床的脑数字孪生, 如癫疖、AD、帕金森、卒中恢复等领域的个体化建模。",
    "digital-twin-medicine": "数字孪生在医学中的应用, 涵盖诊疗决策、药物响应、术前规划等场景。",
    "connectomics": "连接组学（Connectomics）研究脑结构连接模式的采集、分析与建模。",
    "brain-simulation": "脑模拟（Brain Simulation）涵盖从微观神经元到全脑的多尺度脑动力学仿真。",
    "neuromodulation-twin": "Neurotwins + tDCS, 结合个体化脑模型与经颅电/磁刺激建模, 设计个体化刺激方案。",
    "personalized-brain": "个性化脑模型, 用个体连接组/表型驱动脑动力学建模, 用于精准神经学。",
    "digital-brain": "数字孪生+脑, 涵盖神经科学+脑模垄广义主题。",
    "neural-mass-field-model": "神经质量模型 / 神经场模型, 刻画局部神经群体的平均活动与空间动态。",
    "virtual-epileptic-patient": "虚拟癫痫患者 (VEP), 用于颞叶癫痫的个体化建模、癫疖灶定位与手术规划。",
    "personalized-brain-model": "个性化脑模型, 通过结构连接驱动个体化神经动力学仿真。",
    "tms-modeling": "经颅磁刺激建模, 预测电场分布与下游脑动力学响应。",
    "whole-brain": "全脑范围, 涵盖多模态全脑分析/建模。",
    "neurodegeneration-model": "神经退行性脑动力学建模, 涵盖 AD、PD 等。",
    "whole-brain-simulation": "全脑仿真, 涵盖个体连接组驱动的神经动力学模拟。",
    "multiscale-brain-model": "多尺度脑模型, 从微观神经元到宏观全脑的多尺度集成。",
    "tms-ad-dosing": "经颅磁刺激 + AD 剂量预测, 个体化剂量优化。",
    "neuroimaging-disease-progression": "神经影像 + 疾病进展, 涵盖 AD/PD/HD 等进展型脑疾病的多模态分析。",
    "personalized-brain-dynamics": "个性化脑动力学, 面向个体化治疗与机制发现。",
    "digital-twin-cognition": "数字孪生认知, 用虚拟脑模型模拟认知任务与行为预测。",
    "connectome-model": "连接组驱动的脑动力学模型, 基于结构连接预测功能动力学。",
    "eeg-model": "脑电信号与神经动力学模型结合。",
    "fnirs-brain": "fNIRS + 脑动力学建模。",
    "kalman-neural": "卡尔曼滤波 + 神经动力学, 用于状态估计与参数推断。",
    "presurgical-planning": "术前规划, 涵盖脑肿瘤切除、癫疖灶定位等个体化手术计划。",
}


def cmd_topic_import(args, wiki_root: Path) -> int:
    csv_path = Path(args.csv)
    if not csv_path.is_file():
        wc.die(f"找不到 CSV: {csv_path}")

    rows = read_csv(csv_path)
    target = filter_target(rows)
    topics_dir = wiki_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    # 按 topic slug 分组 papers
    from collections import defaultdict
    grouped = defaultdict(list)
    for r in target:
        sr = r.get("screen_reason", "").strip()
        topic_slug = screen_reason_to_topic(sr)
        grouped[topic_slug].append(r)

    print(f"=== Topic 生成 ===")
    print(f"  CSV target: {len(target)}")
    print(f"  topic 数: {len(grouped)}")

    stats = {"created": 0, "existed": 0, "updated": 0}

    for topic_slug, papers in grouped.items():
        topic_path = topics_dir / f"{topic_slug}.md"
        topic_title = topic_slug.replace("-", " ").title()
        cat_zh = papers[0].get("category_new", "")
        description = TOPIC_DESCRIPTION.get(topic_slug, f"{topic_slug} 主题相关论文集合。")

        # 现有 主题 / 仅全 中文 topic (比如 digital-twin-brain)
        if topic_slug == "digital-twin-brain":
            topic_title = "数字孪生脑 (Digital Twin Brain)"
        elif topic_slug == "virtual-brain-tvb":
            topic_title = "The Virtual Brain (TVB)"
        elif topic_slug == "virtual-brain-twin":
            topic_title = "虚拟脑孪生 (Virtual Brain Twin)"
        elif topic_slug == "neurovascular-coupling":
            topic_title = "神经血管耦合 (Neurovascular Coupling)"
        elif topic_slug == "neuromorphic-twin":
            topic_title = "神经形态孪生 (Neuromorphic Twin)"
        elif topic_slug == "surrogate-brain":
            topic_title = "代理脑 (Surrogate Brain)"
        elif topic_slug == "whole-brain-model":
            topic_title = "全脑模型 (Whole-Brain Model)"
        elif topic_slug == "brain-development-evolution":
            topic_title = "脑发育/进化 (Brain Development/Evolution)"
        elif topic_slug == "brain-digital-twin":
            topic_title = "脑数字孪生 (Brain Digital Twin)"
        elif topic_slug == "digital-twin-medicine":
            topic_title = "数字孪生 + 医学 (Digital Twin + Medicine)"
        elif topic_slug == "connectomics":
            topic_title = "连接组学 (Connectomics)"
        elif topic_slug == "brain-simulation":
            topic_title = "脑模拟 (Brain Simulation)"
        elif topic_slug == "neuromodulation-twin":
            topic_title = "Neurotwins + tDCS"
        elif topic_slug == "personalized-brain":
            topic_title = "个性化脑 (Personalized Brain)"
        elif topic_slug == "digital-brain":
            topic_title = "数字孪生 + 脑 (Digital + Brain)"
        elif topic_slug == "neural-mass-field-model":
            topic_title = "神经质量/场模型 (Neural Mass/Field Model)"
        elif topic_slug == "virtual-epileptic-patient":
            topic_title = "虚拟癫痫患者 (Virtual Epileptic Patient)"
        elif topic_slug == "personalized-brain-model":
            topic_title = "个性化脑模型 (Personalized Brain Model)"
        elif topic_slug == "tms-modeling":
            topic_title = "经颅刺激建模 (TMS Modeling)"
        elif topic_slug == "whole-brain":
            topic_title = "全脑 (Whole Brain)"
        elif topic_slug == "neurodegeneration-model":
            topic_title = "神经退行模型 (Neurodegeneration Model)"
        elif topic_slug == "whole-brain-simulation":
            topic_title = "全脑模拟 (Whole-Brain Simulation)"
        elif topic_slug == "multiscale-brain-model":
            topic_title = "多尺度脑模型 (Multiscale Brain Model)"
        elif topic_slug == "tms-ad-dosing":
            topic_title = "经颅刺激 + AD 剂量 (TMS + AD Dosing)"
        elif topic_slug == "neuroimaging-disease-progression":
            topic_title = "神经影像 + 疾病进展 (Neuroimaging + Disease Progression)"
        elif topic_slug == "personalized-brain-dynamics":
            topic_title = "个性化脑动力学 (Personalized Brain Dynamics)"
        elif topic_slug == "digital-twin-cognition":
            topic_title = "数字孪生认知 (Digital Twin Cognition)"
        elif topic_slug == "connectome-model":
            topic_title = "连接组模型 (Connectome Model)"
        elif topic_slug == "eeg-model":
            topic_title = "脑电 + 模型 (EEG + Model)"
        elif topic_slug == "fnirs-brain":
            topic_title = "fNIRS + 脑 (fNIRS + Brain)"
        elif topic_slug == "kalman-neural":
            topic_title = "卡尔曼滤波 + 神经 (Kalman Filter + Neural)"
        elif topic_slug == "presurgical-planning":
            topic_title = "术前规划 + 肿瘤切除 (Presurgical Planning)"

        # 论文列表 (限 20 篇展示, 全部在 wikilink)
        zidx = ZoteroIndex(wz.get_zotero_local())
        lines = []
        for p in papers[:20]:
            title = p.get("title", "").split("|")[0].strip().strip('"')
            doi = parse_doi(p.get("DOI", ""))
            it = zidx.find(doi, title)
            if it:
                ck = (it["data"].get("citationKey") or "").strip()
                ck = wz.safe_filename(ck).replace(".md", "")
                wiki_link = f"[[{ck}]]"
            else:
                wiki_link = "[citekey unknown]"
            lines.append(f"- {wiki_link} — {title[:60]}")
        paper_list = "\n".join(lines) if lines else "- (待 LLM 抽取)"

        # 如果论文 > 20 篇, 加注
        if len(papers) > 20:
            paper_list += f"\n- (还有 {len(papers) - 20} 篇未展示)"

        body = TOPIC_TEMPLATE.format(
            topic_title=topic_title,
            topic_description=description,
            category_new_zh=cat_zh,
            paper_count=len(papers),
            papers_list=paper_list,
        )

        if topic_path.exists() and not args.force:
            stats["existed"] += 1
            if args.verbose:
                print(f"  {topic_slug}.md 已存在 ({len(papers)} 篇)")
        else:
            if not args.dry_run:
                topic_path.write_text(body, encoding="utf-8")
            stats["created"] += 1 if not topic_path.exists() else stats["updated"] + 1
            if args.verbose:
                action = "create" if not topic_path.exists() else "update"
                print(f"  [{action}] {topic_slug}.md ({len(papers)} 篇)")

    print(f"\n=== 统计 ===")
    print(f"  新建: {stats['created']}")
    print(f"  更新: {stats['updated']}")
    print(f"  已存在: {stats['existed']}")
    print(f"  输出: {topics_dir}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="从 CSV 批量导入 paperinfo + paper.md 骨架",
        usage="wiki zotero-csv <subcommand> [args...]",
    )
    sub = parser.add_subparsers(dest="subcommand")

    p_imp = sub.add_parser("csv-import", help="从 CSV 导入论文 (强/弱相关)")
    p_imp.add_argument("csv", help="CSV 路径")
    p_imp.add_argument("--wiki-root", help="wiki 根目录")
    p_imp.add_argument("--dry-run", action="store_true")
    p_imp.add_argument("--verbose", "-v", action="store_true")

    p_st = sub.add_parser("csv-status", help="查看 CSV 论文在 wiki 里的覆盖")
    p_st.add_argument("csv", help="CSV 路径")
    p_st.add_argument("--wiki-root", help="wiki 根目录")

    p_top = sub.add_parser("topic-import", help="从 CSV 生成 topic 节点")
    p_top.add_argument("csv", help="CSV 路径")
    p_top.add_argument("--wiki-root", help="wiki 根目录")
    p_top.add_argument("--dry-run", action="store_true")
    p_top.add_argument("--force", action="store_true")
    p_top.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        return 1

    wiki_root = Path(args.wiki_root) if args.wiki_root else wc.find_wiki_root()

    if args.subcommand == "csv-import":
        return cmd_csv_import(args, wiki_root)
    if args.subcommand == "csv-status":
        return cmd_csv_status(args, wiki_root)
    if args.subcommand == "topic-import":
        return cmd_topic_import(args, wiki_root)
    wc.die(f"Unknown subcommand: {args.subcommand}")
    return 1


def run(argv: list[str]) -> int:
    """统一 CLI 入口: `wiki zotero-csv <subcommand>`"""
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.argv = ["wiki_zotero_csv", "--help"]
        return main()
    sub = argv[0]
    rest = argv[1:]
    sys.argv = ["wiki_zotero_csv", sub] + rest
    return main()


if __name__ == "__main__":
    sys.exit(main())