#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイト tools/ 内の *_rewrite_batch*.py を番号順に guide_articles.csv へ適用する。"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_guide_rewrite_batch import apply_rewrites  # noqa: E402


def _batch_num(path: Path) -> tuple[int, str]:
    m = re.search(r"batch(\d+)", path.stem, re.I)
    return (int(m.group(1)) if m else 0, path.name)


def discover_batches(tools_dir: Path, *, prefix: str = "") -> list[Path]:
    if prefix:
        pattern = f"{prefix}rewrite_batch*.py"
    else:
        pattern = "*_rewrite_batch*.py"
    files = sorted(tools_dir.glob(pattern), key=_batch_num)
    return [p for p in files if p.name != "apply_guide_rewrite_batch.py"]


def load_rewrites(path: Path) -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location(f"batch_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rewrites = getattr(mod, "REWRITES", None)
    if not isinstance(rewrites, dict):
        raise ValueError(f"{path} has no REWRITES dict")
    return rewrites


def main() -> int:
    ap = argparse.ArgumentParser(description="全 rewrite batch を CSV に順次適用")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--prefix", default="", help="batch ファイル名 prefix（例: boiler_）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    csv_path = root / "data" / "guide_articles.csv"
    if not csv_path.is_file():
        print(f"missing {csv_path}", file=sys.stderr)
        return 1

    batches = discover_batches(root / "tools", prefix=args.prefix)
    if not batches:
        print(f"no batches under {root / 'tools'}", file=sys.stderr)
        return 1

    merged: dict[str, dict[str, str]] = {}
    for path in batches:
        merged.update(load_rewrites(path))

    if args.dry_run:
        print(f"would apply {len(batches)} batches covering {len(merged)} slugs")
        return 0

    patched = apply_rewrites(csv_path, merged)
    print(f"applied {len(batches)} batches, patched {patched} rows in {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
