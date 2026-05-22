#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用語詳細記事（glossary_terms.csv）を読みやすい本文にリライトする。

対象: 頻出テーマ行以外の個別用語。
分野ごとに順次実行: --category "ボイラーの構造に関する知識" など。

実行例:
  python3 tools/rewrite_glossary_articles.py --category "ボイラーの構造に関する知識"
  python3 tools/rewrite_glossary_articles.py --all
  python3 tools/build_glossary_pages.py
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import split_semicolon
from tools.internal_links import is_theme_row, norm
from tools.site_config import exam_name

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

# build_glossary_pages.py が参照する列（既存10列 + 詳細記事用）
GLOSSARY_FIELDNAMES = [
    "term",
    "reading",
    "category",
    "tags",
    "short_def",
    "definition",
    "related_terms",
    "legal_basis",
    "importance",
    "explanation",
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "example_question",
    "example_answer",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
    "comparison_html",
]

CATEGORIES = (
    "ボイラーの構造に関する知識",
    "ボイラーの取扱いに関する知識",
    "燃料及び燃焼に関する知識",
    "関係法令",
)

FIELD_SHORT = {
    "ボイラーの構造に関する知識": "構造",
    "ボイラーの取扱いに関する知識": "取扱い",
    "燃料及び燃焼に関する知識": "燃料・燃焼",
    "関係法令": "法令",
}

GENERIC_EXPL = "選択肢の正誤判断に直結しやすい用語です"


def term_kind(term: str, category: str) -> str:
    t = term
    if category == "関係法令" or any(
        k in t for k in ("検査", "届", "技士", "主任者", "作業者", "規則", "禁止", "届出")
    ):
        return "law"
    if any(k in t for k in ("燃焼", "点火", "バーナ", "燃料", "空気", "排ガス", "すす", "重油", "ガス", "油")):
        if category == "燃料及び燃焼に関する知識":
            return "combustion"
    if any(
        k in t
        for k in (
            "吹出し",
            "ブロー",
            "たき",
            "点火",
            "停止",
            "運転",
            "保存",
            "点検",
            "給水",
            "水位",
            "処理",
            "腐食",
            "スケール",
        )
    ):
        if category == "ボイラーの取扱いに関する知識":
            return "operation"
    if any(k in t for k in ("ボイラー", "貫流", "炉筒", "煙管", "水管", "鋳鉄", "丸ボイラー")):
        return "boiler_type"
    if any(
        k in t
        for k in (
            "弁",
            "計",
            "器",
            "管",
            "ポンプ",
            "ファン",
            "タンク",
            "ドラム",
            "ヘッダ",
            "過熱",
            "節炭",
            "予熱",
            "水面",
            "安全",
            "インタ",
        )
    ):
        return "equipment"
    if any(k in t for k in ("圧力", "温度", "熱", "効率", "蒸気", "水", "量", "比", "度")):
        return "concept"
    return "general"


def pick_variant(term: str, options: list[str]) -> str:
    if not options:
        return ""
    return options[hash(term) % len(options)]


def role_sentence(term: str, kind: str, category: str, short: str, detail: str) -> str:
    body = detail or short
    if kind == "equipment":
        return pick_variant(
            term,
            [
                f"{term}は、ボイラー運転で状態を確認したり、異常を早期に察知するために使う附属品・計測器のひとつです。{body}",
                f"現場では{term}の読み取りや動作が、圧力・水位・燃焼の判断につながります。{body}",
            ],
        )
    if kind == "operation":
        return pick_variant(
            term,
            [
                f"{term}は、安全に運転を続けるための取扱い・手順に関わる用語です。タイミングと目的をセットで覚えると、過去問の選択肢に強くなります。",
                f"運転中の判断や異常時対応と結びつく操作です。{body}",
            ],
        )
    if kind == "combustion":
        return pick_variant(
            term,
            [
                f"{term}は、燃料を燃やして有用な熱を得るうえで欠かせない概念・装置です。{body}",
                f"燃焼状態の良し悪しや効率、安全の両面から試験で問われます。{body}",
            ],
        )
    if kind == "law":
        return pick_variant(
            term,
            [
                f"{term}は、ボイラーの設置・検査・運転に関する法令・制度のキーワードです。誰が・いつ・何をするかを整理して覚えます。",
                f"義務の有無や手続の流れが選択肢になりやすい用語です。{body}",
            ],
        )
    if kind == "boiler_type":
        return pick_variant(
            term,
            [
                f"{term}は、ボイラーの形式・構造を分けるときの代表例です。水の循環方式や伝熱面の違いと結びつけて理解します。",
                f"構造の違いが、適用法令・検査区分・運転上の注意に影響することがあります。{body}",
            ],
        )
    if kind == "concept":
        return pick_variant(
            term,
            [
                f"{term}は、熱・蒸気・圧力・効率などを考えるときの基礎概念です。数値や他の用語との関係式で押さえます。",
                f"定義だけでなく、増減や条件が変わると何が起きるかまでつなげると試験で使えます。{body}",
            ],
        )
    return pick_variant(
        term,
        [
            f"{term}は、{category}で繰り返し登場する重要語です。{body}",
            f"試験では言い換えや近い用語との比較で問われることがあります。{body}",
        ],
    )


