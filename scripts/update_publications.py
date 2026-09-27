#!/usr/bin/env python3
"""Fetch a reviewable snapshot from Matt Baker's Google Scholar profile.

This deliberately does not overwrite the curated publication list. Scholar may return a
CAPTCHA or change its markup; in that case the existing site is left untouched.
"""
from __future__ import annotations
import argparse, html, json, re, sys
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://scholar.google.com.au/citations?hl=en&user=CAkKpjwAAAAJ&view_op=list_works&sortby=pubdate"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/publications.auto.json")
    ap.add_argument("--url", default=URL)
    args = ap.parse_args()
    req = Request(args.url, headers={"User-Agent": "Mozilla/5.0 (compatible; BakerLab publication review)"})
    try:
        body = urlopen(req, timeout=20).read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"Publication fetch failed; no files changed: {exc}", file=sys.stderr)
        return 2
    if any(marker in body.lower() for marker in ("captcha", "not a robot", "unusual traffic")):
        print("Google Scholar returned an anti-bot page; no files changed.", file=sys.stderr)
        return 3
    rows = []
    for block in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', body, re.S):
        title = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', block, re.S)
        meta = re.findall(r'class="gsc_a_at"|class="gs_gray"[^>]*>(.*?)</div>', block, re.S)
        year = re.search(r'class="gsc_a_y".*?>(\d{4})<', block, re.S)
        if title:
            clean = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", s))).strip()
            rows.append({"title": clean(title.group(1)), "authors_and_journal": [clean(x) for x in meta], "year": int(year.group(1)) if year else None})
    if not rows:
        print("No publication rows found; Scholar markup may have changed. No files changed.", file=sys.stderr)
        return 4
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": args.url, "records": rows}, indent=2) + "\n")
    print(f"Found {len(rows)} Scholar records. Review {out}; data/publications.yaml was not changed.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
