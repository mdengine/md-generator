from __future__ import annotations

from pathlib import Path

ABAP_SUFFIXES = {".abap", ".prog", ".asprog", ".inc"}
CDS_SUFFIXES = {".ddls", ".cds", ".ddlx"}
DDIC_SUFFIXES = {".dd02l", ".dd03l", ".tabl", ".csv", ".xml"}
ODATA_NAMES = {"$metadata.xml", "metadata.xml", "$metadata", "metadata.json", "$metadata.json"}
BAPI_SUFFIXES = {".bapi.json", ".bapi.xml"}
IDOC_SUFFIXES = {".idoc", ".idoc.xml"}
TRANSPORT_SUFFIXES = {".transport", ".tr", ".co", ".csv"}


HANA_SUFFIXES = {".calculationview", ".hdbview", ".hdbcalculationview"}
HANA_NAME_HINTS = (
    "calculation:scenario",
    "calculationscenario",
    "analyticview",
    "analytic:view",
    "attributeview",
    "attribute:view",
)
BW_SUFFIXES = {".adso", ".bwtr", ".compositeprovider", ".cp", ".infoobject", ".dtp"}
DATASPHERE_SUFFIXES = {".dsview", ".view", ".dataflow", ".df", ".analyticalmodel", ".am"}
EXTERNAL_SUFFIXES = {".avsc", ".avro"}


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
    if suf == ".json" and "bapi" not in name_lower:
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")[:4096]
            if "@odata.context" in raw or "$EntityType" in raw:
                return True
        except OSError:
            pass
    if "dd02l" in name_lower or "dd03l" in name_lower:
        return True
    if "bapi" in name_lower and suf in {".json", ".xml"}:
        return True
    if suf in TRANSPORT_SUFFIXES or "transport" in name_lower:
        return True
    if suf in HANA_SUFFIXES:
        return True
    if suf in BW_SUFFIXES:
        return True
    if suf in DATASPHERE_SUFFIXES:
        return True
    if suf in EXTERNAL_SUFFIXES:
        return True
    if suf == ".sql":
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:2048].upper()
            if "CREATE VIEW" in head or "CREATE TABLE" in head:
                return True
        except OSError:
            pass
    if name_lower == "manifest.json":
        return True
    if suf == ".xml":
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:4096].lower()
            if any(h in head for h in HANA_NAME_HINTS):
                return True
            if "wbobj/dictionary" in head or "dtel:dataelement" in head:
                return True
            if any(
                m in head
                for m in (
                    "doma:domain",
                    "tabl:table",
                    "tabl:structure",
                    "ttyp:tabletype",
                    "rsdt:rangestype",
                    "reft:referencetype",
                )
            ):
                return True
        except OSError:
            pass
    return False
