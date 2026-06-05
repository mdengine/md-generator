from __future__ import annotations

from md_generator.sap.markdown.semantic_types import (
    SemanticTypeKind,
    semantic_type_from_cds,
    semantic_type_from_ddic,
    semantic_type_for_type_reference,
)


def test_semantic_type_from_ddic_domain():
    assert semantic_type_from_ddic("domain") == SemanticTypeKind.SCALAR


def test_semantic_type_from_ddic_structure():
    assert semantic_type_from_ddic("structure") == SemanticTypeKind.STRUCTURE


def test_semantic_type_from_ddic_table_type():
    assert semantic_type_from_ddic("tableType") == SemanticTypeKind.TABLE_TYPE


def test_semantic_type_from_cds_builtin():
    assert semantic_type_from_cds("builtin") == SemanticTypeKind.ENUM


def test_semantic_type_from_cds_structure():
    assert semantic_type_from_cds("structure") == SemanticTypeKind.STRUCTURE


def test_semantic_type_for_type_reference():
    assert semantic_type_for_type_reference("rangeType") == SemanticTypeKind.RANGE_TYPE
