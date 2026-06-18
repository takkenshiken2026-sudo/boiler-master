#!/usr/bin/env python3
"""ハローワーク 免許・資格コード一覧（小分類）のTSVを正本シードとして
certifications.csv（資格カタログの骨格）へ変換する。

- 入力: data/sources/hellowork_license_list.tsv（「# カテゴリ」＋ code<TAB>name）
- 出力: data/certifications.csv（1行=1資格）
- 名称はNFKC正規化（全角英数→半角）。原文は name_raw に保持。
- 末尾 xx99「その他の…関係資格」はバケット項目として is_bucket=1。
- 同一カテゴリ内の同名は is_duplicate=1（先頭以外）。
- 8000番台「海外資格」は scope=overseas（既定の網羅対象=domestic から除外可）。
事実値（受験料/合格率/公式URL等）は本スクリプトでは埋めない（一次情報で後追い検証）。
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "sources" / "hellowork_license_list.tsv"
OUT = ROOT / "data" / "certifications.csv"

# certifications.csv のスキーマ（事実値の列は空で用意し、後工程で検証して埋める）
COLUMNS = [
    "slug", "hellowork_code", "name", "name_raw", "category",
    "scope", "is_bucket", "is_duplicate",
    "type", "authority", "official_url",
    "eligibility", "exam_format", "fee", "pass_rate", "frequency", "difficulty",
    "related_slugs", "source_checked_at", "status",
]


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip()


def slugify(code: str, name: str) -> str:
    """URL用slug。現状は安定一意なコードベース（例 c-6703）。
    将来ローマ字slugに差し替え可能だがリダイレクト維持のためコードを主キーに残す。"""
    return f"c-{code}"


def parse(src: Path):
    rows = []
    category = ""
    for raw in src.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("# "):  # 出典コメント等（半角#+空白）
            continue
        if line.startswith("#"):   # カテゴリ見出し
            category = nfkc(line[1:].strip())
            continue
        if "\t" not in line:
            continue
        code, name_raw = line.split("\t", 1)
        code = code.strip()
        name_raw = name_raw.strip()
        if not re.fullmatch(r"\d{3,5}", code):
            continue
        rows.append((code, name_raw, category))
    return rows


def main() -> int:
    if not SRC.exists():
        print(f"seed source not found: {SRC}", file=sys.stderr)
        return 1
    parsed = parse(SRC)

    seen_by_cat = {}
    out_rows = []
    for code, name_raw, category in parsed:
        name = nfkc(name_raw)
        is_bucket = 1 if code.endswith("99") and name.startswith("その他") else 0
        scope = "overseas" if code.startswith("8") else "domestic"
        key = (category, name)
        is_dup = 1 if key in seen_by_cat else 0
        seen_by_cat[key] = True
        out_rows.append({
            "slug": slugify(code, name),
            "hellowork_code": code,
            "name": name,
            "name_raw": name_raw,
            "category": category,
            "scope": scope,
            "is_bucket": is_bucket,
            "is_duplicate": is_dup,
            "type": "",            # 国家/公的/民間（後工程で分類）
            "authority": "",
            "official_url": "",
            "eligibility": "",
            "exam_format": "",
            "fee": "",
            "pass_rate": "",
            "frequency": "",
            "difficulty": "",
            "related_slugs": "",
            "source_checked_at": "",
            "status": "seed",      # seed -> draft -> published
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out_rows)

    total = len(out_rows)
    buckets = sum(r["is_bucket"] for r in out_rows)
    dups = sum(r["is_duplicate"] for r in out_rows)
    overseas = sum(1 for r in out_rows if r["scope"] == "overseas")
    cats = len({r["category"] for r in out_rows})
    indexable = total - buckets - dups
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  total rows      : {total}")
    print(f"  categories      : {cats}")
    print(f"  bucket (xx99)   : {buckets}  (noindex想定)")
    print(f"  duplicates      : {dups}  (noindex想定)")
    print(f"  overseas(8xxx)  : {overseas}")
    print(f"  candidate pages : {indexable}  (domestic除くバケット/重複)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
