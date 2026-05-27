#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply site-config.json to hand-written HTML/JS placeholders."""

from __future__ import annotations

import csv
import json
import re
import sys
import html as html_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import (
    brand_mark,
    brand_name,
    category_to_field_map,
    clean_origin,
    contact_url,
    copyright_text,
    exam_name,
    fields,
    ga4_measurement_id,
    learning_nav_label,
    official_organization,
    primary_external_link,
    sync_config_files,
)
from tools.html_footer import site_page_footer, site_page_header, site_shell_footer

TEXT_TARGETS = [
    ROOT / "index.html",
    ROOT / "about.html",
    ROOT / "privacy.html",
    ROOT / "related-sites.html",
    ROOT / "articles" / "index.html",
    ROOT / "site-analytics.js",
]

STATIC_PAGE_CURRENTS = {
    ROOT / "about.html": "about",
    ROOT / "privacy.html": "privacy",
    ROOT / "related-sites.html": "related",
    ROOT / "articles" / "index.html": "articles",
}

MHLW_URL = "https://www.mhlw.go.jp/"
EXAM_URL = "https://www.exam.or.jp/"

BOILER_LAW_REGEX = (
    r"労働安全衛生法|ボイラー及び圧力容器安全規則|ガス事業法|高圧ガス保安法|"
    r"消防法|電気事業法|建築基準法|関係法令|法令・制度"
)

BOILER_FIELD_PHRASE = "構造・取扱い・燃料及び燃焼・関係法令"

INDEX_CONTENT_REPLACEMENTS = [
    (
        "法令・通達の原文は<a href=\"https://www.mhlw.go.jp/\" target=\"_blank\" rel=\"noopener\" style=\"color:var(--text2);text-decoration:underline\">国土交通省</a>",
        '法令・通達の原文は<a href="https://www.mhlw.go.jp/" target="_blank" rel="noopener" style="color:var(--text2);text-decoration:underline">厚生労働省</a>',
    ),
    (
        "法令・通達の原文は<a href=\"https://www.mlit.go.jp/\"",
        f'法令・通達の原文は<a href="{MHLW_URL}"',
    ),
    (
        'title="サービス略称（差し替え）">S</div>',
        f'title="{brand_name()}">{brand_mark()}</div>',
    ),
    ('href="/"', 'href="index.html"'),
    ('href="/#', 'href="index.html#'),
    (
        "lawN:'国土交通省令・ガイドライン・関連法令（個人情報・消費者法等）の位置づけを整理します。'",
        "lawN:'燃料の性質・燃焼計算・空気比・排ガスなど、燃焼分野の論点を整理します。'",
    ),
    (
        "rightsN:'契約・管理受託・重要事項説明・紛争防止など、契約実務の論点を整理します。'",
        "rightsN:'日常点検・点火停止・異常時対応・水管理など、取扱い分野の論点を整理します。'",
    ),
    (
        "limit:'建物・設備・会計税務・不動産証券化など、設備と数字の論点を整理します。'",
        "limit:'関係法令・検査・作業主任者・保安監督など、法令分野の論点を整理します。'",
    ),
    (
        "lawH:'法令・制度・登録・遵守事項・監督処分など、学習者の義務と手続を整理します。'",
        "lawH:'ボイラー形式・附属装置・安全弁・制御装置など、構造分野の論点を整理します。'",
    ),
    (
        "rightsH:'契約・実務論点・応用論点・入居者対応など、契約と実務上の論点を整理します。'",
        "rightsH:'取扱い・点検・異常時対応・水処理など、運転管理の論点を整理します。'",
    ),
    (
        "    lawH: '法令・制度',\n    rightsH: '契約・実務等',\n    lawN: '関連法令',\n    rightsN: '実務・書面等',\n    limit: '設備・その他等'",
        "    lawH: 'ボイラーの構造',\n    rightsH: 'ボイラーの取扱い',\n    lawN: '燃料及び燃焼',\n    rightsN: '取扱い・点検',\n    limit: '関係法令'",
    ),
    (
        "   desc:'法令・制度・契約実務・設備等の配分に沿ってランダム抽出します。',",
        "   desc:'4科目の出題バランスに沿ってランダム抽出します。',",
    ),
    ("    '民法は難しい。でも諦めない人が受かる。',", "    '法令は条文と実務の両方から確認しよう。',"),
    ("    '契約実務の問題が解けたとき、ちょっと気持ちいい。',", "    '燃焼計算が解けたとき、ちょっと気持ちいい。',"),
    ("    '法律の言葉に、少しずつ慣れてきた頃だ。',", "    '専門用語に、少しずつ慣れてきた頃だ。',"),
    ("法令・制度・契約実務・設備等", BOILER_FIELD_PHRASE),
    ("法令・制度5・契約実務6・設備等5", "構造4・取扱い4・燃料4・法令4"),
    (
        "2級ボイラー技士試験,S,法令・制度,過去問,模擬試験,用語集,契約,実務論点,応用論点,資格学習,合格",
        f"2級ボイラー技士試験,{brand_mark()},ボイラー,過去問,模擬試験,用語集,燃焼,構造,法令,合格",
    ),
]

