#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイト内SEO用の内部リンク索引（CSVベース）。"""

from __future__ import annotations

import csv
import hashlib
import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
GUIDE_CSV = ROOT / "data" / "guide_articles.csv"

CATEGORY_GUIDE: dict[str, str] = {
    "ボイラーの構造に関する知識": "structure-subject",
    "ボイラーの取扱いに関する知識": "handling-subject",
    "燃料及び燃焼に関する知識": "fuel-combustion-subject",
    "関係法令": "law-subject",
}

GENRE_GUIDE: dict[str, str] = {
    "試験概要": "exam-overview",
    "試験対策": "study-plan",
    "過去問活用": "past-questions-how-to-use",
    "学習法": "beginner-guide",
    "科目別対策": "structure-subject",
    "重要論点": "water-level-safety",
    "法令対策": "law-subject",
}

THEME_GUIDE: dict[str, str] = {
    "水位・低水位": "water-level-safety",
    "吹出し・水管理": "water-level-safety",
    "水処理・スケール・腐食": "water-treatment",
    "燃焼安全装置": "combustion-safety",
    "点火・たき始め": "handling-subject",
    "異常時対応": "handling-subject",
    "空気比・NOx・熱損失": "air-ratio",
    "燃料性質・発熱量": "fuel-properties",
    "検査・検査証": "inspection-certificate",
    "設置・ボイラー室": "boiler-room",
    "作業主任者・取扱資格": "chief-operator",
    "附属品・安全弁・圧力計": "safety-valve-pressure",
    "変更・休止・廃止": "notifications",
    "定期自主検査・変更届": "notifications",
}


def norm(value: str | None) -> str:
    return (value or "").strip()


def term_slug(term: str, reading: str, used: dict[str, str]) -> str:
    base = f"{term.strip()}|{reading.strip()}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]
    s = f"g-{h}"
    if s not in used:
        used[s] = base
        return s
    n = 2
    while True:
        cand = f"g-{h}-{n}"
        if cand not in used:
            used[cand] = base
            return cand
        n += 1


def is_theme_row(row: dict[str, str]) -> bool:
    return "頻出テーマ" in norm(row.get("tags"))


def build_glossary_index() -> tuple[dict[str, str], dict[str, list[str]]]:
    """用語名 -> terms/g-xxx.html、分野 -> 用語名リスト（テーマ除く）。"""
    text = GLOSSARY_CSV.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    used: dict[str, str] = {}
    term_to_href: dict[str, str] = {}
    by_category: dict[str, list[str]] = {}
    for row in rows:
        term = norm(row.get("term"))
        if not term:
            continue
        reading = norm(row.get("reading"))
        slug = term_slug(term, reading, used) + ".html"
        term_to_href[term] = f"terms/{slug}"
        cat = norm(row.get("category"))
        if cat and not is_theme_row(row):
            by_category.setdefault(cat, []).append(term)
    return term_to_href, by_category


def guide_titles() -> dict[str, str]:
    if not GUIDE_CSV.is_file():
        return {}
    text = GUIDE_CSV.read_text(encoding="utf-8-sig")
    return {norm(r["slug"]): norm(r["title"]) for r in csv.DictReader(text.splitlines()) if norm(r.get("slug"))}


def guide_slug_for_category(category: str) -> str | None:
    return CATEGORY_GUIDE.get(category)


def guide_slug_for_theme(term: str, category: str) -> str | None:
    return THEME_GUIDE.get(term) or CATEGORY_GUIDE.get(category)


def guide_slug_for_genre(genre: str) -> str | None:
    return GENRE_GUIDE.get(genre)


def find_terms_in_text(text: str, term_to_href: dict[str, str], limit: int = 5) -> list[tuple[str, str]]:
    if not text:
        return []
    hits: list[tuple[str, str]] = []
    for term in sorted(term_to_href.keys(), key=len, reverse=True):
        if len(term) < 2:
            continue
        if term in text and term not in {t for t, _ in hits}:
            hits.append((term, term_to_href[term]))
        if len(hits) >= limit:
            break
    return hits


