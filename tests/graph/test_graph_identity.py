import pytest

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.model import (
    canonical_entity_node_id,
    canonical_typed_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_relation_edge_id,
)


def test_canonical_entity_node_id_injective_and_delimiter_safe():
    tenant = "corp:prod/us-east"
    entity_a = "user:profile:settings"
    entity_b = "user:profile/settings"

    id_a = canonical_entity_node_id(tenant, entity_a)
    id_b = canonical_entity_node_id(tenant, entity_b)

    assert id_a != id_b
    assert "tenant:corp%3Aprod%2Fus-east:entity:user%3Aprofile%3Asettings" == id_a
    assert "tenant:corp%3Aprod%2Fus-east:entity:user%3Aprofile%2Fsettings" == id_b


def test_canonical_chunk_and_doc_ids():
    tenant = "tenant-1"
    cid = "chunk:001"
    did = "doc:001"

    c_node_id = canonical_chunk_node_id(tenant, cid)
    d_node_id = canonical_document_node_id(tenant, did)

    assert c_node_id == "tenant:tenant-1:chunk:chunk%3A001"
    assert d_node_id == "tenant:tenant-1:doc:doc%3A001"


def test_canonical_relation_edge_id():
    tenant = "tenant-1"
    src = "node:1"
    tgt = "node:2"
    rel_type = "DEPENDS_ON"

    edge_id = canonical_relation_edge_id(tenant, src, rel_type, tgt)
    assert edge_id == "tenant:tenant-1:rel:node%3A1->DEPENDS_ON->node%3A2"

    # Invalid regex rel_type
    with pytest.raises(ValueError):
        canonical_relation_edge_id(tenant, src, "DEPENDS-ON", tgt)


def test_canonical_ids_empty_input_validation():
    with pytest.raises(TenantBoundaryError):
        canonical_entity_node_id("", "entity-1")
    with pytest.raises(TenantBoundaryError):
        canonical_entity_node_id("   ", "entity-1")
    with pytest.raises(ValueError):
        canonical_entity_node_id("tenant-1", "")
    with pytest.raises(ValueError):
        canonical_chunk_node_id("tenant-1", "")
    with pytest.raises(ValueError):
        canonical_document_node_id("tenant-1", "")
