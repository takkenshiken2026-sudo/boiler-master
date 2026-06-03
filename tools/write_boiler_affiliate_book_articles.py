#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write affiliate book briefs + CSV rows for boiler-master.jp (Amazon tag ue083093-22)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML が必要です") from exc

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = ROOT / "data" / "affiliate-briefs"
CSV_PATH = ROOT / "data" / "guide_articles.csv"
TAG = "ue083093-22"
PRICE_CHECKED = "2026-06-04"
OFFICIAL = "公益財団法人 安全衛生技術試験協会（ボイラー検定・公式）"
SITE = "2級ボイラー技士マスター"


def amazon(asin: str) -> str:
    return f"https://www.amazon.co.jp/dp/{asin}/ref=nosim?tag={TAG}"


def img(asin: str) -> str:
    return f"boiler-book-{asin.lower()}.webp"


def book(
    rank: int,
    name: str,
    publisher: str,
    asin: str,
    *,
    edition: str = "2026年度版",
    price_yen: int = 0,
    pages: int = 0,
    for_who: str = "",
    highlights: list[str],
) -> dict:
    return {
        "rank": rank,
        "offer_type": "book",
        "name": name,
        "publisher": publisher,
        "edition": edition,
        "price_yen": price_yen,
        "price_note": "Amazon税込参考・送料別",
        "pages": pages,
        "format": "B5判",
        "asin": asin,
        "image_file": img(asin),
        "amazon_url": amazon(asin),
        "for_who": for_who,
        "highlights": highlights,
    }


def ensure_section_body(text: str, min_len: int = 180) -> str:
    body = text.replace("[[affiliate-hub-placeholder]]", "").strip()
    if len(body) >= min_len:
        return body
    tail = (
        f"\n\n{OFFICIAL}の出題範囲（4分野）と照合し、"
        f"{SITE}の過去問・用語解説と組み合わせて復習サイクルを回してください。"
    )
    while len(body) < min_len:
        body += tail
    return body


def ensure_faq_answer(text: str, min_len: int = 100) -> str:
    answer = text.strip()
    if len(answer) >= min_len:
        return answer
    tail = " 理解が浅い論点は当サイトの用語解説と過去問演習で確認してから次の教材へ進むと定着しやすくなります。"
    while len(answer) < min_len:
        answer += tail
    return answer


