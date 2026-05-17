#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate SEO-oriented exam guide articles under articles/."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (  # noqa: E402
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    footer_href,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.site_config import brand_name, clean_origin, exam_name, primary_external_link  # noqa: E402

ARTICLES_DIR = ROOT / "articles"

AUTHOR_NAME = "2級ボイラー技士マスター編集部"
AUTHOR_PROFILE = "資格学習サイト向けに、過去問形式演習・用語解説・学習導線を整理する編集チームです。"
REVIEWER_NAME = "2級ボイラー技士マスター確認担当"
REVIEWER_PROFILE = "公開前に公式情報への誘導、断定表現、内部リンク、更新日の有無を確認します。"
FACT_CHECKED_AT = "2026-05-17"
REVISION_NOTE = "SEO記事テンプレート運用ルールに合わせ、目次・信頼性・公式情報・FAQ・関連記事を整備。"
FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""


ARTICLES: list[dict[str, object]] = [
    {
        "slug": "exam-overview",
        "title": "2級ボイラー技士試験とは？概要・出題科目・合格に向けた全体像",
        "desc": "2級ボイラー技士試験の概要、出題科目、学習の進め方を初学者向けに整理します。",
        "category": "試験概要",
        "points": ["試験の位置づけ", "4科目の全体像", "学習開始時に確認する公式情報"],
    },
    {
        "slug": "schedule-application",
        "title": "2級ボイラー技士試験の日程・申込・受験前チェック",
        "desc": "試験日程、受験申込、受験前に確認したい公式情報の見方を整理します。",
        "category": "試験概要",
        "points": ["試験日程の確認", "申込時の注意", "受験票・会場・当日の確認"],
    },
    {
        "slug": "license-and-work",
        "title": "2級ボイラー技士免許でできることと試験対策の考え方",
        "desc": "2級ボイラー技士免許の位置づけ、作業主任者との関係、学習時の注意点を解説します。",
        "category": "試験概要",
        "points": ["免許区分の考え方", "作業主任者との関係", "法令問題での確認ポイント"],
    },
    {
        "slug": "passing-score",
        "title": "2級ボイラー技士試験の合格基準と科目別バランス対策",
        "desc": "合格基準を意識した科目別学習、苦手科目を残さない得点戦略を解説します。",
        "category": "試験対策",
        "points": ["総合点と科目バランス", "苦手科目の早期発見", "過去問での到達度確認"],
    },
    {
        "slug": "study-plan",
        "title": "2級ボイラー技士試験の勉強時間と学習計画の作り方",
        "desc": "初学者が無理なく進めるための学習順序、復習頻度、過去問演習の入れ方を紹介します。",
        "category": "試験対策",
        "points": ["基礎用語から始める", "過去問を早めに回す", "復習日を固定する"],
    },
    {
        "slug": "past-questions-how-to-use",
        "title": "2級ボイラー技士試験の過去問活用法｜解きっぱなしを防ぐ復習手順",
        "desc": "過去問形式の演習を使って、頻出論点を効率よく定着させる方法を解説します。",
        "category": "過去問活用",
        "points": ["年度別に全体感をつかむ", "科目別に弱点をつぶす", "間違えた理由を記録する"],
    },
    {
        "slug": "practice-questions",
        "title": "実践演習の使い方｜過去問後に伸びる2級ボイラー技士対策",
        "desc": "過去問形式と実践演習を組み合わせ、知識の穴を埋める学習法を紹介します。",
        "category": "過去問活用",
        "points": ["過去問後に実践演習を解く", "似た選択肢で理解を確認する", "正答理由を言語化する"],
    },
    {
        "slug": "mock-exam",
        "title": "本番形式の模擬試験で確認すべきこと｜時間配分と見直し",
        "desc": "2級ボイラー技士試験の直前期に、本番形式で確認したい時間配分と復習方法をまとめます。",
        "category": "過去問活用",
        "points": ["制限時間を意識する", "迷った問題を残す", "科目別の失点傾向を見る"],
    },
    {
        "slug": "one-question-review",
        "title": "一問一答で2級ボイラー技士の基礎知識を固める方法",
        "desc": "短時間学習に向く一問一答の使い方と、過去問演習へのつなげ方を解説します。",
        "category": "学習法",
        "points": ["短時間で反復する", "正誤だけでなく理由を見る", "用語集へ戻って確認する"],
    },
    {
        "slug": "glossary-study",
        "title": "重要用語から覚える2級ボイラー技士試験対策",
        "desc": "安全弁、水面計、空気比などの重要用語を起点にした学習法を紹介します。",
        "category": "学習法",
        "points": ["用語の定義を押さえる", "関連語をまとめて覚える", "選択肢での言い換えに慣れる"],
    },
    {
        "slug": "structure-subject",
        "title": "ボイラーの構造に関する知識の対策｜頻出装置と覚え方",
        "desc": "水管ボイラー、炉筒煙管ボイラー、安全弁など、構造分野の頻出ポイントを整理します。",
        "category": "科目別対策",
        "points": ["ボイラー形式を比較する", "附属品の役割を整理する", "制御装置の安全目的を見る"],
    },
    {
        "slug": "handling-subject",
        "title": "ボイラーの取扱いに関する知識の対策｜水位・点火・異常時対応",
        "desc": "低水位、吹出し、点火前確認、異常時対応など取扱い分野の学習ポイントを解説します。",
        "category": "科目別対策",
        "points": ["水位管理を最優先で押さえる", "点火前後の手順を整理する", "異常時は原因確認を優先する"],
    },
    {
        "slug": "fuel-combustion-subject",
        "title": "燃料及び燃焼に関する知識の対策｜空気比・燃焼管理・排ガス",
        "desc": "空気比、燃焼の三要素、燃料性質、排ガス分析など燃焼分野の頻出テーマをまとめます。",
        "category": "科目別対策",
        "points": ["燃料性質を比較する", "空気比と不完全燃焼をつなげる", "排ガスから燃焼状態を読む"],
    },
    {
        "slug": "law-subject",
        "title": "関係法令の対策｜検査・届出・作業主任者を整理する",
        "desc": "2級ボイラー技士試験の関係法令で頻出の検査証、届出、作業主任者を解説します。",
        "category": "科目別対策",
        "points": ["検査の種類を分ける", "届出のタイミングを覚える", "作業主任者の職務を確認する"],
    },
    {
        "slug": "water-level-safety",
        "title": "低水位・空だき対策｜2級ボイラー技士で最重要の安全論点",
        "desc": "低水位、空だき、水面計、低水位燃料遮断装置の関係を試験向けに整理します。",
        "category": "重要論点",
        "points": ["低水位の危険を理解する", "水面計の確認を押さえる", "燃料遮断の目的を覚える"],
    },
    {
        "slug": "safety-valve-pressure",
        "title": "安全弁・圧力計・最高使用圧力の覚え方",
        "desc": "過圧防止に関わる安全弁、圧力計、最高使用圧力の関係を解説します。",
        "category": "重要論点",
        "points": ["安全弁は過圧防止", "圧力計は運転監視", "最高使用圧力と法令を結び付ける"],
    },
    {
        "slug": "water-treatment",
        "title": "ボイラー水処理の対策｜スケール・腐食・pH・硬度",
        "desc": "水処理、スケール、腐食、脱酸素剤、りん酸塩処理を試験向けに整理します。",
        "category": "重要論点",
        "points": ["硬度はスケールにつながる", "溶存酸素は腐食につながる", "吹出しで濃縮を管理する"],
    },
    {
        "slug": "combustion-safety",
        "title": "燃焼安全装置とインタロック｜失火・逆火・再点火の注意点",
        "desc": "燃焼安全装置、火炎検出器、燃料遮断弁、パージの役割を整理します。",
        "category": "重要論点",
        "points": ["火炎検出器の役割", "異常時の燃料遮断", "再点火前のパージ"],
    },
    {
        "slug": "air-ratio",
        "title": "空気比と不完全燃焼の対策｜CO・黒煙・排ガス熱損失",
        "desc": "空気比が大きすぎる場合・小さすぎる場合の影響を、排ガスと結び付けて解説します。",
        "category": "重要論点",
        "points": ["空気不足はCOや黒煙", "過剰空気は熱損失", "排ガス分析で状態を推定する"],
    },
    {
        "slug": "fuel-properties",
        "title": "燃料の性質の覚え方｜引火点・発火点・粘度・発熱量",
        "desc": "液体燃料や気体燃料で問われる性質を、選択肢で迷わないよう整理します。",
        "category": "重要論点",
        "points": ["引火点と発火点を区別する", "粘度は温度と霧化に関係する", "発熱量の違いを見る"],
    },
    {
        "slug": "inspection-certificate",
        "title": "ボイラー検査証と性能検査｜法令問題で迷いやすい手続",
        "desc": "ボイラー検査証、有効期間、性能検査、再交付をわかりやすく整理します。",
        "category": "法令対策",
        "points": ["検査証の役割", "有効期間満了前の対応", "紛失時の再交付"],
    },
    {
        "slug": "notifications",
        "title": "設置届・変更届・休止届・廃止届の整理",
        "desc": "ボイラー関係法令で出やすい届出の種類と、判断のポイントをまとめます。",
        "category": "法令対策",
        "points": ["設置時の届出", "変更時の届出", "休止・廃止時の扱い"],
    },
    {
        "slug": "boiler-room",
        "title": "ボイラー室の法令対策｜通路・換気・可燃物・燃料タンク",
        "desc": "ボイラー室に関する法令問題で見落としやすい条件を整理します。",
        "category": "法令対策",
        "points": ["点検スペースを確保する", "換気と燃料漏れに注意する", "可燃物の管理を見る"],
    },
    {
        "slug": "chief-operator",
        "title": "ボイラー取扱作業主任者の職務と覚え方",
        "desc": "作業主任者の職務、水位・圧力・燃焼状態の監視、急激な負荷変動防止を解説します。",
        "category": "法令対策",
        "points": ["水位と圧力を監視する", "燃焼状態を見る", "安全装置を無効化しない"],
    },
    {
        "slug": "common-mistakes",
        "title": "2級ボイラー技士試験でよくある間違いと対策",
        "desc": "受験生が迷いやすい用語、選択肢、法令手続のミスをまとめて対策します。",
        "category": "学習法",
        "points": ["似た用語を混同しない", "安全側の判断を意識する", "法令手続を時系列で覚える"],
    },
    {
        "slug": "last-week",
        "title": "試験直前1週間の2級ボイラー技士対策チェックリスト",
        "desc": "直前期にやるべき過去問、用語、法令、模擬試験の確認順序を紹介します。",
        "category": "学習法",
        "points": ["新しい教材を増やしすぎない", "間違えた問題を優先する", "公式情報を再確認する"],
    },
    {
        "slug": "official-info",
        "title": "公式情報の確認方法｜試験日程・合格基準・法令原文",
        "desc": "試験実施団体、法令・通達、受験案内を確認する際の注意点を整理します。",
        "category": "試験概要",
        "points": ["試験実施団体を見る", "法令原文を確認する", "古い情報に注意する"],
    },
    {
        "slug": "legal-updates",
        "title": "法令改正に注意した2級ボイラー技士試験対策",
        "desc": "法令改正や制度変更により、学習内容の確認が必要になる理由を解説します。",
        "category": "法令対策",
        "points": ["古い解説を鵜呑みにしない", "公式情報を優先する", "過去問形式でも最新法令を意識する"],
    },
    {
        "slug": "beginner-guide",
        "title": "初学者向け2級ボイラー技士試験の始め方",
        "desc": "初めて学習する人向けに、用語、科目、過去問への進み方を解説します。",
        "category": "学習法",
        "points": ["用語集から始める", "科目ごとの役割を知る", "早めに過去問形式へ進む"],
    },
    {
        "slug": "mobile-study",
        "title": "スマホで進める2級ボイラー技士試験対策",
        "desc": "通勤・休憩時間に一問一答、用語確認、過去問復習を進める方法を紹介します。",
        "category": "学習法",
        "points": ["一問一答で短時間学習", "用語を検索して確認", "間違えた問題を復習に回す"],
    },
    {
        "slug": "seo-past-question-guide",
        "title": "過去問形式演習で合格力を上げる2級ボイラー技士対策",
        "desc": "過去問形式の演習問題を使い、出題パターンと選択肢の言い換えに慣れる方法を解説します。",
        "category": "過去問活用",
        "points": ["原文暗記ではなく論点理解", "選択肢の言い換えに慣れる", "頻出テーマを用語集で補強する"],
    },
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def public_url(path: str) -> str:
    return clean_origin().rstrip("/") + "/" + path.lstrip("/")


def article_path(article: dict[str, object]) -> Path:
    return ARTICLES_DIR / f"{article['slug']}.html"


def related_article_links(current_slug: str) -> str:
    links = []
    for article in ARTICLES:
        if article["slug"] == current_slug:
            continue
        links.append(article)
        if len(links) >= 4:
            break
    return "".join(
        f'<a class="related-link" href="{esc(item["slug"])}.html">{esc(item["title"])}</a>'
        for item in links
    )


def faq_items_for(article: dict[str, object]) -> list[tuple[str, str]]:
    title = str(article["title"])
    category = str(article["category"])
    return [
        (
            "この記事だけで公式情報の確認は完了しますか？",
            "いいえ。本記事は学習の進め方を整理するためのものです。試験日程、受験資格、手数料、合格基準、法令の正式な内容は、必ず試験実施団体や法令原文などの一次情報で確認してください。",
        ),
        (
            f"{category}の記事はどの順番で使うとよいですか？",
            f"まず「{title}」で全体像を確認し、次に過去問形式の演習で選択肢を読めるか試します。迷った語句は用語集へ戻し、復習対象として残すと再訪問しやすくなります。",
        ),
    ]


def guide_sections(article: dict[str, object]) -> list[tuple[str, str]]:
    category = str(article["category"])
    points = [str(p) for p in article["points"]]  # type: ignore[index]
    return [
        (
            "最初に確認すること",
            f"まず確認したいのは、この記事のテーマである「{points[0]}」です。制度情報や日程、合格基準のように年度で変わる可能性がある内容は、古い記事だけで判断しないでください。学習前に公式情報を見て、現在の出題範囲や注意事項を確認しておくと、あとから覚え直すリスクを減らせます。特に試験対策では、最初に前提を誤ると、過去問を解いても正しい復習につながりません。受験案内、試験実施団体の告知、法令の正式な内容を確認したうえで、このサイトの演習や用語解説を使う流れにすると安心です。",
        ),
        (
            "全体像・前提を分けて理解する",
            f"{exam_name()}は、構造、取扱い、燃料及び燃焼、関係法令の知識がつながって出題されます。{category}の記事でも、単独の暗記で終わらせず、関連する装置名、事故防止の目的、法令上の扱いを分けて整理しましょう。特に似た用語は、意味の違いを一文で説明できる状態を目標にします。たとえば装置名を覚えるだけではなく、その装置がどの異常を防ぐのか、運転中にどのように確認するのか、法令問題ではどの表現で問われるのかまで結び付けると、選択肢の言い換えにも対応しやすくなります。",
        ),
        (
            "具体的な進め方",
            f"次に「{points[1]}」を過去問形式の演習で確認します。最初から満点を狙うより、読めなかった語句、迷った選択肢、時間がかかった分野を記録してください。間違えた問題の正答だけを見るのではなく、なぜ他の選択肢が違うのかを確認すると、同じ論点の言い換えに強くなります。1回目は全体の弱点発見、2回目は理由の確認、3回目はスピードと安定性の確認というように目的を分けると、ただ解いた回数だけが増える状態を避けられます。記録に残した語句は、用語集で関連語まで確認しましょう。",
        ),
        (
            "復習・確認方法",
            f"復習では「{points[2]}」を意識します。過去問一覧で年度別の傾向を見たあと、アプリの過去問演習、実践演習、一問一答を使って同じ論点を別の角度から確認してください。用語集の関連語まで読むと、選択肢の中で安全装置、燃焼状態、法令手続が入れ替わったときにも判断しやすくなります。復習のタイミングは、解いた直後、翌日、数日後のように間隔を空けると定着を確認しやすくなります。正解した問題でも、根拠を説明できなかったものは復習対象に残すのがおすすめです。",
        ),
        (
            "注意点",
            "試験制度、受験資格、手数料、合格基準、免除制度、法令改正に関わる内容は、断定して覚えないことが大切です。本サイトの解説は学習補助であり、公式見解ではありません。演習問題も公式過去問そのものではなく、著作権上の配慮と最新法令への対応のため編集した過去問形式の問題です。古い年度の問題で正しかった表現が、制度変更や法令改正により注意を要する場合もあります。迷ったときは、暗記した文言よりも公式情報、法令原文、安全側の判断を優先してください。",
        ),
        (
            "つまずきやすいポイント",
            "つまずきやすいのは、用語の意味を知っていても、選択肢で別表現に変わると判断できなくなるケースです。たとえば安全弁、低水位、空気比、検査証のような語は、目的や異常時対応とセットで問われます。用語を単語カードのように覚えるだけでなく、何を防ぐための知識かまで確認しましょう。また、似た装置や手続をまとめて覚えると、細かな違いを見落としやすくなります。比較表や関連用語を使い、共通点と違いを分けて整理することで、ひっかけ選択肢にも対応しやすくなります。",
        ),
        (
            "次にやること",
            "この記事を読んだら、まず関連する過去問を数問解き、分からなかった語句を用語集で確認します。その後、間違えた問題を復習対象に残し、次回の学習で同じ論点を解き直してください。新しい教材を増やすより、公式情報、過去問、用語、復習の流れを固定する方が継続しやすくなります。余裕があれば、同じ分野の実践演習や一問一答も確認し、別の聞かれ方でも判断できるか試してください。最後に、次に読む関連記事を1本だけ選ぶと学習が途切れにくくなります。",
        ),
    ]


def toc_html(sections: list[tuple[str, str]]) -> str:
    fixed = [
        ("article-trust", "この記事の信頼性について"),
        ("article-official", "公式情報の確認"),
        ("article-basic", "記事の基本情報"),
        ("article-can-do", "この記事でできること"),
    ]
    section_links = [(f"article-sec-{i}", title) for i, (title, _) in enumerate(sections, start=1)]
    tail = [("article-faq", "よくある質問"), ("article-related", "関連記事")]
    links = fixed + section_links + tail
    return (
        '<nav class="article-toc" aria-label="目次"><div class="article-toc-title">目次</div><ol>'
        + "".join(f'<li><a href="#{esc(anchor)}">{esc(label)}</a></li>' for anchor, label in links)
        + "</ol></nav>"
    )


def build_article(article: dict[str, object]) -> str:
    slug = str(article["slug"])
    rel_path = Path("articles") / f"{slug}.html"
    title = str(article["title"])
    desc = str(article["desc"])
    category = str(article["category"])
    points = [str(p) for p in article["points"]]  # type: ignore[index]
    canonical = public_url(f"articles/{slug}.html")
    page_title = f"{title}｜{brand_name()}"
    breadcrumb = breadcrumb_html(rel_path, [("トップ", "index.html"), ("試験ガイド", "articles/index.html"), (title, None)])
    header = site_page_header(rel_path, current="articles")
    footer = site_page_footer(rel_path, current="articles")
    official = primary_external_link()
    point_items = "\n".join(f"        <li>{esc(p)}</li>" for p in points)
    sections = guide_sections(article)
    action_items = [
        "公式情報を確認する",
        "過去問を年度別に解く",
        "間違えた問題を復習へ残す",
        "関連用語を読む",
        "次回の見直し日を決める",
    ]
    faq_items = faq_items_for(article)
    section_html = "\n".join(
        f"""    <section class="seo-article-section" aria-labelledby="article-sec-{i}">
      <h2 id="article-sec-{i}">{esc(heading)}</h2>
      <p>{esc(body)}</p>
    </section>"""
        for i, (heading, body) in enumerate(sections, start=1)
    )
    action_html = "".join(f"<li>{esc(item)}</li>" for item in action_items)
    faq_html = "".join(
        f'<details class="term-faq-item" open><summary>{esc(q)}</summary><div>{esc(a)}</div></details>'
        for q, a in faq_items
    )
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": page_title,
                "description": desc,
                "mainEntityOfPage": canonical,
                "author": {"@type": "Organization", "name": AUTHOR_NAME},
                "publisher": {"@type": "Organization", "name": brand_name()},
                "about": exam_name(),
                "dateModified": FACT_CHECKED_AT,
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faq_items
                ],
            },
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:locale" content="ja_JP">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
{FONT_LINKS}
<link rel="stylesheet" href="../site-pages.css">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{header}
<main class="seo-article-main exam-guide-article">
  {breadcrumb}
  <article class="seo-article-card article-body">
    <div class="article-meta">
      <span class="meta-category">試験ガイド</span>
      <span class="meta-updated">更新日：2026-05-17</span>
      <span class="meta-updated">{esc(category)}</span>
    </div>
    <h1 class="article-title">{esc(title)}</h1>
    <p class="article-lead"><strong>{esc(exam_name())}</strong>について、{esc(desc)} 安全・構造・燃焼・法令の知識がつながって出題されるため、用語と過去問を往復して確認することが大切です。</p>
    <blockquote><p><strong>注意：</strong>本ページは学習用の要点整理です。試験日程・合格基準・法令の正式な内容は、試験実施団体や法令原文などの公式情報を確認してください。</p></blockquote>
    {toc_html(sections)}

    <section class="seo-article-section" aria-labelledby="article-trust">
      <h2 id="article-trust">この記事の信頼性について</h2>
      <table class="seo-info-table"><tbody>
        <tr><th>執筆者</th><td><strong>{esc(AUTHOR_NAME)}</strong><span class="article-profile-note">{esc(AUTHOR_PROFILE)}</span></td></tr>
        <tr><th>確認者</th><td><strong>{esc(REVIEWER_NAME)}</strong><span class="article-profile-note">{esc(REVIEWER_PROFILE)}</span></td></tr>
        <tr><th>事実確認日</th><td>{esc(FACT_CHECKED_AT)}</td></tr>
        <tr><th>主な参照元</th><td><a href="{esc(official.get("url", "https://www.exam.or.jp/"))}" target="_blank" rel="noopener noreferrer">{esc(official.get("label", "試験実施団体（公式）"))}</a></td></tr>
        <tr><th>独自メモ</th><td>過去問形式演習・用語解説・復習導線へつなげることを目的に、公式情報の確認を前提として整理しています。</td></tr>
        <tr><th>更新方針</th><td>公式情報、内部リンク、FAQ、最新年度情報を定期的に見直します。</td></tr>
      </tbody></table>
    </section>

    <section class="seo-article-section" aria-labelledby="article-official">
      <h2 id="article-official">公式情報の確認</h2>
      <p>年度、受験資格、手数料、合格基準、免除制度、法改正に関わる内容は、必ず公式情報で確認してください。本サイトでは学習の進め方を整理しますが、公式見解の代わりにはなりません。</p>
      <p><a href="{esc(official.get("url", "https://www.exam.or.jp/"))}" target="_blank" rel="noopener noreferrer">試験実施団体の公式情報</a>を確認し、法令や通達の原文が必要な場合は関係省庁や法令データ提供システムなどの一次情報も確認しましょう。</p>
    </section>

    <section class="seo-article-section" aria-labelledby="article-basic">
      <h2 id="article-basic">記事の基本情報</h2>
      <table class="seo-info-table"><tbody>
        <tr><th>対象</th><td>{esc(exam_name())}</td></tr>
        <tr><th>カテゴリ</th><td>{esc(category)}</td></tr>
        <tr><th>検索意図</th><td>{esc(title)}について、最初に確認することと学習への使い方を知りたい人向け。</td></tr>
        <tr><th>活用方法</th><td>過去問演習・実践演習・用語確認とあわせて復習</td></tr>
        <tr><th>更新メモ</th><td>{esc(REVISION_NOTE)}</td></tr>
      </tbody></table>
    </section>

    <section class="seo-article-section" aria-labelledby="article-can-do">
      <h2 id="article-can-do">この記事でできること</h2>
      <p>{esc(title)}について、公式情報で確認すべき点、学習時に見るべきポイント、過去問形式演習へのつなげ方を整理できます。</p>
      <ol class="term-point-list">{action_html}</ol>
    </section>

