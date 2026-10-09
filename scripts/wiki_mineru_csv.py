#!/usr/bin/env python3
"""wiki_mineru_csv.py — 文献清单 CSV → MinerU API(vlm) → raw/<citekey>/ 批量队列。

纯机械管道(S0/S2 辅助,不做任何语义抽取,ARCHITECTURE §1.2 铁律 3/4):
  CSV(citation_key, pdf_path, relevance_score) → 逐篇上传 PDF → 轮询 →
  解压 full.md + images/ → raw/<citekey>/(一次命名到位,已存在即跳过,幂等续跑)。

用法:
  python3 wiki_mineru_csv.py <csv> [--limit N] [--only ck1,ck2] [--retry-failed]
环境: MINERU_API_TOKEN(缺省回退内置 token,同 _tmp_martin_2026_adv_sci_mineru.py)
日志: /tmp/mineru_batch/<citekey>.log + 进度打印 stdout
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path

import requests

WIKI_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_URL = "https://mineru.net/api/v4"
MODEL_VERSION = "vlm"
LANGUAGE = "en"
POLL_INTERVAL = 5
POLL_TIMEOUT = 900
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def get_token() -> str:
    """Token comes exclusively from the MINERU_API_TOKEN environment variable."""
    tok = os.environ.get("MINERU_API_TOKEN", "").strip()
    if not tok:
        raise SystemExit("MINERU_API_TOKEN is not set — export it before running.")
    return tok


def upload_single(pdf: Path, token: str, log: logging.Logger) -> str:
    url = f"{BASE_URL}/file-urls/batch"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "files": [{"name": pdf.name}],
        "model_version": MODEL_VERSION,
        "is_ocr": True,
        "enable_formula": True,
        "enable_table": True,
        "language": LANGUAGE,
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"submit failed: {resp.status_code} {resp.text[:200]}")
    rj = resp.json()
    if rj.get("code") != 0:
        raise RuntimeError(f"submit err: {rj.get('msg')}")
    batch_id = rj["data"]["batch_id"]
    with open(pdf, "rb") as f:
        put_resp = requests.put(rj["data"]["file_urls"][0], data=f, timeout=300)
    if put_resp.status_code not in (200, 201):
        raise RuntimeError(f"upload failed: {put_resp.status_code}")
    return batch_id


def poll(batch_id: str, token: str, log: logging.Logger) -> list:
    url = f"{BASE_URL}/extract-results/batch/{batch_id}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    t0 = time.time()
    while time.time() - t0 < POLL_TIMEOUT:
        resp = requests.get(url, headers=headers, timeout=30)
        rj = resp.json()
        if rj.get("code") != 0:
            raise RuntimeError(f"poll err: {rj.get('msg')}")
        items = rj.get("data", {}).get("extract_result", [])
        if items and all(it.get("state") in ("done", "failed") for it in items):
            return items
        time.sleep(POLL_INTERVAL)
    raise RuntimeError("poll timeout")


def download_zip(items: list, target: Path, log: logging.Logger) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in items:
        if item.get("state") != "done":
            continue
        url = item.get("full_zip_url")
        if not url:
            continue
        resp = requests.get(url, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"download zip failed: {resp.status_code}")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        md_content = None
        images_dir = target / "images"
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            data = zf.read(name)
            base = Path(name).name
            if base.endswith("full.md"):
                md_content = data.decode("utf-8")
            elif base.startswith("image_") or base.lower().endswith(tuple(IMAGE_EXTS)):
                images_dir.mkdir(parents=True, exist_ok=True)
                (images_dir / base).write_bytes(data)
        if md_content is None:
            raise RuntimeError("no full.md in zip")
        md_content = re.sub(r"!\[([^\]]*)\]\((image_[^)]+)\)", r"![\1](images/\2)", md_content)
        (target / "full.md").write_text(md_content, encoding="utf-8")
        return
    raise RuntimeError(f"no done item: {items}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--min-score", type=int, default=0)
    args = ap.parse_args()

    logdir = Path("/tmp/mineru_batch")
    logdir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    root_log = logging.getLogger("root")
    token = get_token()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    rows.sort(key=lambda r: -int(r.get("relevance_score") or 0))
    only = {x.strip() for x in args.only.split(",") if x.strip()}

    todo, skipped, no_pdf, done_before = [], 0, [], 0
    for r in rows:
        ck = r["citation_key"]
        pdf = r.get("pdf_path", "")
        if (WIKI_ROOT / "raw" / ck / "full.md").is_file():
            done_before += 1
            continue
        if not pdf or not os.path.exists(pdf):
            no_pdf.append(ck)
            continue
        if only and ck not in only:
            continue
        if int(r.get("relevance_score") or 0) < args.min_score:
            skipped += 1
            continue
        todo.append((ck, pdf))
    if args.limit:
        todo = todo[: args.limit]

    root_log.info(f"队列 {len(todo)} 篇(raw 已有 {done_before},无 PDF {len(no_pdf)},跳过 {skipped})")
    if no_pdf:
        root_log.info("无 PDF: " + " ".join(no_pdf))

    ok, fail = 0, 0
    state_path = logdir / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"ok": [], "fail": []}
    for ck, pdf in todo:
        if ck in state["ok"]:
            root_log.info(f"[skip-state] {ck}")
            continue
        log = logging.getLogger(ck)
        t0 = time.time()
        try:
            bid = upload_single(Path(pdf), token, log)
            items = poll(bid, token, log)
            download_zip(items, WIKI_ROOT / "raw" / ck, log)
            ok += 1
            state["ok"].append(ck)
            root_log.info(f"[OK {time.time()-t0:.0f}s] {ck} ({ok}/{len(todo)})")
        except Exception as e:
            fail += 1
            state["fail"].append({"ck": ck, "err": str(e)[:300]})
            root_log.error(f"[FAIL {time.time()-t0:.0f}s] {ck}: {e}")
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    root_log.info(f"=== MinerU done: ok={ok} fail={fail} ===")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
