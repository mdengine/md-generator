from __future__ import annotations

from md_generator.odata.models.domain import ODataEntityType, ODataMetadataDocument


def to_legacy_entity_dict(entity: ODataEntityType) -> dict:
    return {
        "name": entity.name,
        "properties": [{"name": p.name, "type": p.type_name} for p in entity.properties],
        "navigation": [
            {
                "name": n.name,
                "target": n.target_type,
                "multiplicity": n.multiplicity,
            }
            for n in entity.navigation_properties
        ],
    }


def document_to_legacy_entities(doc: ODataMetadataDocument) -> list[dict]:
    return [to_legacy_entity_dict(e) for e in doc.entity_types]