def related_terms_for_category(
    category: str,
    by_category: dict[str, list[str]],
    term_to_href: dict[str, str],
    limit: int = 5,
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for term in by_category.get(category, []):
        href = term_to_href.get(term)
        if href:
            out.append((term, href))
        if len(out) >= limit:
            break
    return out


def past_questions_for_page(
    pages: list[dict],
    page: dict,
    limit: int = 4,
) -> list[tuple[str, str]]:
    same = [
        p
        for p in pages
        if p["category"] == page["category"] and (p["year"], p["qno"]) != (page["year"], page["qno"])
    ]
    same.sort(key=lambda x: (-x["year"], x["qno"]))
    out: list[tuple[str, str]] = []
    for p in same[:limit]:
        label = f"{p['wareki']} 第{p['qno']}問"
        href = p["rel_path"]
        out.append((label, href))
    return out


def guide_link(slug: str | None, titles: dict[str, str]) -> tuple[str, str] | None:
    if not slug or slug not in titles:
        return None
    return (titles[slug], f"articles/{slug}/index.html")


def rel_href(from_file: Path, to_rel: str) -> str:
    """from_file から見た to_rel への相対パス。"""
    try:
        return Path(os.path.relpath(Path(to_rel), from_file.parent)).as_posix()
    except ValueError:
        return to_rel


def rel_prefix_from_path(rel_path: Path) -> str:
    depth = len(rel_path.parent.parts)
    return "/".join([".."] * depth) + "/" if depth else ""


def past_question_link_sections(page: dict, pages: list[dict], rel_path: Path) -> str:
    term_to_href, by_category = build_glossary_index()
    titles = guide_titles()
    text = " ".join(
        [
            page.get("stem_plain", ""),
            page.get("exp", ""),
            page.get("category", ""),
        ]
    )
    term_links = find_terms_in_text(text, term_to_href, 5)
    if not term_links:
        term_links = related_terms_for_category(page["category"], by_category, term_to_href, 5)
    term_links = [(label, rel_href(rel_path, href)) for label, href in term_links]

    past_links = [
        (label, rel_href(rel_path, href))
        for label, href in past_questions_for_page(pages, page, 4)
    ]

    guide_slug = guide_slug_for_category(page["category"])
    guide_links: list[tuple[str, str]] = []
    g = guide_link(guide_slug, titles)
    if g:
        guide_links.append((g[0], rel_href(rel_path, g[1])))

    parts = [
        related_box_html("関連用語", term_links),
        related_box_html("同じ分野の過去問", past_links),
        related_box_html("関連する試験ガイド", guide_links),
    ]
    return "".join(parts)


def article_link_sections(article: dict[str, str], rel_path: Path) -> str:
    term_to_href, by_category = build_glossary_index()
    titles = guide_titles()
    genre = norm(article.get("genre"))
    text = " ".join(
        norm(article.get(k, ""))
        for k in ("title", "lead", "user_intent", "meta_description")
    )
    term_links = find_terms_in_text(text, term_to_href, 5)
    if not term_links:
        for cat, terms in by_category.items():
            if cat[:2] in text or any(t in text for t in terms[:3]):
                term_links = related_terms_for_category(cat, by_category, term_to_href, 5)
                break
    term_links = [(label, rel_href(rel_path, href)) for label, href in term_links]

    current_slug = norm(article.get("slug"))
    guide_slug = guide_slug_for_genre(genre)
    guide_links: list[tuple[str, str]] = []
    g = guide_link(guide_slug, titles)
    if g and guide_slug != current_slug:
        guide_links.append((g[0], rel_href(rel_path, g[1])))

    q_links = [(f"過去問一覧（{exam_name_short()}）", rel_href(rel_path, "q/index.html"))]
    parts = [
        related_box_html("関連用語", term_links),
        related_box_html("過去問で確認する", q_links),
    ]
    if guide_links:
        parts.append(related_box_html("あわせて読むガイド", guide_links))
    return "".join(parts)


def exam_name_short() -> str:
    return "2級ボイラー"


def term_page_link_sections(entry: dict, rel_path: Path) -> str:
    term_to_href, by_category = build_glossary_index()
    titles = guide_titles()
    term = norm(entry.get("term"))
    category = norm(entry.get("category"))
    is_theme = "頻出テーマ" in norm(entry.get("tags"))

    term_links = related_terms_for_category(category, by_category, term_to_href, 5)
    term_links = [(label, rel_href(rel_path, href)) for label, href in term_links if label != term][:5]

    guide_slug = guide_slug_for_theme(term, category) if is_theme else guide_slug_for_category(category)
    guide_links: list[tuple[str, str]] = []
    g = guide_link(guide_slug, titles)
    if g:
        guide_links.append((g[0], rel_href(rel_path, g[1])))

    q_links = [(f"{category}の過去問を見る", rel_href(rel_path, "q/index.html"))]
    return "".join(
        [
            related_box_html("関連用語", term_links),
            related_box_html("関連する試験ガイド", guide_links),
            related_box_html("過去問で確認", q_links),
        ]
    )


def related_box_html(title: str, links: list[tuple[str, str]], rel_prefix: str = "") -> str:
    if not links:
        return ""
    prefix = rel_prefix.rstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    items = "".join(
        f'<a class="related-link" href="{html.escape(prefix + href)}">{html.escape(label)}</a>'
        for label, href in links
    )
    return (
        f'<section class="seo-article-section" aria-label="{html.escape(title)}">'
        f'<div class="related-box"><div class="related-box-title">{html.escape(title)}</div>'
        f'<div class="related-links">{items}</div></section>'
    )
