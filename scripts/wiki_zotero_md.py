#!/usr/bin/env python3
"""
DEPRECATED (T-W4-028): 此脚本功能仍可用(Zotero → Paper MD 转换),但调用方式已被
wiki-zotero-sync 微 Skill 取代。新同步请走 Skill,不直调 Python。
原 docstring 保留如下:

Zotero → Paper MD Bridge

从 Zotero SQLite 自动生成 Evidence Wiki 的 Paper 节点骨架。
用法:
    python wiki_zotero_md.py collections [--db PATH]
    python wiki_zotero_md.py generate --collection NAME [--output DIR] [--modality M] [--dry-run]
    python wiki_zotero_md.py sync --collection NAME [--output DIR]
"""

import argparse
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime

# ── 默认配置 ──────────────────────────────────────────────
DEFAULT_DB = os.path.expanduser("~/Zotero/zotero.sqlite")
DEFAULT_OUTPUT = "./wiki/papers"

# ── 停用词（提取 short-keyword 时跳过）─────────────────────
STOP_WORDS = {
    "the", "of", "and", "in", "a", "an", "for", "with", "to", "on",
    "by", "from", "at", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "this", "that", "these", "those", "it", "its", "using", "based",
    "between", "through", "during", "before", "after", "above",
    "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "about", "into", "via", "vs", "vs.",
    "their", "they", "them", "we", "our", "your", "he", "she",
    "his", "her", "how", "what", "which", "who", "whom", "when",
    "where", "why", "not", "no", "nor", "but", "or", "so", "if",
    "both", "each", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "just", "also", "only",
}

ZH_STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
    "它", "们", "那", "里", "为", "什么", "怎么", "如何", "可以",
    "以", "及", "与", "或", "但", "而", "把", "被", "从", "对",
    "等", "能", "将", "已", "于", "由", "这个", "那个", "些",
    "研究", "方法", "基于", "使用", "分析", "一种", "进行", "通过",
}


class ZoteroDB:
    """Zotero SQLite 数据库连接（复制一份避免锁）"""

    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            print(f"错误: 找不到 Zotero 数据库 {db_path}", file=sys.stderr)
            sys.exit(1)
        self._tmp = tempfile.mktemp(suffix=".sqlite")
        shutil.copy2(db_path, self._tmp)
        self.conn = sqlite3.connect(self._tmp)

    def close(self):
        self.conn.close()
        if os.path.exists(self._tmp):
            os.unlink(self._tmp)

    def cursor(self):
        return self.conn.cursor()


# ── 数据库查询 ────────────────────────────────────────────

def list_collections(db: ZoteroDB):
    """列出所有 Collection 及论文数"""
    c = db.cursor()
    c.execute("""
        SELECT c.collectionID, c.collectionName, c.parentCollectionID,
               COUNT(ci.itemID) as cnt
        FROM collections c
        LEFT JOIN collectionItems ci ON c.collectionID = ci.collectionID
        LEFT JOIN items i ON ci.itemID = i.itemID
        LEFT JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
        WHERE it.typeName = 'journalArticle' OR it.typeName IS NULL
        GROUP BY c.collectionID
        HAVING cnt > 0
        ORDER BY cnt DESC
    """)
    rows = c.fetchall()
    print(f"{'ID':>6}  {'论文数':>6}  {'名称'}")
    print("-" * 60)
    for row in rows:
        indent = "  " if row[2] else ""
        print(f"{row[0]:>6}  {row[3]:>6}  {indent}{row[1]}")


def get_collection_items(db: ZoteroDB, collection_name: str) -> list:
    """获取指定 Collection 中的所有 journalArticle"""
    c = db.cursor()
    c.execute("""
        SELECT i.itemID, i.key
        FROM items i
        JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
        JOIN collectionItems ci ON i.itemID = ci.itemID
        JOIN collections col ON ci.collectionID = col.collectionID
        WHERE col.collectionName = ?
        AND it.typeName = 'journalArticle'
    """, (collection_name,))
    return c.fetchall()


