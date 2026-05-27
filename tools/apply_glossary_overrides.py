#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glossary_article_overrides を CSV に反映する。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.deepen_glossary_articles import build_example_qa
from tools.glossary_article_overrides import ARTICLE_OVERRIDES
from tools.glossary_comparison_registry import comparison_for_term
from tools.internal_links import norm
from tools.rewrite_glossary_articles import GLOSSARY_CSV, GLOSSARY_FIELDNAMES, term_kind

OVERRIDE_FIELDS = (
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "explanation",
    "comparison_html",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
)


def main() -> int:
    if not GLOSSARY_CSV.is_file():
        print(f"Missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    fieldnames = list(GLOSSARY_FIELDNAMES)
    if "comparison_html" not in fieldnames:
        fieldnames.append("comparison_html")

    applied = 0
    for row in rows:
        term = norm(row.get("term"))
        patch = ARTICLE_OVERRIDES.get(term)
        if not patch:
            continue
        for key, val in patch.items():
            if key in OVERRIDE_FIELDS or key in fieldnames:
                row[key] = val
        cmp_html = norm(row.get("comparison_html")) or comparison_for_term(term)
        if cmp_html:
            row["comparison_html"] = cmp_html
        if not norm(row.get("example_question")):
            kind = term_kind(term, norm(row.get("category")))
            q, a = build_example_qa(
                term,
                norm(row.get("short_def")),
                norm(row.get("definition")),
                kind,
            )
            row["example_question"] = q
            row["example_answer"] = a
        applied += 1

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") or "" for k in fieldnames})

    print(f"Applied overrides to {applied} terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
