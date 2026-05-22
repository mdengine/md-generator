from __future__ import annotations

from pathlib import Path

ABAP_SUFFIXES = {".abap", ".prog", ".asprog", ".inc"}
CDS_SUFFIXES = {".ddls", ".cds", ".ddlx"}
DDIC_SUFFIXES = {".dd02l", ".dd03l", ".tabl", ".csv", ".xml"}
ODATA_NAMES = {"$metadata.xml", "metadata.xml"}
BAPI_SUFFIXES = {".bapi.json", ".bapi.xml"}
IDOC_SUFFIXES = {".idoc", ".idoc.xml"}
TRANSPORT_SUFFIXES = {".transport", ".tr", ".co", ".csv"}


def discover_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for root in paths:
        if root.is_file():
            if root not in seen:
                seen.add(root)
                out.append(root)
            continue
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if p in seen:
                continue
            if _is_candidate(p):
                seen.add(p)
                out.append(p)
    return out


def _is_candidate(p: Path) -> bool:
    name_lower = p.name.lower()
    suf = p.suffix.lower()
    if suf in ABAP_SUFFIXES | CDS_SUFFIXES | DDIC_SUFFIXES | BAPI_SUFFIXES | IDOC_SUFFIXES:
        return True
    if name_lower in ODATA_NAMES or name_lower.endswith(".edmx"):
        return True
    if "dd02l" in name_lower or "dd03l" in name_lower:
        return True
    if "bapi" in name_lower and suf in {".json", ".xml"}:
        return True
    if suf in TRANSPORT_SUFFIXES or "transport" in name_lower:
        return True
    return False