def exam_points_list(term: str, kind: str, category: str, short: str, related: list[str]) -> list[str]:
    pts: list[str] = []
    field = FIELD_SHORT.get(category, "本分野")
    pts.append(f"「{short.rstrip('。')}」を一言で言えるようにする（{field}の基本語）。")
    if kind == "equipment":
        pts.extend(
            [
                f"{term}の目的（何を見る・何を防ぐか）と、設置・取付け上の要点を整理する。",
                "他の計器・弁・安全装置との役割分担を混同しない（関連用語とセットで確認）。",
                "異常時・運転停止時にどう扱うか、選択肢の正誤で差がつきやすい。",
            ]
        )
    elif kind == "operation":
        pts.extend(
            [
                "実施するタイミング（点火前・運転中・停止後など）と、しなかった場合のリスクを結びつける。",
                "手順の前後関係（例: パージ→点火、暖管→本運転）を順序問題として押さえる。",
                "「やってはいけない操作」との違いを明確にする。",
            ]
        )
    elif kind == "combustion":
        pts.extend(
            [
                "燃焼効率・排ガス・安全（不完全燃焼、CO、黒煙）への影響を短く説明できるようにする。",
                "空気比・理論空気量・過剰空気など、数値・比率の問題と結びつける。",
                "重油・ガスなど燃料種別ごとの注意点があれば分けて覚える。",
            ]
        )
    elif kind == "law":
        pts.extend(
            [
                "義務者（設置者・作業者・選任者）と、届出・検査・記録の要否を区別する。",
                "数値基準（圧力・伝熱面積・容量など）や区分が絡む場合は表で整理する。",
                "「認められない」「原則禁止」「例外で可」などの文言に注意する。",
            ]
        )
    elif kind == "concept":
        pts.extend(
            [
                "定義・単位・符号（増える/減る）を正しく把握する。",
                "関連する別概念（例: ゲージ圧力と絶対圧力）との違いを一言で言えるようにする。",
                "ボイラー効率・損失・運転条件への影響を結びつけて覚える。",
            ]
        )
    else:
        pts.extend(
            [
                f"{category}の出題文脈で、どの装置・操作・法令と一緒に問われるかを把握する。",
                "選択肢の言い換え（似た語・反対語）に弱くならないよう、関連用語を往復する。",
            ]
        )
    if related:
        pts.append(f"関連用語（{'・'.join(related[:3])}）とセットで復習し、違いを説明できるようにする。")
    return pts[:5]


def mistakes_list(term: str, kind: str, related: list[str], short: str) -> list[str]:
    items: list[str] = []
    if related:
        rel = related[0]
        items.append(f"「{rel}」と「{term}」の役割・定義を取り違える（それぞれのページで違いを確認）。")
    if kind == "concept" and "圧力" in term:
        items.append("ゲージ圧力・絶対圧力・大気圧の関係を逆に覚える。")
    if kind == "equipment" and "弁" in term:
        items.append("安全弁・逃がし弁・止弁など、名称が近い弁の目的を混同する。")
    if kind == "operation":
        items.append("実施タイミングを前後逆にする、または「不要」と「禁止」を混同する。")
    if kind == "law":
        items.append("届出・検査・記録の要否を逆に覚える、または期限・主体（誰が行うか）を取り違える。")
    if kind == "combustion":
        items.append("完全燃焼と不完全燃焼の原因・結果（すす、CO、効率低下）を逆に結びつける。")
    items.append(f"定義を丸暗記するだけで、選択肢の言い換えや数値条件に対応できない。")
    if "。" not in short:
        items.append("短い定義だけ覚え、現場での意味や試験での言い換えを軽視する。")
    return items[:4]


def memory_tip_text(term: str, kind: str, category: str, short: str) -> str:
    tips = {
        "equipment": f"「{term}＝何を見る／止めるか」を先に固定し、関連する弁・計と役割分担で覚える。",
        "operation": f"「いつ・なぜ・何が危ないか」の3点セットで{term}を整理する。",
        "combustion": f"空気・燃料・排ガスのバランスで{term}を位置づける。",
        "law": f"主体（誰）・タイミング（いつ）・要否（届出/検査）の3列で{term}をメモする。",
        "concept": f"定義→単位→増減の影響、の順で{term}をカード化する。",
        "boiler_type": f"構造スケッチとセットで{term}の特徴（循環・水量・用途）を1行で。",
    }
    return tips.get(kind, f"短い定義のあと、{FIELD_SHORT.get(category, '本分野')}の過去問で出た言い回しを1つ足す。")


