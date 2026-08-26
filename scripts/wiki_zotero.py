#!/usr/bin/env python3
"""
wiki_zotero.py — Evidence Wiki 与 Zotero 库的双向同步

子命令:
  list      列出所有 Zotero collection + 论文数
  pull      按 collection 一次性生成 paperinfo/<BBT citekey>.md
  sync      增量同步 (zotero-lastmod 指纹)
  stats     统计 paperinfo/paper 对齐
  match     给 paper 找对应的 paperinfo (匹配 BBT citekey)
  backfill  现有 paper 补 zotero-key 字段 + 重命名为 BBT citekey

设计:
- 直读 zotero.sqlite (pyzotero local=True, 走 WAL 模式只读连接)
- 文件名 = BBT citekey (人类可读 + 唯一 + 稳定)
- zotero-key 作为 frontmatter 字段 (跨库唯一 ID)
- zotero-lastmod 作为增量同步指纹
- 字段命名 kebab-case (zotero-key, zotero-link, zotero-lastmod)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc

try:
    from pyzotero import Zotero
except ImportError:
    print("✗ 需要 pyzotero: pip install pyzotero", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────
# Zotero 工具
# ──────────────────────────────────────────────────────────────────────

def get_zotero_local():
    """Zotero 本地访问。

    优先走 pyzotero local=True (Zotero 桌面版 HTTP API, http://localhost:23119)。
    如果 Zotero 桌面版未运行 (connection refused), fallback 到 SQLite 直读
    ~/Zotero/zotero.sqlite.
    """
    try:
        zot = Zotero(library_id="0", library_type="user", local=True)
        # 探一下能不能联通
        zot.items(limit=1)
        return zot
    except Exception as e:
        # Zotero 未运行 / 端口未开 → fallback 到 SQLite
        wc.eprint(f"⚠ pyzotero local 模式不可用 ({type(e).__name__}), fallback 到 SQLite 直读")
        return _sqlite_fallback()


def _sqlite_fallback():
    """纯 sqlite3 fallback, 不依赖 pyzotero / Zotero 进程。
    返回一个 sqlite-backed zot-like object, 只实现 wiki_zotero.py 用到的 API.

    2026-08-25 修复(database is locked):Zotero 客户端运行时持有锁,
    mode=ro 直连原库仍可能 locked。策略:先试原库 ro;失败则复制主库
    (+ -wal/-shm)到临时文件再读——副本永不被锁,committed 数据完整。
    """
    import sqlite3
    import shutil
    import tempfile

    DB_PATH = os.path.expanduser("~/Zotero/zotero.sqlite")
    if not os.path.exists(DB_PATH):
        wc.die(f"找不到 Zotero 数据库 {DB_PATH}")

    # 先试原库只读;Zotero 未运行时这是最快路径
    try:
        _conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        _conn.execute("SELECT COUNT(*) FROM items").fetchone()
    except sqlite3.OperationalError as e:
        # locked / busy → 复制副本(带 WAL)到临时文件,永不被锁
        wc.eprint(f"⚠ 原库直读失败({e}),复制临时副本绕过锁…")
        tmp = tempfile.mktemp(suffix=".sqlite")
        shutil.copy2(DB_PATH, tmp)
        for ext in ("-wal", "-shm"):
            if os.path.exists(DB_PATH + ext):
                shutil.copy2(DB_PATH + ext, tmp + ext)
        _conn = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
        wc.ok(f"已切换到临时副本 {tmp}(Zotero 可保持运行)")

    final_conn = _conn

    class SQLiteZotero:
        def __init__(self):
            self.conn = final_conn
            self.conn.row_factory = sqlite3.Row

        def _rows(self, sql, params=()):
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

        def items(self, q=None, limit=None, start=0, top_only=True):
            """裸 items() 或搜索 — 取简化字段集以够 wiki_zotero 用。
            top_only=True (默认) 只返顶层 items, 过滤 attachment/note/annotation。
            贴近 pyzotero 的 items() / all_top() 语义。
            """
            sql = """
                SELECT i.itemID, i.key, i.dateAdded, i.dateModified,
                       it.typeName AS itemType
                FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                WHERE 1=1
            """
            params = []
            if top_only:
                sql += " AND it.typeName NOT IN ('attachment', 'note', 'annotation')"
            if q:
                sql += " AND i.itemID IN (SELECT id.itemID FROM itemData id JOIN itemDataValues v ON id.valueID=v.valueID WHERE v.value LIKE ?)"
                params.append(f"%{q}%")
            if limit:
                sql += f" LIMIT {limit} OFFSET {start}"
            rows = self._rows(sql, params)
            return [self._hydrate(r['itemID']) for r in rows]

        def all_top(self):
            return self.items(limit=50000)

        def collection_items(self, key, limit=100, start=0):
            """key 可以是 collectionName 或 collectionID"""
            cid = self._resolve_collection_id(key)
            if cid is None:
                return []
            sql = """
                SELECT i.itemID FROM items i
                JOIN collectionItems ci ON i.itemID = ci.itemID
                WHERE ci.collectionID = ?
            """
            params = [cid]
            sql += f" ORDER BY i.itemID"
            if limit:
                sql += f" LIMIT {limit} OFFSET {start}"
            rows = self._rows(sql, params)
            return [self._hydrate(r['itemID']) for r in rows]

        def collections(self, start=0, limit=100):
            sql = "SELECT collectionID FROM collections ORDER BY collectionID"
            if limit:
                sql += f" LIMIT {limit} OFFSET {start}"
            rows = self._rows(sql)
            return [{"data": self._coll(r['collectionID'])} for r in rows]

        def collection(self, key):
            """key 可以是 collectionID (int)、collectionName (str) 或 collectionKey (8 字符串)"""
            data = self._coll_data(key)
            if data is None:
                raise KeyError(f"collection {key}")
            return {"data": data}

        def item(self, key):
            """key 是 zotero item key (string)"""
            rows = self._rows("SELECT itemID FROM items WHERE key = ?", (key,))
            if not rows:
                raise KeyError(f"item {key}")
            return self._hydrate(rows[0]['itemID'])

        # ---------- 内部 helpers ----------

        def _coll(self, cid):
            row = self._rows("SELECT * FROM collections WHERE collectionID = ?", (cid,))[0]
            return self._coll_row_to_dict(row)

        def _coll_data(self, key):
            """key 可以是 collectionID (int) / collectionName / collectionKey"""
            try:
                cid = int(key)
                rows = self._rows("SELECT * FROM collections WHERE collectionID = ?", (cid,))
            except ValueError:
                rows = self._rows(
                    "SELECT * FROM collections WHERE collectionName = ? OR key = ?",
                    (key, key),
                )
            if not rows:
                return None
            return self._coll_row_to_dict(rows[0])

        def _coll_row_to_dict(self, row):
            return {
                "key": row['key'],
                "collectionID": row['collectionID'],
                "collectionName": row['collectionName'],
                "name": row['collectionName'],
                "parentCollectionID": (row['parentCollectionID']
                                       if row['parentCollectionID'] != 0 else False),
                "parentCollection": (row['parentCollectionID']
                                     if row['parentCollectionID'] != 0 else False),
            }

        def _resolve_collection_id(self, key):
            data = self._coll_data(key)
            return data['collectionID'] if data else None

        def _hydrate(self, item_id):
            """构造 pyzotero 风格的 item dict: {"data": {...}, "meta": {...}}"""
            item_row = self._rows("SELECT * FROM items WHERE itemID = ?", (item_id,))[0]

            # 拿所有 field
            fields = {
                'key': item_row['key'],
                'dateAdded': item_row.get('dateAdded', ''),
                'dateModified': item_row.get('dateModified', ''),
                'libraryID': item_row.get('libraryID'),
            }
            for r in self._rows("""
                SELECT f.fieldName, v.value
                FROM itemData id
                JOIN fields f ON id.fieldID = f.fieldID
                JOIN itemDataValues v ON id.valueID = v.valueID
                WHERE id.itemID = ?
            """, (item_id,)):
                fields[r['fieldName']] = r['value']

            # itemType
            type_row = self._rows("""
                SELECT it.typeName FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID WHERE i.itemID = ?
            """, (item_id,))[0]
            fields['itemType'] = type_row['typeName']

            # creators
            creators = []
            for r in self._rows("""
                SELECT cr.firstName, cr.lastName, cr.fieldMode,
                       (SELECT creatorType FROM creatorTypes WHERE creatorTypeID = ic.creatorTypeID) AS role,
                       ic.orderIndex
                FROM itemCreators ic
                JOIN creators cr ON ic.creatorID = cr.creatorID
                WHERE ic.itemID = ?
                ORDER BY ic.orderIndex
            """, (item_id,)):
                creators.append({
                    'firstName': r['firstName'],
                    'lastName': r['lastName'],
                    'creatorType': r['role'],
                    'fieldMode': r['fieldMode'] if r['fieldMode'] is not None else 0,
                })
            fields['creators'] = creators

            # tags
            tags = []
            for r in self._rows("""
                SELECT t.name FROM itemTags it
                JOIN tags t ON it.tagID = t.tagID
                WHERE it.itemID = ?
            """, (item_id,)):
                tags.append({'tag': r['name']})
            fields['tags'] = tags

            # collections
            collections = []
            for r in self._rows("""
                SELECT collectionID FROM collectionItems WHERE itemID = ?
            """, (item_id,)):
                collections.append(r['collectionID'])
            fields['collections'] = collections

            # dateAdded / dateModified 已在 fields 初化时添加, 不需重复
            return {"data": fields, "meta": {"itemID": item_id}}

    return SQLiteZotero()


def collection_path(zot, key: str, _cache: dict | None = None) -> str:
    """返回 collection 的完整路径, 如 '7统计学习 / 孪生脑算法'。"""
    if _cache is None:
        _cache = {}
    if key in _cache:
        return _cache[key]
    c = zot.collection(key)["data"]
    parent = c.get("parentCollection", False)
    name = c.get("name", "")
    if parent:
        path = collection_path(zot, parent, _cache) + " / " + name
    else:
        path = name
    _cache[key] = path
    return path


def nullable(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


# ──────────────────────────────────────────────────────────────────────
# L1 字段规范化 (一个 Zotero item → paperinfo frontmatter dict)
# ──────────────────────────────────────────────────────────────────────

def normalize_item(item: dict, zot) -> dict:
    """从 Zotero item 抽 paperinfo 节点所需的字段。"""
    data = item["data"]
    key = data.get("key", "")
    item_type = data.get("itemType", "")

    # creators: BBT 偶尔装反 (lastName="P" firstName="Triebkorn")
    creators = []
    for c in data.get("creators", []):
        if c.get("fieldMode") == 1:
            creators.append({
                "type": "organisation",
                "family": "",
                "given": "",
                "literal": nullable(c.get("lastName")),
                "role": c.get("creatorType", "author"),
                "full_name": nullable(c.get("lastName")) or "",
            })
        else:
            family = nullable(c.get("lastName")) or ""
            given = nullable(c.get("firstName")) or ""
            if 1 <= len(family) <= 2 and len(given) > len(family):
                family, given = given, family
            creators.append({
                "type": "person",
                "family": family,
                "given": given,
                "literal": None,
                "role": c.get("creatorType", "author"),
                "full_name": f"{family} {given}".strip(),
            })

    primary_creator_type = {
        "journalArticle": "author",
        "book": "author",
        "preprint": "author",
        "conferencePaper": "author",
        "blogPost": "author",
        "bookSection": "author",
    }.get(item_type)
    primary_authors = [c for c in creators if c["role"] == primary_creator_type] if primary_creator_type else creators
    if not primary_authors:
        primary_authors = creators

    def fmt_short(ca):
        return ca["full_name"] if ca["type"] == "organisation" else ca["family"]

    if len(primary_authors) == 0:
        authors_short = ""
    elif len(primary_authors) == 1:
        authors_short = fmt_short(primary_authors[0])
    elif len(primary_authors) == 2:
        authors_short = f"{fmt_short(primary_authors[0])} & {fmt_short(primary_authors[1])}"
    else:
        authors_short = f"{fmt_short(primary_authors[0])} et al."

    indexed_key = key  # 本地模式: key 即库内唯一 ID

    # 年份: 提取 4 位数字
    date_raw = nullable(data.get("date"))
    year = ""
    if date_raw:
        m = re.search(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b", date_raw)
        if m:
            year = m.group(1)

    # collection 路径
    collections = []
    for cid in data.get("collections", []):
        try:
            collections.append(collection_path(zot, cid))
        except Exception:
            collections.append(f"<unresolved:{cid}>")

    tags = [t.get("tag", "") for t in data.get("tags", []) if t.get("tag")]

    title = nullable(data.get("title"))
    abstract = nullable(data.get("abstractNote"))
    container_title = (
        nullable(data.get("publicationTitle"))
        or nullable(data.get("proceedingsTitle"))
        or nullable(data.get("bookTitle"))
    )
    citation_key = nullable(data.get("citationKey"))

    return {
        "key": key,
        "indexed_key": indexed_key,
        "item_type": item_type,
        "title": title,
        "abstract": abstract,
        "container_title": container_title,
        "citation_key": citation_key,
        "date": date_raw,
        "year": year,
        "doi": nullable(data.get("DOI")),
        "url": nullable(data.get("url")),
        "issn": nullable(data.get("ISSN")),
        "isbn": nullable(data.get("ISBN")),
        "issue": nullable(data.get("issue")),
        "publisher": nullable(data.get("publisher")),
        "language": nullable(data.get("language")),
        "creators": creators,
        "primary_authors": primary_authors,
        "authors_short": authors_short,
        "tags": tags,
        "collections": collections,
        "date_modified": data.get("dateModified", ""),
    }


# ──────────────────────────────────────────────────────────────────────
# 渲染 paperinfo 节点
# ──────────────────────────────────────────────────────────────────────

def yaml_escape(s: str) -> str:
    if not s:
        return '""'
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def yaml_list(items: list[str]) -> str:
    return ", ".join(yaml_escape(x) for x in items)


def render_paperinfo(n: dict) -> str:
    """生成 paperinfo 节点 markdown content (含 frontmatter + body)。

    输出文件命名 = BBT citekey.md (人类可读 + 唯一)。
    """
    primary = n["primary_authors"]
    authors_yaml = ", ".join(yaml_escape(a["full_name"]) for a in primary)

    pub = n["container_title"] or ""
    citation_key = n["citation_key"] or ""
    issn_line = f"ISSN: {n['issn']}\n" if n["issn"] else ""
    isbn_line = f"ISBN: {n['isbn']}\n" if n["isbn"] else ""

    fm_lines = [
        "# 身份 / 同步 (scripts 维护, 不要手动改)",
        f"type: paperinfo",
        f"schema_version: plan_final_v1",
        f"citekey: {citation_key or '(无)'}",
        f"zotero-key: {n['indexed_key']}",
        f"zotero-link: zotero://select/library/items/{n['key']}",
        f"zotero-lastmod: {n['date_modified']}",
        "",
        "# 标题",
        f'title: "{n["title"] or "(无标题)"}"',
        "",
        "# 作者",
        f"authors: [{authors_yaml}]",
        f"first-author: {primary[0]['family'] if primary and primary[0]['family'] else (primary[0]['full_name'] if primary else '')}",
        f"authors-short: {n.get('authors_short', '')}",
        "",
        "# 出版",
        f"year: {n['year'] or ''}",
        f"publication: {yaml_escape(pub)}",
        f"language: {n['language'] or ''}",
        "",
        "# 标识符",
        f"DOI: {n['doi'] or ''}",
        f"{issn_line}{isbn_line}URL: {n['url'] or ''}",
        "",
        "# 摘要 (Zotero 导入, 71% 填充)",
        f"abstract: |",
        f"  {n['abstract'] or '(Zotero 中未维护 - 待 LLM 从 PDF 抽取)'}",
        "",
        "# 分类",
        f"zotero-collections: [{yaml_list(n['collections'])}]",
        f"zotero-tags: [{yaml_list(n['tags'])}]",
    ]
    fm = "---\n" + "\n".join(fm_lines) + "\n---\n"

    # Body
    first_author = primary[0]["family"] if primary and primary[0]["family"] else (primary[0]["full_name"] if primary else "(未知)")
    author_count = len(primary)

    authors_list = "\n".join(
        f"- {a['full_name']}" if a["type"] == "person" else f"- {a['full_name']} (organisation)"
        for a in primary
    ) or "- (无作者)"

    body = f"""# {n['title'] or '(无标题)'}

> **Zotero 链接**: [打开](zotero://select/library/items/{n['key']})
> **DOI**: {f'[{n["doi"]}](https://doi.org/{n["doi"]})' if n['doi'] else '无'}
> **引用键**: `{citation_key}`

## 元信息

| 字段 | 值 |
|------|-----|
| 作者 | {first_author} |
| 年份 | {n['year']} |
| 期刊 | {pub or '(未指定)'} |
| DOI | {n['doi'] or '(无)'} |
| 语言 | {n['language'] or ''} |
| Library Key | `{n['indexed_key']}` |

## 摘要

{n['abstract'] or '(Zotero 中未维护 - 待 LLM 从 PDF 抽取)'}

## Authors

{authors_list}

## Collections

{chr(10).join(f'- `{c}`' for c in n['collections']) or '- (无)'}

## Tags

{chr(10).join(f'- `{t}`' for t in n['tags']) or '- (无)'}

<!-- paperinfo 节点只放 L1 元数据。LLM 抽取 L2/L3 字段请在 papers/ 节点。 -->
"""
    return fm + "\n" + body


def safe_filename(citekey: str) -> str:
    """用 BBT citekey 做文件名, 清理末尾下划线。"""
    if not citekey:
        return "untitled.md"
    s = re.sub(r'_+', '_', citekey).rstrip('_')
    safe_chars = " -_.,()[]{}"
    s = "".join(c for c in s if c.isalnum() or c in safe_chars).strip()
    s = s.replace(" ", "_") or "untitled"
    return s[:200] + ".md"


# ──────────────────────────────────────────────────────────────────────
# 增量同步指纹
# ──────────────────────────────────────────────────────────────────────

def should_write_paperinfo(out_path: Path, date_modified: str, force: bool = False) -> tuple[bool, str]:
    if force:
        return True, "force"
    if not out_path.exists():
        return True, "new"
    text = out_path.read_text(encoding="utf-8")
    m = re.search(r"^zotero-lastmod:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return True, "no-fingerprint"
    if m.group(1).strip() != date_modified:
        return True, "modified"
    return False, "unchanged"


# ──────────────────────────────────────────────────────────────────────
# 子命令 1: zotero-list
# ──────────────────────────────────────────────────────────────────────

def cmd_list(args, wiki_root: Path) -> int:
    zot = get_zotero_local()
    cols = []
    start = 0
    while True:
        batch = zot.collections(start=start, limit=100)
        if not batch:
            break
        cols.extend(batch)
        if len(batch) < 100:
            break
        start += 100

    print(f"=== Zotero collections (共 {len(cols)}) ===\n")
    for c in cols:
        name = c["data"].get("name", "")
        key = c["data"]["key"]
        parent = c["data"].get("parentCollection", False)
        indent = "  " if parent else ""
        # 统计主条目
        try:
            items = zot.collection_items(key, limit=500)
            primary = [it for it in items if it["data"].get("itemType") not in ("attachment", "note", "annotation")]
            count = len(primary)
        except Exception:
            count = "?"
        print(f"{indent}{name:40s}  key={key:12s}  items={count}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# 子命令 2: zotero-pull
# ──────────────────────────────────────────────────────────────────────

def cmd_pull(args, wiki_root: Path) -> int:
    zot = get_zotero_local()
    out_dir = wiki_root / "paperinfo"
    out_dir.mkdir(parents=True, exist_ok=True)

    if getattr(args, "all_items", False):
        print(f"=== 拉取 Zotero 全部顶层条目 (--all) ===")
        all_items = []
        start = 0
        while True:
            batch = zot.all_top()
            # all_top 不支持分页, 但 limit 通常足够
            break
        all_items = batch or []
    else:
        print(f"=== 拉取 collection {args.collection} 的全部主条目 ===")
        all_items = []
        start = 0
        while True:
            batch = zot.collection_items(args.collection, start=start, limit=100)
            if not batch:
                break
            all_items.extend(batch)
            if len(batch) < 100:
                break
            start += 100

    parents = [it for it in all_items
               if it["data"].get("itemType") not in ("attachment", "note", "annotation")]
    if args.types:
        allowed = set(args.types.split(","))
        parents = [it for it in parents if it["data"].get("itemType") in allowed]

    print(f"  collection 总条目: {len(all_items)}")
    print(f"  主条目: {len(parents)}")

    if args.limit:
        parents = parents[:args.limit]
        print(f"  限制: {args.limit}")

    stats = {"new": 0, "modified": 0, "unchanged": 0, "failed": 0}
    for i, item in enumerate(parents, 1):
        try:
            n = normalize_item(item, zot)
            ck = n["citation_key"] or ""
            if not ck:
                stats["failed"] += 1
                print(f"  [{i:3d}] ✗ {n['key']}: 无 BBT citekey", file=sys.stderr)
                continue
            filename = safe_filename(ck)
            out_path = out_dir / filename
            should, reason = should_write_paperinfo(out_path, n["date_modified"], force=args.force)

            if not should:
                stats["unchanged"] += 1
                if args.verbose:
                    print(f"  [{i:3d}] {filename:50s}  skip ({reason})")
                continue

            content = render_paperinfo(n)
            if args.dry_run:
                stats["new" if reason == "new" else "modified"] += 1
                print(f"  [{i:3d}] {filename:50s}  would-write ({reason})")
            else:
                out_path.write_text(content, encoding="utf-8")
                stats["new" if reason == "new" else "modified"] += 1
                print(f"  [{i:3d}] {filename:50s}  {reason}")
        except Exception as e:
            stats["failed"] += 1
            print(f"  [{i:3d}] ✗ {item['data'].get('key', '?')}: {e}", file=sys.stderr)

    print(f"\n=== 统计 ===")
    print(f"  新建: {stats['new']}")
    print(f"  更新: {stats['modified']}")
    print(f"  跳过: {stats['unchanged']}")
    print(f"  失败: {stats['failed']}")
    print(f"  输出: {out_dir}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# 子命令 7: zotero-extract (单篇拉取)
# ──────────────────────────────────────────────────────────────────────

def cmd_extract(args, wiki_root: Path) -> int:
    """按 zotero-key 单篇拉取并写 paperinfo/<BBT citekey>.md。
    适用于:某篇论文不在 collection 里,需要手动补齐。
    """
    from pyzotero import Zotero  # noqa: F811  (与 get_zotero_local 同模块)

    zot = get_zotero_local()
    out_dir = wiki_root / "paperinfo"
    out_dir.mkdir(parents=True, exist_ok=True)

    zotero_key = args.zotero_key
    try:
        item = zot.item(zotero_key)
    except KeyError:
        wc.die(f"Zotero item {zotero_key} 不存在")

    n = normalize_item(item, zot)
    bbt_ck = n["citation_key"] or ""

    # ⚠️ attachment 检测(ARCHITECTURE §15.4.4): 防止误用 PDF attachment key
    # Zotero 中 attachment / note / annotation 不含 paper 元数据
    if n.get("item_type") in ("attachment", "note", "annotation"):
        wc.die(
            f"❌ zotero-key {zotero_key} 是 '{n['item_type']}' 类型,不是 paper 节点。\n"
            f"   请用 parent paper 的 zotero-key,不是 attachment key。\n"
            f"   查询方法:在 Zotero 桌面版右键 PDF 附件 → 'Show Parent Item' → 复制 paper 的 key"
        )

    # Wiki 侧 citekey 优先用 --citekey,否则用 Zotero BBT citekey
    wiki_ck = getattr(args, "citekey", None) or bbt_ck
    if not wiki_ck:
        wc.die(f"Zotero item {zotero_key} 无 BBT citekey (在 Zotero Better BibTeX 中未设置)")

    # 用 wiki citekey 作为文件名 + frontmatter citekey
    n["citation_key"] = wiki_ck
    n["bbt_citekey"] = bbt_ck  # 保留 BBT 在 frontmatter 作为 bbt-citekey 字段

    filename = safe_filename(wiki_ck)
    out_path = out_dir / filename
    should, reason = should_write_paperinfo(out_path, n["date_modified"], force=args.force)

    if not should:
        print(f"  ✗ skip ({reason})")
        if args.force:
            print(f"  --force 已指定,覆盖之")
        else:
            return 0

    content = render_paperinfo(n)
    if args.dry_run:
        print(f"  [dry-run] would write {filename} ({reason})")
    else:
        out_path.write_text(content, encoding="utf-8")
        print(f"  ✓ {filename}  {reason}")

    if args.verbose:
        print(f"\n  title: {n['title']}")
        print(f"  authors: {len(n['primary_authors'])}")
        print(f"  year: {n['year']}")
        print(f"  DOI: {n['doi']}")
        zotero_link = f"zotero://select/library/items/{n['key']}"
        print(f"  zotero-link: {zotero_link}")
    return 0


# ──────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────

def cmd_sync(args, wiki_root: Path) -> int:
    args.force = False  # sync 永远不强制
    return cmd_pull(args, wiki_root)


# ──────────────────────────────────────────────────────────────────────
# 子命令 4: zotero-stats
# ──────────────────────────────────────────────────────────────────────

def cmd_stats(args, wiki_root: Path) -> int:
    paperinfo_dir = wiki_root / "paperinfo"
    papers_dir = wiki_root / "papers"

    pi_count = len(list(paperinfo_dir.glob("*.md"))) if paperinfo_dir.is_dir() else 0
    pa_count = len(list(papers_dir.glob("*.md"))) if papers_dir.is_dir() else 0

    # 统计 paper 里有 zotero-key 的
    zk_count = 0
    if papers_dir.is_dir():
        for p in papers_dir.glob("*.md"):
            fm, _ = wc.parse_frontmatter(p.read_text(encoding="utf-8"))
            if fm.get("zotero-key"):
                zk_count += 1

    # 统计 paperinfo 里有 paper 反向链接的
    pi_with_paper = 0
    if paperinfo_dir.is_dir():
        for p in paperinfo_dir.glob("*.md"):
            text = p.read_text(encoding="utf-8")
            if "paperinfo" in text or "papers/" in text:
                pi_with_paper += 1

    print(f"=== Wiki × Zotero 对齐统计 ===\n")
    print(f"  paperinfo/{pi_count} 篇")
    print(f"  papers/   {pa_count} 篇")
    print(f"  其中 papers/ 有 zotero-key: {zk_count}/{pa_count}")
    print(f"  paperinfo 有 paper 反向链接: {pi_with_paper}/{pi_count}")

    # 缺漏
    if papers_dir.is_dir():
        missing = []
        for p in papers_dir.glob("*.md"):
            fm, _ = wc.parse_frontmatter(p.read_text(encoding="utf-8"))
            if not fm.get("zotero-key"):
                missing.append(p.name)
        if missing:
            print(f"\n  缺 zotero-key 的 paper:")
            for m in missing[:10]:
                print(f"    - {m}")
            if len(missing) > 10:
                print(f"    ... 还有 {len(missing) - 10} 篇")
    return 0


# ──────────────────────────────────────────────────────────────────────
# 子命令 5: zotero-match (给 paper 找 paperinfo)
# ──────────────────────────────────────────────────────────────────────

def cmd_match(args, wiki_root: Path) -> int:
    """给 paper 找匹配 paperinfo:
       1. 先用 BBT citekey (paper.md frontmatter 里)
       2. fallback: 用 title + author + year 模糊匹配
    """
    zot = get_zotero_local()
    paper_path = Path(args.paper)
    if not paper_path.is_file():
        wc.die(f"找不到 paper: {paper_path}")
    text = paper_path.read_text(encoding="utf-8")
    fm, _ = wc.parse_frontmatter(text)

    # 试 1: paperinfo 字段直接给了
    pi_field = fm.get("paperinfo", "")
    if pi_field:
        m = re.search(r"\[\[paperinfo/([^\]|]+)", pi_field)
        if m:
            pi_name = m.group(1).strip()
            pi_path = wiki_root / "paperinfo" / f"{pi_name}.md"
            if pi_path.is_file():
                wc.ok(f"✓ paperinfo 字段已指向: {pi_path}")
                return 0

    # 试 2: 用 description 里的 BBT citekey
    description = fm.get("description", "")
    citekey_candidate = None
    # zotero-md 风格的文件名: <FirstAuthor>_<Year>_<keyword>.md
    # 或 BBT citekey 风格: <author>_<year>_<journal>
    name = paper_path.stem
    # 找原始 paperinfo
    paperinfo_dir = wiki_root / "paperinfo"
    if paperinfo_dir.is_dir():
        # 试 1: 精确匹配
        for pi in paperinfo_dir.glob("*.md"):
            pi_fm, _ = wc.parse_frontmatter(pi.read_text(encoding="utf-8"))
            if pi_fm.get("citekey") and pi_fm.get("citekey").lower() == name.lower():
                wc.ok(f"✓ 精确匹配: {pi.name}")
                return 0
        # 试 2: title 模糊匹配
        title = fm.get("title", "")
        if title:
            for pi in paperinfo_dir.glob("*.md"):
                pi_text = pi.read_text(encoding="utf-8")
                pi_fm, _ = wc.parse_frontmatter(pi_text)
                pi_title = pi_fm.get("title", "")
                # 简化的相似度: 标题前 30 字
                if pi_title and title[:30].lower() == pi_title[:30].lower():
                    wc.ok(f"✓ 标题匹配: {pi.name}")
                    wc.eprint(f"  paper title:  {title}")
                    wc.eprint(f"  paperinfo:    {pi_title}")
                    return 0

    wc.eprint(f"✗ 未找到匹配 paperinfo")
    wc.eprint(f"  建议: 跑 `wiki zotero-pull --collection <name>` 补全")
    return 1


# ──────────────────────────────────────────────────────────────────────
# 子命令 6: zotero-backfill (给现有 paper 补 zotero-key)
# ──────────────────────────────────────────────────────────────────────

def cmd_backfill(args, wiki_root: Path) -> int:
    """扫描 papers/, 给没 zotero-key 的 paper 补 zotero-key 字段。

    匹配策略:
      1. 用 paper 文件名作为 BBT citekey 候选
      2. 在 Zotero 找 BBT citekey 精确匹配
      3. 找到 → 补 zotero-key, zotero-link, dateAdded 等
    """
    zot = get_zotero_local()
    papers_dir = wiki_root / "papers"
    paperinfo_dir = wiki_root / "paperinfo"
    paperinfo_dir.mkdir(parents=True, exist_ok=True)

    if not papers_dir.is_dir():
        wc.die(f"找不到 {papers_dir}")

    # 缓存 zotero items
    print(f"=== 加载 Zotero 数据 ===")
    items = zot.all_top()
    zk_to_item = {}
    for it in items:
        ck = it["data"].get("citationKey", "")
        if ck:
            zk_to_item[ck] = it
    print(f"  Zotero items 有 citekey: {len(zk_to_item)}")

    papers = sorted(papers_dir.glob("*.md"))
    print(f"  现有 papers: {len(papers)}")

    stats = {"matched": 0, "skipped": 0, "no-zk": 0}
    for i, p in enumerate(papers, 1):
        fm, body = wc.parse_frontmatter(p.read_text(encoding="utf-8"))

        if fm.get("zotero-key"):
            stats["skipped"] += 1
            continue

        # 候选 citekey
        candidates = [p.stem]
        # 试 description 字段
        desc = fm.get("description", "")
        # 也试 paper 文件名首字母大写化

        matched_item = None
        matched_ck = None

        # 阶段 1: 精确 / 模糊匹配 citekey
        for cand in candidates:
            if cand in zk_to_item:
                matched_item = zk_to_item[cand]
                matched_ck = cand
                break
            for ck in zk_to_item:
                if ck.lower() == cand.lower():
                    matched_item = zk_to_item[ck]
                    matched_ck = ck
                    break
            if matched_item:
                break

        # 阶段 2: title 模糊匹配 (适用于 Claude 风格命名)
        if not matched_item:
            title = fm.get("title") or fm.get("description", "")
            if title:
                # 抽 title 连续 25+ 字符子串到 Zotero 查
                title_short = title[:25].lower().strip()
                if title_short:
                    for ck, it in zk_to_item.items():
                        item_title = (it["data"].get("title") or "").lower()
                        if title_short in item_title:
                            matched_item = it
                            matched_ck = ck
                            break

        if not matched_item:
            stats["no-zk"] += 1
            if args.verbose:
                wc.eprint(f"  [{i:3d}] ✗ {p.name}: 无匹配 citekey")
            continue

        # 补 frontmatter
        n = normalize_item(matched_item, zot)
        fm["citekey"] = n["citation_key"] or matched_ck
        fm["zotero-key"] = n["indexed_key"]
        fm["zotero-link"] = f"zotero://select/library/items/{n['key']}"
        fm["zotero-lastmod"] = n["date_modified"]

        # 写回
        new_text = wc.write_frontmatter(fm, body)
        if args.dry_run:
            print(f"  [{i:3d}] would-write: {p.name} (citekey={matched_ck})")
        else:
            p.write_text(new_text, encoding="utf-8")
            print(f"  [{i:3d}] backfilled: {p.name} (citekey={matched_ck})")

        # 如果 paperinfo 还不存在, 顺便生成
        pi_filename = safe_filename(matched_ck)
        pi_path = paperinfo_dir / pi_filename
        if not pi_path.exists():
            content = render_paperinfo(n)
            if not args.dry_run:
                pi_path.write_text(content, encoding="utf-8")
            print(f"           + created paperinfo/{pi_filename}")

        # 重命名 paper 文件名为 BBT citekey (可选)
        if p.name != pi_filename and not args.dry_run:
            new_path = p.parent / pi_filename
            if not new_path.exists():
                p.rename(new_path)
                print(f"           renamed: {p.name} → {pi_filename}")

        stats["matched"] += 1

    print(f"\n=== 统计 ===")
    print(f"  匹配补全: {stats['matched']}")
    print(f"  跳过(已有): {stats['skipped']}")
    print(f"  未匹配: {stats['no-zk']}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evidence Wiki × Zotero 双向同步",
        usage="wiki zotero <subcommand> [args...]",
    )
    sub = parser.add_subparsers(dest="subcommand")

    p_list = sub.add_parser("list", help="列出所有 Zotero collection")
    p_list.add_argument("--wiki-root", help="wiki 根目录")

    p_pull = sub.add_parser("pull", help="按 collection 一次性生成 paperinfo")
    p_pull.add_argument("--collection", "-c", default="XRIVDICN", help="Collection key")
    p_pull.add_argument("--wiki-root", help="wiki 根目录")
    p_pull.add_argument("--limit", type=int, default=0)
    p_pull.add_argument("--force", action="store_true")
    p_pull.add_argument("--dry-run", action="store_true")
    p_pull.add_argument("--verbose", "-v", action="store_true")
    p_pull.add_argument("--types", default="journalArticle,preprint,conferencePaper,book,bookSection,blogPost")
    p_pull.add_argument("--all", dest="all_items", action="store_true",
                        help="拉取 Zotero 全部顶层 items (不在 collection 里的新加条目也能捕获)")

    p_sync = sub.add_parser("sync", help="增量同步 (zotero-lastmod 指纹)")
    p_sync.add_argument("--collection", "-c", default="XRIVDICN")
    p_sync.add_argument("--wiki-root", help="wiki 根目录")
    p_sync.add_argument("--limit", type=int, default=0)
    p_sync.add_argument("--dry-run", action="store_true")
    p_sync.add_argument("--verbose", "-v", action="store_true")
    p_sync.add_argument("--types", default="journalArticle,preprint,conferencePaper,book,bookSection,blogPost")

    p_stats = sub.add_parser("stats", help="统计对齐")
    p_stats.add_argument("--wiki-root", help="wiki 根目录")

    p_match = sub.add_parser("match", help="给 paper 找 paperinfo")
    p_match.add_argument("paper", help="paper 文件路径")
    p_match.add_argument("--wiki-root", help="wiki 根目录")

    p_backfill = sub.add_parser("backfill", help="现有 paper 补 zotero-key")
    p_backfill.add_argument("--wiki-root", help="wiki 根目录")
    p_backfill.add_argument("--dry-run", action="store_true")
    p_backfill.add_argument("--verbose", "-v", action="store_true")

    p_extract = sub.add_parser("extract", help="单篇抽取: 按 zotero-key 拉取并写 paperinfo")
    p_extract.add_argument("--zotero-key", required=True, help="Zotero item key(8 字符串)")
    p_extract.add_argument("--citekey", help="Wiki 侧 citekey(默认 = Zotero BBT citekey;用 ARCHITECTURE §2.3 语义命名覆盖)")
    p_extract.add_argument("--wiki-root", help="wiki 根目录")
    p_extract.add_argument("--force", action="store_true", help="覆盖已存在的 paperinfo")
    p_extract.add_argument("--dry-run", action="store_true")
    p_extract.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        return 1

    wiki_root = Path(args.wiki_root) if args.wiki_root else wc.find_wiki_root()

    if args.subcommand == "list":
        return cmd_list(args, wiki_root)
    if args.subcommand == "pull":
        return cmd_pull(args, wiki_root)
    if args.subcommand == "sync":
        return cmd_sync(args, wiki_root)
    if args.subcommand == "stats":
        return cmd_stats(args, wiki_root)
    if args.subcommand == "match":
        return cmd_match(args, wiki_root)
    if args.subcommand == "backfill":
        return cmd_backfill(args, wiki_root)
    if args.subcommand == "extract":
        return cmd_extract(args, wiki_root)
    wc.die(f"Unknown subcommand: {args.subcommand}")
    return 1


def run(argv: list[str]) -> int:
    """统一 CLI 入口: `wiki zotero <subcommand>`"""
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.argv = ["wiki_zotero", "--help"]
        return main()
    sub = argv[0]
    rest = argv[1:]
    # 把 `zotero <sub> ...` 转给 main
    sys.argv = ["wiki_zotero", sub] + rest
    return main()


if __name__ == "__main__":
    sys.exit(main())