def get_item_metadata(db: ZoteroDB, item_id: int) -> dict:
    """获取单篇论文的完整元数据"""
    c = db.cursor()

    # 基本字段
    c.execute("""
        SELECT f.fieldName, iv.value
        FROM itemData id
        JOIN fields f ON id.fieldID = f.fieldID
        JOIN itemDataValues iv ON id.valueID = iv.valueID
        WHERE id.itemID = ?
    """, (item_id,))
    fields = {r[0]: r[1] for r in c.fetchall()}

    # 作者
    c.execute("""
        SELECT cr.lastName, cr.firstName
        FROM itemCreators ic
        JOIN creators cr ON ic.creatorID = cr.creatorID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
    """, (item_id,))
    authors = [{"last": r[0], "first": r[1]} for r in c.fetchall()]

    # 标签
    c.execute("""
        SELECT t.name FROM itemTags it JOIN tags t ON it.tagID = t.tagID
        WHERE it.itemID = ?
    """, (item_id,))
    tags = [r[0] for r in c.fetchall()]

    # 附件
    c.execute("""
        SELECT ia.contentType, ia.path
        FROM itemAttachments ia
        WHERE ia.parentItemID = ?
    """, (item_id,))
    attachments = [{"mime": r[0], "path": r[1]} for r in c.fetchall()]

    return {
        "item_id": item_id,
        "title": fields.get("title", ""),
        "date": fields.get("date", ""),
        "year": extract_year(fields.get("date", "")),
        "doi": fields.get("DOI", ""),
        "pmid": fields.get("PMID", ""),
        "volume": fields.get("volume", ""),
        "issue": fields.get("issue", ""),
        "pages": fields.get("pages", ""),
        "abstract": fields.get("abstractNote", ""),
        "journal": fields.get("publicationTitle", ""),
        "journal_abbr": fields.get("journalAbbreviation", ""),
        "language": fields.get("language", ""),
        "citation_key": fields.get("citationKey", ""),
        "url": fields.get("url", ""),
        "authors": authors,
        "tags": tags,
        "attachments": attachments,
    }


def get_item_key(db: ZoteroDB, item_id: int) -> str:
    """获取 item 的 Zotero key"""
    c = db.cursor()
    c.execute("SELECT key FROM items WHERE itemID = ?", (item_id,))
    row = c.fetchone()
    return row[0] if row else ""


def get_item_type_name(db: ZoteroDB, item_id: int) -> str:
    """获取 item 的类型名"""
    c = db.cursor()
    c.execute("""
        SELECT it.typeName FROM items i JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
        WHERE i.itemID = ?
    """, (item_id,))
    row = c.fetchone()
    return row[0] if row else "unknown"


# ── 工具函数 ──────────────────────────────────────────────

def extract_year(date_str: str) -> int:
    """从 date 字段提取年份"""
    if not date_str:
        return 0
    m = re.search(r"(\d{4})", date_str)
    return int(m.group(1)) if m else 0


def extract_short_keyword(title: str) -> str:
    """从标题提取 2-4 个关键词作为文件名的一部分"""
    if not title:
        return "untitled"

    zh_count = len(re.findall(r"[一-鿿]", title))
    if zh_count > len(title) * 0.3:
        words = re.findall(r"[一-鿿]+", title)
        keywords = [w for w in words if w not in ZH_STOP_WORDS and len(w) >= 2]
        return "_".join(keywords[:4]) if keywords else "untitled"
    else:
        words = re.findall(r"[a-zA-Z]+", title.lower())
        keywords = [w for w in words if w not in STOP_WORDS and len(w) >= 3]
        return "_".join(keywords[:4]) if keywords else "untitled"


def format_authors(authors: list) -> str:
    """格式化作者列表为可读字符串"""
    parts = []
    for a in authors:
        if a["first"] and a["last"]:
            parts.append(f"{a['last']}, {a['first']}")
        elif a["last"]:
            parts.append(a["last"])
    return "; ".join(parts)


