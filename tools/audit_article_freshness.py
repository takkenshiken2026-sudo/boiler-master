#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit generated SEO guide articles for freshness and required blocks."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"

REQUIRED_SNIPPETS = [
    'class="article-toc"',
    'id="article-trust"',
    'id="article-official"',
    'id="article-basic"',
    'id="article-can-do"',
    'id="article-faq"',
    'id="article-related"',
    '<details class="term-faq-item" open>',
    'class="related-link"',
]


def audit_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if "example.com" in text:
        issues.append("example.com が残っています")
    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            issues.append(f"必須ブロック不足: {snippet}")
    m = re.search(r"事実確認日</th><td>(\d{4}-\d{2}-\d{2})</td>", text)
    if not m:
        issues.append("事実確認日が見つかりません")
    else:
        checked = date.fromisoformat(m.group(1))
        if (date.today() - checked).days > 45:
            issues.append(f"事実確認日が古い可能性があります: {checked.isoformat()}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args()

    all_issues: list[tuple[Path, list[str]]] = []
    for path in sorted(ARTICLES.glob("*.html")):
        if path.name == "index.html":
            continue
        issues = audit_file(path)
        if issues:
            all_issues.append((path, issues))

    if not all_issues:
        print("Article freshness audit passed")
        return 0

    for path, issues in all_issues:
        print(f"{path.relative_to(ROOT)}")
        for issue in issues:
            print(f"  - {issue}")
    return 1 if args.fail_on_review else 0


if __name__ == "__main__":
    raise SystemExit(main())
