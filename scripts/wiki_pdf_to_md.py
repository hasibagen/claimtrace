#!/usr/bin/env python3
"""wiki_pdf_to_md.py — 单篇/少量 PDF → MinerU API(vlm) → raw/ 直转(S0a 可选步)。

场景:用户直接把 PDF 交给 wiki(懒得先转 md)。转换是纯机械管道(ARCHITECTURE
§1.2 铁律 3),复用 wiki_mineru_csv.py 的 upload/poll/download,不重复实现 API 层;
产出仍是「交给 wiki 的最终形态是 md」(ARCHITECTURE §5.0)。

落位两种:
  1. --citekey <ck>(canonical = paperinfo 节点名)→ 直接 raw/<ck>/
     (幂等:已有 full.md 即跳过,--force 重转)
  2. 未给 citekey → 暂存 raw/_incoming/<pdf-stem>/;S1 按标题/DOI 匹配或从
     Zotero 创建 paperinfo 定 canonical citekey 后,由 S2 把暂存目录整体移到
     raw/<citekey>/(一次命名到位,永不改名)

用法:
  python3 wiki_pdf_to_md.py <pdf> [--citekey <ck>] [--lang en] [--force]
  python3 wiki_pdf_to_md.py a.pdf b.pdf ...        # 批量暂存(不配 --citekey)
  wiki pdf2md <pdf> [--citekey <ck>]               # 统一 CLI 入口
环境: MINERU_API_TOKEN(缺省回退内置 token,同 wiki_mineru_csv.py)
日志: /tmp/mineru_batch/pdf2md.log
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_mineru_csv as mc

WIKI_ROOT = mc.WIKI_ROOT
STAGING = WIKI_ROOT / "raw" / "_incoming"

# 云端 API 逐页成本/超时经验阈值(yiruide 书目批次:≤200 页 API 直转,更大走本地)
BIG_PDF_PAGES = 200


def page_count(pdf: Path) -> int:
    try:
        import fitz
        doc = fitz.open(str(pdf))
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return 0


def convert_one(pdf: Path, target: Path, token: str, log: logging.Logger,
                force: bool) -> str:
    """转换单个 PDF → target/{full.md, images/}。返回 ok/skipped/failed。"""
    if (target / "full.md").is_file() and not force:
        return "skipped"
    if force and target.exists():
        shutil.rmtree(target)
    bid = mc.upload_single(pdf, token, log)
    items = mc.poll(bid, token, log)
    mc.download_zip(items, target, log)
    if not (target / "full.md").is_file():
        return "failed"
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PDF → MinerU → raw/(S0a 可选步;--citekey 直转,否则暂存 raw/_incoming/)")
    ap.add_argument("pdfs", nargs="+", type=Path, help="PDF 文件路径(可多个)")
    ap.add_argument("--citekey", default="",
                    help="canonical citekey(paperinfo 节点名);给了直转 raw/<ck>/,不给暂存")
    ap.add_argument("--lang", default="en", help="ch/en(默认 en,中文 PDF 用 ch)")
    ap.add_argument("--force", action="store_true", help="目标已有 full.md 也重转")
    args = ap.parse_args()

    if args.citekey:
        if len(args.pdfs) > 1:
            print("✗ --citekey 只能配单个 PDF(多 PDF 一律暂存,待 S1 逐篇定名)")
            return 1
        if not re.fullmatch(r"[A-Za-z0-9_.\-]+", args.citekey):
            print(f"✗ citekey 含非法字符(须为路径安全 slug): {args.citekey}")
            return 1

    pdfs: list[Path] = []
    for p in args.pdfs:
        rp = Path(p).expanduser().resolve()
        if rp.suffix.lower() != ".pdf" or not rp.is_file():
            print(f"✗ 不是 PDF 文件: {p}")
            return 1
        pdfs.append(rp)

    mc.LANGUAGE = args.lang

    logdir = Path("/tmp/mineru_batch")
    logdir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.StreamHandler()])
    log = logging.getLogger("pdf2md")

    token = mc.get_token()
    ok = skipped = failed = 0

    for pdf in pdfs:
        target = (WIKI_ROOT / "raw" / args.citekey) if args.citekey \
            else (STAGING / pdf.stem)
        pages = page_count(pdf)
        if pages > BIG_PDF_PAGES:
            print(f"⚠ {pdf.name} {pages} 页 > {BIG_PDF_PAGES}:云端 API 慢且贵,"
                  f"建议本地 mineru(conda run -n mineru mineru_local_batch.py)")
        print(f"→ {pdf.name}({pages or '?'} 页) → {target.relative_to(WIKI_ROOT)}/")
        try:
            r = convert_one(pdf, target, token, log, args.force)
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            failed += 1
            continue
        if r == "skipped":
            print("  ✓ 已有 full.md,跳过(--force 重转)")
            skipped += 1
        elif r == "failed":
            print("  ✗ 转换完成但缺 full.md")
            failed += 1
        else:
            n_img = len(list((target / "images").glob("*"))) if (target / "images").is_dir() else 0
            print(f"  ✓ full.md + {n_img} images")
            ok += 1

    print(f"\n=== pdf2md: ok={ok} skipped={skipped} failed={failed} ===")
    if ok:
        if args.citekey:
            print(f"下一步:raw/{args.citekey}/full.md 就绪 → wiki-extract-paper S3"
                  f"(S1/S2 已由本次完成)"
                  if (WIKI_ROOT / "paperinfo" / f"{args.citekey}.md").is_file()
                  else f"下一步:raw/{args.citekey}/full.md 就绪,但 paperinfo/{args.citekey}.md 不存在"
                       f" → 先走 S1 定/建 paperinfo(若 citekey 需改,由 S2 改名 raw 目录)")
        else:
            print("下一步:S1 按暂存 full.md 标题/DOI 匹配或创建 paperinfo 定 canonical citekey"
                  " → S2 把 raw/_incoming/<stem>/ 整体移到 raw/<citekey>/ → S3 抽取")
    return 0 if failed == 0 else 1


def run(argv: list[str]) -> int:
    """统一 CLI 入口: `wiki pdf2md [args]`"""
    sys.argv = ["wiki_pdf_to_md"] + argv
    return main()


if __name__ == "__main__":
    sys.exit(main())
