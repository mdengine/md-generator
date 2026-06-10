from __future__ import annotations

import hashlib
import re

_RE_LITERAL = re.compile(r"'(?:''|[^'])*'")
_RE_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_RE_HOST_VAR = re.compile(r"@\w+|@\([^)]+\)|sy-\w+", re.I)
_RE_WHITESPACE = re.compile(r"\s+")


def normalize_sql(text: str) -> str:
    """Normalize SQL for fingerprinting: lowercase, collapse whitespace, mask literals."""
    s = text.strip().lower()
    s = _RE_LITERAL.sub("?", s)
    s = _RE_NUMBER.sub("?", s)
    s = _RE_HOST_VAR.sub("?", s)
    s = _RE_WHITESPACE.sub(" ", s)
    return s.strip()


def sql_fingerprint(text: str) -> str:
    normalized = normalize_sql(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
