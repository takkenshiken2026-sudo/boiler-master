#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glossary_terms_export.json から分野別 handwritten モジュールを生成する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.handwrite_glossary_articles import generate_term_content

EXPORT = ROOT / "data" / "glossary_terms_export.json"
OUT_DIR = ROOT / "tools" / "glossary_handwritten"

CATEGORY_MODULE = {
    "ボイラーの構造に関する知識": "structure",
    "ボイラーの取扱いに関する知識": "handling",
    "燃料及び燃焼に関する知識": "combustion",
    "関係法令": "law",
}


def py_str(s: str) -> str:
    return repr(s)


def write_module(name: str, entries: dict[str, dict[str, str]]) -> None:
    lines = [
        "# -*- coding: utf-8 -*-",
        f'"""手書き用語スニペット: {name}（自動生成後に編集可）"""',
        "",
        "from __future__ import annotations",
        "",
        "SNIPPET_OVERRIDES: dict[str, dict[str, str]] = {",
    ]
    for term in sorted(entries.keys()):
        fields = entries[term]
        lines.append(f"    {py_str(term)}: {{")
        for key in (
            "article_title",
            "article_lead",
            "term_detail_body",
            "exam_points",
            "common_mistakes",
            "memory_tip",
            "explanation",
            "example_question",
            "example_answer",
            "comparison_html",
            "faq_1_question",
            "faq_1_answer",
            "faq_2_question",
            "faq_2_answer",
            "faq_3_question",
            "faq_3_answer",
            "faq_4_question",
            "faq_4_answer",
        ):
            val = fields.get(key, "")
            if not val:
                continue
            lines.append(f"        {py_str(key)}: {py_str(val)},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    path = OUT_DIR / f"{name}.py"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path} ({len(entries)} terms)")


def main() -> int:
    if not EXPORT.is_file():
        print(f"Missing {EXPORT}", file=sys.stderr)
        return 1
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    buckets: dict[str, dict[str, dict[str, str]]] = {v: {} for v in CATEGORY_MODULE.values()}

    for category, terms in data.items():
        mod = CATEGORY_MODULE.get(category)
        if not mod:
            continue
        for item in terms:
            row = {
                "term": item["term"],
                "category": category,
                "short_def": item["short"],
                "definition": item["def"],
                "related_terms": item["related"],
                "importance": item.get("imp", "A"),
                "tags": "重要用語;頻出用語",
            }
            buckets[mod][item["term"]] = generate_term_content(row, use_snippets=False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, entries in buckets.items():
        write_module(name, entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
