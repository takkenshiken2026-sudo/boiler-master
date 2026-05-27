#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用語詳細記事を手作り品質の本文・FAQ・例題で全件リライトする。

平易な文体・具体例付きの要点・詳しい覚え方・FAQ4件を生成する。
比較表は glossary_comparison_registry を利用。

  python3 tools/handwrite_glossary_articles.py --all --include-themes
  python3 tools/handwrite_glossary_articles.py --all --no-snippets  # スニペットを無視して全再生成
  python3 tools/build_glossary_pages.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import split_semicolon
from tools.deepen_glossary_articles import (
    build_comparison_html,
    filter_related,
)
from tools.glossary_article_compose import (
    FIELD_LABEL,
    compose_body,
    compose_exam_points,
    compose_explanation,
    compose_example,
    compose_faqs,
    compose_key_summary,
    compose_lead,
    compose_memory,
    compose_mistakes,
    compose_title,
)
from tools.glossary_handwritten_snippets import SNIPPET_OVERRIDES
from tools.internal_links import is_theme_row, norm
from tools.rewrite_glossary_articles import (
    CATEGORIES,
    FIELD_SHORT,
    GLOSSARY_CSV,
    GLOSSARY_FIELDNAMES,
    term_kind,
)
from tools.site_config import exam_name


def generate_term_content(row: dict, *, use_snippets: bool = True) -> dict[str, str]:
    term = norm(row.get("term"))
    category = norm(row.get("category"))
    short = norm(row.get("short_def"))
    detail = norm(row.get("definition"))
    related = filter_related(term, split_semicolon(norm(row.get("related_terms"))))
    importance = norm(row.get("importance")) or "A"
    kind = term_kind(term, category)

    snippet = SNIPPET_OVERRIDES.get(term, {}) if use_snippets else {}
    comparison_html = snippet.get("comparison_html") or build_comparison_html(term, related)
    has_table = bool(comparison_html)

    body = snippet.get("term_detail_body") or compose_body(
        term, short, detail, category, related, kind, has_table
    )
    exam_pts = compose_exam_points(term, short, detail, kind, category, related)
    mistakes = compose_mistakes(term, kind, related)
    if snippet.get("exam_points"):
        exam_pts = split_semicolon(snippet["exam_points"])
    if snippet.get("common_mistakes"):
        mistakes = split_semicolon(snippet["common_mistakes"])

    key_summary = snippet.get("short_def") or compose_key_summary(
        term, short, detail, kind, category, related
    )
    memory_tip = snippet.get("memory_tip") or compose_memory(
        term, kind, category, short, related, has_table
    )
    expl = snippet.get("explanation") or compose_explanation(term, detail, short, kind)
    ex_q, ex_a = compose_example(term, short, detail, kind, category)
    if snippet.get("example_question"):
        ex_q = snippet["example_question"]
        ex_a = snippet.get("example_answer", ex_a)

    (q1, a1), (q2, a2), (q3, a3), (q4, a4) = compose_faqs(
        term, short, detail, category, kind, related, exam_pts, mistakes
    )

    return {
        "short_def": key_summary,
        "article_title": snippet.get("article_title") or compose_title(term, category),
        "article_lead": snippet.get("article_lead") or compose_lead(term, short, detail, category),
        "term_detail_body": body,
        "exam_points": ";".join(exam_pts),
        "common_mistakes": ";".join(mistakes),
        "memory_tip": memory_tip,
        "explanation": expl,
        "example_question": ex_q,
        "example_answer": ex_a,
        "comparison_html": comparison_html,
        "faq_1_question": snippet.get("faq_1_question") or q1,
        "faq_1_answer": snippet.get("faq_1_answer") or a1,
        "faq_2_question": snippet.get("faq_2_question") or q2,
        "faq_2_answer": snippet.get("faq_2_answer") or a2,
        "faq_3_question": snippet.get("faq_3_question") or q3,
        "faq_3_answer": snippet.get("faq_3_answer") or a3,
        "faq_4_question": snippet.get("faq_4_question") or q4,
        "faq_4_answer": snippet.get("faq_4_answer") or a4,
        "tags": norm(row.get("tags")) or "重要用語;頻出用語",
        "importance": importance,
    }


def handwrite_row(row: dict) -> dict[str, str]:
    return generate_term_content(row, use_snippets=True)


