from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin
from md_generator.sap.parser.ddic.ddic_resolver import expand_nested_structures

from md_generator.sap.markdown.builders.ddic_adapters import (
    data_element_view_from_metadata,
    structure_view_from_metadata,
)
from md_generator.sap.models.metadata.ddic_canonical import (
    DataElementMetadata,
    DdicCanonicalMetadata,
    StructureMetadata,
)
from md_generator.sap.models.metadata.ddic_canonical_io import (
    attach_ddic_canonical,
    parse_ddic_canonical,
    resolve_ddic_meta,
)

FIXTURES = Path(__file__).parent / "fixtures" / "ddic"


def test_attach_ddic_canonical_typed_payload():
    legacy = {
        "name": "CHAR100",
        "type_kind": "domain",
        "type_name": "CHAR100",
        "data_type": "CHAR",
        "data_type_length": 100,
        "short_field_label": "Label",
    }
    metadata: dict = {"data_element": legacy}
    attach_ddic_canonical(metadata, "DATA_ELEMENT", legacy)
    canonical = parse_ddic_canonical(metadata)
    assert canonical is not None
    assert canonical.object_kind == "DATA_ELEMENT"
    assert isinstance(canonical.payload, DataElementMetadata)
    assert canonical.payload.type_name == "CHAR100"
    assert canonical.payload.data_type_length == 100


def test_normalizer_emits_typed_canonical():
    plugin = AdtDdicParserPlugin()
    ctx = ParseContext(root=FIXTURES)
    result = plugin.parse(FIXTURES / "bal_s_cont.tabl.xml", ctx)
    obj = result.objects[0]
    expand_nested_structures([obj])
    normalizer = default_normalizer_registry()
    artifact, _ = normalizer.normalize(obj)
    canonical = parse_ddic_canonical(artifact.metadata)
    assert canonical is not None
    assert canonical.object_kind == "STRUCTURE"
    assert isinstance(canonical.payload, StructureMetadata)
    assert len(canonical.payload.components) == 2


def test_resolve_prefers_canonical_over_empty_legacy():
    metadata = {
        "structure": {},
        "ddic_canonical": DdicCanonicalMetadata(
            object_kind="STRUCTURE",
            definition_source="adt_xml",
            payload=StructureMetadata(
                components=[
                    {
                        "name": "MSG",
                        "data_element": "SYCHAR100",
                        "data_type": "CHAR",
                        "length": 100,
                    }
                ]
            ),
        ).model_dump(mode="json"),
    }
    resolved = resolve_ddic_meta(metadata, "STRUCTURE", name="BAL_S_CONT")
    assert resolved["name"] == "BAL_S_CONT"
    assert len(resolved["components"]) == 1
    assert resolved["components"][0]["name"] == "MSG"


def test_adapter_reads_canonical_when_legacy_missing():
    metadata = {
        "ddic_canonical": DdicCanonicalMetadata(
            object_kind="DATA_ELEMENT",
            payload=DataElementMetadata(type_kind="domain", type_name="CHAR100"),
        ).model_dump(mode="json"),
    }
    view = data_element_view_from_metadata(metadata, name="CHAR100")
    assert view.name == "CHAR100"
    assert view.type_name == "CHAR100"


def test_adapter_merges_legacy_labels_with_canonical():
    metadata = {
        "data_element": {"short_field_label": "My label"},
        "ddic_canonical": DdicCanonicalMetadata(
            object_kind="DATA_ELEMENT",
            payload=DataElementMetadata(type_kind="domain", type_name="CHAR100", data_type="CHAR"),
        ).model_dump(mode="json"),
    }
    view = data_element_view_from_metadata(metadata, name="CHAR100")
    assert view.type_name == "CHAR100"
    assert view.short_field_label == "My label"


def test_structure_view_from_metadata_nested():
    metadata = {
        "structure": {
            "name": "BAL_S_HDR",
            "components": [
                {
                    "name": "CONT",
                    "type_kind": "structure",
                    "type_name": "BAL_S_CONT",
                    "children": [{"name": "MSG", "data_element": "SYCHAR100"}],
                }
            ],
        },
    }
    attach_ddic_canonical(metadata, "STRUCTURE", metadata["structure"])
    view = structure_view_from_metadata(metadata, name="BAL_S_HDR")
    assert view.components[0].children[0].name == "MSG"
