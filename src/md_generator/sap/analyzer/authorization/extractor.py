from __future__ import annotations

from typing import Any

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject


def extract_authorization(objects: list[SapObject]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for obj in objects:
        meta = obj.raw_metadata or {}
        if obj.kind != SapObjectKind.PROGRAM or "abap" not in meta:
            continue
        for a in meta["abap"].get("auth_checks", []):
            checks.append(
                {
                    "program": obj.name,
                    "object": a.get("object"),
                    "fields": a.get("fields", []),
                    "line": a.get("line"),
                }
            )
    return checks
