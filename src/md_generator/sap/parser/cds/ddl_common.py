from __future__ import annotations

import re

_RE_ANNOTATION = re.compile(
    r"@([\w.]+)\s*:\s*(?:#(\w+)|'([^']*)'|\"([^\"]*)\"|(\S+))",
    re.I,
)


def extract_braced_body(source: str) -> str:
    start = source.find("{")
    end = source.rfind("}")
    if start < 0 or end <= start:
        return ""
    return source[start + 1 : end]


def parse_annotations(source: str) -> dict[str, str]:
    annotations: dict[str, str] = {}
    for am in _RE_ANNOTATION.finditer(source):
        key = am.group(1)
        value = am.group(2) or am.group(3) or am.group(4) or am.group(5) or ""
        annotations[key] = value.strip().lstrip("#")
    return annotations


def end_user_label(annotations: dict[str, str]) -> str:
    return annotations.get("EndUserText.label", "")
