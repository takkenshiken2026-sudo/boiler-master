# -*- coding: utf-8 -*-
"""分野別の手書き用語スニペットを統合する。"""

from __future__ import annotations

SNIPPET_OVERRIDES: dict[str, dict[str, str]] = {}

_MODULES = (
    "structure",
    "handling",
    "combustion",
    "law",
)

for _mod in _MODULES:
    try:
        m = __import__(f"tools.glossary_handwritten.{_mod}", fromlist=["SNIPPET_OVERRIDES"])
        SNIPPET_OVERRIDES.update(getattr(m, "SNIPPET_OVERRIDES", {}))
    except ImportError:
        pass