def format_authors_yaml(authors: list) -> list:
    """格式化作者列表为 YAML 数组"""
    parts = []
    for a in authors:
        if a["first"] and a["last"]:
            parts.append(f'"{a["last"]}, {a["first"]}"')
        elif a["last"]:
            parts.append(f'"{a["last"]}"')
    return parts


def detect_modality(collection_name: str, tags: list, explicit: str = "") -> str:
    """自动检测 modality"""
    if explicit:
        return explicit.lower()

    cn = collection_name.lower()
    tag_str = " ".join(tags).lower()

    for keyword, mod in [
        ("fmri", "fmri"), ("fri", "fmri"),
        ("eeg", "eeg"),
        ("fnirs", "fnirs"),
        ("机器学习", "ml"), ("ml", "ml"),
        ("统计", "stats"), ("stats", "stats"),
    ]:
        if keyword in cn:
            return mod

    for keyword, mod in [
        ("fmri", "fmri"), ("eeg", "eeg"), ("fnirs", "fnirs"),
    ]:
        if keyword in tag_str:
            return mod

    return "other"


def build_filename(meta: dict, modality: str) -> str:
    """生成文件名: <FirstAuthor>_<Year>_<keyword>.md"""
    if meta["authors"]:
        first_author = meta["authors"][0]["last"]
    else:
        first_author = "unknown"

    zh = re.findall(r"[一-鿿]", first_author)
    if zh:
        author_part = first_author
    else:
        author_part = re.sub(r"[^a-z0-9]", "", first_author.lower())

    year = meta["year"] or "0000"
    keyword = extract_short_keyword(meta["title"])

    filename = f"{author_part}_{year}_{keyword}.md"
    filename = re.sub(r"_+", "_", filename)
    return filename


# ── 渲染 ──────────────────────────────────────────────────

def render_paper_skeleton(meta: dict, modality: str, collection_name: str) -> str:
    """渲染 Paper 骨架 Markdown"""
    authors_yaml = format_authors_yaml(meta["authors"])
    authors_yaml_str = "\n".join(f"  - {a}" for a in authors_yaml) if authors_yaml else "  []"

    tags_yaml = "\n".join(f"  - {t}" for t in meta["tags"]) if meta["tags"] else "  []"

    zotero_link = f"zotero://select/library/items/{meta['key']}"
    now = datetime.now().strftime("%Y-%m-%d")

    # 构建 YAML，跳过空值字段
    yaml_lines = [
        "---",
        f"id: {build_filename(meta, modality).replace('.md', '')}",
        f"citekey: {meta['citation_key']}",
        f'title: "{meta["title"]}"',
        "authors:",
        authors_yaml_str,
        f"year: {meta['year']}",
        f'journal: "{meta["journal"]}"',
    ]
    if meta["doi"]:
        yaml_lines.append(f'doi: "{meta["doi"]}"')
    if meta["pmid"]:
        yaml_lines.append(f'pmid: "{meta["pmid"]}"')
    if meta["volume"]:
        yaml_lines.append(f'volume: "{meta["volume"]}"')
    if meta["issue"]:
        yaml_lines.append(f'issue: "{meta["issue"]}"')
    if meta["pages"]:
        yaml_lines.append(f'pages: "{meta["pages"]}"')
    yaml_lines += [
        "item_type: journalArticle",
        f'language: "{meta["language"]}"',
        "tags:",
        tags_yaml,
        f'zotero_key: "{meta["key"]}"',
        f'zotero_link: "{zotero_link}"',
        f'collection: "{collection_name}"',
        f"modality: {modality}",
        "status: pending",
        f"created: {now}",
        f"updated: {now}",
        "---",
    ]
    yaml = "\n".join(yaml_lines)

    authors_display = format_authors(meta["authors"])
    doi_link = f"[{meta['doi']}](https://doi.org/{meta['doi']})" if meta["doi"] else ""
    pmid_line = f"- **PMID**: {meta['pmid']}" if meta["pmid"] else ""
    # 构建期刊显示：只在有值时拼接
    vol_parts = []
    if meta["volume"]:
        vol_parts.append(f"Vol {meta['volume']}")
        if meta["issue"]:
            vol_parts[0] += f"({meta['issue']})"
    if meta["pages"]:
        vol_parts.append(f"pp. {meta['pages']}")
    journal_display = meta["journal"]
    if vol_parts:
        journal_display += " | " + ", ".join(vol_parts)

    template_map = {
        "fmri": "paper_fmri",
        "eeg": "paper_eeg",
        "fnirs": "paper_fnirs",
        "multimodal": "paper_multimodal",
        "ml": "paper_ml",
        "stats": "paper_stats",
    }
    analysis_template = template_map.get(modality, "paper_fmri")

    body = f"""
# {meta['title']}

**元信息**
- **作者**: {authors_display}
- **年份**: {meta['year']}
- **期刊**: {journal_display}
- **DOI**: {doi_link}
{pmid_line}
- **Zotero**: [打开]({zotero_link})
"""

    return yaml + body


