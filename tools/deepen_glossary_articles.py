#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用語詳細記事の品質を深化する（全個別用語向け）。

- 定義・関連用語を本文に反映し、汎用テンプレ文を排除
- 比較表（登録済みペア + 関連用語との簡易表）
- 例題・FAQ・試験ポイントの具体化

実行例:
  python3 tools/deepen_glossary_articles.py --category "ボイラーの構造に関する知識"
  python3 tools/deepen_glossary_articles.py --all
  python3 tools/apply_glossary_overrides.py
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
from tools.glossary_article_overrides import ARTICLE_OVERRIDES
from tools.glossary_comparison_registry import comparison_for_term
from tools.internal_links import is_theme_row, norm
from tools.rewrite_glossary_articles import (
    CATEGORIES,
    FIELD_SHORT,
    GLOSSARY_CSV,
    GLOSSARY_FIELDNAMES,
    exam_points_list,
    mistakes_list,
    memory_tip_text,
    term_kind,
)
from tools.site_config import exam_name

STUDY_TIP_BY_CATEGORY = {
    "ボイラーの構造に関する知識": (
        "構造分野の過去問では、系統図の読み取りと附属装置の役割がセットで問われます。"
        "この用語を図上の位置に置きながら、関連用語ページへリンクして往復してください。"
    ),
    "ボイラーの取扱いに関する知識": (
        "取扱い分野では「いつ・何のために・やってはいけないこと」の3点が正誤の分かれ目です。"
        "異常時の最初の対応まで含めて、手順の順序を声に出して確認すると定着しやすくなります。"
    ),
    "燃料及び燃焼に関する知識": (
        "燃焼分野は数値（空気比・発熱量・排ガス成分）と現象説明がセットで出ます。"
        "増やす・減らすと何が起きるかを短いメモにしてから演習に入ってください。"
    ),
    "関係法令": (
        "法令分野は主体（誰が）・時期（いつ）・要否（届出・検査）の整理が重要です。"
        "公式テキストの数字と手続名を、用語ごとに1行メモで残しておくと復習が速くなります。"
    ),
}


def pick_variant(term: str, options: list[str]) -> str:
    if not options:
        return ""
    return options[hash(term) % len(options)]


def filter_related(term: str, related: list[str]) -> list[str]:
    out: list[str] = []
    for r in related:
        if not r or r == term:
            continue
        if r not in out:
            out.append(r)
    return out


def opening_paragraph(
    term: str, kind: str, category: str, short: str, detail: str
) -> str:
    s = short.rstrip("。")
    d = detail.rstrip("。") if detail else ""
    if d and d != s:
        core = f"{s}。{d}。"
    elif d:
        core = f"{d}。"
    else:
        core = f"{s}。"

    if kind == "law":
        tail = "届出・検査・記録の要否を問う選択肢では、主体と期限の組み合わせが正誤の鍵になります。"
    elif kind == "operation":
        tail = "手順問題では実施タイミング（点火前・運転中・停止後）と、誤操作のリスクがセットで出ます。"
    elif kind == "combustion":
        tail = "燃焼効率・排ガス・安全（CO、黒煙、すす）への影響まで一言で説明できると得点源になります。"
    elif kind == "equipment" and any(k in term for k in ("節炭", "予熱", "エコノ", "回収")):
        tail = "排ガス熱の回収装置として、効率向上と腐食・漏れなどの運転上の注意が同時に問われます。"
    elif kind == "equipment":
        tail = "系統図上の位置と、他の計器・弁・安全装置との役割分担をセットで押さえてください。"
    elif kind == "concept":
        tail = "定義に加え、数値が増減したときの影響（効率・安全・他の用語との関係）までつなげます。"
    elif kind == "boiler_type":
        tail = "水量・起動時間・適用法令・水質管理の違いが、構造問題と法令問題の両方に現れます。"
    else:
        tail = f"{FIELD_SHORT.get(category, '本分野')}の文脈で、近い用語との違いが問われることが多いです。"

    return f"{term}は、{core}{tail}"


