#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""related_terms の未登録ラベルを登録済み用語名へ置換する。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glossary_related_aliases import RELATED_ALIASES
from tools.internal_links import norm
from tools.rewrite_glossary_articles import GLOSSARY_CSV, GLOSSARY_FIELDNAMES


def normalize_related(value: str, term_set: set[str]) -> tuple[str, int]:
    if not value.strip():
        return value, 0
    changed = 0
    out: list[str] = []
    for label in value.split(";"):
        label = label.strip()
        if not label:
            continue
        resolved = label
        for _ in range(6):
            if resolved in term_set:
                break
            nxt = RELATED_ALIASES.get(resolved)
            if not nxt or nxt == resolved:
                break
            resolved = nxt
        if resolved != label:
            changed += 1
        out.append(resolved)
    return ";".join(out), changed


def main() -> int:
    if not GLOSSARY_CSV.is_file():
        print(f"Missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    term_set = {norm(r["term"]) for r in rows if norm(r.get("term"))}
    total = 0

    for row in rows:
        rel = norm(row.get("related_terms"))
        if not rel:
            continue
        new_rel, n = normalize_related(rel, term_set)
        if n:
            row["related_terms"] = new_rel
            total += n

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GLOSSARY_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") or "" for k in GLOSSARY_FIELDNAMES})

    print(f"Normalized related_terms ({total} label replacements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
