from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.odata import ODataMetadataDocument, SapObjectCategory
from md_generator.sap.parser.odata.legacy import document_to_legacy_entities, to_legacy_entity_dict


def document_to_sap_objects(doc: ODataMetadataDocument, source_path: Path, package_hint: str = "") -> list[SapObject]:
    objects: list[SapObject] = []
    svc_name = doc.service_name.upper()
    svc_meta = {
        "odata_service": doc.service_name,
        "entity_count": len(doc.entity_types),
        "odata_version": doc.odata_version.value,
        "odata_analysis": doc.to_dict(),
        "stable_id": doc.stable_id,
        "service_root": doc.service_root,
        "metadata_url": doc.metadata_url,
        "container_name": doc.container_name,
    }
    objects.append(
        SapObject(
            kind=SapObjectKind.ODATA_SERVICE,
            name=svc_name,
            package=package_hint or doc.default_namespace,
            source_path=source_path,
            raw_metadata=svc_meta,
            tags=["odata", "service"],
            category=SapObjectCategory.API,
            is_catalog_object=True,
        )
    )
    for es in doc.entity_sets:
        objects.append(
            SapObject(
                kind=SapObjectKind.ODATA_ENTITY_SET,
                name=es.name.upper(),
                package=doc.service_name,
                source_path=source_path,
                raw_metadata={
                    "odata_entity_set": es.name,
                    "entity_type": es.entity_type,
                    "capabilities": es.capabilities.to_dict(),
                    "odata_version": doc.odata_version.value,
                    "odata_analysis": doc.to_dict(),
                    "stable_id": es.stable_id,
                },
                tags=["odata", "entity-set"],
                category=SapObjectCategory.API,
                is_catalog_object=True,
            )
        )
    for entity in doc.entity_types:
        legacy = to_legacy_entity_dict(entity)
        objects.append(
            SapObject(
                kind=SapObjectKind.ODATA_ENTITY,
                name=entity.name.upper(),
                package=doc.service_name,
                source_path=source_path,
                raw_metadata={
                    "odata": legacy,
                    "odata_version": doc.odata_version.value,
                    "odata_analysis": doc.to_dict(),
                    "stable_id": entity.stable_id,
                },
                tags=["odata"],
                category=SapObjectCategory.API,
                is_catalog_object=True,
            )
        )
    for action in doc.actions:
        objects.append(
            SapObject(
                kind=SapObjectKind.ODATA_ACTION,
                name=action.name.upper(),
                package=doc.service_name,
                source_path=source_path,
                raw_metadata={
                    "odata_action": action.name,
                    "is_bound": action.is_bound,
                    "odata_analysis": doc.to_dict(),
                    "stable_id": action.stable_id,
                },
                tags=["odata", "action"],
                category=SapObjectCategory.API,
                is_catalog_object=True,
            )
        )
    for fn in doc.functions:
        objects.append(
            SapObject(
                kind=SapObjectKind.ODATA_FUNCTION,
                name=fn.name.upper(),
                package=doc.service_name,
                source_path=source_path,
                raw_metadata={
                    "odata_function": fn.name,
                    "return_type": fn.return_type,
                    "odata_analysis": doc.to_dict(),
                    "stable_id": fn.stable_id,
                },
                tags=["odata", "function"],
                category=SapObjectCategory.API,
                is_catalog_object=True,
            )
        )
    return objects
