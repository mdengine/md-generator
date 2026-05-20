from __future__ import annotations

from typing import Any

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject


def extract_validations(objects: list[SapObject]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for obj in objects:
        meta = obj.raw_metadata or {}
        if obj.kind == SapObjectKind.PROGRAM and "abap" in meta:
            for v in meta["abap"].get("validations", []):
                rules.append(
                    {
                        "source": obj.name,
                        "source_kind": obj.kind.value,
                        "rule_type": v.get("rule_type"),
                        "expression": v.get("expression"),
                        "line": v.get("line"),
                    }
                )
        if obj.kind == SapObjectKind.CDS_VIEW and "cds" in meta:
            for k, val in meta["cds"].get("annotations", {}).items():
                if "assert" in k.lower():
                    rules.append(
                        {
                            "source": obj.name,
                            "source_kind": obj.kind.value,
                            "rule_type": "cds_assert",
                            "expression": f"{k}={val}",
                        }
                    )
    return rules
