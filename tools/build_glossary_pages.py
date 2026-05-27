#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/glossary_terms.csv から用語ページ terms/g-*.html と terms/index.html を生成し、
過去問と合わせた sitemap.xml を書き直す。
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.site_config import (
    brand_name,
    category_order,
    category_to_field_map,
    clean_origin,
    css_safe_field_id,
    exam_name,
    field_labels,
)

HEAD_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
TERMS_DIR = ROOT / "terms"
BASE_DEFAULT = clean_origin()

# site-config.json の fields[].aliases / name と揃える
FIELD_LABELS = field_labels()
GLOSSARY_CAT_TO_FIELD: dict[str, str] = category_to_field_map()

# 用語索引ページの科目チップ・見出しの並び（CSV のカテゴリ名と一致）
GLOSSARY_CAT_ORDER = tuple(category_order())

RELATED_TERM_ALIASES: dict[str, str] = {
    "LPガス": "LPガス（プロパンガス）",
    "換気": "換気設備",
    "消防用設備": "消防用設備等点検",
    "安全弁": "安全弁（リリーフ弁）",
    "低水位": "低水位警報装置",
    "空気比": "理論空気量",
}


def norm(s: str | None) -> str:
    return (s or "").strip()


def lookup_key(s: str) -> str:
    return re.sub(r"\s+", "", s)


def term_alias_variants(term: str) -> set[str]:
    variants = {term, lookup_key(term)}
    no_paren = re.sub(r"（[^）]+）|\([^)]*\)", "", term).strip()
    if no_paren and no_paren != term:
        variants.add(no_paren)
        variants.add(lookup_key(no_paren))
    for part in re.findall(r"（([^）]+)）|\(([^)]*)\)", term):
        inner = next((x for x in part if x), "").strip()
        if inner:
            variants.add(inner)
            variants.add(lookup_key(inner))
    return {v for v in variants if v}


