#!/usr/bin/env python3
"""
wiki_common.py — Evidence Wiki Skill 共享工具

所有 wiki_* 脚本都依赖此模块。
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional


# === 路径解析 ===

def find_wiki_root(start: Optional[Path] = None) -> Path:
    """
    从 start（默认 cwd）向上找含 AGENTS.md 的目录作为 wiki root。

    优先匹配含 ``papers/`` 数据目录的祖先（真正的 wiki root）；
    找不到才回退到最近的 AGENTS.md（兼容孤立 skill 仓库或迁移中状态）；
    最后兜底返回 cwd。

    变更动机（2026-08-21）: skill 仓库迁入 wiki root 的 .skill/ 子目录后，
    .skill/AGENTS.md 是 skill **开发者文档**，不是给 pi 的操作规范。
    原"向上找 AGENTS.md"会先匹配 .skill/AGENTS.md，错过真正的 wiki root。
    现在以"含 papers/ 数据目录"为权威标志，避免混淆。
    """
    cur = (start or Path.cwd()).resolve()

    # 第一遍：含 papers/ 数据目录 = 真正的 wiki root
    for parent in [cur, *cur.parents]:
        if (parent / "papers").is_dir() and (parent / "AGENTS.md").is_file():
            return parent

    # 第二遍：任何含 AGENTS.md 的（兜底，兼容 skill 仓库或迁移中）
    for parent in [cur, *cur.parents]:
        if (parent / "AGENTS.md").is_file():
            return parent

    return cur


def papers_dir(wiki_root: Path) -> Path:
    return wiki_root / "papers"


def topics_dir(wiki_root: Path) -> Path:
    return wiki_root / "topics"


def claims_dir(wiki_root: Path) -> Path:
    return wiki_root / "claims"


def syntheses_dir(wiki_root: Path) -> Path:
    return wiki_root / "syntheses"


def pending_dir(wiki_root: Path) -> Path:
    return wiki_root / "00-pending"


def index_file(wiki_root: Path) -> Path:
    return wiki_root / "index.md"


def log_file(wiki_root: Path) -> Path:
    return wiki_root / "log" / "ops.md"


# === Frontmatter 解析（极简 YAML 子集） ===

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    解析极简 YAML frontmatter（key: value 格式）。
    返回 (frontmatter_dict, body_str)。
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    fm_text, body = m.group(1), m.group(2)
    fm: dict = {}

    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # 去掉引号
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        # 列表 [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            items = [x.strip().strip("\"'") for x in value[1:-1].split(",") if x.strip()]
            fm[key] = items
        else:
            fm[key] = value

    return fm, body


def write_frontmatter(fm: dict, body: str) -> str:
    """构造带 frontmatter 的 markdown 文本。"""
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
    return "\n".join(lines) + "\n"


def _flatten_yaml_value(v):
    """拍平 YAML round-trip 产生的嵌套列表([['x']] → 'x';[a, ['b']] → [a, 'b'])。"""
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, list):
                inner = _flatten_yaml_value(x)
                out.extend(inner if isinstance(inner, list) else [inner])
            else:
                out.append(x)
        return out
    return v


def _quote_yaml_scalar(s: str) -> str:
    """给 YAML 标量加安全引号:纯 ASCII 词字符(alnum/_-/.)不加引号,
    其余(含 [[wikilink]]、冒号、井号、空格、中文)一律双引号——
    否则写回后会被下次解析成嵌套列表或注释(2026-08-25 papers 损坏事故根因)。"""
    s = str(s)
    if _is_plain_safe(s):
        return s
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _is_plain_safe(s: str) -> bool:
    """纯 ASCII 词字符(alnum/_-/.)且**不会被 YAML 隐式解析成数字/布尔/日期**才免引号。
    (2026-08-25 教训:日期形字符串不加引号 → yaml 读回 date 对象 → schema 报错死循环)"""
    if not s or not all(c.isascii() and (c.isalnum() or c in "_-.") for c in s):
        return False
    import re as _re
    if _re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", s):
        return False
    if s.lower() in ("true", "false", "null", "yes", "no", "on", "off", "~"):
        return False
    if _re.fullmatch(r"\d{4}-\d{2}-\d{2}([T ].*)?", s):
        return False
    return True


def dump_frontmatter_safe(fm: dict, body: str = "") -> str:
    """
    安全 frontmatter 序列化(批次修复 2026-08-25):
      1. 自动拍平嵌套列表(YAML round-trip 损坏防御)
      2. wikilink([[x]])与含特殊字符的标量强制双引号(防再次解析成嵌套/注释)
      3. 列表用 flow 格式但每项带引号(防中文/空格项粘连)
    所有需要写 frontmatter 的脚本应使用本函数,不要手拼。
    """
    lines = ["---"]
    for k, v in fm.items():
        v = _flatten_yaml_value(v)
        if isinstance(v, list):
            items = ", ".join("null" if x is None else _quote_yaml_scalar(x) for x in v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, float):
            # e 记数法必须带小数点(YAML 1.1: '1e-20' 读回 str,'1.0e-20' 才是 float)
            s = repr(v)
            mant, _, exp = s.lower().partition("e")
            if exp and "." not in mant:
                s = f"{v:.1e}"
            lines.append(f"{k}: {s}")
        elif isinstance(v, int):
            lines.append(f"{k}: {v}")
        elif isinstance(v, dict):
            # 浅层 dict(如 field_status.mode)单行 flow 映射,schema 要求 object;
            # 深层嵌套才退化为拍平字符串
            items, ok = [], True
            for dk, dv in v.items():
                if isinstance(dv, (dict, list)) or not isinstance(dv, (str, int, float, bool, type(None))):
                    ok = False
                    break
                if isinstance(dv, bool):
                    sv = "true" if dv else "false"
                elif isinstance(dv, float):
                    sv = repr(dv)
                    mant, _, exp = sv.lower().partition("e")
                    if exp and "." not in mant:
                        sv = f"{dv:.1e}"
                elif dv is None:
                    sv = "null"
                elif isinstance(dv, int):
                    sv = str(dv)
                else:
                    sv = _quote_yaml_scalar(str(dv))
                dk_s = str(dk) if _is_plain_safe(str(dk)) else _quote_yaml_scalar(str(dk))
                items.append(f"{dk_s}: {sv}")
            if ok:
                lines.append(f"{k}: {{{', '.join(items)}}}")
            else:
                lines.append(f"{k}: {_quote_yaml_scalar(v)}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {_quote_yaml_scalar(v)}")
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
    return "\n".join(lines) + "\n"


# === 文件读写 ===

def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# === Wikilink 提取 ===

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def extract_wikilinks(text: str) -> list[str]:
    """从 markdown body 中提取 [[wikilink]] 列表。"""
    return list(set(_WIKILINK_RE.findall(text)))


# === Section 锚点提取 ===

_SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def extract_sections(text: str) -> list[tuple[str, int]]:
    """
    提取 markdown 章节（标题 + 行号）。
    返回 [(title, line_number), ...]
    """
    sections = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _SECTION_RE.match(line)
        if m:
            sections.append((m.group(1).strip(), i))
    return sections


# === 数值抽取 ===

_NUM_RE = re.compile(
    r"""
    (?<![\w.])                   # 前面不是字母或点
    \d+\.?\d*                    # 整数或小数
    (?:[eE][+-]?\d+)?           # 科学计数法
    (?![\w.])                    # 后面不是字母或点
    """,
    re.VERBOSE,
)


def extract_numbers(text: str) -> list[str]:
    """从文本中抽取候选数值（用于 grep 校验）。"""
    return _NUM_RE.findall(text)


# === CLI 工具 ===

def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def die(msg: str, code: int = 1) -> None:
    eprint(f"✗ {msg}")
    sys.exit(code)


def ok(msg: str) -> None:
    print(f"✓ {msg}")


# === 子命令分派（统一 CLI 用） ===

def dispatch(argv: list[str]) -> int:
    """
    统一 wiki CLI 入口。子命令：
        init, ingest, lint, search, status, index, archive
    """
    if not argv:
        print_help()
        return 1

    cmd = argv[0]
    rest = argv[1:]

    if cmd in ("-h", "--help", "help"):
        print_help()
        return 0

    try:
        if cmd == "init":
            from wiki_init import run
            return run(rest)
        if cmd == "ingest":
            from wiki_ingest import run
            return run(rest)
        if cmd == "lint":
            from wiki_lint import run
            return run(rest)
        if cmd == "search":
            from wiki_search import run
            return run(rest)
        if cmd == "status":
            from wiki_status import run
            return run(rest)
        if cmd == "index":
            from wiki_index import run
            return run(rest)
        if cmd == "archive":
            from wiki_archive import run
            return run(rest)
        if cmd == "promote":
            import wiki_promote
            sys.argv = ["wiki_promote"] + sys.argv[2:]
            sys.exit(wiki_promote.main())
        if cmd == "check-evidence":
            from wiki_check_evidence import run
            return run(rest)
        if cmd == "zotero":
            from wiki_zotero import run
            return run(rest)
        if cmd == "zotero-csv":
            from wiki_zotero_csv import run
            return run(rest)
        if cmd == "sync-raw":
            from sync_raw import run
            return run(rest)
        if cmd == "pdf2md":
            from wiki_pdf_to_md import run
            return run(rest)
        die(f"Unknown subcommand: {cmd}. Run 'wiki help' for usage.")
        return 1  # unreachable, but explicit
    except ImportError as e:
        die(f"Subcommand module not available: {e}")
        return 1


def print_help() -> None:
    print("""Usage: wiki <subcommand> [args...]

Evidence Wiki Skill — unified CLI.

Subcommands:
  init                    Initialize wiki directories (AGENTS.md + index.md + log.md)
  ingest <paper-path>     6-stage ingestion (place paper in 00-pending/)
  lint                    4-layer lint (structure / evidence / semantic / consistency)
  check-evidence <paper>  Verify numbers/quotes are grep-able in raw full.md
  search <query>           Cross-paper search
  status                  Show wiki status (paper/claim/topic counts)
  index                   Rebuild index.md
  archive <page>           Archive outdated page (set status: archived)
  zotero <sub>             Zotero sync (list/pull/sync/stats/match/backfill)
  zotero-csv <sub>         Bulk import from CSV (csv-import/csv-status)
  sync-raw [--force]        Sync Zotero raw (full.md + images/) to wiki/raw/<citekey>/
  pdf2md <pdf> [--citekey <ck>]  PDF → MinerU → raw/<ck>/ or raw/_incoming/ (S0a)

Run 'wiki <subcommand> --help' for subcommand-specific help.

Setup:
  This CLI lives in evidence-wiki-skill/scripts/.
  Run ./install.sh to symlink as 'wiki' command.""")


if __name__ == "__main__":
    sys.exit(dispatch(sys.argv[1:]))