ORIG_UNITS_BLOCK = """const ORIG_UNITS = {
  structure:[
    {id:'s_boiler',label:'ボイラー形式・本体構造'},
    {id:'s_safety',label:'安全弁・附属装置'},
    {id:'s_control',label:'計装・制御装置'},
    {id:'s_water',label:'給水・蒸気系統'},
  ],
  handling:[
    {id:'h_daily',label:'日常点検・運転操作'},
    {id:'h_water',label:'水位・水処理'},
    {id:'h_abnormal',label:'異常時対応'},
    {id:'h_stop',label:'停止・保存・清掃'},
  ],
  fuel:[
    {id:'f_fuel',label:'燃料の性質'},
    {id:'f_burn',label:'燃焼・空気比'},
    {id:'f_gas',label:'排ガス・燃焼装置'},
    {id:'f_calc',label:'燃焼計算'},
  ],
  law:[
    {id:'l_rule',label:'ボイラー及び圧力容器安全規則'},
    {id:'l_inspect',label:'検査・検査証'},
    {id:'l_operator',label:'作業主任者・保安'},
    {id:'l_other',label:'関係法令'},
  ],
};"""

STATIC_CONTENT_REPLACEMENTS = [
    (
        "出題範囲・得点・合格基準・最新法令は、<strong>国土交通省</strong>や試験実施主体の<strong>公式情報</strong>で必ずご確認ください。",
        f"出題範囲・得点・合格基準・最新法令は、<strong>{official_organization()}</strong>や<strong>厚生労働省</strong>の<strong>公式情報</strong>で必ずご確認ください。",
    ),
    (
        "画面上の「S」はサービス内の短い表記であり、公的な試験名の正式略称ではありません。",
        f"画面上の「{brand_mark()}」はサービス内の短い表記であり、公的な試験名の正式略称ではありません。",
    ),
    (
        '<a href="https://www.exam.or.jp/contact" target="_blank" rel="noopener noreferrer">お問い合わせフォーム</a>',
        f'<a href="{contact_url()}" target="_blank" rel="noopener noreferrer">お問い合わせフォーム</a>',
    ),
    (
        '<code></code>',
        f'<code>{ga4_measurement_id()}</code>',
    ),
    (
        """          <li>
            <a href="https://www.mlit.go.jp/jutakukentiku/house/" target="_blank" rel="noopener noreferrer">国土交通省 住宅局</a>
            … 法令・制度や住宅政策に関する情報の窓口です。
          </li>""",
        f"""          <li>
            <a href="{MHLW_URL}" target="_blank" rel="noopener noreferrer">厚生労働省</a>
            … 労働安全衛生法やボイラー関連の法令情報の窓口です。
          </li>
          <li>
            <a href="https://www.meti.go.jp/policy/safety_security/industrial_safety/" target="_blank" rel="noopener noreferrer">経済産業省（高圧ガス・保安）</a>
            … 高圧ガス保安法など関連制度の参考情報です。
          </li>""",
    ),
]

