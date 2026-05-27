#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive site quality audit: text issues, broken links, placeholders."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import load_config  # noqa: E402

TEXT_COLUMNS = {
    "past_questions.csv": [
        "exam_wareki",
        "category",
        "stem",
        "choice_1",
        "choice_2",
        "choice_3",
        "choice_4",
        "choice_5",
        "explanation",
    ],
    "original_questions.csv": [
        "category",
        "stem",
        "choice_1",
        "choice_2",
        "choice_3",
        "choice_4",
        "choice_5",
        "explanation",
    ],
    "past_questions_marubatsu_all_explanations.csv": ["question", "explanation"],
    "glossary_terms.csv": [
        "term",
        "reading",
        "short_def",
        "definition",
        "related_terms",
        "legal_basis",
        "explanation",
    ],
}

PLACEHOLDER_PATTERNS = [
    (r"example\.com", "プレースホルダーURL (example.com)"),
    (r"lorem ipsum", "ダミーテキスト"),
    (r"TODO|FIXME", "未完了マーカー"),
    (r"テンプレートサイト", "テンプレート文言"),
    (r"資格学習サイト", "テンプレート文言"),
    (r"chintaikanrishi", "他サイト名の残存"),
    (r"管理業務主任者", "他資格名の残存"),
    (r"ガスボイラー", "他資格名の残存（要確認）"),
]

# 明らかな誤字・重複文字パターン（日本語学習サイト向け）
TYPO_PATTERNS = [
    (r"しし{2,}", "「し」の重複"),
    (r"すす{2,}", "「す」の重複"),
    (r"とと{2,}", "「と」の重複"),
    (r"がが{2,}", "「が」の重複"),
    (r"のの{2,}", "「の」の重複"),
    (r"をを{2,}", "「を」の重複"),
    (r"はは{2,}", "「は」の重複"),
    (r"てて{2,}", "「て」の重複"),
    (r"いい{3,}", "「い」の過剰重複"),
    (r"。。{2,}", "句点の重複"),
    (r"、、{2,}", "読点の重複"),
    (r"  {2,}", "半角スペースの連続"),
    (r"　　+", "全角スペースの連続"),
    (r"[\u3000 ]{3,}", "空白の過剰"),
    (r"\.{4,}", "ピリオドの過剰"),
    (r"!{2,}", "感嘆符の重複"),
    (r"\?{2,}", "疑問符の重複"),
    (r"ボイラーラ", "「ボイラー」の誤字疑い"),
    (r"蒸気機関", "ボイラー試験外の用語（要確認）"),
    (r"管理業務", "他資格の用語"),
    (r"マンション管理", "他資格の用語"),
    (r"区分所有法", "他資格の用語"),
    (r"宅建", "他資格の用語"),
    (r"建築士", "他資格の用語（要確認）"),
    (r"電気工事士", "他資格の用語（要確認）"),
]

SKIP_DUP_CHAR_CONTEXT = re.compile(
    r"(正しい|誤り|誤っている|誤りがある|誤りのある|正しくない|"
    r"一問一答|○|×|記述|選択|比較|除去|replace|regex|test|"
    r"placeholder|example\.com|demo@)"
)


@dataclass
class Issue:
    level: str
    source: str
    message: str

    def format(self) -> str:
        return f"[{self.level}] {self.source} - {self.message}"


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        if tag == "a" and attr_map.get("href"):
            self.links.append(("a", attr_map["href"]))
        elif tag == "link" and attr_map.get("href"):
            self.links.append(("link", attr_map["href"]))
        elif tag == "script" and attr_map.get("src"):
            self.links.append(("script", attr_map["src"]))
        elif tag == "img" and attr_map.get("src"):
            self.links.append(("img", attr_map["src"]))


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def visible_text_from_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return strip_html(raw)


def scan_text(source: str, text: str, issues: list[Issue]) -> None:
    if not text or not text.strip():
        return
    for pattern, label in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            snippet = text[max(0, m.start() - 20) : m.end() + 20]
            issues.append(Issue("ERROR", source, f"{label}: …{snippet}…"))

    for pattern, label in TYPO_PATTERNS:
        for m in re.finditer(pattern, text):
            if label.endswith("要確認）") and "ガスボイラー" in label:
                continue
            ctx = text[max(0, m.start() - 30) : m.end() + 30]
            if SKIP_DUP_CHAR_CONTEXT.search(ctx):
                continue
            snippet = text[max(0, m.start() - 15) : m.end() + 15]
            issues.append(Issue("WARN", source, f"{label}: …{snippet}…"))

    # 同一文字3連続以上（カタカナ長音・数字・記号除く）
    for m in re.finditer(r"(.)\1{2,}", text):
        ch = m.group(1)
        if ch in "ー0123456789０１２３４５６７８９…・":
            continue
        ctx = text[max(0, m.start() - 20) : m.end() + 20]
        if SKIP_DUP_CHAR_CONTEXT.search(ctx):
            continue
        snippet = text[max(0, m.start() - 10) : m.end() + 10]
        issues.append(Issue("WARN", source, f"文字の3連続以上: '{ch}' …{snippet}…"))


