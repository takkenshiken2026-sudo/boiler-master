#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開済み affiliate 比較記事の相互 related_links を整える（2級ボイラー）。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

AFFILIATE_CROSS_LINKS: dict[str, list[str]] = {
    "affiliate-textbooks-recommend": [
        "textbook-selection:テキストの選び方",
        "exam-overview:試験概要",
        "wrong-answer-notebook:誤答ノートの作り方",
        "affiliate-problem-books:おすすめ問題集3選",
        "affiliate-mock-exam-materials:公表問題・公式教材3選",
        "past-questions-by-field:分野別過去問",
    ],
    "affiliate-problem-books": [
        "past-questions-by-field:分野別過去問",
        "weak-subject-rotation:苦手科目ローテーション",
        "affiliate-textbooks-recommend:おすすめテキスト3選",
        "affiliate-mock-exam-materials:公表問題・公式教材3選",
        "retake-exam-strategy:再受験戦略",
        "textbook-selection:テキストの選び方",
    ],
    "affiliate-mock-exam-materials": [
        "final-day-checklist:前日チェックリスト",
        "exam-day-flow:試験当日の流れ",
        "affiliate-textbooks-recommend:おすすめテキスト3選",
        "affiliate-problem-books:おすすめ問題集3選",
        "past-questions-by-field:分野別過去問",
        "retake-exam-strategy:再受験戦略",
    ],
}


def _split_related(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _merge_affiliate_related(existing: str, internal: list[str]) -> str:
    asp = [p for p in _split_related(existing) if p.startswith("http")]
    merged: list[str] = []
    seen: set[str] = set()
    for token in internal:
        slug = token.split(":", 1)[0]
        if slug in seen:
            continue
        seen.add(slug)
        merged.append(token)
    for token in asp:
        if token not in merged:
            merged.append(token)
    return ";".join(merged)


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, internal in AFFILIATE_CROSS_LINKS.items():
        row = by_slug.get(slug)
        if not row or (row.get("content_status") or "").strip() != "published":
            continue
        new_rl = _merge_affiliate_related(row.get("related_links", ""), internal)
        if new_rl != row.get("related_links", ""):
            row["related_links"] = new_rl
            changed += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Affiliate crosslinks: {len(AFFILIATE_CROSS_LINKS)} articles, {changed} updated")


if __name__ == "__main__":
    main()
