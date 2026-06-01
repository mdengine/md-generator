"""OData V2/V3 EDMX parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from md_generator.sap.models.metadata.odata import (
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
from md_generator.sap.parser.odata import namespaces as ns
from md_generator.sap.parser.odata.associations import AssociationIndex
from md_generator.sap.parser.odata.capabilities import parse_capabilities_from_annotations


def parse_v2_v3_xml(path: Path, version: ODataVersion, text: str | None = None) -> ODataMetadataDocument:
    root = ET.fromstring(text) if text else ET.parse(path).getroot()
    service_name = path.stem
    doc = ODataMetadataDocument(
        service_name=service_name,
        odata_version=version,
        odata_format=ODataFormat.EDMX_XML,
        metadata_url=str(path),
        stable_id=make_stable_id(version, "_", "service", service_name),
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
                stable_id=make_stable_id(version, namespace, "entity", name),
            )
            for prop in ns.find_children(et_elem, "Property"):
                entity.properties.append(
                    ODataProperty(
                        name=prop.get("Name") or "",
                        type_name=prop.get("Type") or "",
                        nullable=prop.get("Nullable", "true").lower() != "false",
                    )
                )
            for key in ns.find_children(et_elem, "Key"):
                for ref in ns.find_children(key, "PropertyRef"):
                    k = ref.get("Name")
                    if k:
                        entity.keys.append(k)
            for nav in ns.find_children(et_elem, "NavigationProperty"):
                rel = nav.get("Relationship") or ""
                to_role = nav.get("ToRole") or ""
                target_type = nav.get("Type") or ""
                mult = "n"
                if rel:
                    target, mult = assoc_index.resolve_nav_target(rel, to_role)
                elif target_type:
                    target = target_type.split(".")[-1]
                    mult = AssociationIndex.multiplicity_from_type(target_type)
                else:
                    target = ""
                entity.navigation_properties.append(
                    ODataNavigationProperty(
                        name=nav.get("Name") or "",
                        target_type=target,
                        multiplicity=mult,
                        stable_id=make_stable_id(version, namespace, "nav", nav.get("Name") or ""),
                    )
                )
            doc.entity_types.append(entity)

    for container in ns.find_descendants(root, "EntityContainer"):
        cname = container.get("Name") or "Container"
        doc.container_name = cname
        cns = container.get("Namespace") or doc.default_namespace
        for es in ns.find_children(container, "EntitySet"):
            et_fqn = es.get("EntityType") or ""
            et_short = et_fqn.split(".")[-1]
            anns = ns.find_children(es, "Annotation") + [
                a for a in es if ns.local_name(a.tag) == "Annotation"
            ]
            doc.entity_sets.append(
                ODataEntitySet(
                    name=es.get("Name") or "",
                    entity_type=et_short,
                    namespace=cns,
                    capabilities=parse_capabilities_from_annotations(anns),
                    stable_id=make_stable_id(version, cns, "entitySet", es.get("Name") or ""),
                )
            )
        for fi in ns.find_children(container, "FunctionImport"):
            doc.functions.append(
                ODataFunction(
                    name=fi.get("Name") or "",
                    namespace=cns,
                    return_type=fi.get("ReturnType") or "",
                    stable_id=make_stable_id(version, cns, "function", fi.get("Name") or ""),
                )
            )
    return doc