def term_slug(term: str, reading: str, used: dict[str, str]) -> str:
    """用語+読みで安定したスラッグ。衝突時は連番を付与。"""
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


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def rel_to_root(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/index.html"


def rel_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css?v=20260515-topgray"


def rel_theme_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-theme.css"


def glossary_field_id(category: str) -> str | None:
    return GLOSSARY_CAT_TO_FIELD.get(norm(category))


def glossary_field_badge_html(category: str) -> str:
    fid = glossary_field_id(category)
    if not fid:
        return ""
    label = FIELD_LABELS.get(fid, fid)
    return f'<span class="term-field-badge term-field-{css_safe_field_id(fid)}">{html.escape(label)}</span>'


def ordered_term_categories(by_cat: dict[str, list]) -> list[str]:
    keys = set(by_cat.keys())
    out: list[str] = [c for c in GLOSSARY_CAT_ORDER if c in keys]
    for c in sorted(keys):
        if c not in out:
            out.append(c)
    return out


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def split_sentences(s: str) -> list[str]:
    text = re.sub(r"\s+", " ", s or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def study_points(explanation: str, limit: int = 4) -> list[str]:
    points: list[str] = []
    for sentence in split_sentences(explanation):
        s = sentence.rstrip("。")
        if len(s) < 14:
            continue
        if s.endswith("です") and "とは、" in s:
            continue
        points.append(s + "。")
        if len(points) >= limit:
            break
    return points


def make_term_lookup(entries: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    conflicts: set[str] = set()
    exact_keys: set[str] = set()

    def add(key: str, href: str, *, exact: bool = False) -> None:
        if not key or key in conflicts:
            return
        existing = lookup.get(key)
        if existing and existing != href:
            if key in exact_keys:
                return
            lookup.pop(key, None)
            conflicts.add(key)
            return
        lookup[key] = href
        if exact:
            exact_keys.add(key)

    for e in entries:
        term = e["term"]
        add(term, e["slug_file"], exact=True)
        add(lookup_key(term), e["slug_file"], exact=True)
    for e in entries:
        term = e["term"]
        for key in term_alias_variants(term):
            add(key, e["slug_file"])
    for alias, target in RELATED_TERM_ALIASES.items():
        target_href = lookup.get(target) or lookup.get(lookup_key(target))
        if target_href:
            add(alias, target_href)
            add(lookup_key(alias), target_href)
    return lookup


def related_terms_html(related: str, term_lookup: dict[str, str]) -> str:
    items: list[str] = []
    for label in split_semicolon(related):
        href = term_lookup.get(label) or term_lookup.get(lookup_key(label))
        if href:
            items.append(f'<a class="related-link" href="{html.escape(href)}">{html.escape(label)}</a>')
        else:
            items.append(f'<span class="related-link related-link-static">{html.escape(label)}</span>')
    if not items:
        return ""
    return "".join(items)


def legal_basis_html(legal: str) -> str:
    items = split_semicolon(legal)
    if len(items) <= 1:
        return html.escape(legal).replace("\n", "<br>\n")
    return '<ul class="term-legal-list">' + "".join(f"<li>{html.escape(x)}</li>" for x in items) + "</ul>"


def faq_items_for_term(term: str, reading: str, short_def: str, definition: str, explanation: str) -> list[dict[str, str]]:
    first_points = study_points(explanation, limit=2)
    exam_answer = " ".join(first_points) if first_points else explanation
    return [
        {
            "question": f"{term}とは何ですか？",
            "answer": f"{term}（{reading}）とは、{short_def.rstrip('。')}。{definition}",
        },
        {
            "question": f"{term}は試験でどう押さえればよいですか？",
            "answer": exam_answer,
        },
    ]


def faq_section_html(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    body = []
    for item in items:
        body.append(
            '<details class="term-faq-item">'
            f'<summary>{html.escape(item["question"])}</summary>'
            f'<div>{html.escape(item["answer"])}</div>'
            "</details>"
        )
    return "".join(body)


def write_sitemap(urls: list[str], out: Path) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(urls)):
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(u)}</loc>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_sitemap_urls(base: str) -> list[str]:
    urls = [
        f"{base}/",
        f"{base}/about.html",
        f"{base}/privacy.html",
        f"{base}/related-sites.html",
        f"{base}/articles/index.html",
        f"{base}/q/index.html",
    ]
    articles_dir = ROOT / "articles"
    if articles_dir.is_dir():
        for p in sorted(articles_dir.glob("*.html")):
            rel = p.relative_to(ROOT).as_posix()
            urls.append(f"{base}/{rel}")
    qroot = ROOT / "q"
    if qroot.is_dir():
        for p in sorted(qroot.rglob("index.html")):
            rel = p.relative_to(ROOT).as_posix()
            urls.append(f"{base}/{rel}")
    if (TERMS_DIR / "index.html").is_file():
        urls.append(f"{base}/terms/index.html")
    for p in sorted(TERMS_DIR.glob("g-*.html")):
        rel = p.relative_to(ROOT).as_posix()
        urls.append(f"{base}/{rel}")
    return urls


def build_term_html(entry: dict, rel_path: Path, base_url: str, term_lookup: dict[str, str]) -> str:
    term = entry["term"]
    reading = entry["reading"]
    category = entry["category"]
    tags = entry["tags"]
    short_def = entry["short_def"]
    definition = entry["definition"]
    related = entry["related_terms"]
    legal = entry["legal_basis"]
    importance = entry["importance"]
    explanation = entry["explanation"]
    slug_file = entry["slug_file"]

    title = f"{term}とは？意味・根拠・試験ポイント｜{brand_name()}"
    desc = meta_description(
        f"{term}（{reading}）の意味、法令・根拠、試験で押さえるポイントを{exam_name()}向けに整理。{short_def or definition}"
    )
    canonical = public_url(base_url, f"terms/{slug_file}")
    root_idx = rel_to_root(rel_path)
    css_href = rel_css(rel_path)
    theme_href = rel_theme_css(rel_path)

    tags_list = split_semicolon(tags)
    rel_html = related_terms_html(related, term_lookup)

    def text_paragraphs(body: str) -> str:
        if not body.strip():
            return ""
        paras = [p.strip() for p in re.split(r"\n{2,}", body.strip()) if p.strip()]
        if not paras:
            paras = [body.strip()]
        return "\n".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in paras)

    def article_section(sec_id: str, label: str, body_html: str) -> str:
        if not body_html.strip():
            return ""
        hid = f"term-sec-{sec_id}"
        return (
            f'<section class="seo-article-section" aria-labelledby="{hid}">'
            f'<h2 id="{hid}">{html.escape(label)}</h2>'
            f"{body_html}</section>"
        )

    info_rows: list[tuple[str, str]] = []
    if category:
        info_rows.append(("分野", category))
    if importance:
        info_rows.append(("重要度", importance))
    if legal:
        info_rows.append(("法令・根拠", " / ".join(split_semicolon(legal))))
    if tags_list:
        info_rows.append(("関連タグ", " / ".join(tags_list)))
    info_table = ""
    if info_rows:
        info_table = (
            '<table class="seo-info-table"><tbody>'
            + "".join(
                f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>"
                for k, v in info_rows
            )
            + "</tbody></table>"
        )

    rel_section = ""
    if rel_html:
        rel_section = (
            '<div class="related-box"><div class="related-box-title">関連用語</div>'
            f'<div class="related-links term-related-links">{rel_html}</div></div>'
        )

    lead = (
        f"{term}は、{short_def.rstrip('。')}。"
        f"{exam_name()}では、{category}分野の用語として、意味・根拠・似た用語との違いをセットで押さえると理解しやすくなります。"
    )
    points = study_points(explanation)
    points_html = ""
    if points:
        points_html = '<ol class="term-point-list">' + "".join(f"<li>{html.escape(p)}</li>" for p in points) + "</ol>"
    faq_items = faq_items_for_term(term, reading, short_def, definition, explanation)
    faq_html = faq_section_html(faq_items)

    badge_html = glossary_field_badge_html(category)
    meta_bits: list[str] = ['<span class="q-id">用語</span>']
    if badge_html:
        meta_bits.append(badge_html)
    if category:
        meta_bits.append(f"<span>{html.escape(category)}</span>")
    meta_line = " · ".join(meta_bits)

    crumb_items = [
        ("トップ", "index.html"),
        ("用語解説一覧", "terms/index.html"),
        (term, None),
    ]
    page_header = site_page_header(rel_path, current="terms")
    page_breadcrumb = breadcrumb_html(rel_path, crumb_items)
    page_footer = site_page_footer(rel_path, current="terms")

    app_glossary_href = f"{root_idx}#glossary"
    updated = date.today().isoformat()

    note_html = (
        "<blockquote><p><strong>注意：</strong>"
        "本ページは学習用の要点整理です。出題範囲・法令・公式見解は変更される場合があります。"
        "本番前には必ず試験実施団体や法令原文などの公式情報を確認してください。"
        "</p></blockquote>"
    )

    next_links = (
        '<div class="related-box"><div class="related-box-title">次に確認するページ</div>'
        '<div class="related-links">'
        '<a class="related-link" href="index.html">用語解説一覧へ戻る</a>'
        f'<a class="related-link" href="{html.escape(root_idx)}#glossary">アプリ内の用語解説を開く</a>'
        f'<a class="related-link" href="{html.escape(root_idx)}#past">過去問演習で確認する</a>'
        "</div></div>"
    )

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "DefinedTerm",
                "@id": canonical + "#term",
                "name": term,
                "description": meta_description(definition or short_def, 300),
                "inDefinedTermSet": public_url(base_url, "terms/index.html"),
            },
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": title,
                "description": desc,
                "about": term,
                "mainEntityOfPage": canonical,
                "inLanguage": "ja-JP",
                "isPartOf": public_url(base_url, "terms/index.html"),
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url(base_url, "index.html")},
                    {"@type": "ListItem", "position": 2, "name": "用語解説", "item": public_url(base_url, "terms/index.html")},
                    {"@type": "ListItem", "position": 3, "name": term, "item": canonical},
                ],
            },
            {
                "@type": "FAQPage",
                "@id": canonical + "#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq_items
                ],
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(css_href)}">
<link rel="stylesheet" href="{html.escape(theme_href)}">
</head>
<body>
{site_page_wrap_open()}
{page_header}
<main class="seo-article-main">
  {page_breadcrumb}
  <article class="seo-article-card article-body">
    <div class="article-meta">
      <span class="meta-category">用語解説</span>
      <span class="meta-updated">更新日：{html.escape(updated)}</span>
      <span class="meta-updated">{meta_line}</span>
    </div>
    <h1 class="article-title">{html.escape(term)}とは？意味・根拠・試験ポイントを整理</h1>
    <p class="article-lead"><strong>{html.escape(term)}</strong>{f"（{html.escape(reading)}）" if reading else ""}について、定義・根拠・試験での押さえ方をまとめます。{html.escape(lead)}</p>
    {note_html}
    {article_section("summary", "まず押さえる要点", text_paragraphs(short_def) + info_table)}
    {article_section("points", "試験で押さえるポイント", points_html)}
    {article_section("definition", "定義と基本理解", text_paragraphs(definition))}
    {article_section("legal", "法令・根拠", legal_basis_html(legal))}
    {article_section("exam", "選択肢で問われやすい点", text_paragraphs(explanation))}
    {article_section("faq", "よくある確認ポイント", faq_html)}
    {rel_section}
    {next_links}
  </article>
