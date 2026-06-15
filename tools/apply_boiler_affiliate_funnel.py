#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学習系ガイドへ公開済み affiliate 比較記事の導線を追加する（2級ボイラー）。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

AFFILIATE_TITLES = {
    "affiliate-textbooks-recommend": "2級ボイラー技士のおすすめテキスト3選【2026年版・独学】",
    "affiliate-problem-books": "2級ボイラー技士のおすすめ問題集3選【2026年版・過去問】",
    "affiliate-mock-exam-materials": "2級ボイラー技士の公表問題・公式教材3選【2026年版】",
}

BODY = {
    "affiliate-textbooks-recommend": (
        "テキスト1冊は、affiliate-textbooks-recommend で4分野対応の3冊を比較してから固定すると、途中で乗り換えずに済みます。"
    ),
    "affiliate-problem-books": (
        "演習1冊は、affiliate-problem-books で過去問の収録形式を比較してから週次計画に組み込むと迷いが減ります。"
    ),
    "affiliate-mock-exam-materials": (
        "公表問題の解説は、affiliate-mock-exam-materials で公式教材3冊を比較してから直前4週のカレンダーに入れると安全です。"
    ),
}

GUIDE_AFFILIATE: dict[str, tuple[str, int]] = {
    "exam-overview": ("affiliate-textbooks-recommend", 2),
    "textbook-selection": ("affiliate-textbooks-recommend", 2),
    "wrong-answer-notebook": ("affiliate-problem-books", 2),
    "weak-subject-rotation": ("affiliate-problem-books", 2),
    "past-questions-by-field": ("affiliate-problem-books", 2),
    "retake-exam-strategy": ("affiliate-problem-books", 2),
    "final-day-checklist": ("affiliate-mock-exam-materials", 2),
}

SECONDARY_AFFILIATE: dict[str, str] = {
    "exam-overview": "affiliate-problem-books",
    "textbook-selection": "affiliate-problem-books",
    "wrong-answer-notebook": "affiliate-textbooks-recommend",
    "past-questions-by-field": "affiliate-textbooks-recommend",
    "retake-exam-strategy": "affiliate-mock-exam-materials",
    "final-day-checklist": "affiliate-problem-books",
}


def _split_related(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _append_related(value: str, token: str) -> str:
    parts = _split_related(value)
    slug = token.split(":", 1)[0]
    if any(p.split(":", 1)[0] == slug for p in parts):
        return ";".join(parts)
    parts.append(token)
    return ";".join(parts)


def _append_body(body: str, aff_slug: str) -> str:
    sentence = BODY[aff_slug]
    if aff_slug in (body or ""):
        return body
    text = (body or "").rstrip()
    if not text:
        return sentence
    if not text.endswith("。"):
        text += "。"
    return text + sentence


def apply_guide_updates(rows: list[dict[str, str]]) -> int:
    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, (aff_slug, sec_n) in GUIDE_AFFILIATE.items():
        row = by_slug.get(slug)
        if not row or (row.get("content_status") or "").strip() != "published":
            continue
        body_key = f"section_{sec_n}_body"
        old_body = row.get(body_key, "")
        new_body = _append_body(old_body, aff_slug)
        if new_body != old_body:
            row[body_key] = new_body

        token = f"{aff_slug}:{AFFILIATE_TITLES[aff_slug]}"
        new_rl = _append_related(row.get("related_links", ""), token)
        sec = SECONDARY_AFFILIATE.get(slug)
        if sec:
            new_rl = _append_related(new_rl, f"{sec}:{AFFILIATE_TITLES[sec]}")
        if new_rl != row.get("related_links", "") or new_body != old_body:
            row["related_links"] = new_rl
            changed += 1
    return changed


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    changed = apply_guide_updates(rows)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Guide funnel: {len(GUIDE_AFFILIATE)} targets, {changed} row(s) updated")


if __name__ == "__main__":
    main()
