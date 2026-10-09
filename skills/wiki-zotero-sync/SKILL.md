---
name: wiki-zotero-sync
description: >-
  Sync Zotero library to wiki's paperinfo/ directory. Pull creates new
  paperinfo nodes from Zotero collection; sync incrementally updates existing
  nodes by zotero-lastmod fingerprint. Scripts read Zotero local SQLite
  (~/Zotero/zotero.sqlite), no network. Use when user says "/sync" or
  "zotero 同步".
---

# Wiki Zotero Sync

Zotero 库同步到 wiki的 `paperinfo/` 节点。

## 何时使用

- 用户说:`/sync` / `zotero 同步` / `拉取 Zotero paperinfo`
- 添加新论文后(增量)
- 每月一次(全量)

## 工作流

### 1. 拉取(Pull,全量)

```bash
# 从 Zotero collection 拉取所有 paperinfo
python3 .skill/scripts/wiki_zotero.py pull --collection "fNIRS"
```

输入:
- `--collection`:Zotero collection 名称(如 "fNIRS"、"孪生脑")

输出:
- `paperinfo/<BBT-citekey>.md` 全部生成

### 2. 同步(Sync,增量)

```bash
# 只更新 zotero-lastmod 变化的
python3 .skill/scripts/wiki_zotero.py sync --collection "fNIRS"
```

输入:
- 同样的 collection
- 用 `zotero-lastmod` 字段做指纹

输出:
- 新增:`paperinfo/<new-citekey>.md`
- 更新:`paperinfo/<changed-citekey>.md`
- 不动:已存在且 lastmod 未变的

### 3. 论文身份信息(Source of Truth)

paperinfo 节点是**论文身份信息**的唯一源(ARCHITECTURE §3.1):
- `citekey` (BBT citekey,唯一标识)
- `zotero-key` (Zotero item key)
- `title` / `authors` / `year` / `DOI`
- `zotero-collections` / `zotero-tags`

scripts 维护,不手动改。

## BBT citekey

Better BibTeX(Zotero 插件)自动生成的 citekey:
- 例:`zhang_2021_fnirs` / `smith_2020_wm_reading`
- 用作 paperinfo 文件名 + paper 节点文件名
- 文件名 = wikilink 唯一地址

## 数据流

```
Zotero SQLite (~/Zotero/zotero.sqlite)
   ↓
scripts 读 + 解析 BBT citekey
   ↓
生成 paperinfo/<citekey>.md(frontmatter + abstract)
   ↓
LLM 抽取 paper + claim + evidence(读 raw/<citekey>/full.md)
   ↓
paper.md 含 `paperinfo: "[[paperinfo/<citekey>]]"` 强制 link
```

## 边界

- **不**修改 Zotero / MinerU 原始层(ARCHITECTURE §1.2 铁律 1)
- **不**修改 LLM 已抽取的 paper 节点
- 只写 `paperinfo/` 目录
- scripts 用 Zotero local SQLite,不需要联网

## 关联

- paperinfo 节点 schema:`ARCHITECTURE.md §3.1`
- 节点强制 link:`ARCHITECTURE.md §3.2`(paper.md 必含 `paperinfo: "[[...]]"`)
- 备份:`~/.pi/agent/memory/`(Zotero 操作日志)

## Resources

- `ARCHITECTURE.md §3.1` Paperinfo 节点 schema
- `wiki zotero pull`(wiki_zotero.py)
- `wiki zotero sync`(wiki_zotero.py,按 zotero-lastmod 指纹增量)
- `~/Zotero/zotero.sqlite` Zotero 数据库
- Zotero Better BibTeX 插件(自动生成 citekey)