</main>
{page_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_terms_index(entries: list[dict], base_url: str) -> str:
    by_cat: dict[str, list[dict]] = {}
    for e in entries:
        by_cat.setdefault(e["category"] or "その他", []).append(e)
    for c in by_cat:
        by_cat[c].sort(key=lambda x: x["term"])

    cat_keys = ordered_term_categories(by_cat)
    body_sections: list[str] = []
    for i, cat in enumerate(cat_keys):
        lis = []
        for e in by_cat[cat]:
            href = e["slug_file"]
            lis.append(
                f'    <li><a href="{html.escape(href)}">{html.escape(e["term"])}</a></li>'
            )
        hid = f"terms-idx-cat-{i}"
        body_sections.append(
            f'<section class="terms-idx-cat" aria-labelledby="{hid}">\n'
            f'  <h2 id="{hid}">{html.escape(cat)}</h2>\n'
            f'  <ul class="terms-idx-list">\n'
            + "\n".join(lis)
            + "\n  </ul>\n</section>"
        )
    body_html = "\n".join(body_sections)

    chip_lines = [
        '    <button type="button" class="terms-idx-chip on" data-cat="all">すべて</button>'
    ]
    for cat in cat_keys:
        chip_lines.append(
            "    "
            f'<button type="button" class="terms-idx-chip" data-cat="{html.escape(cat, quote=True)}">'
            f"{html.escape(cat)}</button>"
        )
    chips_html = "\n".join(chip_lines)

    list_items_ld: list[dict] = []
    pos = 1
    for cat in cat_keys:
        for e in by_cat[cat]:
            list_items_ld.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": e["term"],
                    "item": public_url(base_url, f"terms/{e['slug_file']}"),
                }
            )
            pos += 1
    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{exam_name()} 用語解説一覧",
        "description": "試験で出やすい用語ごとの解説記事への索引です。",
        "numberOfItems": len(entries),
        "itemListElement": list_items_ld,
    }
    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)

    n_terms = len(entries)
    terms_idx_script = f"""<script>
(() => {{
  try {{ if ('scrollRestoration' in history) history.scrollRestoration = 'manual'; }} catch (_e) {{}}
  window.scrollTo(0, 0);
  const q = document.getElementById('terms-idx-q');
  const chips = Array.from(document.querySelectorAll('.terms-idx-chip[data-cat]'));
  const cats = Array.from(document.querySelectorAll('.terms-idx-cat'));
  const totalEl = document.getElementById('terms-idx-total');
  const hitEl = document.getElementById('terms-idx-hit');
  let activeCat = 'all';
  function norm(s) {{
    return (s || '').toString().trim().toLowerCase();
  }}
  function apply() {{
    const query = norm(q.value);
    let shown = 0;
    cats.forEach((sec) => {{
      const cat = sec.querySelector('h2')?.textContent || '';
      const catOk = activeCat === 'all' || cat === activeCat;
      const items = Array.from(sec.querySelectorAll('li'));
      let anyInCat = 0;
      items.forEach((li) => {{
        const a = li.querySelector('a');
        const t = norm(a?.textContent || '');
        const ok = catOk && (!query || t.includes(query));
        li.classList.toggle('hide', !ok);
        if (ok) {{
          anyInCat++;
          shown++;
        }}
      }});
      sec.classList.toggle('hide', anyInCat === 0);
    }});
    if (totalEl) totalEl.textContent = String({n_terms});
    if (hitEl) {{
      hitEl.textContent =
        (query || activeCat !== 'all') ? '表示：' + shown + '件' : '';
    }}
  }}
  q.addEventListener('input', apply);
  chips.forEach((btn) => {{
    btn.addEventListener('click', () => {{
      chips.forEach((b) => b.classList.remove('on'));
      btn.classList.add('on');
      activeCat = btn.dataset.cat || 'all';
      apply();
    }});
  }});
  apply();
}})();
</script>"""

    idx_path = Path("terms/index.html")
    terms_header = site_page_header(
        idx_path,
        current="terms",
        wide=True,
    )
    terms_breadcrumb = breadcrumb_html(idx_path, [("トップ", "index.html"), ("用語解説一覧", None)])
    terms_footer = site_page_footer(idx_path, current="terms", wide=True)

    canonical = public_url(base_url, "terms/index.html")
    title = f"用語解説一覧（全記事索引）｜{brand_name()}（{exam_name()}）"
    desc = (
        f"{exam_name()}の重要用語を一覧し、各用語の解説記事へリンクします。"
        "法令・制度・契約・実務・設備・その他などの語句を整理しています。"
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{html.escape(canonical)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="試験で出やすい用語ごとの解説記事への索引です。">
<meta property="og:locale" content="ja_JP">
<script type="application/ld+json">
{ld_json}
</script>
{HEAD_FONTS}
<link rel="stylesheet" href="../site-pages.css?v=20260515-topgray">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{terms_header}
<main class="site-page-main terms-idx-main">
  {terms_breadcrumb}
  <h1 class="terms-idx-page-title">用語解説一覧（全記事索引）</h1>
  <p class="terms-idx-lead">{html.escape(exam_name())}で頻出の用語を分野別にまとめ、各用語の解説記事（静的HTML）へ直接リンクします。上の検索・分野フィルタで目的の用語に素早く到達できます。演習アプリ内の<strong><a href="../index.html#glossary">用語解説</a></strong>では検索や折りたたみカードも利用できます。</p>

  <div class="terms-idx-meta-row">
    <span class="terms-idx-pill">全 <span id="terms-idx-total">{n_terms}</span> 記事</span>
    <div class="terms-idx-search" role="search" aria-label="用語検索">
      <input id="terms-idx-q" type="search" inputmode="search" placeholder="例：定期借家、実務論点、法令・制度…" autocomplete="off">
    </div>
  </div>

  <div class="terms-idx-chips" aria-label="分野フィルタ">
{chips_html}
  </div>

  <section class="terms-idx-panel" aria-label="用語一覧">
{body_html}
    <div class="terms-idx-panel-footer">
      <span id="terms-idx-hit"></span>
      <div class="terms-idx-panel-footer-app">学習アプリ本体は <a href="../index.html">トップ</a> から利用できます。</div>
    </div>
  </section>
</main>
{terms_footer}
{site_page_wrap_close()}
{terms_idx_script}
</body>
</html>
"""


def load_glossary_rows() -> list[dict]:
    if not GLOSSARY_CSV.is_file():
        raise FileNotFoundError(str(GLOSSARY_CSV))
    text = GLOSSARY_CSV.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    rows = load_glossary_rows()
    used_slugs: dict[str, str] = {}
    entries: list[dict] = []
    for i, row in enumerate(rows, start=2):
        term = norm(row.get("term"))
        if not term:
            raise ValueError(f"line {i}: term が空です")
        reading = norm(row.get("reading"))
        slug_file = term_slug(term, reading, used_slugs) + ".html"
        entries.append(
            {
                "term": term,
                "reading": reading,
                "category": norm(row.get("category")),
                "tags": norm(row.get("tags")),
                "short_def": norm(row.get("short_def")),
                "definition": norm(row.get("definition")),
                "related_terms": norm(row.get("related_terms")),
                "legal_basis": norm(row.get("legal_basis")),
                "importance": norm(row.get("importance")),
                "explanation": norm(row.get("explanation")),
                "slug_file": slug_file,
            }
        )

    term_lookup = make_term_lookup(entries)

    TERMS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in TERMS_DIR.glob("g-*.html"):
        stale.unlink()

    for e in entries:
        out_file = TERMS_DIR / e["slug_file"]
        rel_path = out_file.relative_to(ROOT)
        out_file.write_text(build_term_html(e, rel_path, base, term_lookup), encoding="utf-8")

    (TERMS_DIR / "index.html").write_text(build_terms_index(entries, base), encoding="utf-8")

    urls = collect_sitemap_urls(base)
    write_sitemap(urls, ROOT / "sitemap.xml")

    print(f"Wrote {len(entries)} term pages under {TERMS_DIR}")
    print(f"Wrote {TERMS_DIR / 'index.html'}")
    print(f"Updated {ROOT / 'sitemap.xml'} ({len(set(urls))} URLs)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
