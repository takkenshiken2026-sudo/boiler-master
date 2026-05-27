#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off: export guide_articles.csv from legacy build_exam_guide_articles.py."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_exam_guide_articles import ARTICLES, faq_items_for, guide_sections  # noqa: E402

OUT = ROOT / "data" / "guide_articles.csv"
TODAY = "2026-05-19"
NEXT_REVIEW = "2026-08-19"
PRIMARY_SOURCES = "安全衛生技術試験協会（公式）|https://www.exam.or.jp/"

HEADER = [
    "slug",
    "genre",
    "title",
    "meta_description",
    "lead",
    "priority",
    "tags",
    "author_name",
    "author_profile",
    "reviewer_name",
    "reviewer_profile",
    "fact_checked_at",
    "primary_sources",
    "original_note",
    "user_intent",
    "action_items",
    "update_policy",
    "last_reviewed_at",
    "next_review_at",
    "source_checked_at",
    "content_status",
    "revision_note",
    "section_1_heading",
    "section_1_body",
    "section_2_heading",
    "section_2_body",
    "section_3_heading",
    "section_3_body",
    "section_4_heading",
    "section_4_body",
    "section_5_heading",
    "section_5_body",
    "section_6_heading",
    "section_6_body",
    "section_7_heading",
    "section_7_body",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "related_links",
]


def related_for(index: int, articles: list[dict]) -> str:
    picks: list[str] = []
    for offset in (1, 2, -1):
        j = (index + offset) % len(articles)
        if j == index:
            continue
        other = articles[j]
        picks.append(f'{other["slug"]}:{other["title"]}')
        if len(picks) >= 2:
            break
    return ";".join(picks)


def lead_for(desc: str, category: str) -> str:
    text = desc.rstrip("。")
    if len(text) > 120:
        return text[:117] + "…"
    return (
        f"{category}を学習する受験生向けに、{text}。"
        "制度面は公式情報で確認しながら、過去問演習と用語解説で定着を図してください。"
    )[:140]


def main() -> int:
    rows: list[dict[str, str]] = []
    for i, article in enumerate(ARTICLES):
        slug = str(article["slug"])
        genre = str(article["category"])
        title = str(article["title"])
        desc = str(article["desc"])
        points = [str(p) for p in article["points"]]  # type: ignore[index]
        sections = guide_sections(article)
        faqs = faq_items_for(article)
        row: dict[str, str] = {
            "slug": slug,
            "genre": genre,
            "title": title,
            "meta_description": desc,
            "lead": lead_for(desc, genre),
            "priority": str((i + 1) * 10),
            "tags": genre.replace("対策", "").replace("活用", "過去問"),
            "author_name": "2級ボイラー技士マスター編集部",
            "author_profile": "資格学習サイト向けに、過去問形式演習・用語解説・学習導線を整理する編集チームです。",
            "reviewer_name": "2級ボイラー技士マスター確認担当",
            "reviewer_profile": "公開前に公式情報への誘導、断定表現、内部リンク、更新日の有無を確認します。",
            "fact_checked_at": TODAY,
            "primary_sources": PRIMARY_SOURCES,
            "original_note": f"{genre}の学習導線と、過去問・用語集への内部リンクを整理した記事です。",
            "user_intent": desc,
            "action_items": ";".join(
                [
                    "公式情報を確認する",
                    points[0] if points else "出題範囲を確認する",
                    "過去問形式の演習を解く",
                    "間違えた問題を復習へ残す",
                    "関連用語を読む",
                ]
            ),
            "update_policy": "試験要項や公式ページが更新されたタイミングで本文と参照元を見直します。",
            "last_reviewed_at": TODAY,
            "next_review_at": NEXT_REVIEW,
            "source_checked_at": TODAY,
            "content_status": "published",
            "revision_note": "SEO記事テンプレート運用ルールに合わせ、目次・信頼性・FAQ・関連記事を整備。",
            "faq_1_question": faqs[0][0],
            "faq_1_answer": faqs[0][1],
            "faq_2_question": faqs[1][0],
            "faq_2_answer": faqs[1][1],
            "related_links": related_for(i, ARTICLES),  # type: ignore[arg-type]
        }
        for sec_i, (heading, body) in enumerate(sections[:7], start=1):
            row[f"section_{sec_i}_heading"] = heading
            row[f"section_{sec_i}_body"] = body
        rows.append(row)

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