{section_html}

    <section class="seo-article-section" aria-labelledby="article-points">
      <h2 id="article-points">要点チェック</h2>
      <ol class="term-point-list">
{point_items}
      </ol>
      <p><a href="../q/index.html">過去問一覧</a>で年度別の出題を確認し、迷った語句は<a href="../terms/index.html">用語集</a>で定義と関連語を確認しましょう。アプリ側では<a href="../index.html#past">過去問演習</a>、<a href="../index.html#orig">実践演習</a>、<a href="../index.html#ichimon">一問一答</a>を組み合わせて復習できます。</p>
    </section>

    <section class="seo-article-section" aria-labelledby="article-faq">
      <h2 id="article-faq">よくある質問</h2>
      {faq_html}
    </section>

    <div class="related-box" id="article-related"><div class="related-box-title">関連記事</div><div class="related-links">{related_article_links(slug)}</div></div>
    <div class="related-box"><div class="related-box-title">次に確認するページ</div><div class="related-links"><a class="related-link" href="index.html">試験ガイド一覧へ戻る</a><a class="related-link" href="../q/index.html">過去問一覧を見る</a><a class="related-link" href="../terms/index.html">用語集で確認する</a><a class="related-link" href="../index.html#past">アプリで演習する</a></div></div>
  </article>
