#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静的アセットにビルド版 ?v= を付与し、長期キャッシュと更新の両立を図る。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 内容が変わるたび v= を更新する対象（リポジトリルート相対）
VERSION_SOURCES = [
    "site-config.js",
    "site-theme.css",
    "site-spa-fields.js",
    "site-spa-load-data.js",
    "site-analytics.js",
    "eisei1-data-glossary.js",
    "eisei1-data-original.js",
    "eisei1-master-data.js",
    "eisei1-data-ichimon.js",
]

# ?v= を付ける HTML（glob は index のみ手動 + 主要静的）
HTML_TARGETS = [
    ROOT / "index.html",
    ROOT / "related-sites.html",
    ROOT / "about.html",
    ROOT / "privacy.html",
]

ASSET_NAMES = (
    "site-config.js",
    "site-theme.css",
    "site-spa-fields.js",
    "site-spa-load-data.js",
    "site-analytics.js",
    "eisei1-data-glossary.js",
    "eisei1-data-original.js",
    "eisei1-master-data.js",
    "eisei1-data-ichimon.js",
)


def asset_version() -> str:
    h = hashlib.sha256()
    for name in VERSION_SOURCES:
        path = ROOT / name
        if path.is_file():
            h.update(name.encode())
            h.update(path.read_bytes())
    return h.hexdigest()[:12]


def strip_old_query(path: str) -> str:
    return re.sub(r"\?v=[a-f0-9]{8,16}", "", path)


def inject_html(text: str, version: str) -> str:
    for name in ASSET_NAMES:
        bare = re.escape(name)
        # href="site-theme.css?v=old" → 新 v
        text = re.sub(
            rf'(href=")({bare})(\?v=[a-f0-9]{{8,16}})?(")',
            rf"\g<1>\g<2>?v={version}\g<4>",
            text,
        )
        text = re.sub(
            rf'(src=")({bare})(\?v=[a-f0-9]{{8,16}})?(")',
            rf"\g<1>\g<2>?v={version}\g<4>",
            text,
        )
        # まだ ?v= が無い参照
        text = re.sub(
            rf'(href=")({bare})(")',
            rf'\1\2?v={version}\3',
            text,
        )
        text = re.sub(
            rf'(src=")({bare})(")',
            rf'\1\2?v={version}\3',
            text,
        )
    return text


def sync_loader_version(version: str) -> None:
    loader = ROOT / "site-spa-load-data.js"
    if not loader.is_file():
        return
    text = loader.read_text(encoding="utf-8")
    updated = re.sub(
        r"(\?v=)(?:__ASSET_VERSION__|[a-f0-9]{8,16})",
        rf"\g<1>{version}",
        text,
    )
    if updated != text:
        loader.write_text(updated, encoding="utf-8")
        print(f"inject_asset_cache_bust: site-spa-load-data.js v={version}")


def main() -> int:
    version = asset_version()
    (ROOT / "data" / "asset_version.txt").write_text(version + "\n", encoding="utf-8")
    sync_loader_version(version)
    for path in HTML_TARGETS:
        if not path.is_file():
            continue
        original = path.read_text(encoding="utf-8")
        updated = inject_html(original, version)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"inject_asset_cache_bust: {path.name} ?v={version}")
    print(f"asset_version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
