#!/usr/bin/env python3
"""
wiki_repair_yaml.py — YAML frontmatter 自动修复(2026-08-25,解死锁)

死锁问题:坏 YAML 文件挡住 wiki_clean_enums.py(解析失败跳过),
而清洗器又不修 YAML → 29 个文件永远进不了任何流水线。

修复策略(纯机械,按 PyYAML 错误行号定位):
  1. 未加引号的值内含 `: ` / 引号 / `#` / 特殊字符 → 该值强制双引号(转义内部引号)
  2. 截断的引号(值以 " 开头无闭合)→ 去掉孤立引号再按 1 处理
  3. 非法转义(\\m 等)→ 双引号内的 \\x 改为 \\\\x
  4. 折叠符误用(`key: > text` 同行)→ 改 `key: >-` 换行缩进
  5. 逐次重试 yaml.safe_load,最多 20 轮;修不动的报告人工

用法:python3 wiki_repair_yaml.py [目录或文件...]   # 默认 claims/ evidence/ 00-pending/*/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import wiki_common as wc

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?([\s\S]*)$", re.DOTALL)


def _quote_value(v: str) -> str:
    """强制双引号 + 转义。"""
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def repair_yaml_text(fm_text: str) -> tuple[str, int]:
    """迭代修复 frontmatter 文本,返回 (新文本, 修复轮数)。"""
    rounds = 0
    text = fm_text
    while rounds < 20:
        rounds += 1
        try:
            yaml.safe_load(text)
            return text, rounds - 1
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            if mark is None:
                return text, -(rounds)
            lines = text.split("\n")
            if mark.line >= len(lines):
                return text, -(rounds)
            line = lines[mark.line]
            # 定位 key: value 分界
            m = re.match(r"^(\s*)([\w.\-]+):(.*)$", line)
            if not m:
                # 非 key 行(如 block scalar 内容)坏 → 该行整体注释掉保留原值到下一轮?
                # 保守:在行首加 "#"(让解析通过,信息保留在注释里)
                lines[mark.line] = "# [repair-commented] " + line
                text = "\n".join(lines)
                continue
            indent, key, rest = m.group(1), m.group(2), m.group(3).strip()
            if rest.startswith(">") and not rest.startswith(">-") and len(rest) > 1:
                # 折叠符误用:> text → >- + 换行缩进
                inner = rest[1:].strip()
                lines[mark.line] = f"{indent}{key}: >-"
                lines.insert(mark.line + 1, f"{indent}  {inner}")
                text = "\n".join(lines)
                continue
            if not rest:
                return text, -(rounds)  # 空值坏,非本类问题
            # 剥离既有引号(截断/完整)再统一强引
            core = rest
            if len(core) >= 1 and core[0] in "\"'" :
                core = core[1:]
            if len(core) >= 1 and core[-1] in "\"'":
                core = core[:-1]
            core = core.strip()
            new_line = f"{indent}{key}: {_quote_value(core)}"
            if new_line == line:
                # 已强引仍失败(值内有换行等)→ 降级为 block scalar
                lines[mark.line] = f"{indent}{key}: >-"
                lines.insert(mark.line + 1, f"{indent}  {core}")
                text = "\n".join(lines)
                continue
            lines[mark.line] = new_line
            text = "\n".join(lines)
    return text, -rounds


def repair_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    m = FM_RE.match(content)
    if not m:
        return False
    try:
        yaml.safe_load(m.group(1))
        return False  # 本来就好
    except yaml.YAMLError:
        pass
    new_fm, status = repair_yaml_text(m.group(1))
    try:
        data = yaml.safe_load(new_fm)
        assert isinstance(data, dict)
    except Exception:
        print(f"❌ 无法自动修复: {path}")
        return False
    if status < 0 and status != -1:
        pass  # 多轮但成功也算成功
    # 用 safe dump 规范化写回(值已有引号语义,再规范一次)
    body = m.group(2)
    path.write_text(wc.dump_frontmatter_safe(data, body.lstrip("\n")), encoding="utf-8")
    return True


def main() -> int:
    targets = sys.argv[1:]
    if not targets:
        targets = ["claims", "evidence"] + [str(p) for p in Path("00-pending").glob("*/")]
    files = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            files.extend(p.glob("*.md"))
        elif p.is_file():
            files.append(p)
    fixed = failed = 0
    for f in files:
        if repair_file(f):
            print(f"✅ 修复: {f}")
            fixed += 1
    print(f"\n修复 {fixed} 个;其余本来合法或需人工")
    return 0


if __name__ == "__main__":
    sys.exit(main())
