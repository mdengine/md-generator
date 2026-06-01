"""OData V1 CSDL parser (best-effort)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from md_generator.sap.models.metadata.odata import (
    ODataEntityType,
    ODataFormat,
    ODataMetadataDocument,
    ODataNavigationProperty,
    ODataProperty,
    ODataVersion,
    make_stable_id,
)
from md_generator.sap.parser.odata import namespaces as ns
from md_generator.sap.parser.odata.associations import AssociationIndex


def parse_v1_xml(path: Path, text: str | None = None) -> ODataMetadataDocument:
    root = ET.fromstring(text) if text else ET.parse(path).getroot()
    service_name = path.stem
    doc = ODataMetadataDocument(
        service_name=service_name,
        odata_version=ODataVersion.V1,
        odata_format=ODataFormat.EDMX_XML,
        metadata_url=str(path),
        stable_id=make_stable_id(ODataVersion.V1, "_", "service", service_name),
    )
    assoc_index = AssociationIndex()
    for schema in ns.find_descendants(root, "Schema"):
        namespace = ns.schema_namespace(schema)
        if not doc.default_namespace:
            doc.default_namespace = namespace
        for assoc in ns.find_children(schema, "Association"):
            assoc_index.add(namespace, assoc)
        for et_elem in ns.find_children(schema, "EntityType"):
            name = et_elem.get("Name") or ""
            entity = ODataEntityType(
                name=name,
                namespace=namespace,
                stable_id=make_stable_id(ODataVersion.V1, namespace, "entity", name),
            )
            for prop in ns.find_children(et_elem, "Property"):
                entity.properties.append(
                    ODataProperty(name=prop.get("Name") or "", type_name=prop.get("Type") or "")
                )
            for nav in ns.find_children(et_elem, "NavigationProperty"):
                rel = nav.get("Relationship") or ""
                to_role = nav.get("ToRole") or ""
                target, mult = assoc_index.resolve_nav_target(rel, to_role)
                entity.navigation_properties.append(
                    ODataNavigationProperty(
                        name=nav.get("Name") or "",
                        target_type=target,
                        multiplicity=mult,
                    )
                )
            doc.entity_types.append(entity)
    return doc
