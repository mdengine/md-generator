"""Tests for SymbolIdentity and controlled taxonomies."""

from md_generator.semantic.chunkers.identity import (
    EntityType,
    RelationshipType,
    SymbolIdentity,
    VALID_ENTITY_TYPES,
    VALID_RELATIONSHIP_TYPES,
    compute_fqn,
)


def test_symbol_identity_semantic_key_computation():
    identity = SymbolIdentity(
        language="java",
        symbol_kind="class",
        local_name="PaymentProcessor",
        qualified_name="com.company.service.PaymentProcessor",
    )
    assert identity.compute_semantic_key() == "class:com.company.service.PaymentProcessor"


def test_controlled_taxonomies():
    assert "CLASS" in VALID_ENTITY_TYPES
    assert "ENDPOINT" in VALID_ENTITY_TYPES
    assert "TABLE" in VALID_ENTITY_TYPES
    assert "SAP_OBJECT" in VALID_ENTITY_TYPES

    assert "CALLS" in VALID_RELATIONSHIP_TYPES
    assert "CONTAINS" in VALID_RELATIONSHIP_TYPES
    assert "INHERITS" in VALID_RELATIONSHIP_TYPES
    assert "IMPLEMENTS" in VALID_RELATIONSHIP_TYPES