def exam_focus_paragraph(term: str, kind: str, category: str, detail: str) -> str:
    d = detail.rstrip("。")
    if kind == "law" and "検査" in term:
        return (
            f"過去問では、{term}の目的（いつ・誰が・何を確認するか）と、"
            "使用検査・性能検査・定期自主検査・再使用検査など他の検査との違いが頻出です。"
            "下の比較表がある場合は、手続の流れを表で見比べてから暗記してください。"
        )
    if kind == "operation" and any(k in term for k in ("水位", "だき", "吹出")):
        return (
            f"{term}は安全運転の核心に関わります。"
            "異常時は「燃焼を続ける／急給水する」など誤った対応が誤答になりやすいので、"
            "公式テキストの手順どおりに整理してください。"
        )
    if kind == "combustion":
        return (
            f"選択肢では{d or term}の因果が言い換えられます。"
            "空気量・燃料量・排ガス分析の数値と結びつけ、"
            "「大きすぎ／小さすぎ」それぞれの結果を逆にしないよう注意してください。"
        )
    if "弁" in term:
        return (
            "名称が近い弁（安全弁・逃がし弁・止弁・放散弁など）と目的が入れ替わる選択肢に注意してください。"
            "自動で開くか、操作で開閉するか、流れを遮断するかを軸に整理します。"
        )
    return pick_variant(
        term,
        [
            f"試験では「{d}」という説明の一部が変形され、似た用語と取り違える設問になります。"
            "定義のキーワードだけでなく、目的と条件までセットで覚えてください。",
            f"{exam_name()}の{d or category}では、正しい記述／誤った記述の組み合わせで"
            f"{term}の理解度が問われます。関連用語との違いを説明できる状態を目標にしてください。",
        ],
    )


def related_paragraph(
    term: str, category: str, related: list[str], has_comparison: bool
) -> str:
    if not related:
        return STUDY_TIP_BY_CATEGORY.get(
            category,
            "同分野の用語索引から近い語を探し、定義の違いをメモしてください。",
        )
    names = "」「".join(related[:3])
    cmp_note = (
        "本文下の比較表で共通点と違いを確認し、"
        if has_comparison
        else ""
    )
    return (
        f"学習の次のステップは、「{names}」の用語ページを読み、"
        f"{cmp_note}過去問形式の演習で3語を並べた正誤問題として仕分けることです。"
    )


def build_detail_body(
    term: str,
    category: str,
    short: str,
    detail: str,
    kind: str,
    related: list[str],
    has_comparison: bool,
) -> str:
    paragraphs = [
        opening_paragraph(term, kind, category, short, detail),
        exam_focus_paragraph(term, kind, category, detail),
        related_paragraph(term, category, related, has_comparison),
        STUDY_TIP_BY_CATEGORY.get(category, ""),
    ]
    return "\n\n".join(p for p in paragraphs if p.strip())


def build_comparison_html(term: str, related: list[str]) -> str:
    """登録済みの比較表、または関連用語経由で共有される比較表のみ付与。"""
    registered = comparison_for_term(term)
    if registered:
        return registered
    for rel in related:
        peer_cmp = comparison_for_term(rel)
        if peer_cmp:
            return peer_cmp
    return ""


def build_example_qa(term: str, short: str, detail: str, kind: str) -> tuple[str, str]:
    q = f"次のうち、「{term}」について正しい説明はどれか。"
    base = short.rstrip("。")
    d = detail.rstrip("。")
    if kind == "law":
        a = f"正解の要点：{base}。手続の主体・時期・要否を条文の趣旨どおりに選ぶ。"
    elif kind == "operation":
        a = f"正解の要点：{base}。実施タイミングと安全上の目的が一致している選択肢を選ぶ。"
    else:
        a = f"正解の要点：{base}。"
        if d and d != base:
            a += f" {d}。"
    return q, a


def build_faqs(
    term: str,
    short: str,
    detail: str,
    exam_pts: list[str],
    mistakes: list[str],
    category: str,
) -> tuple[tuple[str, str], tuple[str, str], tuple[str, str]]:
    d = detail.rstrip("。")
    q1 = f"{term}とは何ですか？"
    a1 = f"{term}は、{short.rstrip('。')}。"
    if d and d not in short:
        a1 += f"{d}。"

    q2 = f"{exam_name()}で{term}はどの分野で重要ですか？"
    a2 = (
        f"主に「{category}」で出題されます。"
        + (" ".join(exam_pts[:2]) if exam_pts else "")
    )

    q3 = f"{term}でよくある誤解は？"
    a3 = mistakes[0] if mistakes else (
        f"定義だけを覚え、「{term}」の目的や条件が変わった選択肢に対応できないことです。"
    )
    return (q1, a1), (q2, a2), (q3, a3)


