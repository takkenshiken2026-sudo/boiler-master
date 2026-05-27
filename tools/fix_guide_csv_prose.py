#!/usr/bin/env python3
"""Fix double periods and operator '検索意図' phrasing in guide_articles.csv."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

TEXT_COLS = [
    "meta_description",
    "lead",
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
    "faq_3_question",
    "faq_3_answer",
]


def fix_text(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"。{2,}", "。", s)
    s = s.replace(
        "検索意図は次のとおりです：",
        "この記事では、",
    )
    # 「…整理したい。。制度」→ single period before 制度
    s = re.sub(r"したい。+制度", "したい。制度", s)
    s = re.sub(r"します。+制度", "します。制度", s)
    return s


def main() -> int:
    rows: list[dict[str, str]] = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("empty csv", file=sys.stderr)
            return 1
        for row in reader:
            for col in TEXT_COLS:
                if col in row and row[col]:
                    row[col] = fix_text(row[col])
            rows.append(row)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    text = CSV_PATH.read_text(encoding="utf-8")
    print(f"Fixed {CSV_PATH.name}: 。。={text.count('。。')}, 検索意図={text.count('検索意図')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
