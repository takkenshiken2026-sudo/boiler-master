#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2級ボイラー site の誤った exam.or.jp 参照をボイラー協会向けに差し替える。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import is_published_guide, norm  # noqa: E402
from tools.guide_prose_patterns import PROSE_COLUMNS  # noqa: E402

OFFICIAL_LABEL = "ボイラー検定（公式）"
OFFICIAL_URL = "https://www.jbba.or.jp/"
PRIMARY_SOURCES = f"{OFFICIAL_LABEL}|{OFFICIAL_URL}"
ORG = "一般社団法人 日本ボイラー協会"
WRONG_ORG = "公益財団法人 安全衛生技術試験協会"
WRONG_LABEL = "安全衛生技術試験協会（公式）"

PROSE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (WRONG_ORG, ORG),
    (WRONG_LABEL, OFFICIAL_LABEL),
    ("https://www.exam.or.jp/", OFFICIAL_URL),
    ("exam.or.jp", "jbba.or.jp"),
)


def fix_site_config(root: Path, *, dry_run: bool) -> bool:
    cfg_path = root / "site-config.json"
    if not cfg_path.is_file():
        return False
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    changed = False
    if cfg.get("officialOrganization") == WRONG_ORG:
        cfg["officialOrganization"] = ORG
        changed = True
    links = cfg.get("externalLinks") or []
    for link in links:
        if link.get("url") == "https://www.exam.or.jp/":
            link["label"] = OFFICIAL_LABEL
            link["url"] = OFFICIAL_URL
            link["description"] = "2級ボイラー技士試験の日程・受験案内・公式テキストなどの公式情報を確認してください。"
            changed = True
    if changed and not dry_run:
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def fix_row(row: dict[str, str]) -> bool:
    before = {k: row.get(k, "") for k in row}
    if is_published_guide(row):
        row["primary_sources"] = PRIMARY_SOURCES
    for col in PROSE_COLUMNS:
        text = norm(row.get(col))
        if not text:
            continue
        out = text
        for old, new in PROSE_REPLACEMENTS:
            out = out.replace(old, new)
        if out != text:
            row[col] = out
    return before != {k: row.get(k, "") for k in row}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    csv_path = root / "data" / "guide_articles.csv"
    if not csv_path.is_file():
        print(f"missing {csv_path}", file=sys.stderr)
        return 1

    cfg_changed = fix_site_config(root, dry_run=args.dry_run)
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    changed = sum(1 for row in rows if fix_row(row))
    if changed and not args.dry_run:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(f"official refs: csv_rows={changed}, site_config={cfg_changed}, dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