def explanation_text(term: str, kind: str, category: str, short: str, detail: str) -> str:
    base = detail.rstrip("。") or short.rstrip("。")
    tails = {
        "equipment": "図や系統を思い浮かべながら読むと、他装置との違いが整理しやすくなります。",
        "operation": "異常時の最初の対応と、日常の手順を混同しないよう注意してください。",
        "combustion": "排ガス分析や空気比の数値とセットで復習すると理解が定着します。",
        "law": "最新の試験要項・公式テキストで数字と主体を確認してください。",
        "concept": "関連する別概念との比較表を見ながら覚えると効率的です。",
        "boiler_type": "水管・炉筒煙管・貫流との比較が構造分野の定番です。",
    }
    tail = tails.get(kind, f"{category}では言い換えに注意してください。")
    return f"{base}。{tail}"


def deepen_row(row: dict) -> dict[str, str]:
    term = norm(row.get("term"))
    category = norm(row.get("category"))
    short = norm(row.get("short_def"))
    detail = norm(row.get("definition"))
    related = filter_related(term, split_semicolon(norm(row.get("related_terms"))))
    importance = norm(row.get("importance")) or "A"
    kind = term_kind(term, category)

    comparison_html = build_comparison_html(term, related)
    term_detail_body = build_detail_body(
        term, category, short, detail, kind, related, bool(comparison_html)
    )
    exam_pts = exam_points_list(term, kind, category, short, related)
    mistakes = mistakes_list(term, kind, related, short)
    memory = memory_tip_text(term, kind, category, short)
    expl = explanation_text(term, kind, category, short, detail)
    ex_q, ex_a = build_example_qa(term, short, detail, kind)
    (q1, a1), (q2, a2), (q3, a3) = build_faqs(term, short, detail, exam_pts, mistakes, category)

    field = FIELD_SHORT.get(category, "本分野")
    article_title = f"{term}とは？2級ボイラー技士試験で押さえる意味・{field}のポイント"
    article_lead = (
        f"{short.rstrip('。')}。"
        f"{field}分野で頻出の{term}について、定義の整理、試験で問われやすい角度、"
        f"よくある誤解、関連用語へのリンクをまとめました。"
    )

    return {
        "article_title": article_title,
        "article_lead": article_lead,
        "term_detail_body": term_detail_body,
        "exam_points": ";".join(exam_pts),
        "common_mistakes": ";".join(mistakes),
        "memory_tip": memory,
        "explanation": expl,
        "example_question": ex_q,
        "example_answer": ex_a,
        "comparison_html": comparison_html,
        "faq_1_question": q1,
        "faq_1_answer": a1,
        "faq_2_question": q2,
        "faq_2_answer": a2,
        "faq_3_question": q3,
        "faq_3_answer": a3,
        "tags": norm(row.get("tags")) or "重要用語;頻出用語",
        "importance": importance,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", help="対象分野")
    ap.add_argument("--all", action="store_true", help="4分野すべて")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not GLOSSARY_CSV.is_file():
        print(f"Missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    targets: list[str]
    if args.all or not args.category:
        targets = list(CATEGORIES)
    else:
        if args.category not in CATEGORIES:
            print(f"Unknown category: {args.category}", file=sys.stderr)
            return 1
        targets = [args.category]

    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    fieldnames = list(GLOSSARY_FIELDNAMES)
    if "comparison_html" not in fieldnames:
        fieldnames.append("comparison_html")

    updated = 0
    skipped_override = 0
    for cat in targets:
        cat_count = 0
        for row in rows:
            if norm(row.get("category")) != cat:
                continue
            if is_theme_row(row):
                continue
            term = norm(row.get("term"))
            if term in ARTICLE_OVERRIDES:
                skipped_override += 1
                continue
            content = deepen_row(row)
            for key, val in content.items():
                row[key] = val
            cat_count += 1
            updated += 1
        print(f"deepened [{cat}]: {cat_count} terms")

    if args.dry_run:
        print(f"dry-run: would update {updated} rows (skipped overrides: {skipped_override})")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") or "" for k in fieldnames})

    print(f"Updated {updated} rows (skipped {skipped_override} override terms)")
    print("Next: python3 tools/apply_glossary_overrides.py")
    print("      python3 tools/build_glossary_pages.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