# ── 主流程 ────────────────────────────────────────────────

def generate_papers(
    db: ZoteroDB,
    collection_name: str,
    output_dir: str,
    modality_override: str = "",
    dry_run: bool = False,
    sync: bool = False,
):
    """为指定 Collection 生成 Paper 骨架"""
    items = get_collection_items(db, collection_name)
    if not items:
        print(f"错误: Collection '{collection_name}' 中没有 journalArticle", file=sys.stderr)
        return

    os.makedirs(output_dir, exist_ok=True)

    created = 0
    skipped = 0
    errors = 0

    for i, (item_id, _) in enumerate(items):
        try:
            key = get_item_key(db, item_id)
            item_type = get_item_type_name(db, item_id)

            meta = get_item_metadata(db, item_id)
            meta["key"] = key
            meta["item_type"] = item_type

            modality = detect_modality(collection_name, meta["tags"], modality_override)
            filename = build_filename(meta, modality)
            filepath = os.path.join(output_dir, filename)

            if sync and os.path.exists(filepath):
                skipped += 1
                continue

            content = render_paper_skeleton(meta, modality, collection_name)

            if dry_run:
                print(f"  [DRY-RUN] {filename}")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                created += 1

            if (i + 1) % 20 == 0:
                print(f"  进度: {i + 1}/{len(items)}")

        except Exception as e:
            errors += 1
            print(f"  错误: item {item_id} - {e}", file=sys.stderr)

    print(f"\n完成:")
    print(f"  总计: {len(items)} 篇")
    print(f"  新建: {created}")
    print(f"  跳过: {skipped}")
    print(f"  错误: {errors}")
    print(f"  输出: {os.path.abspath(output_dir)}")


def main():
    parser = argparse.ArgumentParser(
        description="Zotero → Paper MD Bridge: 自动生成 Evidence Wiki 的 Paper 节点骨架"
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Zotero SQLite 数据库路径")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("collections", help="列出所有 Collection")

    gen = sub.add_parser("generate", help="按 Collection 生成 Paper 骨架")
    gen.add_argument("--collection", "-c", required=True, help="Collection 名称")
    gen.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="输出目录")
    gen.add_argument("--modality", "-m", default="", help="指定 modality（覆盖自动检测）")
    gen.add_argument("--dry-run", action="store_true", help="干跑模式")

    sync = sub.add_parser("sync", help="增量同步（只处理新增论文）")
    sync.add_argument("--collection", "-c", required=True, help="Collection 名称")
    sync.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="输出目录")
    sync.add_argument("--modality", "-m", default="", help="指定 modality")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    db = ZoteroDB(args.db)
    try:
        if args.command == "collections":
            list_collections(db)
        elif args.command == "generate":
            generate_papers(db, args.collection, args.output, args.modality, args.dry_run)
        elif args.command == "sync":
            generate_papers(db, args.collection, args.output, args.modality, sync=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
