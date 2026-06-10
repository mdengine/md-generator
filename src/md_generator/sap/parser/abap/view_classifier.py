from __future__ import annotations

import re

from md_generator.sap.models.metadata.abap import AbapViewReference, ResolutionResult, ViewKind

_RE_SCHEMA_QUALIFIED = re.compile(r'"([^"]+)"\s*\.\s*"([^"]+)"', re.I)
_RE_SCHEMA_ARROW = re.compile(r"(\w+)\s*=>\s*(\w+)", re.I)


def classify_object(name: str, schema: str = "") -> tuple[ViewKind, float, str]:
    """Return (kind, confidence, match_reason) for a SQL object reference."""
    base = name.upper().split("/")[-1]
    if schema:
        return _classify_hana_schema(base, schema)
    if base.startswith(("ZI_", "I_", "C_")) or "/DMO/" in name.upper():
        return "cds", 0.75, f"CDS naming prefix on '{base}'"
    if base.startswith("CV_") or base.endswith("_CV"):
        return "hana_calc", 0.7, f"HANA calculation view naming on '{base}'"
    if len(base) == 5 and base.isalpha() and base.isupper():
        return "ddic_table", 0.9, f"DDIC-style 5-char name '{base}'"
    if base.startswith(("Z", "Y")) and len(base) <= 30:
        return "unknown", 0.55, f"Custom object '{base}'"
    return "unknown", 0.5, f"Unclassified object '{base}'"


def _classify_hana_schema(name: str, schema: str) -> tuple[ViewKind, float, str]:
    base = name.upper()
    if base.startswith("CV_") or base.endswith("_CV"):
        return "hana_calc", 0.72, f"Schema-qualified HANA calc view '{schema}.{base}'"
    if base.startswith(("AV_", "HA_")):
        return "hana_analytic", 0.68, f"Schema-qualified HANA analytic view '{schema}.{base}'"
    if base.startswith(("AT_", "HA_")):
        return "hana_attribute", 0.65, f"Schema-qualified HANA attribute view '{schema}.{base}'"
    return "hana_sql", 0.65, f"Schema-qualified HANA object '{schema}.{base}'"


def parse_schema_qualified(token: str) -> tuple[str, str]:
    m = _RE_SCHEMA_QUALIFIED.search(token)
    if m:
        return m.group(1).upper(), m.group(2).upper()
    m2 = _RE_SCHEMA_ARROW.search(token)
    if m2:
        return m2.group(1).upper(), m2.group(2).upper()
    return "", token.upper().split("/")[-1]


def build_view_references(
    objects: list[tuple[str, int]],
) -> list[AbapViewReference]:
    """Build deduplicated view references from (object_token, line) pairs."""
    seen: set[tuple[str, str]] = set()
    refs: list[AbapViewReference] = []
    for token, line in objects:
        schema, name = parse_schema_qualified(token)
        key = (schema, name)
        if key in seen:
            continue
        seen.add(key)
        kind, confidence, reason = classify_object(name, schema)
        refs.append(
            AbapViewReference(
                name=name,
                schema=schema,
                kind=kind,
                confidence=confidence,
                source_sql_line=line,
                resolution=ResolutionResult(
                    target=name,
                    confidence=confidence,
                    resolution_strategy="heuristic",
                    match_reason=reason,
                ),
            )
        )
    return refs
