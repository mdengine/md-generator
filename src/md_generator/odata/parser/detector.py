from __future__ import annotations

import json
from pathlib import Path

from md_generator.odata.models.domain import ODataFormat, ODataVersion
from md_generator.odata.parser import namespaces as ns


def detect_format(path: Path, text: str | None = None) -> ODataFormat:
    if path.suffix.lower() == ".json" or path.name.lower().endswith(".json"):
        return ODataFormat.CSDL_JSON
    raw = text if text is not None else path.read_text(encoding="utf-8", errors="replace")[:8192]
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        try:
            data = json.loads(raw if text else path.read_text(encoding="utf-8", errors="replace"))
            if "@odata.context" in data or "$EntityType" in data or "$Version" in data:
                return ODataFormat.CSDL_JSON
        except json.JSONDecodeError:
            pass
    return ODataFormat.EDMX_XML


def detect_version(path: Path, fmt: ODataFormat, text: str | None = None) -> ODataVersion:
    if fmt == ODataFormat.CSDL_JSON:
        raw = text if text is not None else path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return ODataVersion.UNKNOWN
        ver = str(data.get("$Version") or data.get("version") or "")
        if ver.startswith("4"):
            return ODataVersion.V4
        return ODataVersion.V4

    raw = text if text is not None else path.read_text(encoding="utf-8", errors="replace")
    if ns.EDM_NS_V4 in raw or "docs.oasis-open.org/odata/ns/edm" in raw:
        return ODataVersion.V4
    if 'DataServiceVersion="3.0"' in raw or "DataServiceVersion='3.0'" in raw:
        return ODataVersion.V3
    if 'DataServiceVersion="2.0"' in raw or "DataServiceVersion='2.0'" in raw:
        return ODataVersion.V2
    if 'Version="1.0"' in raw and ns.EDMX_NS_V1 in raw:
        if "NavigationProperty" not in raw and "Association" in raw:
            return ODataVersion.V1
        return ODataVersion.V2
    return ODataVersion.UNKNOWN