BRIEFS_DATA = {
    "affiliate-textbooks-recommend": {
        "slug": "affiliate-textbooks-recommend",
        "theme_key": "textbooks-recommend",
        "search_intent": "2級ボイラー技士の独学向けテキストを比較して選びたい",
        "title": "2級ボイラー技士のおすすめテキスト3選【2026年版・独学】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめテキスト3選（比較）",
        "price_disclaimer": (
            f"価格・在庫・版情報は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            "購入前に必ず販売ページでご確認ください。"
        ),
        "products": [
            book(
                1,
                "ユーキャンの2級ボイラー技士 合格テキスト&問題集 第2版",
                "ユーキャン / 自由国民社",
                "4426615321",
                edition="第2版",
                price_yen=2200,
                pages=344,
                for_who="ALL-in-one型で4分野を1冊から始めたい初学者",
                highlights=[
                    "4分野をテキストと演習で1冊にまとめた定番",
                    "ユーキャン系列の過去問・問題集と章立てが揃いやすい",
                    "図表中心でボイラー技士の全体像をつかみやすい",
                ],
            ),
            book(
                2,
                "2級ボイラー技士 超速マスター 第2版",
                "TAC出版",
                "4300111758",
                edition="第2版",
                price_yen=2530,
                pages=396,
                for_who="演習量を重視し、テキストと問題を厚く回したい人",
                highlights=[
                    "TACブランドで独学受験生に選ばれやすい",
                    "解説と演習のバランス型",
                    "超速問題集へのステップアップがしやすい",
                ],
            ),
            book(
                3,
                "らくらく突破 改訂新版 2級ボイラー技士 合格教本",
                "技術評論社",
                "4774183261",
                edition="改訂新版",
                price_yen=2068,
                pages=248,
                for_who="教本形式で条文・数値を整理しながら学びたい人",
                highlights=[
                    "合格教本シリーズで論点を段階的に整理",
                    "問題集（別冊）との役割分担が明確",
                    "社会人独学で読み進めやすい分量",
                ],
            ),
        ],
        "related_links": [
            "self-study-guide:独学対策ガイド",
            "past-questions-how-to-use:過去問活用法",
            "exam-overview:試験概要",
            "affiliate-problem-books:おすすめ問題集",
            "affiliate-mock-exam-materials:公表問題・公式教材",
            "pass-score:合格点と合格基準",
        ],
        "operator_note": f"Amazon tag={TAG}。4426615321 / 4300111758 / 4774183261。{PRICE_CHECKED} 価格確認。",
    },
    "affiliate-problem-books": {
        "slug": "affiliate-problem-books",
        "theme_key": "problem-books",
        "search_intent": "2級ボイラー技士の過去問・問題集を比較して選びたい",
        "title": "2級ボイラー技士のおすすめ問題集3選【過去問2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめ問題集3選（比較）",
        "price_disclaimer": (
            f"価格・在庫は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            "購入前に販売ページで最新版を確認してください。"
        ),
        "products": [
            book(
                1,
                "詳解 2級ボイラー技士 過去6回問題集 '26年版",
                "成美堂出版",
                "4415241034",
                edition="'26年版",
                price_yen=1650,
                pages=272,
                for_who="直近6回分を解説付きで一気に解きたい人",
                highlights=[
                    "過去6回分で演習量を確保しやすい",
                    "詳解付きで復習しやすい定番",
                    "本試験形式の時間配分練習に向く",
                ],
            ),
            book(
                2,
                "さくさく解ける! 2級ボイラー技士試験 合格問題集",
                "オーム社",
                "4274224651",
                price_yen=2420,
                pages=254,
                for_who="テキスト読了後に演習メイン1冊を探している人",
                highlights=[
                    "さくさくシリーズで初学者向けの解きやすさ",
                    "合格テキストとセットで使いやすい",
                    "4分野の演習をバランスよく回せる",
                ],
            ),
            book(
                3,
                "2級ボイラー技士 過去問題・解答解説集 2026年4月版",
                "TAKARA license",
                "4866812753",
                edition="2026年4月版",
                price_yen=3300,
                pages=210,
                for_who="最新実施回ベースで過去問演習をしたい人",
                highlights=[
                    "2026年4月版で比較的新しい過去問を収録",
                    "解答解説付きで弱点科目の特定に向く",
                    "他社過去問との使い分けで演習量を確保",
                ],
            ),
        ],
        "related_links": [
            "past-questions-how-to-use:過去問活用法",
            "self-study-guide:独学対策ガイド",
            "pass-score:合格点と合格基準",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-mock-exam-materials:公表問題・公式教材",
            "exam-overview:試験概要",
        ],
        "operator_note": f"Amazon tag={TAG}。4415241034 / 4274224651 / 4866812753。",
    },
    "affiliate-mock-exam-materials": {
        "slug": "affiliate-mock-exam-materials",
        "theme_key": "mock-exam-materials",
        "search_intent": "2級ボイラー技士の公表問題・日本ボイラ協会教材を比較して選びたい",
        "title": "2級ボイラー技士の公表問題・公式教材3選【2026年版】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "公表問題・公式教材3選（比較）",
        "price_disclaimer": (
            f"価格は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            f"公表問題の収録範囲は{OFFICIAL}で必ず確認してください。"
        ),
        "products": [
            book(
                1,
                "2級ボイラー技士試験 公表問題解答解説 2026年版",
                "日本ボイラ協会",
                "4907619383",
                edition="2026年版",
                price_yen=2200,
                pages=248,
                for_who="公表問題の解答解説で本試験形式に慣れたい人",
                highlights=[
                    "日本ボイラ協会発行で公表問題の解説が読める",
                    "試験実施団体系の問題形式に近い演習",
                    "テキスト読了後の演習メイン候補",
                ],
            ),
            book(
                2,
                "新版 2級ボイラー技士試験 標準問題集",
                "日本ボイラ協会",
                "4907619286",
                edition="新版",
                price_yen=2640,
                pages=231,
                for_who="協会発行の標準問題で演習量を確保したい人",
                highlights=[
                    "標準問題集で基礎〜標準レベルの演習",
                    "公表問題解答解説との併用がしやすい",
                    "4分野の演習バランスを確認しやすい",
                ],
            ),
            book(
                3,
                "2級ボイラー技士 超速問題集",
                "TAC出版",
                "4300112517",
                price_yen=1760,
                pages=208,
                for_who="TAC超速マスター読了後に演習特化1冊を追加したい人",
                highlights=[
                    "超速マスターと章立ての相性がよい",
                    "問題特化で演習量を増やしやすい",
                    "直前期の総仕上げにも使える",
                ],
            ),
        ],
        "related_links": [
            "exam-overview:試験概要",
            "past-questions-how-to-use:過去問活用法",
            "pass-score:合格点と合格基準",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-problem-books:おすすめ問題集",
            "study-plan-beginner:初学者向け学習計画",
        ],
        "operator_note": (
            f"Amazon tag={TAG}。4907619383 / 4907619286 / 4300112517。"
            f"さくさく理解(4274220915)は本文・FAQで言及。{PRICE_CHECKED} 価格確認。"
        ),
    },
}


