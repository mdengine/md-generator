from __future__ import annotations

from md_generator.sap.markdown.builders.ddic_adapters import (
    structure_view_from_cds,
    structure_view_from_ddic,
    data_element_view_from_raw,
)
from md_generator.sap.markdown.semantic_types import SemanticTypeKind


def test_structure_view_from_ddic():
    view = structure_view_from_ddic({
        "name": "BAL_S_CONT",
        "description": "Context",
        "package": "SZS",
        "definition_source": "adt_xml",
        "components": [
            {"name": "MSG", "data_element": "SYCHAR100", "data_type": "CHAR", "length": 100},
        ],
    })
    assert view.name == "BAL_S_CONT"
    assert view.definition_source == "adt_xml"
    assert len(view.components) == 1
    assert view.components[0].name == "MSG"
    assert view.components[0].data_element == "SYCHAR100"


def test_structure_view_from_cds():
    view = structure_view_from_cds({
        "name": "BAL_S_MSG",
        "description": "Log message",
        "enhancement_category": "NOT_CLASSIFIED",
        "components": [
            {"name": "MSGTY", "type_name": "SYMSGTY", "type_kind": "builtin"},
            {"name": "CONTEXT", "type_name": "BAL_S_CONT", "type_kind": "structure"},
        ],
    })
    assert view.name == "BAL_S_MSG"
    assert view.definition_source == "cds_ddl"
    assert view.components[1].semantic_type == SemanticTypeKind.STRUCTURE


def test_data_element_view_semantic_type():
    view = data_element_view_from_raw({"type_kind": "domain", "type_name": "CHAR100"})
    assert view.semantic_type == SemanticTypeKind.SCALAR