def explanation_text(term: str, kind: str, category: str, short: str, detail: str) -> str:
    if GENERIC_EXPL not in (detail or ""):
        base = detail
    else:
        base = short
    extras = {
        "equipment": (
            f"過去問では、{term}の有無・役割・他装置との違いを問う形式が多いです。"
            "図や系統を頭に描きながら読むと定着しやすくなります。"
        ),
        "operation": (
            f"手順問題では、{term}の前後（例: 点火前か、停止後か）が正誤の分かれ目になります。"
            "異常時の最初の対応と混同しないよう整理してください。"
        ),
        "combustion": (
            f"燃焼計算・空気比・排ガス温度など、数値とセットで出る場合は計算過程より"
            f"「増やすとどうなるか」を押さえるとよいです。"
        ),
        "law": (
            f"法令問題は、{term}が「誰に」「いつ」「何を義務づけるか」の形で出やすいです。"
            "最新の試験要項・公式テキストで数字と主体を確認してください。"
        ),
    }
    tail = extras.get(kind, f"{category}の選択肢では、近い語句への言い換えに注意してください。")
    return f"{base.rstrip('。')}。{tail}"


def faq_triplet(term: str, short: str, detail: str, exam_pts: list[str], mistakes: list[str]) -> tuple[
    tuple[str, str], tuple[str, str], tuple[str, str]
]:
    q1 = f"{term}とは何ですか？"
    a1 = f"{term}は、{short.rstrip('。')}。{detail.rstrip('。')}。"
    q2 = f"{exam_name()}で{term}はどう出ますか？"
    a2 = " ".join(exam_pts[:2]) if exam_pts else explanation_text(term, "general", "", short, detail)
    rel = mistakes[0] if mistakes else f"定義だけを覚え、言い換えや関連語との違いを確認しないことです。"
    q3 = f"{term}でよくある誤解は？"
    a3 = rel
    return (q1, a1), (q2, a2), (q3, a3)


def rewrite_row(row: dict) -> dict[str, str]:
    term = norm(row.get("term"))
    category = norm(row.get("category"))
    short = norm(row.get("short_def"))
    detail = norm(row.get("definition"))
    related = split_semicolon(norm(row.get("related_terms")))
    importance = norm(row.get("importance")) or "A"
    kind = term_kind(term, category)

    role = role_sentence(term, kind, category, short, detail)
    exam_pts = exam_points_list(term, kind, category, short, related)
    mistakes = mistakes_list(term, kind, related, short)
    memory = memory_tip_text(term, kind, category, short)
    expl = explanation_text(term, kind, category, short, detail)

    paragraphs = [
        role,
        pick_variant(
            term,
            [
                f"2級ボイラー技士の学習では、{term}を単独で暗記するより、"
                f"同じ分野の装置・操作・数値と結びつけると理解が安定します。",
                f"一問一答や過去問形式の演習で「正しい記述／誤った記述」を選ぶ練習に使うと効果的です。",
            ],
        ),
        pick_variant(
            term,
            [
                f"関連する用語（{'・'.join(related[:4]) or '同分野の索引'}）と往復し、"
                f"試験本番では選択肢の言い換えに惑わされないよう整理しておきましょう。",
                f"試験では定義文の一部が変形された選択肢が出るため、"
                f"キーワードだけでなく目的・条件まで押さえておくことが重要です。",
            ],
        ),
    ]
    term_detail_body = "\n\n".join(paragraphs)

    article_title = f"{term}とは？試験で押さえる意味・使い方・注意点"
    article_lead = (
        f"{short.rstrip('。')}。"
        f"{FIELD_SHORT.get(category, '本分野')}で頻出の{term}について、"
        f"定義の整理、試験ポイント、よくある誤解、関連用語へのリンクをまとめました。"
    )

    (q1, a1), (q2, a2), (q3, a3) = faq_triplet(term, short, detail, exam_pts, mistakes)

    return {
        "article_title": article_title,
        "article_lead": article_lead,
        "term_detail_body": term_detail_body,
        "exam_points": ";".join(exam_pts),
        "common_mistakes": ";".join(mistakes),
        "memory_tip": memory,
        "explanation": expl,
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
    ap.add_argument("--category", help="対象分野（省略時は --all と同様）")
    ap.add_argument("--all", action="store_true", help="4分野すべてを順に処理")
    ap.add_argument("--dry-run", action="store_true", help="CSVを書き換えない")
    args = ap.parse_args()

    if not GLOSSARY_CSV.is_file():
        print(f"Missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    targets: list[str] = []
    if args.all or not args.category:
        targets = list(CATEGORIES)
    else:
        if args.category not in CATEGORIES:
            print(f"Unknown category. Choose from: {CATEGORIES}", file=sys.stderr)
            return 1
        targets = [args.category]

    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    fieldnames = list(GLOSSARY_FIELDNAMES)
    updated = 0

    for cat in targets:
        cat_count = 0
        for row in rows:
            if norm(row.get("category")) != cat:
                continue
            if is_theme_row(row):
                continue
            content = rewrite_row(row)
            for key, val in content.items():
                row[key] = val
            cat_count += 1
            updated += 1
        print(f"rewrote [{cat}]: {cat_count} terms")

    if args.dry_run:
        print(f"dry-run: would update {updated} rows")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {k: row.get(k, "") or "" for k in fieldnames}
            writer.writerow(out)

    print(f"Updated {updated} rows in {GLOSSARY_CSV}")
    print("Next: python3 tools/build_glossary_pages.py && python3 tools/validate_csv.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
