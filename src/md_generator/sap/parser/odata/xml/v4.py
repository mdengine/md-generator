"""OData V4 CSDL XML parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from md_generator.sap.models.metadata.odata import (
    ODataAction,
    ODataComplexType,
    ODataEntitySet,
    ODataEntityType,
    ODataEnumType,
    ODataFormat,
    ODataFunction,
    ODataMetadataDocument,
    ODataNavigationProperty,
    ODataProperty,
    ODataVersion,
    make_stable_id,
)
from md_generator.sap.parser.odata import namespaces as ns
from md_generator.sap.parser.odata.associations import AssociationIndex
from md_generator.sap.parser.odata.capabilities import parse_capabilities_from_annotations


def parse_v4_xml(path: Path, text: str | None = None) -> ODataMetadataDocument:
    root = ET.fromstring(text) if text else ET.parse(path).getroot()
    service_name = path.stem
    doc = ODataMetadataDocument(
        service_name=service_name,
        odata_version=ODataVersion.V4,
        odata_format=ODataFormat.EDMX_XML,
        metadata_url=str(path),
        stable_id=make_stable_id(ODataVersion.V4, "_", "service", service_name),
    )
    for schema in ns.find_descendants(root, "Schema"):
        namespace = ns.schema_namespace(schema)
        if not doc.default_namespace:
            doc.default_namespace = namespace
        for ct in ns.find_children(schema, "ComplexType"):
            doc.complex_types.append(
                ODataComplexType(
                    name=ct.get("Name") or "",
                    namespace=namespace,
                    stable_id=make_stable_id(ODataVersion.V4, namespace, "complex", ct.get("Name") or ""),
                )
            )
        for en in ns.find_children(schema, "EnumType"):
            members = [m.get("Name") or "" for m in ns.find_children(en, "Member")]
            doc.enum_types.append(
                ODataEnumType(
                    name=en.get("Name") or "",
                    namespace=namespace,
                    members=members,
                    stable_id=make_stable_id(ODataVersion.V4, namespace, "enum", en.get("Name") or ""),
                )
            )
        for action in ns.find_children(schema, "Action"):
            doc.actions.append(
                ODataAction(
                    name=action.get("Name") or "",
                    namespace=namespace,
                    is_bound=action.get("IsBound", "false").lower() == "true",
                    stable_id=make_stable_id(ODataVersion.V4, namespace, "action", action.get("Name") or ""),
                )
            )
        for fn in ns.find_children(schema, "Function"):
            doc.functions.append(
                ODataFunction(
                    name=fn.get("Name") or "",
                    namespace=namespace,
                    is_bound=fn.get("IsBound", "false").lower() == "true",
                    stable_id=make_stable_id(ODataVersion.V4, namespace, "function", fn.get("Name") or ""),
                )
            )
        for et_elem in ns.find_children(schema, "EntityType"):
            name = et_elem.get("Name") or ""
            entity = ODataEntityType(
                name=name,
                namespace=namespace,
                stable_id=make_stable_id(ODataVersion.V4, namespace, "entity", name),
            )
            for prop in ns.find_children(et_elem, "Property"):
                entity.properties.append(
                    ODataProperty(name=prop.get("Name") or "", type_name=prop.get("Type") or "")
                )
            for key in ns.find_children(et_elem, "Key"):
                for ref in ns.find_children(key, "PropertyRef"):
                    k = ref.get("Name")
                    if k:
                        entity.keys.append(k)
            for nav in ns.find_children(et_elem, "NavigationProperty"):
                t = nav.get("Type") or ""
                entity.navigation_properties.append(
                    ODataNavigationProperty(
                        name=nav.get("Name") or "",
                        target_type=t.split(".")[-1].rstrip(")").replace("Collection(", ""),
                        partner=nav.get("Partner") or "",
                        multiplicity=AssociationIndex.multiplicity_from_type(t),
                        stable_id=make_stable_id(ODataVersion.V4, namespace, "nav", nav.get("Name") or ""),
                    )
                )
            doc.entity_types.append(entity)

    for container in ns.find_descendants(root, "EntityContainer"):
        cname = container.get("Name") or "Container"
        doc.container_name = cname
        cns = doc.default_namespace
        for es in ns.find_children(container, "EntitySet"):
            et_fqn = es.get("EntityType") or ""
            anns = [a for a in es if ns.local_name(a.tag) == "Annotation"]
            doc.entity_sets.append(
                ODataEntitySet(
                    name=es.get("Name") or "",
                    entity_type=et_fqn.split(".")[-1],
                    namespace=cns,
                    capabilities=parse_capabilities_from_annotations(anns),
                    stable_id=make_stable_id(ODataVersion.V4, cns, "entitySet", es.get("Name") or ""),
                )
            )
    return doc
