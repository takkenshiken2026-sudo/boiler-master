#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/practice_questions.csv の解説を data/past_questions.csv へ同期する。

同一 stem・同一選択肢集合を前提に、正答番号の並び替えを選択肢テキストでマッピングする。
explanation_choices 内の肢番号も past 側の番号へ付け替える。

  python3 tools/sync_past_explanations_from_practice.py
  python3 tools/sync_past_explanations_from_practice.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.q_explanation import parse_explanation_choices

PAST_CSV = ROOT / "data" / "past_questions.csv"
PRACTICE_CSV = ROOT / "data" / "practice_questions.csv"

EXTRA_COLS = (
    "explanation_summary",
    "explanation_correct",
    "explanation_choices",
    "explanation_point",
)


def norm(s: str | None) -> str:
    return (s or "").strip()


def choice_texts(row: dict) -> dict[int, str]:
    out: dict[int, str] = {}
    for i in range(1, 6):
        t = norm(row.get(f"choice_{i}"))
        if t:
            out[i] = t
    return out


def text_to_num(texts: dict[int, str]) -> dict[str, int]:
    return {t: n for n, t in texts.items()}


def find_practice_row(past_row: dict, practice_by_stem: dict[str, list[dict]]) -> dict | None:
    stem = norm(past_row.get("stem"))
    cands = practice_by_stem.get(stem) or []
    if not cands:
        return None
    past_set = set(choice_texts(past_row).values())
    for pr in cands:
        if set(choice_texts(pr).values()) == past_set:
            return pr
    return cands[0]


def remap_choice_refs(text: str, prac_to_past: dict[int, int]) -> str:
    out = text
    for prac_n in sorted(prac_to_past, reverse=True):
        past_n = prac_to_past[prac_n]
        out = re.sub(rf"選択肢\s*{prac_n}\b", f"選択肢{past_n}", out)
        out = re.sub(rf"（{prac_n}）", f"（{past_n}）", out)
        out = re.sub(rf"[（(]{prac_n}[）)]", f"（{past_n}）", out)
    return out


def remap_explanation_choices(raw: str, prac_to_past: dict[int, int], correct: int) -> str:
    parsed = parse_explanation_choices(raw)
    parts: list[str] = []
    for prac_n, note in sorted(parsed.items()):
        past_n = prac_to_past.get(prac_n)
        if not past_n or past_n == correct:
            continue
        parts.append(f"{past_n}:{remap_choice_refs(note, prac_to_past)}")
    return ";".join(parts)


def build_practice_index(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for row in rows:
        out.setdefault(norm(row.get("stem")), []).append(row)
    return out


def sync_row(past_row: dict, practice_row: dict) -> dict[str, str]:
    past_texts = choice_texts(past_row)
    prac_texts = choice_texts(practice_row)
    past_to_text = {n: t for n, t in past_texts.items()}
    text_to_past = text_to_num(past_texts)
    text_to_prac = text_to_num(prac_texts)

    try:
        past_correct = int(past_row["correct"])
        prac_correct = int(practice_row["correct"])
    except (TypeError, ValueError):
        return {}

    correct_text = past_to_text.get(past_correct, "")
    if not correct_text or text_to_past.get(correct_text) != past_correct:
        return {}

    prac_to_past: dict[int, int] = {}
    for text, prac_n in text_to_prac.items():
        past_n = text_to_past.get(text)
        if past_n is not None:
            prac_to_past[prac_n] = past_n

    if prac_to_past.get(prac_correct) != past_correct:
        return {}

    updates: dict[str, str] = {}
    exp = norm(practice_row.get("explanation"))
    if exp and "公表問題のため" not in exp:
        updates["explanation"] = remap_choice_refs(exp, prac_to_past)

    for col in EXTRA_COLS:
        val = norm(practice_row.get(col))
        if not val:
            continue
        if col == "explanation_choices":
            val = remap_explanation_choices(val, prac_to_past, past_correct)
        else:
            val = remap_choice_refs(val, prac_to_past)
        if val:
            updates[col] = val

    return updates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not PAST_CSV.is_file() or not PRACTICE_CSV.is_file():
        print("error: CSV not found", file=sys.stderr)
        return 1

    past_rows = list(csv.DictReader(PAST_CSV.read_text(encoding="utf-8-sig").splitlines()))
    practice_rows = list(csv.DictReader(PRACTICE_CSV.read_text(encoding="utf-8-sig").splitlines()))
    practice_by_stem = build_practice_index(practice_rows)

    fieldnames = list(past_rows[0].keys())
    for col in EXTRA_COLS:
        if col not in fieldnames:
            fieldnames.append(col)

    updated = 0
    skipped = 0
    for row in past_rows:
        pr = find_practice_row(row, practice_by_stem)
        if not pr:
            skipped += 1
            continue
        changes = sync_row(row, pr)
        if not changes:
            skipped += 1
            continue
        for k, v in changes.items():
            row[k] = v
        updated += 1

    print(f"past rows={len(past_rows)} updated={updated} skipped={skipped}")

    if args.dry_run:
        sample = next(r for r in past_rows if norm(r.get("explanation")) and "公表問題" not in r.get("explanation", ""))
        print("sample explanation:", sample["exam_year"], sample["question_no"], sample["explanation"][:120])
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = PAST_CSV.with_suffix(f".csv.bak.{ts}")
    shutil.copy2(PAST_CSV, backup)
    with PAST_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(past_rows)
    print(f"wrote {PAST_CSV} (backup {backup.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