</main>
{footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_index() -> str:
    rel_path = Path("articles/index.html")
    canonical = public_url("articles/")
    header = site_page_header(rel_path, current="articles")
    footer = site_page_footer(rel_path, current="articles")
    breadcrumb = breadcrumb_html(rel_path, [("トップ", "index.html"), ("試験ガイド", None)])
    categories = []
    for article in ARTICLES:
        cat = str(article["category"])
        if cat not in categories:
            categories.append(cat)
    category_blocks = []
    for cat in categories:
        cards = []
        for article in ARTICLES:
            if article["category"] != cat:
                continue
            cards.append(
                f'<a class="exam-guide-card" href="{esc(article["slug"])}.html">'
                f'<p class="exam-guide-card-cat">{esc(cat)}</p>'
                f'<h3>{esc(article["title"])}</h3>'
                f'<p>{esc(article["desc"])}</p>'
                "</a>"
            )
        category_blocks.append(
            f'<section class="site-page-section exam-guide-section" aria-labelledby="guide-{esc(cat)}">'
            f'<h2 id="guide-{esc(cat)}">{esc(cat)}</h2>'
            f'<div class="exam-guide-grid">{"".join(cards)}</div>'
            "</section>"
        )
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{exam_name()} 試験ガイド",
        "description": "試験概要、試験対策、過去問活用、重要論点をまとめたガイド記事一覧です。",
        "url": canonical,
        "numberOfItems": len(ARTICLES),
    }
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>試験ガイド｜{esc(brand_name())}（{esc(exam_name())}）</title>
<meta name="description" content="{esc(exam_name())}の試験概要、試験対策、過去問活用、重要論点をまとめたガイド記事一覧です。">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:title" content="試験ガイド｜{esc(brand_name())}（{esc(exam_name())}）">
<meta property="og:description" content="{esc(exam_name())}の試験概要・過去問活用・重要論点をまとめて確認できます。">
<meta property="og:locale" content="ja_JP">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
{FONT_LINKS}
<link rel="stylesheet" href="../site-pages.css">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{header}
<main class="site-page-main exam-guide-main">
  {breadcrumb}
  <section class="exam-guide-hero">
    <p class="q-index-kicker">Exam Guide</p>
    <h1>試験ガイド</h1>
    <p class="site-page-lead">{esc(exam_name())}の概要、科目別対策、過去問活用、重要論点をまとめたSEOガイドです。公式情報で最新情報を確認しながら、過去問形式の演習と用語学習を組み合わせて進めましょう。</p>
    <div class="q-index-stats" aria-label="試験ガイドの収録状況">
      <span><b>{len(ARTICLES)}</b>記事</span>
      <span><b>{len(categories)}</b>カテゴリ</span>
    </div>
  </section>
  {"".join(category_blocks)}
</main>
{footer}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for old in ARTICLES_DIR.glob("*.html"):
        if old.name != "index.html":
            old.unlink()
    for article in ARTICLES:
        article_path(article).write_text(build_article(article), encoding="utf-8")
    (ARTICLES_DIR / "index.html").write_text(build_index(), encoding="utf-8")
    print(f"Wrote {len(ARTICLES)} exam guide articles under {ARTICLES_DIR}")
    print(f"Wrote {ARTICLES_DIR / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
