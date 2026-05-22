from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult

_EDM_NS = {
    "edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
    "edm": "http://schemas.microsoft.com/ado/2008/09/edm",
    "edmx4": "http://docs.oasis-open.org/odata/ns/edmx",
    "edm4": "http://docs.oasis-open.org/odata/ns/edm",
}


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_odata_metadata(path: Path) -> tuple[str, list[dict]]:
    tree = ET.parse(path)
    root = tree.getroot()
    service_name = path.stem
    entities: list[dict] = []

    for elem in root.iter():
        if _local(elem.tag) != "EntityType":
            continue
        name = elem.get("Name") or ""
        props: list[dict] = []
        navs: list[dict] = []
        for child in elem:
            lt = _local(child.tag)
            if lt == "Property":
                props.append({"name": child.get("Name"), "type": child.get("Type")})
            elif lt == "NavigationProperty":
                navs.append({"name": child.get("Name"), "target": child.get("Type")})
        entities.append({"name": name, "properties": props, "navigation": navs})
    return service_name, entities


class ODataParserPlugin:
    name = "odata"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return n in ("$metadata.xml", "metadata.xml") or path.suffix.lower() in {".edmx", ".xml"} and "metadata" in n

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        service, entities = parse_odata_metadata(path)
        objects: list[SapObject] = []
        for ent in entities:
            name = (ent.get("name") or "UNKNOWN").upper()
            obj = SapObject(
                kind=SapObjectKind.ODATA_ENTITY,
                name=name,
                package=service,
                source_path=path,
                raw_metadata={"odata": ent},
                tags=["odata"],
            )
            objects.append(obj)
        svc = SapObject(
            kind=SapObjectKind.ODATA_SERVICE,
            name=service.upper(),
            package=ctx.package_hint,
            source_path=path,
            raw_metadata={"odata_service": service, "entity_count": len(entities)},
            tags=["odata", "service"],
        )
        return SapParseResult(path=path, objects=[svc, *objects], metadata={"odata_entities": entities})
