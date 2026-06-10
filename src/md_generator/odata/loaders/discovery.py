from __future__ import annotations

from pathlib import Path

ODATA_NAMES = {"$metadata.xml", "metadata.xml", "$metadata", "metadata.json", "$metadata.json"}


def is_odata_metadata(path: Path) -> bool:
    n = path.name.lower()
    if n in ODATA_NAMES or n.endswith(".edmx"):
        return True
    if path.suffix.lower() == ".xml":
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")[:4096]
            if "Edmx" in raw or "edmx:Edmx" in raw or "schemas.microsoft.com/ado" in raw:
                return True
            if "metadata" in n:
                return True
        except OSError:
            pass
    if path.suffix.lower() == ".json" and "bapi" not in n:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")[:4096]
            if "@odata.context" in raw or "$EntityType" in raw:
                return True
        except OSError:
            pass
    return False


def discover_metadata_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for root in paths:
        if root.is_file():
            if is_odata_metadata(root) and root not in seen:
                seen.add(root)
                out.append(root)
            continue
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and is_odata_metadata(p) and p not in seen:
                seen.add(p)
                out.append(p)
    return out