def audit_csv_files(issues: list[Issue]) -> None:
    data_dir = ROOT / "data"
    for filename, columns in TEXT_COLUMNS.items():
        path = data_dir / filename
        if not path.is_file():
            issues.append(Issue("ERROR", str(path.relative_to(ROOT)), "CSVが見つかりません"))
            continue
        rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
        for idx, row in enumerate(rows, start=2):
            for col in columns:
                value = (row.get(col) or "").strip()
                if not value:
                    continue
                scan_text(f"data/{filename}:{idx}:{col}", value, issues)


def collect_html_files(site_root: Path) -> list[Path]:
    skip = {"public_site", ".git", "node_modules", "__pycache__"}
    files: list[Path] = []
    for path in site_root.rglob("*.html"):
        if any(part in skip for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def resolve_internal(target: Path, href: str) -> Path | None:
    href = href.split("#")[0].split("?")[0].strip()
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return None
    if href.startswith("/"):
        return (ROOT / href.lstrip("/")).resolve()
    return (target.parent / href).resolve()


def audit_html_files(site_root: Path, issues: list[Issue]) -> tuple[set[str], list[tuple[str, str]]]:
    html_files = collect_html_files(site_root)
    existing = {p.resolve() for p in html_files}
    external: list[tuple[str, str]] = []

    for path in html_files:
        rel = str(path.relative_to(ROOT))
        text = visible_text_from_html(path)
        scan_text(rel, text, issues)

        parser = LinkExtractor()
        try:
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            issues.append(Issue("ERROR", rel, f"HTML解析失敗: {exc}"))
            continue

        for kind, href in parser.links:
            if not href or href.startswith("#"):
                continue
            if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if href.startswith(("http://", "https://")):
                external.append((rel, href))
                continue
            resolved = resolve_internal(path, href)
            if resolved is None:
                continue
            if kind == "a" and href.endswith("/"):
                if not resolved.is_dir() and not (resolved / "index.html").is_file():
                    issues.append(Issue("ERROR", rel, f"リンク切れ: {href}"))
                continue
            if not resolved.is_file():
                # index.html 省略
                alt = resolved / "index.html"
                if alt.is_file():
                    continue
                issues.append(Issue("ERROR", rel, f"リンク切れ ({kind}): {href}"))

    return existing, external


def check_external_links(links: list[tuple[str, str]], issues: list[Issue], timeout: float) -> None:
    seen: set[str] = set()
    for source, url in links:
        if url in seen:
            continue
        seen.add(url)
        if "example.com" in url:
            issues.append(Issue("ERROR", source, f"外部リンクがプレースホルダー: {url}"))
            continue
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "boiler-master-quality-audit/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status >= 400:
                    issues.append(Issue("ERROR", source, f"外部リンク HTTP {resp.status}: {url}"))
        except urllib.error.HTTPError as exc:
            if exc.code in {403, 405}:
                # HEAD 不可のサイトは GET で再試行
                try:
                    req_get = urllib.request.Request(
                        url,
                        headers={"User-Agent": "boiler-master-quality-audit/1.0"},
                    )
                    with urllib.request.urlopen(req_get, timeout=timeout) as resp:
                        if resp.status >= 400:
                            issues.append(Issue("ERROR", source, f"外部リンク HTTP {resp.status}: {url}"))
                except Exception as exc2:
                    issues.append(Issue("WARN", source, f"外部リンク確認不可: {url} ({exc2})"))
            else:
                issues.append(Issue("ERROR", source, f"外部リンク HTTP {exc.code}: {url}"))
        except Exception as exc:
            issues.append(Issue("WARN", source, f"外部リンク確認不可: {url} ({exc})"))


def audit_js_files(issues: list[Issue]) -> None:
    for path in sorted(ROOT.glob("*.js")):
        text = path.read_text(encoding="utf-8", errors="replace")
        scan_text(str(path.relative_to(ROOT)), text, issues)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit site content quality")
    parser.add_argument("--site-root", default=str(ROOT), help="Root directory to scan")
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--external-timeout", type=float, default=15.0)
    args = parser.parse_args()

    site_root = Path(args.site_root).resolve()
    issues: list[Issue] = []

    load_config()
    print("=== CSV テキスト監査 ===")
    audit_csv_files(issues)

    print("=== HTML テキスト・内部リンク監査 ===")
    _, external = audit_html_files(site_root, issues)

    print("=== JS テキスト監査 ===")
    audit_js_files(issues)

    if not args.skip_external and external:
        print(f"=== 外部リンク監査 ({len(set(u for _, u in external))} URL) ===")
        check_external_links(external, issues, args.external_timeout)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    for issue in issues:
        stream = sys.stderr if issue.level == "ERROR" else sys.stdout
        print(issue.format(), file=stream)

    print(
        f"\n監査結果: {len(errors)} エラー, {len(warns)} 警告",
        file=sys.stderr if errors else sys.stdout,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
