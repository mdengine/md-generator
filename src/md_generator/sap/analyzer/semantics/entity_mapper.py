from __future__ import annotations

import re

_PREFIX_RE = re.compile(r"^[ZY]_?", re.I)
_CAMEL_RE = re.compile(r"([a-z])([A-Z])")


def infer_semantic_entity(view_name: str, annotations: dict[str, str] | None = None) -> str:
    if annotations:
        for k, v in annotations.items():
            if "businessobject" in k.lower() or "semantics.businessobject" in k.lower():
                return v.strip().strip("'\"")
    name = _PREFIX_RE.sub("", view_name)
    name = name.replace("_", " ")
    name = _CAMEL_RE.sub(r"\1 \2", name)
    parts = [p for p in name.split() if p and p.upper() not in ("I", "C", "VIEW", "DDIC")]
    if parts:
        return " ".join(p.capitalize() for p in parts)
    return view_name
