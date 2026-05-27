#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-command build for the exam-site template."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    py = sys.executable
    run([py, "tools/validate_csv.py"])
    run([py, "tools/apply_site_config.py"])
    run([py, "tools/build_exam_guide_articles.py"])
    run([py, "tools/csv_to_exam_site_master.py"])
    run([py, "tools/glossary_csv_to_eisei_embed_js.py"])
    run([py, "tools/csv_to_eisei_ichimon_js.py"])
    run([py, "tools/build_past_question_pages.py"])
    run([py, "tools/build_glossary_pages.py"])
    run(["bash", "tools/prepare_public_site.sh"])
    run([py, "tools/audit_article_freshness.py", "--fail-on-review"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