def handwrite_theme_row(row: dict) -> dict[str, str]:
    term = norm(row.get("term"))
    category = norm(row.get("category"))
    related = filter_related(term, split_semicolon(norm(row.get("related_terms"))))
    rel_names = related_phrase_theme(term, related, 5)
    field = FIELD_LABEL.get(category, category)

    body = (
        f"「{term}」は、{category}分野でまとめて学ぶテーマです。"
        f"用語をバラバラに暗記するのではなく、{rel_names}などを意味のつながりで整理すると、"
        f"過去問の選択肢に強くなります。\n\n"
        f"たとえば、テーマ名だけ覚えて個別の定義が説明できない状態だと、"
        f"似た語が並んだ選択肢で迷いやすくなります。関連用語ごとに「何が違うか」を一言で言えるようにしましょう。\n\n"
        f"学習の流れ：①試験ガイドで分野の全体像 → ②このページの関連用語を読む → "
        f"③過去問形式で正誤を仕分ける。弱点になった語句だけ、各用語ページで深掘りしてください。"
    )
    exam_pts = (
        f"{category}の過去問で{term}に関係する語句を記録する;"
        f"関連用語5件以上を読んで意味の違いを整理する;"
        f"同分野の過去問を5問以上解いて復習リストに残す;"
        f"試験ガイドの科目別記事で弱点を補う"
    )
    summary = (
        f"「{term}」は、{category}でまとめて押さえる学習テーマです。\n\n"
        f"具体例：過去問では、テーマに含まれる複数の用語が並んだ選択肢で、"
        f"定義の取り違えや手順の前後の誤りが問われることが多いです。"
        f"まず関連語の一覧を眺め、似た語の違いを表にまとめると効率的です。"
    )
    memory = (
        f"テーマ名「{term}」→ 関連語リスト（5語以上）→ 過去問5問で確認、の順で覚える。\n\n"
        f"整理のコツ：関連語を「目的・タイミング・主体」のどれで区別するか決め、"
        f"ノートの見出しをそろえる。\n\n"
        f"直前チェック：テーマに含まれる語を3つ、違いを一言ずつ言えるか確認する。"
    )
    return {
        "short_def": summary,
        "article_title": f"【{FIELD_LABEL.get(category, category)}】{term}の学習の進め方｜2級ボイラー技士",
        "article_lead": (
            f"「{term}」を起点に、{category}の学習を整理するページです。"
            f"関連用語と過去問演習への導線をまとめています。"
        ),
        "term_detail_body": body,
        "exam_points": exam_pts,
        "common_mistakes": (
            f"テーマ名だけ覚え、選択肢の言い換えに対応できない;"
            f"関連語の細かな違いを見落とす"
        ),
        "memory_tip": memory,
        "explanation": (
            f"試験では{term}に関連する知識が、{category}の選択肢として問われます。"
            f"関連用語ページと往復して定着を図ってください。"
        ),
        "example_question": f"「{term}」を学ぶとき、最初に何をすべきか。",
        "example_answer": "分野の全体像（試験ガイド）を確認し、関連用語と過去問で定着を確認する。",
        "comparison_html": "",
        "faq_1_question": f"「{term}」はどの記事とあわせて学ぶとよいですか？",
        "faq_1_answer": (
            f"同分野の試験ガイド記事で全体像を押さえ、"
            f"このページの関連用語リンクから個別の用語解説へ進んでください。"
        ),
        "faq_2_question": f"{exam_name()}で「{term}」はどう出ますか？",
        "faq_2_answer": (
            f"主に「{field}」から、関連する複数語が組み合わされた選択肢として問われます。"
            f"個別の定義と、語と語の違いの両方を確認してください。"
        ),
        "faq_3_question": f"「{term}」学習でよくある失敗は？",
        "faq_3_answer": (
            f"見出しだけ暗記し、類似語の違いを説明できないことです。"
            f"関連語ページで比較表を使い、違いを言葉にしてください。"
        ),
        "faq_4_question": f"「{term}」の復習のコツは？",
        "faq_4_answer": (
            f"週1回、関連語を5語選び、正しい記述と誤った記述を1組ずつ作って声に出す。"
            f"過去問演習で間違えた語だけ深掘りすると効率がよいです。"
        ),
        "tags": "頻出テーマ;学習導線",
        "importance": norm(row.get("importance")) or "A",
    }


def related_phrase_theme(term: str, related: list[str], max_n: int) -> str:
    names = [r for r in related if r != term][:max_n]
    if not names:
        return "同分野の用語"
    if len(names) == 1:
        return f"「{names[0]}」"
    return f"「{'」「'.join(names)}」"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", help="対象分野")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--include-themes", action="store_true", help="頻出テーマ行も手書き")
    ap.add_argument(
        "--no-snippets",
        action="store_true",
        help="glossary_handwritten のスニペットを使わずエンジンで全再生成",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not GLOSSARY_CSV.is_file():
        print(f"Missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    targets = list(CATEGORIES) if args.all or not args.category else [args.category]
    if args.category and args.category not in CATEGORIES:
        print(f"Unknown category: {args.category}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    fieldnames = list(GLOSSARY_FIELDNAMES)
    for col in ("comparison_html", "faq_4_question", "faq_4_answer"):
        if col not in fieldnames:
            fieldnames.append(col)

    updated = 0
    themes = 0
    use_snippets = not args.no_snippets
    for cat in targets:
        n = 0
        for row in rows:
            if norm(row.get("category")) != cat:
                continue
            if is_theme_row(row):
                if not args.include_themes:
                    continue
                content = handwrite_theme_row(row)
                themes += 1
            else:
                content = generate_term_content(row, use_snippets=use_snippets)
                n += 1
            for k, v in content.items():
                row[k] = v
            updated += 1
        extra = f" (+{themes} themes)" if args.include_themes and themes else ""
        mode = "engine only" if not use_snippets else "with snippets"
        print(f"handwrote [{cat}]: {n} terms{extra} ({mode})")

    if args.dry_run:
        print(f"dry-run: would update {updated} rows")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") or "" for k in fieldnames})

    print(f"Updated {updated} rows ({updated - themes} individual, {themes} themes)")
    print("Next: python3 tools/build_glossary_pages.py")
    if args.no_snippets:
        print("Optional: python3 tools/build_handwritten_modules.py  # スニペット同期")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