def _json_ld_text(value: str, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return json.dumps(text, ensure_ascii=False)


def build_index_faq_jsonld() -> str:
    path = ROOT / "data" / "past_questions.csv"
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    picked: list[dict[str, str]] = []
    seen_fields: set[str] = set()
    for row in rows:
        category = str(row.get("category") or "").strip()
        fid = category_to_field_map().get(category, category)
        if fid in seen_fields:
            continue
        stem = str(row.get("stem") or "").strip()
        explanation = str(row.get("explanation") or "").strip()
        if not stem or not explanation:
            continue
        seen_fields.add(fid)
        picked.append({"stem": stem, "explanation": explanation})
        if len(picked) >= 8:
            break
    if len(picked) < 8:
        for row in rows:
            stem = str(row.get("stem") or "").strip()
            explanation = str(row.get("explanation") or "").strip()
            if not stem or not explanation:
                continue
            if any(item["stem"] == stem for item in picked):
                continue
            picked.append({"stem": stem, "explanation": explanation})
            if len(picked) >= 8:
                break

    entities = []
    for item in picked:
        entities.append(
            "    {\n"
            '      "@type": "Question",\n'
            f'      "name": {_json_ld_text(item["stem"], 220)},\n'
            '      "acceptedAnswer": {\n'
            '        "@type": "Answer",\n'
            f'        "text": {_json_ld_text(item["explanation"], 420)}\n'
            "      }\n"
            "    }"
        )
    body = ",\n".join(entities)
    return (
        '<script type="application/ld+json">\n'
        "{\n"
        '  "@context": "https://schema.org",\n'
        '  "@type": "FAQPage",\n'
        f'  "name": {_json_ld_text(f"{exam_name()} よく出る問題と解説", 120)},\n'
        '  "mainEntity": [\n'
        f"{body}\n"
        "  ]\n"
        "}\n"
        "</script>"
    )


def update_index_faq_jsonld(text: str) -> str:
    new_block = build_index_faq_jsonld()
    return re.sub(
        r'<script type="application/ld\+json">[\s\S]*?</script>\s*(?=</head>)',
        new_block + "\n",
        text,
        count=1,
    )


def update_index_template_content(text: str) -> str:
    for src, dst in INDEX_CONTENT_REPLACEMENTS:
        text = text.replace(src, dst)
    text = re.sub(
        r"const ORIG_UNITS = \{[\s\S]*?\};",
        ORIG_UNITS_BLOCK,
        text,
        count=1,
    )
    old_law_alt = (
        "民法|法令・制度|宅地建物取引業法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|"
        "都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|租税特別措置法|"
        "地方税法|地価公示法"
    )
    old_law_alt2 = (
        "民法|法令・制度|宅地建物取引業法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|"
        "都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|宅造法|"
        "租税特別措置法|地方税法|地価公示法|住宅品質確保法|住宅金融支援機構法|住宅瑕疵担保履行法"
    )
    text = text.replace(f"(?:{old_law_alt2})", f"(?:{BOILER_LAW_REGEX})")
    text = text.replace(f"(?:{old_law_alt})", f"(?:{BOILER_LAW_REGEX})")
    text = text.replace("// 1. 法令条文をバッジ化（民法○条、法令・制度○条など）", "// 1. 法令条文をバッジ化（関係法令○条など）")
    return text


def update_static_page_content(text: str) -> str:
    for src, dst in STATIC_CONTENT_REPLACEMENTS:
        text = text.replace(src, dst)
    return text


def replace_all(text: str) -> str:
    origin = clean_origin()
    host = origin.replace("https://", "").replace("http://", "").strip("/")
    official = primary_external_link()
    orig_nav_label = learning_nav_label("tnav-orig", "実践演習")
    replacements = [
        ("© 2026 Sampleマスター学習支援・YOUR-DOMAIN.example", copyright_text()),
        ("Sampleマスター", brand_name()),
        ("◯◯試験（プレースホルダー）", exam_name()),
        ("YOUR-DOMAIN.example", host),
        ("https://YOUR-DOMAIN.example", origin),
        ("https://example.com/contact", contact_url()),
        ("window.__GA4_MEASUREMENT_ID__=\"\"", f'window.__GA4_MEASUREMENT_ID__="{ga4_measurement_id()}"'),
        ('var DEFAULT_MID = "";', f'var DEFAULT_MID = "{ga4_measurement_id()}";'),
        ("一般社団法人 試験実施団体", official_organization()),
        ("試験実施団体（試験・登録の公式）", official.get("label", official_organization())),
        ("https://example.com/", official.get("url", "https://example.com/")),
    ]
    if orig_nav_label == "実践演習":
        replacements.extend(
            [
                ("オリジナル問題", "実践演習"),
                ("オリジナル演習", "実践演習"),
                ("単元別問題データ", "実践演習データ"),
            ]
        )
    if exam_name() != "◯◯試験（プレースホルダー）":
        replacements.append(("◯◯試験", exam_name()))
    for src, dst in replacements:
        text = text.replace(src, dst)

    marker = '<script src="./site-config.js"></script>'
    if "site-config.js" not in text and "site-analytics.js" in text:
        for old, new_block in (
            (
                '<script defer src="./site-analytics.js"></script>',
                marker + '\n<script defer src="./site-analytics.js"></script>',
            ),
            (
                '<script defer src="site-analytics.js"></script>',
                '<script src="site-config.js"></script>\n<script defer src="site-analytics.js"></script>',
            ),
        ):
            if old in text:
                text = text.replace(old, new_block, 1)
                break
    return text


def ensure_theme_link(text: str, rel_path: Path) -> str:
    if "site-theme.css" in text:
        return text
    href = "site-theme.css" if rel_path.parent == Path(".") else "../site-theme.css"
    text = text.replace(
        '<link rel="stylesheet" href="./site-pages.css">',
        '<link rel="stylesheet" href="./site-pages.css">\n  <link rel="stylesheet" href="./site-theme.css">',
    )
    text = text.replace(
        '<link rel="stylesheet" href="../site-pages.css">',
        '<link rel="stylesheet" href="../site-pages.css">\n  <link rel="stylesheet" href="../site-theme.css">',
    )
    if "site-theme.css" not in text and "site-pages.css" in text:
        text = re.sub(
            r'(<link rel="stylesheet" href="[^"]*site-pages\.css[^"]*">)',
            rf'\1\n  <link rel="stylesheet" href="{href}">',
            text,
            count=1,
        )
    return text


def replace_static_chrome(text: str, path: Path) -> str:
    current = STATIC_PAGE_CURRENTS.get(path)
    if not current:
        return text
    rel_path = path.relative_to(ROOT)
    text = re.sub(
        r'\s*<header class="(?:site-page-header(?: site-page-header--wide)?|topnav site-shell-header(?: site-shell-header--wide)?)">.*?</header>',
        "\n" + site_page_header(rel_path, current=current),
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'\s*<footer class="(?:site-page-footer(?: site-page-footer--wide)?|site-footer)[^"]*".*?</footer>\s*(?:<!-- GA4:.*?-->\s*)?(?:<script>window\.__GA4_MEASUREMENT_ID__="[^"]*";</script>\s*)?(?:<script defer src="[^"]*site-analytics\.js"></script>\s*)?',
        "\n" + site_page_footer(rel_path, current=current),
        text,
        count=1,
        flags=re.S,
    )
    text = text.replace("</script></div>", "</script>\n  </div>")
    text = re.sub(
        r'(</div>)\s*<!-- GA4:.*?site-analytics\.js"></script>\s*(?=</body>)',
        r"\1\n",
        text,
        count=1,
        flags=re.S,
    )
    return ensure_theme_link(text, rel_path)


def ensure_index_theme(text: str) -> str:
    if "site-theme.css" in text:
        return text
    theme_link = '<link rel="stylesheet" href="site-theme.css">'
    for needle, repl in (
        ('<script src="site-config.js"></script>', theme_link + '\n<script src="site-config.js"></script>'),
        ('<script src="./site-config.js"></script>', theme_link + '\n  <script src="./site-config.js"></script>'),
        ('<script defer src="site-analytics.js"></script>', theme_link + '\n<script defer src="site-analytics.js"></script>'),
        (
            '<script defer src="./site-analytics.js"></script>',
            theme_link + '\n<script defer src="./site-analytics.js"></script>',
        ),
    ):
        if needle in text:
            return text.replace(needle, repl, 1)
    if "</head>" in text:
        return text.replace("</head>", f"  {theme_link}\n</head>", 1)
    return text


def update_index_shell_footer(text: str) -> str:
    """SPA フッターを site-config の navigation.footer と同型に揃える。"""
    block = site_shell_footer(Path("index.html"), fixed=True, include_analytics=False)
    indented = "\n".join(("  " + line) if line else line for line in block.splitlines())
    return re.sub(
        r'\n  <footer class="site-footer[^"]*" role="contentinfo">.*?</footer>',
        "\n" + indented,
        text,
        count=1,
        flags=re.S,
    )


def update_index_brand_mark(text: str) -> str:
    mark = html_module.escape(brand_mark())

    def inject(match: re.Match[str]) -> str:
        return f"{match.group(1)}{mark}{match.group(3)}"

    text = re.sub(
        r'(<div class="topnav-logo-mark"[^>]*>)(.*?)(</div>)',
        inject,
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'(<div class="auth-logo-mark"[^>]*>)(.*?)(</div>)',
        inject,
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'(<span class="site-footer-logo-mark"[^>]*>)(.*?)(</span>)',
        inject,
        text,
        count=1,
        flags=re.S,
    )
    return text


def update_index_glossary_excerpt(text: str) -> str:
    csv_path = ROOT / "data" / "glossary_terms.csv"
    if not csv_path.is_file() or '<section class="glos-static-section"' not in text:
        return text
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8-sig").splitlines()))
    cat_map = category_to_field_map()
    by_field: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        fid = cat_map.get(str(row.get("category") or "").strip())
        if not fid:
            continue
        by_field.setdefault(fid, []).append(row)

    blocks: list[str] = []
    for f in fields():
        fid = str(f["id"])
        items = by_field.get(fid, [])[:2]
        if not items:
            continue
        legacy = str(f.get("legacyGlossaryCat") or fid)
        articles = []
        for item in items:
            term = html_module.escape(str(item.get("term") or "").strip())
            desc = html_module.escape(str(item.get("short_def") or item.get("definition") or "").strip())
            articles.append(
                '<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">\n'
                f'  <h4 class="glos-static-term" itemprop="name">{term}</h4>\n'
                f'  <p class="glos-static-desc" itemprop="description">{desc}</p>\n'
                "</article>"
            )
        blocks.append(
            f'<div class="glos-cat-section" data-cat="{html_module.escape(legacy)}">\n'
            f'<h3 class="glos-cat-heading">{html_module.escape(str(f.get("name") or fid))}</h3>\n'
            + "\n".join(articles)
            + "\n</div>"
        )
    if not blocks:
        return text

    start = text.find('<section class="glos-static-section"')
    first_block = text.find('<div class="glos-cat-section"', start)
    end = text.find("</section>", first_block)
    if start < 0 or first_block < 0 or end < 0:
        return text
    intro = text[start:first_block]
    replacement = intro + "\n".join(blocks) + "\n</section>"
    return text[:start] + replacement + text[end + len("</section>") :]


def main() -> int:
    sync_config_files()
    for path in TEXT_TARGETS:
        if not path.is_file():
            continue
        old = path.read_text(encoding="utf-8")
        new = replace_static_chrome(replace_all(old), path)
        new = update_static_page_content(new)
        if path == ROOT / "index.html":
            new = ensure_index_theme(new)
            new = update_index_shell_footer(new)
            new = update_index_brand_mark(new)
            new = update_index_glossary_excerpt(new)
            new = update_index_faq_jsonld(new)
            new = update_index_template_content(new)
        if new != old:
            path.write_text(new, encoding="utf-8")
            print(f"Updated {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
