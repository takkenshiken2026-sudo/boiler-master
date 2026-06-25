#!/usr/bin/env python3
"""articles/ 直下のフラット *.html リダイレクト stub の多段リダイレクトを解消する。

旧記事システムの名残で `articles/<slug>.html`（フラット）→ `articles/<slug>/`（ディレクトリ）
→ 退役先（exam-overview/ 等）という二段リダイレクトが残っていた。検索エンジンの
クロール効率と評価伝達のため、フラット stub のリンク先を **最終到達先**へ単段化する。
リンク形は記事 canonical と同じ末尾スラッシュ形に統一する。

build_all.py はフラット *.html を再生成しないため、この修正はその場の静的書き換えで永続する。
冪等。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"

REFRESH_RE = re.compile(r'http-equiv="refresh"\s+content="0;?\s*url=([^"]+)"', re.I)


def redirect_target(path: Path) -> str | None:
    """リダイレクト stub なら url= の値を返す。実記事なら None。"""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if "http-equiv=\"refresh\"" not in text:
        return None
    m = REFRESH_RE.search(text)
    return m.group(1).strip() if m else None


def resolve_final(slug: str, seen: set[str]) -> str | None:
    """フラット slug.html の最終到達ディレクトリ slug を解決する。"""
    if slug in seen:
        return None
    seen.add(slug)
    # フラット stub の一次リンク先（通常は同名ディレクトリ）
    flat = ARTICLES / f"{slug}.html"
    tgt = redirect_target(flat)
    if tgt is None:
        return None
    cur = tgt
    # ディレクトリ stub をたどって最終到達先まで降りる
    for _ in range(10):
        name = cur.strip("./").removesuffix("index.html").strip("/")
        if name.startswith(("http://", "https://")):
            return cur  # 外部はそのまま
        idx = ARTICLES / name / "index.html"
        nxt = redirect_target(idx)
        if nxt is None:
            return name  # 実記事に到達
        cur = nxt
    return None


def main() -> int:
    fixed = 0
    for flat in sorted(ARTICLES.glob("*.html")):
        if flat.name == "index.html":
            continue
        slug = flat.stem
        tgt = redirect_target(flat)
        if tgt is None:
            continue  # 実記事はスキップ
        final = resolve_final(slug, set())
        if not final:
            continue
        if final.startswith(("http://", "https://")):
            new_href = final
        else:
            new_href = f"{final}/"  # フラット articles/<slug>.html から見た相対（末尾スラッシュ）
        # 既に単段（リンク先が実記事ディレクトリ）かつ正しい形なら触らない
        if tgt.rstrip("/") == new_href.rstrip("/"):
            continue
        text = flat.read_text(encoding="utf-8")
        esc = new_href
        text = REFRESH_RE.sub(f'http-equiv="refresh" content="0;url={esc}"', text, count=1)
        text = re.sub(r'(<link rel="canonical" href=")[^"]+(">)', rf'\g<1>{esc}\g<2>', text, count=1)
        text = re.sub(r"location\.replace\(([^)]+)\)", f"location.replace('{esc}')", text, count=1)
        text = re.sub(r'(<a href=")[^"]+(">こちら</a>)', rf'\g<1>{esc}\g<2>', text, count=1)
        flat.write_text(text, encoding="utf-8")
        fixed += 1
    print(f"Rewrote {fixed} flat redirect stub(s) to single-hop final targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
