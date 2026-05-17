#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import 2級ボイラー技士 CSV files into the exam-site template data format."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def norm(value: object) -> str:
    return str(value or "").strip()


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"Wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def wareki_to_year_month(label: str) -> tuple[int, int]:
    m = re.search(r"(令和|平成)(\d+)年(\d+)月", label)
    if not m:
        raise ValueError(f"公表年月を解釈できません: {label!r}")
    era, y, month = m.groups()
    year = int(y)
    western = (2018 + year) if era == "令和" else (1988 + year)
    return western, int(month)


def session_id(label: str) -> int:
    year, month = wareki_to_year_month(label)
    return year * 100 + month


def base_question_row(row: dict[str, str]) -> dict[str, object]:
    choices = {f"choice_{i}": norm(row.get(f"選択肢{i}")) for i in range(1, 6)}
    return {
        "type": "single",
        "category": norm(row.get("科目")),
        "tags": norm(row.get("頻出テーマ")) or norm(row.get("OCR確認")) or norm(row.get("由来")),
        "stem": norm(row.get("設問")),
        "preamble": "",
        "statement_a": "",
        "statement_b": "",
        "statement_c": "",
        "statement_d": "",
        **choices,
        "correct": norm(row.get("正答")),
    }


def convert_past(path: Path) -> None:
    rows = []
    for row in read_rows(path):
        pub = norm(row.get("公表年月"))
        notes = [norm(row.get("OCR確認")), norm(row.get("元過去問掲載可否")), norm(row.get("元オリジナル問題ID"))]
        q = base_question_row(row)
        q.update(
            {
                "exam_year": session_id(pub),
                "exam_wareki": pub,
                "question_no": int(norm(row.get("問番号"))),
                "is_exempt": "FALSE",
                "is_invalidated": "FALSE",
                "note": " / ".join(x for x in notes if x),
                "explanation": f"正答は（{norm(row.get('正答'))}）です。公表問題のため、選択肢ごとの理解は一問一答でも確認してください。",
            }
        )
        rows.append(q)
    write_rows(
        DATA / "past_questions.csv",
        [
            "exam_year",
            "exam_wareki",
            "question_no",
            "type",
            "category",
            "tags",
            "stem",
            "preamble",
            "statement_a",
            "statement_b",
            "statement_c",
            "statement_d",
            "choice_1",
            "choice_2",
            "choice_3",
            "choice_4",
            "choice_5",
            "correct",
            "is_exempt",
            "is_invalidated",
            "note",
            "explanation",
        ],
        rows,
    )


def convert_original(path: Path) -> None:
    rows = []
    for row in read_rows(path):
        q = base_question_row(row)
        q.update(
            {
                "question_no": int(norm(row.get("問番号"))),
                "tags": norm(row.get("頻出テーマ")),
                "explanation": norm(row.get("解説")),
            }
        )
        rows.append(q)
    write_rows(
        DATA / "original_questions.csv",
        [
            "question_no",
            "type",
            "category",
            "tags",
            "stem",
            "preamble",
            "statement_a",
            "statement_b",
            "statement_c",
            "statement_d",
            "choice_1",
            "choice_2",
            "choice_3",
            "choice_4",
            "choice_5",
            "correct",
            "explanation",
        ],
        rows,
    )


def convert_ichimon(path: Path) -> None:
    rows = []
    for row in read_rows(path):
        pub = norm(row.get("公表年月"))
        rows.append(
            {
                "id": norm(row.get("一問一答ID")),
                "question": norm(row.get("問題文")),
                "answer": norm(row.get("正誤")),
                "explanation": f"元問題の正答選択肢は（{norm(row.get('元正答'))}）です。選択肢{norm(row.get('選択肢番号'))}の正誤を確認しましょう。",
                "category": norm(row.get("科目")),
                "tags": pub,
                "source": f"{pub} 問{norm(row.get('元問番号'))}",
                "note": norm(row.get("確認状況")),
            }
        )
    write_rows(
        DATA / "past_questions_marubatsu_all_explanations.csv",
        ["id", "question", "answer", "explanation", "category", "tags", "source", "note"],
        rows,
    )


def convert_glossary(original_path: Path, past_path: Path) -> None:
    by_theme: dict[tuple[str, str], int] = {}
    for row in read_rows(original_path):
        key = (norm(row.get("頻出テーマ")), norm(row.get("科目")))
        if key[0] and key[1]:
            by_theme[key] = by_theme.get(key, 0) + 1
    for row in read_rows(past_path):
        key = (norm(row.get("科目")), norm(row.get("科目")))
        if key[0]:
            by_theme[key] = by_theme.get(key, 0) + 1

    rows = []
    for (theme, category), count in sorted(by_theme.items(), key=lambda x: (x[0][1], x[0][0])):
        rows.append(
            {
                "term": theme,
                "reading": theme,
                "category": category,
                "tags": "頻出テーマ",
                "short_def": f"{category}で確認したい頻出テーマ。",
                "definition": f"{theme}は、2級ボイラー技士試験の{category}で問われやすい学習テーマです。",
                "related_terms": category,
                "legal_basis": "",
                "importance": "A" if count >= 10 else "B",
                "explanation": f"過去公表問題と実践演習で、{theme}に関する代表的な知識・用語・数値を確認しましょう。",
            }
        )
    write_rows(
        DATA / "glossary_terms.csv",
        ["term", "reading", "category", "tags", "short_def", "definition", "related_terms", "legal_basis", "importance", "explanation"],
        rows,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--ichimon", required=True)
    parser.add_argument("--past", required=True)
    args = parser.parse_args()

    original = Path(args.original)
    ichimon = Path(args.ichimon)
    past = Path(args.past)
    convert_past(past)
    convert_original(original)
    convert_ichimon(ichimon)
    convert_glossary(original, past)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
