from __future__ import annotations

import re

_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify_segment(text: str) -> str:
    s = text.strip().lower()
    s = _SLUG_RE.sub("_", s)
    return s.strip("_") or "object"