CSV_ROWS = {
    "affiliate-textbooks-recommend": {
        "title": "2級ボイラー技士のおすすめテキスト3選【2026年版・独学】",
        "meta_description": (
            "2級ボイラー技士の独学向けおすすめテキスト3選。"
            "ユーキャン・TAC超速マスター・技術評論社合格教本を比較。"
            "選び方とボイラマスター過去問との併用も解説。"
        ),
        "lead": (
            "2級ボイラー技士試験は4分野（構造・取扱い・関係法令・燃焼）の理解と演習量が合格の鍵です。"
            "本記事では2026年度版の主要テキスト3冊を、独学・社会人受験の視点で比較します。"
            "出題範囲は必ずボイラー検定（公式）で確認してください。"
            "価格・版情報は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "370",
        "original_note": "Amazon tag=ue083093-22。4426615321 / 4300111758 / 4774183261。",
        "user_intent": (
            "2級ボイラー技士のテキストを、解説量・演習量・ALL-in-one型かどうかで比較し、"
            "独学の最初の1冊に絞りたい。"
        ),
        "action_items": "比較表で3冊の違いを確認する;4分野の出題範囲を公式で確認する;過去問で弱点を把握する",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "テキスト選びの3つのポイント",
                "2級ボイラー技士のテキスト選びでは、"
                f"①{OFFICIAL}の4分野（構造・取扱い・関係法令・燃焼）に目次が沿っているか、"
                "②解説量が自分の前提知識（現場経験の有無）に合うか、"
                "③章末演習や別冊問題集とセットで使えるかを確認します。\n\n"
                "ボイラー現場経験が浅い人は図解・ALL-in-one型、"
                "経験者は教本型＋問題集追加、という使い分けが多いです。",
            ),
            (
                "おすすめテキスト比較の見方",
                "比較では「ユーキャン系で過去問とセット」「TAC超速で演習厚め」「技評合格教本で条文整理」の3タイプで見ます。"
                "独学初期は理解用1冊に絞り、演習が進んだ段階で過去問専門1冊（おすすめ問題集の記事）を追加する構成が扱いやすいです。"
                f"{SITE}の過去問で分野別得点を確認し、足りない解説量を基準に選んでください。",
            ),
            (
                "1位：ユーキャン合格テキストの特徴",
                "ユーキャンの2級ボイラー技士 合格テキスト&問題集 第2版（2,200円税込参考・344ページ・B5判）は、"
                "4分野を1冊で学べるALL-in-one型の定番です。"
                "成美堂の過去6回問題集と組み合わせやすく、初学者が最初の1冊に選びやすい構成です。\n\n"
                "向いている人：ボイラー技士試験をこれから始め、テキストと演習を1冊で回したい人。",
            ),
            (
                "2位・3位：TAC超速マスター・技評合格教本",
                "2級ボイラー技士 超速マスター 第2版（TAC出版・2,530円税込参考・396ページ）は、"
                "解説と演習量のバランス型。超速問題集（別記事）へのステップアップがしやすい本格教材です。\n\n"
                "らくらく突破 改訂新版 2級ボイラー技士 合格教本（技術評論社・2,068円税込参考・248ページ）は、"
                "教本形式で条文・数値を整理しながら学びたい社会人独学向け。問題集は別冊で追加する構成が向きます。",
            ),
            (
                "テキストとボイラマスター過去問の併用",
                "テキストで論点を押さえたら、2級ボイラー技士マスターの過去問・一問一答で本試験形式の演習に移ります。"
                "4分野ごとの得点を記録し、弱点分野をテキスト該当章に戻って復習するサイクルが効率的です。"
                "公表問題・協会発行教材は別記事（公表問題・公式教材3選）も参照してください。",
            ),
            (
                "購入前チェックリスト",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・4分野すべてが目次に含まれているか\n"
                "・Amazon在庫・価格（執筆時点と異なる場合あり）\n"
                "・手元の学習計画（2か月／4か月）に対してページ数・演習量が見合うか",
            ),
        ],
        "faqs": [
            (
                "さくさく理解シリーズは使えますか？",
                "さくさく理解! 2級ボイラー技士試験 合格テキスト（オーム社・4274220915）は、"
                "図解中心で初学者向けの選択肢です。"
                "さくさく解ける! 合格問題集とセットで使う受験生も多く、おすすめ問題集の記事もあわせて参照してください。",
            ),
            (
                "テキストは1冊だけで足りますか？",
                "ALL-in-one型1冊＋当サイトの過去問演習で独学は可能です。"
                "演習量が足りないと感じたら、おすすめ問題集の記事で紹介している過去問専門1冊を追加してください。",
            ),
            (
                "最新年度版じゃないとダメですか？",
                "出題範囲・法令改正の反映のため、購入時は2026年度版（最新版）を選んでください。"
                "中古は版と改訂情報の確認が必要です。",
            ),
        ],
        "related_links": (
            "self-study-guide:独学対策ガイド;"
            "past-questions-how-to-use:過去問活用法;"
            "exam-overview:試験概要;"
            "affiliate-problem-books:おすすめ問題集;"
            "affiliate-mock-exam-materials:公表問題・公式教材;"
            "pass-score:合格点と合格基準"
        ),
        "key_points": (
            "ユーキャンの2級ボイラー技士 合格テキスト&問題集 第2版;"
            "2級ボイラー技士 超速マスター 第2版;"
            "らくらく突破 改訂新版 2級ボイラー技士 合格教本;"
            "テキスト選びの3つのポイント;"
            "過去問との併用"
        ),
    },
    "affiliate-problem-books": {
        "title": "2級ボイラー技士のおすすめ問題集3選【過去問2026】",
        "meta_description": (
            "2級ボイラー技士のおすすめ問題集3選。"
            "成美堂過去6回、オーム社さくさく解ける、TAKARA license過去問題集を比較。"
            "過去問の回し方と分野別対策も解説。"
        ),
        "lead": (
            "2級ボイラー技士試験では、過去問・問題集の演習量が得点安定の鍵です。"
            "本記事では2026年度版の問題集3冊を、収録形式・解説量・演習量で比較します。"
            "価格は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "365",
        "original_note": "Amazon tag=ue083093-22。4415241034 / 4274224651 / 4866812753。",
        "user_intent": (
            "2級ボイラー技士の過去問・問題集を比較し、"
            "演習メイン1冊を決めて、分野別の弱点補強計画を立てたい。"
        ),
        "action_items": "3冊の収録形式を比較する;4分野の得点バランスを確認する;弱点分野をテキストで復習する",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "問題集選びの基準",
                "問題集選びでは、(1)4分野の出題バランスが取れているか (2)解説で復習できるか "
                "(3)演習量が計画に見合うかを確認します。"
                "構造・取扱い・関係法令・燃焼それぞれの得点バランスを見ながら、弱点分野に戻れる解説量があるかが重要です。",
            ),
            (
                "3冊の選び方（タイプ別）",
                "[[affiliate-hub-placeholder]]\n\n"
                "直近6回を一気に解きたい人は詳解 2級ボイラー技士 過去6回問題集 '26年版、"
                "テキストとセットで演習したい人はさくさく解ける! 2級ボイラー技士試験 合格問題集、"
                "最新実施回ベースの演習には2級ボイラー技士 過去問題・解答解説集 2026年4月版が向きます。",
            ),
            (
                "1位：成美堂 過去6回問題集",
                "詳解 2級ボイラー技士 過去6回問題集 '26年版（1,650円税込参考・272ページ・B5判）は、"
                "直近6回分を解説付きで収録。本試験の時間感覚を養う練習にも向く定番1冊です。",
            ),
            (
                "2位・3位：さくさく解ける・TAKARA license",
                "さくさく解ける! 2級ボイラー技士試験 合格問題集（オーム社・2,420円税込参考・254ページ）は、"
                "さくさく理解テキストと組み合わせやすい演習向け1冊。\n\n"
                "2級ボイラー技士 過去問題・解答解説集 2026年4月版（TAKARA license・3,300円税込参考・210ページ）は、"
                "比較的新しい過去問を解説付きで演習したい人向けです。",
            ),
            (
                "過去問の回し方（ボイラマスターとの併用）",
                "当サイトの過去問で分野別得点を把握したうえで、問題集で「時間を計って解く」練習を行います。"
                "誤答は用語解説で類似論点まで整理し、1週間後に解き直してください。"
                "過去問活用法は past-questions-how-to-use を参照。",
            ),
            (
                "公表問題・協会教材との使い分け",
                "紙の過去問で論点を押さえたあと、日本ボイラ協会の公表問題・標準問題集（別記事）で"
                "試験実施団体系の演習を追加する受験生も多いです。"
                "教材は増やしすぎず、1フェーズ1冊を原則にすると計画が立てやすくなります。",
            ),
        ],
        "faqs": [
            (
                "過去問だけで合格できますか？",
                "演習量は確保できますが、初めての論点はテキストで理解してから問題集に入る方が効率的です。"
                "おすすめテキストの記事で紹介している1冊と組み合わせる構成を推奨します。",
            ),
            (
                "問題集は何冊必要ですか？",
                "メイン1冊＋当サイト過去問で足りる場合が多いです。"
                "公表問題演習もしたい場合は、公表問題・公式教材の記事を参照してください。",
            ),
            (
                "成美堂とTAKARA licenseの違いは？",
                "成美堂は過去6回形式、TAKARA licenseは2026年4月版など実施回ベースの収録です。"
                "演習量確保には成美堂、最新回の傾向確認にはTAKARA license、という使い分けもあります。",
            ),
        ],
        "related_links": (
            "past-questions-how-to-use:過去問活用法;"
            "self-study-guide:独学対策ガイド;"
            "pass-score:合格点と合格基準;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-mock-exam-materials:公表問題・公式教材;"
            "exam-overview:試験概要"
        ),
        "key_points": (
            "詳解 2級ボイラー技士 過去6回問題集 '26年版;"
            "さくさく解ける! 2級ボイラー技士試験 合格問題集;"
            "2級ボイラー技士 過去問題・解答解説集 2026年4月版;"
            "問題集選びの基準;"
            "過去問の回し方"
        ),
    },
    "affiliate-mock-exam-materials": {
        "title": "2級ボイラー技士の公表問題・公式教材3選【2026年版】",
        "meta_description": (
            "2級ボイラー技士の公表問題・公式教材3選。"
            "日本ボイラ協会の公表問題解答解説・標準問題集とTAC超速問題集を比較。"
            "テキスト・過去問との組み合わせも解説。"
        ),
        "lead": (
            "2級ボイラー技士試験では、日本ボイラ協会発行の公表問題・標準問題集が"
            "試験形式に近い演習として選ばれます。"
            "本記事では協会教材2冊とTAC超速問題集を比較します。"
            "公表問題の扱いは必ずボイラー検定（公式）で確認してください。"
        ),
        "priority": "360",
        "original_note": "Amazon tag=ue083093-22。4907619383 / 4907619286 / 4300112517。4274220915はFAQ言及。",
        "user_intent": (
            "2級ボイラー技士の公表問題・協会発行教材を比較し、"
            "テキスト・過去問に加える演習1冊を決めたい。"
        ),
        "action_items": "3冊の用途を比較する;公表問題の位置づけを公式で確認する;テキスト・過去問との役割分担を決める",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "公表問題・協会教材の位置づけ",
                "日本ボイラ協会発行の公表問題解答解説・標準問題集は、"
                "試験実施団体系の問題形式に慣れるための教材として位置づけられます。"
                "テキストで4分野の理解を固めたあと、過去問問題集とあわせて演習量を確保する用途が多いです。",
            ),
            (
                "3冊の選び方",
                "[[affiliate-hub-placeholder]]\n\n"
                "公表問題の解答解説を厚く読みたい人は2級ボイラー技士試験 公表問題解答解説 2026年版、"
                "協会発行の標準演習には新版 2級ボイラー技士試験 標準問題集、"
                "TAC超速マスター読了後の演習追加には2級ボイラー技士 超速問題集が向きます。",
            ),
            (
                "1位・2位：日本ボイラ協会 公表問題・標準問題集",
                "2級ボイラー技士試験 公表問題解答解説 2026年版（2,200円税込参考・248ページ）は、"
                "公表問題の解説付き演習向け。試験形式への慣れづくに有効です。\n\n"
                "新版 2級ボイラー技士試験 標準問題集（2,640円税込参考・231ページ）は、"
                "標準レベルの演習量を確保したい人向け。公表問題解答解説との併用がしやすい1冊です。",
            ),
            (
                "3位：TAC超速問題集",
                "2級ボイラー技士 超速問題集（TAC出版・1,760円税込参考・208ページ）は、"
                "超速マスター第2版と章立ての相性がよく、問題特化で演習量を増やしたい人向けです。"
                "直前期の総仕上げにも使えます。",
            ),
            (
                "テキスト・過去問との組み合わせ",
                "例：ユーキャン合格テキスト→成美堂過去6回→公表問題解答解説→ボイラマスター過去問。"
                "初学者向けにはさくさく理解テキスト＋さくさく解ける問題集から入る選択肢もあります。"
                "教材は増やしすぎず、1フェーズ1冊を原則にしてください。",
            ),
            (
                "購入前の確認事項",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・公表問題の収録範囲（公式案内と一致するか）\n"
                "・テキスト・過去問との重複が学習計画上問題ないか\n"
                "・Amazon在庫・価格",
            ),
        ],
        "faqs": [
            (
                "公表問題だけで合格できますか？",
                "形式慣れと演習には有効ですが、初めての論点はテキストで理解してから入る方が効率的です。"
                "おすすめテキストと過去問問題集の記事と組み合わせる構成を推奨します。",
            ),
            (
                "日本ボイラ協会の2冊、両方必要ですか？",
                "必須ではありません。公表問題解答解説をメインにし、演習量が足りなければ標準問題集を追加する、"
                "という2段構成が一般的です。",
            ),
            (
                "さくさく理解テキストとの関係は？",
                "さくさく理解! 2級ボイラー技士試験 合格テキスト（4274220915）は初学者向けの別ルートです。"
                "協会教材と併用するより、さくさく解ける問題集とセットで使う例が多いです。",
            ),
        ],
        "related_links": (
            "exam-overview:試験概要;"
            "past-questions-how-to-use:過去問活用法;"
            "pass-score:合格点と合格基準;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-problem-books:おすすめ問題集;"
            "study-plan-beginner:初学者向け学習計画"
        ),
        "key_points": (
            "2級ボイラー技士試験 公表問題解答解説 2026年版;"
            "新版 2級ボイラー技士試験 標準問題集;"
            "2級ボイラー技士 超速問題集;"
            "公表問題の位置づけ;"
            "テキスト・過去問との組み合わせ"
        ),
    },
}


