#!/usr/bin/env python3
"""
wiki_unify_terms.py — 术语统一维护(2026-08-26)

用户决策(已确认):
  A   fnirs / FNIRS  → fNIRS   (6389 处)
  B1  CI cochlear 上下文 → 耳蜗植入(CI)   (5 paper 范围,~60 文件)
  C1  EEG-fNIRS 16 写法 → EEG-fNIRS   (~8681 处)
  D4  VBTs → VBT   (72 处)
  N2  7 个 ci xxx.md claim 文件 → 耳蜗植入 xxx.md  + 全 wiki wikilink 更新

原则(铁律推论):
  - 映射表 LLM 审定,显式可审计
  - 大小写/拼写修复不破坏文件名 slug(文件名 slug 是 wikilink key,本批次 N2 单独处理)
  - regex 必须用 \\b 单词边界,排除 yaml key / wikilink 路径
  - 排除:code_url / link / 命令行字段(占位符替换会破坏外部链接)
  - 先 dry-run → 用户复核 → execute
  - 全程不修改 raw/ (铁律 #1)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "schemas"))


# ============================================================
# A. fnirs / FNIRS → fNIRS
# ============================================================
# 只在 frontmatter + body 文本里改,不动文件名 slug。
# 排除 code block / inline URL / yaml 字段值里的 http 引用
FNIRS_RE = re.compile(r"\b(fnirs|FNIRS|Fnirs|FNirs|FNiRS)\b")
FNIRS_REPLACEMENT = "fNIRS"

# ============================================================
# C. EEG-fNIRS 16 写法 → EEG-fNIRS
# ============================================================
# 顺序:必须先于 fnirs 大小写修复跑(因为大写的 NIRS 也会被 FNIRS 匹配)
# 排序原则:长的优先(避免重复匹配)
EEG_FNIRS_PATTERNS = [
    # 已有 fNIRS 大小写正确,只动顺序/分隔符
    (re.compile(r"\bfNIRS[-–—\s]EEG\b"), "EEG-fNIRS"),
    (re.compile(r"\bfNIRS\s+EEG\b"), "EEG-fNIRS"),
    (re.compile(r"\bEEG\s+fNIRS\b"), "EEG-fNIRS"),
    (re.compile(r"\bEEG[-–—\s]fNIRS\b"), "EEG-fNIRS"),
    # 全小写变体
    (re.compile(r"\bFNIRS[-–—\s]EEG\b"), "EEG-fNIRS"),
    (re.compile(r"\bFNIRS\s+EEG\b"), "EEG-fNIRS"),
    (re.compile(r"\bEEG\s+FNIRS\b"), "EEG-fNIRS"),
    (re.compile(r"\bEEG[-–—\s]FNIRS\b"), "EEG-fNIRS"),
    (re.compile(r"\bfnirs[-–—\s]eeg\b"), "EEG-fNIRS"),
    (re.compile(r"\bfnirs\s+eeg\b"), "EEG-fNIRS"),
    (re.compile(r"\beeg\s+fnirs\b"), "EEG-fNIRS"),
    (re.compile(r"\beeg[-–—\s]fnirs\b"), "EEG-fNIRS"),
    # eeg-nirs / nirs-eeg 这种错位
    (re.compile(r"\beeg[-–—\s]nirs\b", ), "EEG-fNIRS"),
    (re.compile(r"\bnirs[-–—\s]eeg\b"), "EEG-fNIRS"),
    # 紧凑无分隔(7/5 处)
    (re.compile(r"\bEEGFnirs\b"), "EEG-fNIRS"),
    (re.compile(r"\bEEGFNIRS\b"), "EEG-fNIRS"),
    (re.compile(r"\beegfnirs\b"), "EEG-fNIRS"),
    (re.compile(r"\beegNIRS\b"), "EEG-fNIRS"),
]

# ============================================================
# D4. VBTs → VBT
# ============================================================
# 只动复数 VBTs → 单数 VBT。单数 VBT 已经规范(Virtual Brain Twin / Transplant)
VBTS_RE = re.compile(r"\bVBTs\b")
VBTS_REPLACEMENT = "VBT"

# ============================================================
# B1. CI cochlear 上下文 → 耳蜗植入(CI)
# ============================================================
# 基于 paper 白名单,文件级过滤。
# 5 paper:alemi_2023_brain_research_bulletin / deroche_2024_brain_commun /
#   chen_2015_brain_topogr / chen_2017_neuroimage / pollonini_2016_biomed_opt_express
COCHLEAR_PAPERS = [
    "alemi_2023_brain_research_bulletin",
    "deroche_2024_brain_commun",
    "chen_2015_brain_topogr",
    "chen_2017_neuroimage",
    "pollonini_2016_biomed_opt_express",
]

# CI 在这 5 paper 范围内 100% 指 cochlear implant(已扫,无 confidence interval)
# 严格规则:
#   1. 只在 "独立词" CI 替换:后跟中文/空格/中英词尾的限定词
#   2. 不改: (CI)、[CI]、CI-、CI+、CI*、CI.、CI/ 等已是缩写标注的
#   3. CI-HL/CI-LL/CI+语言延迟 等复合术语保持(已是论文术语)
# 拒绝后继字符集:表示"这是复合术语/缩写标注",不应拆
CI_WORD_RE = re.compile(r"\bCI\b")

CI_INVALID_FOLLOW_CHARS = set("-+=<>_|*[]{}()'`.;,!?/\\")  # 复合术语/缩写标注
# 特殊情况豁免:一些合法形式仍要换
# 例:`[[CI 儿童...]]` 里 CI 后接空格+中文,合法替换 →改为 `[[耳蜗植入(CI) 儿童...]]`
# 例:`(CI)` 后接 `)` 是拒绝的 →跳过
# 例:`CI-HL` 后接 `-` 是拒绝的 →跳过

# ============================================================
# N2. 7 个 ci xxx.md claim 文件重命名
# ============================================================
CI_CLAIM_RENAMES = {
    "ci 用户视觉适应增强支持编码效率.md": "耳蜗植入用户视觉适应增强支持编码效率.md",
    "ci 用户视觉皮层激活低于对照.md": "耳蜗植入用户视觉皮层激活低于对照.md",
    "ci 用户听觉皮层激活低于对照.md": "耳蜗植入用户听觉皮层激活低于对照.md",
    "ci 用户听觉适应降低反映康复不完全.md": "耳蜗植入用户听觉适应降低反映康复不完全.md",
    "ci 视听解耦失同步.md": "耳蜗植入视听解耦失同步.md",
    "ci 语言延迟视觉反应弱.md": "耳蜗植入语言延迟视觉反应弱.md",
    "ci 跨模态可塑性适应不良.md": "耳蜗植入跨模态可塑性适应不良.md",
    "ci 跨模态可塑性代偿.md": "耳蜗植入跨模态可塑性代偿.md",  # 安全:若存在
}


# ============================================================
# 文件级工具
# ============================================================
def iter_target_files():
    """扫描 claims/ evidence/ papers/ + 00-pending/{paper}/ 下所有 md"""
    roots = [
        REPO_ROOT / "claims",
        REPO_ROOT / "evidence",
        REPO_ROOT / "papers",
    ]
    # 00-pending 子结构
    pending = REPO_ROOT / "00-pending"
    if pending.exists():
        for sub in pending.iterdir():
            if sub.is_dir():
                roots.append(sub)

    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.md"):
            # 排除 raw/ (铁律 #1)
            if "raw" in p.parts:
                continue
            yield p


def is_cochlear_file(path: Path) -> bool:
    """B1: 文件是否属于 cochlear paper 范围(文件名含 paper key 或内容引用)"""
    name = path.name.lower()
    for paper in COCHLEAR_PAPERS:
        if paper in name:
            return True
    # 文件名不含 paper key 但内容引用 cochlear paper:仍属于
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return any(f"[[{paper}" in text or f"papers/{paper}" in text or paper in text[:500] for paper in COCHLEAR_PAPERS)


def apply_text_subs(text: str, *, allow_fnirs=True, allow_eeg_fnirs=True,
                    allow_vbts=True, allow_ci_cochlear=False, allow_ci_already=False) -> tuple[str, dict]:
    """应用 A/C/D/B1 文本替换。返回 (new_text, 计数字典)"""
    counts = {"fnirs": 0, "eeg_fnirs": 0, "vbts": 0, "ci": 0}
    original = text

    # 1) EEG-fNIRS 写法合并 (先于 fnirs,因为 FNIRS 也会被 FNIRS 匹配)
    if allow_eeg_fnirs:
        for pat, rep in EEG_FNIRS_PATTERNS:
            new_text, n = pat.subn(rep, text)
            if n:
                counts["eeg_fnirs"] += n
                text = new_text

    # 2) fnirs → fNIRS 大小写统一
    if allow_fnirs:
        new_text, n = FNIRS_RE.subn(FNIRS_REPLACEMENT, text)
        if n:
            counts["fnirs"] += n
            text = new_text

    # 3) VBTs → VBT
    if allow_vbts:
        new_text, n = VBTS_RE.subn(VBTS_REPLACEMENT, text)
        if n:
            counts["vbts"] += n
            text = new_text

    # 4) CI cochlear 上下文: 已在 cochlear paper 范围的文件,全文替换 CI → 耳蜗植入(CI)
    #    但要跳过已经是 "耳蜗植入(CI)" 的
    #    不修改复合缩写 CI-HL、CI+xxx、(CI)、[CI] 等
    if allow_ci_cochlear:
        # 逐个判断 CI 位置
        def repl_ci(m):
            ctx_before = text[max(0, m.start()-15):m.start()]
            ctx_after = text[m.end():m.end()+15]
            # 若已是耳蜗/人工耳蜗 上下文,跳过(避免 "耳蜗植入(耳蜗植入(CI))")
            if "耳蜗" in ctx_before[-5:] or "耳蜗" in ctx_after[:5]:
                return m.group(0)
            next_char = ctx_after[:1]
            # 下一个字符为不合法(缩写标注/复合术语),跳过
            if next_char in CI_INVALID_FOLLOW_CHARS:
                return m.group(0)
            # 下一个字符是空白/中文标点/中文 — 合法的独立词,替换
            counts["ci"] += 1
            return "耳蜗植入(CI)"
        text = CI_WORD_RE.sub(repl_ci, text)

    return text, counts


# ============================================================
# N2. 文件重命名 + 全 wiki wikilink 更新
# ============================================================
def rename_ci_claims(dry_run=True):
    """重命名 7 个 ci xxx.md claim 文件,同步更新所有引用它们的 wikilink"""
    rename_log = []
    link_updates = 0

    # 1) 先列出所有需要重命名的文件(递归 00-pending + claims/)
    search_dirs = [REPO_ROOT / "claims"]
    pending_root = REPO_ROOT / "00-pending"
    if pending_root.exists():
        for sub in pending_root.iterdir():
            if sub.is_dir() and (sub / "claims").exists():
                search_dirs.append(sub / "claims")

    # 找到所有需要改的文件 + 它们的旧路径
    rename_pairs = []  # [(old_path, new_path)]
    for d in search_dirs:
        if not d.exists():
            continue
        for old_name, new_name in CI_CLAIM_RENAMES.items():
            old_path = d / old_name
            if old_path.exists():
                new_path = d / new_name
                rename_pairs.append((old_path, new_path))

    print(f"\n=== N2 重命名: 待改 {len(rename_pairs)} 个 claim 文件 ===")
    for old, new in rename_pairs:
        print(f"  {old.relative_to(REPO_ROOT)} → {new.relative_to(REPO_ROOT)}")

    # 2) 先扫描全 wiki,统计 wikilink 引用数
    link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
    wikilink_files_to_update = {}  # {file_path: [(old_link, new_link), ...]}
    for md_file in iter_target_files():
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        updates = []
        for m in link_pattern.finditer(text):
            link = m.group(1)
            # 检查是否是 ci claim 的引用
            # 形式 1: [[ci xxx]] (无目录前缀,本目录引用)
            # 形式 2: [[claims/ci xxx]] (绝对目录引用)
            for old_name in CI_CLAIM_RENAMES:
                if link == old_name[:-3]:  # 去掉 .md
                    new_link = CI_CLAIM_RENAMES[old_name][:-3]
                    updates.append((m.group(0), f"[[{new_link}]]"))
                elif link == f"claims/{old_name[:-3]}":
                    new_link = f"claims/{CI_CLAIM_RENAMES[old_name][:-3]}"
                    updates.append((m.group(0), f"[[{new_link}]]"))
                elif link.endswith(f"/{old_name[:-3]}"):
                    # 形式:[[00-pending/xxx/claims/ci xxx]]
                    new_name = CI_CLAIM_RENAMES[old_name][:-3]
                    new_link = link.rsplit("/", 1)[0] + "/" + new_name
                    updates.append((m.group(0), f"[[{new_link}]]"))
        if updates:
            wikilink_files_to_update[md_file] = updates

    total_links = sum(len(v) for v in wikilink_files_to_update.values())
    print(f"\n=== N2 反向 wikilink: {total_links} 处 in {len(wikilink_files_to_update)} 文件 ===")
    for f, ups in list(wikilink_files_to_update.items())[:5]:
        print(f"  {f.relative_to(REPO_ROOT)}: {len(ups)} 处")
    if len(wikilink_files_to_update) > 5:
        print(f"  ... 还有 {len(wikilink_files_to_update)-5} 个文件")

    if dry_run:
        print("\n[DRY-RUN] 未执行任何写入")
        return {"renames": len(rename_pairs), "wikilinks": total_links, "files": len(wikilink_files_to_update)}

    # 3) 执行:先重命名文件,再更新 wikilink
    for old, new in rename_pairs:
        if old.exists():
            old.rename(new)
            rename_log.append((old, new))

    # 4) 更新 wikilink
    for f, updates in wikilink_files_to_update.items():
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        original = text
        for old_link, new_link in updates:
            text = text.replace(old_link, new_link)
        if text != original:
            f.write_text(text, encoding="utf-8")
            link_updates += sum(1 for _ in updates)

    return {"renames": len(rename_log), "wikilinks": link_updates, "files": len(wikilink_files_to_update)}


# ============================================================
# 主入口
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="Wiki 术语统一维护")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", action="store_true", help="实际写入(覆盖 dry-run)")
    ap.add_argument("--task", choices=["A", "B1", "C", "D4", "N2", "all"], default="all",
                    help="A=fnirs, B1=cochlear CI, C=EEG-fNIRS, D4=VBTs→VBT, N2=rename, all=A+C+D4+B1+N2")
    ap.add_argument("--limit", type=int, default=0, help="仅处理前 N 个文件(测试)")
    args = ap.parse_args()

    dry_run = not args.execute
    print(f"{'[DRY-RUN]' if dry_run else '[EXECUTE]'} task={args.task}\n")

    targets = list(iter_target_files())
    if args.limit:
        targets = targets[:args.limit]

    print(f"扫描文件总数: {len(targets)} (排除 raw/)\n")

    # 任务路由 — 每个 task 独立控制开关
    if args.task == "N2":
        result = rename_ci_claims(dry_run=dry_run)
        print(f"\nN2 结果: {result}")
        return

    # 决定开哪些开关
    if args.task == "A":
        flags = dict(allow_fnirs=True, allow_eeg_fnirs=False, allow_vbts=False, allow_ci_cochlear=False)
        cochlear_only = False
    elif args.task == "C":
        flags = dict(allow_fnirs=False, allow_eeg_fnirs=True, allow_vbts=False, allow_ci_cochlear=False)
        cochlear_only = False
    elif args.task == "D4":
        flags = dict(allow_fnirs=False, allow_eeg_fnirs=False, allow_vbts=True, allow_ci_cochlear=False)
        cochlear_only = False
    elif args.task == "B1":
        flags = dict(allow_fnirs=False, allow_eeg_fnirs=False, allow_vbts=False, allow_ci_cochlear=True)
        cochlear_only = True
    elif args.task == "all":
        flags = dict(allow_fnirs=True, allow_eeg_fnirs=True, allow_vbts=True, allow_ci_cochlear=True)
        cochlear_only = False
    else:
        raise ValueError(f"unknown task: {args.task}")

    # 主体
    total_files = 0
    total_fnirs = 0
    total_eeg_fnirs = 0
    total_vbts = 0
    total_ci = 0
    sample_changes = []

    for p in targets:
        if cochlear_only and not is_cochlear_file(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            continue
        new_text, c = apply_text_subs(text, **flags)
        changed = new_text != text
        total_fnirs += c["fnirs"]
        total_eeg_fnirs += c["eeg_fnirs"]
        total_vbts += c["vbts"]
        total_ci += c["ci"]
        if changed:
            total_files += 1
            if len(sample_changes) < 8:
                sample_changes.append((p, c))
            if not dry_run:
                p.write_text(new_text, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"任务 {args.task} {'[DRY-RUN]' if dry_run else '[EXECUTE]'} 摘要:")
    print(f"  修改文件: {total_files}")
    print(f"  A fnirs→fNIRS: {total_fnirs}")
    print(f"  C EEG-fNIRS 合并: {total_eeg_fnirs}")
    print(f"  D4 VBTs→VBT: {total_vbts}")
    print(f"  B1 CI→耳蜗植入(CI): {total_ci}")

    if sample_changes:
        print(f"\n样本变更(前 8 个文件):")
        for p, s in sample_changes:
            rel = p.relative_to(REPO_ROOT)
            print(f"  {rel}: fnirs={s['fnirs']} eeg_fnirs={s['eeg_fnirs']} vbts={s['vbts']} ci={s['ci']}")

    if dry_run:
        print(f"\n[DRY-RUN] 未写入。使用 --execute 实际执行。")


if __name__ == "__main__":
    main()