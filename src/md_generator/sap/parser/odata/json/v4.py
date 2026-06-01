"""OData V4 CSDL JSON parser."""

from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.models.metadata.odata import (
    ODataAction,
    ODataEntitySet,
    ODataEntityType,
    ODataFormat,
    ODataFunction,
    ODataMetadataDocument,
    ODataNavigationProperty,
    ODataProperty,
    ODataVersion,
    make_stable_id,
)
from md_generator.sap.parser.odata.capabilities import parse_capabilities_json


def parse_v4_json(path: Path, text: str | None = None) -> ODataMetadataDocument:
    raw = text if text is not None else path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)
    service_name = path.stem
    doc = ODataMetadataDocument(
        service_name=service_name,
        odata_version=ODataVersion.V4,
        odata_format=ODataFormat.CSDL_JSON,
        metadata_url=str(path),
        stable_id=make_stable_id(ODataVersion.V4, "_", "service", service_name),
    )
    for et in data.get("$EntityType") or data.get("EntityType") or []:
        name = et.get("Name") or et.get("name") or ""
        namespace = et.get("@Namespace") or doc.default_namespace or "Default"
        if not doc.default_namespace:
            doc.default_namespace = namespace
        entity = ODataEntityType(
            name=name,
            namespace=namespace,
            stable_id=make_stable_id(ODataVersion.V4, namespace, "entity", name),
        )
        for prop in et.get("Property") or et.get("Properties") or []:
            entity.properties.append(
                ODataProperty(name=prop.get("Name") or "", type_name=prop.get("Type") or "")
            )
        for nav in et.get("NavigationProperty") or []:
            t = nav.get("Type") or ""
            entity.navigation_properties.append(
                ODataNavigationProperty(
                    name=nav.get("Name") or "",
                    target_type=t.split(".")[-1].rstrip(")").replace("Collection(", ""),
                    multiplicity="n" if "Collection(" in t else "1",
                )
            )
        doc.entity_types.append(entity)

    for container in data.get("$EntityContainer") or []:
        doc.container_name = container.get("Name") or "Container"
        for es in container.get("EntitySet") or []:
            anns = es.get("Annotations") or []
            doc.entity_sets.append(
                ODataEntitySet(
                    name=es.get("Name") or "",
                    entity_type=(es.get("EntityType") or "").split(".")[-1],
                    namespace=doc.default_namespace,
                    capabilities=parse_capabilities_json(anns if isinstance(anns, list) else []),
                    stable_id=make_stable_id(
                        ODataVersion.V4, doc.default_namespace, "entitySet", es.get("Name") or ""
                    ),
                )
            )
    for action in data.get("$Action") or []:
        doc.actions.append(
            ODataAction(name=action.get("Name") or "", namespace=doc.default_namespace)
        )
    for fn in data.get("$Function") or []:
        doc.functions.append(
            ODataFunction(name=fn.get("Name") or "", namespace=doc.default_namespace)
        )
    return doc