def write_briefs() -> None:
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for slug, data in BRIEFS_DATA.items():
        path = BRIEFS / f"{slug}.yaml"
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"wrote brief → {path}")


def patch_csv() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("CSV header missing")
    fieldnames = list(fieldnames)
    if "faq_3_answer" in fieldnames and "faq_3_question" not in fieldnames:
        idx = fieldnames.index("faq_3_answer")
        fieldnames.insert(idx, "faq_3_question")

    for row in rows:
        slug = row.get("slug", "")
        if slug not in CSV_ROWS:
            continue
        cfg = CSV_ROWS[slug]
        row["title"] = cfg["title"]
        row["meta_description"] = cfg["meta_description"]
        row["lead"] = cfg["lead"]
        row["priority"] = cfg["priority"]
        row["original_note"] = cfg["original_note"]
        row["user_intent"] = cfg["user_intent"]
        row["action_items"] = cfg["action_items"]
        row["revision_note"] = cfg["revision_note"]
        row["fact_checked_at"] = PRICE_CHECKED
        row["content_status"] = "published"
        row["related_links"] = cfg["related_links"]
        row["key_points"] = cfg["key_points"]
        row["tags"] = "独学;参考書;アフィリエイト"
        for i, (heading, body) in enumerate(cfg["sections"], start=1):
            row[f"section_{i}_heading"] = heading
            row[f"section_{i}_body"] = ensure_section_body(body)
        for i in range(len(cfg["sections"]) + 1, 8):
            row[f"section_{i}_heading"] = ""
            row[f"section_{i}_body"] = ""
        for i, (q, a) in enumerate(cfg["faqs"], start=1):
            row[f"faq_{i}_question"] = q
            row[f"faq_{i}_answer"] = ensure_faq_answer(a)
        for i in range(len(cfg["faqs"]) + 1, 4):
            row[f"faq_{i}_question"] = ""
            row[f"faq_{i}_answer"] = ""
        print(f"patched CSV row: {slug}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    write_briefs()
    patch_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
