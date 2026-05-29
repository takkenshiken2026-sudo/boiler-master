#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""過去問 CSV と生成解説 HTML の正答・解説整合性を検証する。"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_past_question_pages import parse_correct
from tools.q_explanation import (
    build_choice_commentary,
    build_explanation_html,
    parse_explanation_choices,
    question_ask_mode,
)

PAST_CSV = ROOT / "data" / "past_questions.csv"


def norm(s: str | None) -> str:
    return (s or "").strip()


def row_to_page(row: dict) -> dict:
    opts = [norm(row.get(f"choice_{i}")) for i in range(1, 6)]
    opts = [o for o in opts if o]
    return {
        "stem": row.get("stem", ""),
        "stem_plain": row.get("stem", ""),
        "opts": opts,
        "correct": parse_correct(row.get("correct", "")),
        "category": row.get("category", ""),
        "tags": (row.get("tags") or "").split(","),
        "is_invalidated": norm(row.get("is_invalidated")).upper() == "TRUE",
    }


def validate_row(row: dict) -> list[str]:
    page = row_to_page(row)
    correct = page["correct"]
    if not correct or page["is_invalidated"]:
        return []

    key = f"y{row['exam_year']}/q{int(row['question_no']):02d}"
    errors: list[str] = []

    for field in ("explanation", "explanation_summary", "explanation_correct", "explanation_point"):
        txt = norm(row.get(field))
        if not txt:
            continue
        for m in re.finditer(r"正[答解]は\s*[（(]?(\d+)[）)]?", txt):
            n = int(m.group(1))
            if n != correct:
                errors.append(f"{key}: {field} が correct={correct} と不一致（正答（{n}）と記載）")

    parsed = parse_explanation_choices(norm(row.get("explanation_choices")))
    if correct in parsed:
        errors.append(f"{key}: explanation_choices に正答肢（{correct}）が誤肢として含まれています")

    html = build_explanation_html(page, row)
    if f'q-exp-choice-num">（{correct}）' in html.split("q-exp-wrong-h")[-1]:
        wrong_part = html.split("q-exp-wrong-h", 1)[1] if "q-exp-wrong-h" in html else ""
        if f'q-exp-choice-num">（{correct}）' in wrong_part.split("</section>", 1)[0]:
            errors.append(f"{key}: 生成 HTML の「他の選択肢」に正答（{correct}）が含まれています")

    mode = question_ask_mode(page["stem"])
    for n, _opt, note in build_choice_commentary(page, row):
        if re.search(rf"(?:本問の)?正答[は（(]?{n}[）)]", note):
            errors.append(f"{key}: 誤肢（{n}）の解説がその肢自身を正答としています")

    corr_section = re.search(
        r"q-exp-correct-h.*?(?=q-exp-wrong-h|q-exp-tip-h|</div>)",
        html,
        re.DOTALL,
    )
    if corr_section:
        plain = re.sub(r"<[^>]+>", " ", corr_section.group(0))
        if re.search(rf"（{correct}）[^。]*(?:誤り|不正解|正しくない|適切でない記述)", plain):
            errors.append(f"{key}: 「正解の理由」で正答（{correct}）を誤りと説明しています")

    return errors


def main() -> int:
    if not PAST_CSV.is_file():
        print(f"error: {PAST_CSV} not found", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(PAST_CSV.read_text(encoding="utf-8-sig").splitlines()))
    all_errors: list[str] = []
    for row in rows:
        all_errors.extend(validate_row(row))

    if all_errors:
        print(f"validate_past_explanation_consistency: {len(all_errors)} error(s)", file=sys.stderr)
        for e in all_errors[:50]:
            print(e, file=sys.stderr)
        if len(all_errors) > 50:
            print(f"... and {len(all_errors) - 50} more", file=sys.stderr)
        return 1

    print(f"validate_past_explanation_consistency: OK ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
