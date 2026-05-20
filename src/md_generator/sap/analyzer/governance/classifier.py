from __future__ import annotations

import re
from typing import Any

PII_PATTERNS = [
    (re.compile(r"EMAIL", re.I), "PII"),
    (re.compile(r"\b(SSN|SOCIAL.?SECURITY)\b", re.I), "PII"),
    (re.compile(r"\b(PHONE|MOBILE|TELNR)\b", re.I), "PII"),
    (re.compile(r"\b(NAME|FIRSTNAME|LASTNAME|NACHN|VORNA)\b", re.I), "PII"),
]
FINANCIAL_PATTERNS = [
    (re.compile(r"\b(AMOUNT|BETRW|WRBTR|DMBTR|NETWR)\b", re.I), "FINANCIAL"),
    (re.compile(r"\b(IBAN|BANK|BANKL|BANKN)\b", re.I), "FINANCIAL"),
    (re.compile(r"\b(TAX|STCEG|MWSKZ)\b", re.I), "FINANCIAL"),
]
HR_PATTERNS = [
    (re.compile(r"\b(SALARY|LGART|BETRG)\b", re.I), "HR_SENSITIVE"),
    (re.compile(r"^PA\d", re.I), "HR_TABLE"),
]


def classify_field(field_name: str, *, table_name: str = "", domain: str = "") -> str | None:
    for pat, label in PII_PATTERNS + FINANCIAL_PATTERNS + HR_PATTERNS:
        if pat.search(field_name) or pat.search(domain):
            return label
    if table_name.upper().startswith("PA"):
        return "HR_TABLE"
    if table_name.upper() in ("BKPF", "BSEG", "BSID", "BSAD"):
        return "FINANCIAL_TABLE"
    return None


def classify_objects(objects: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for obj in objects:
        meta = getattr(obj, "raw_metadata", {}) or {}
        ddic = meta.get("ddic")
        if isinstance(ddic, dict):
            for f in ddic.get("fields", []):
                fname = f.get("name", "")
                cls = classify_field(fname, table_name=obj.name, domain=f.get("domain", ""))
                if cls:
                    out.append(
                        {
                            "field": fname,
                            "table": obj.name,
                            "classification": cls,
                            "object_id": obj.object_id,
                        }
                    )
    return out
