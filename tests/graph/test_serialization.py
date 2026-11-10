import json
import pytest

from md_generator.graph.model import EntityNode, RelationEdge, KnowledgeGraph
from md_generator.graph.serialization import (
    to_dict,
    to_json_ld,
    to_cytoscape,
    to_cypher_statements,
    JSON_LD_CONTEXT,
)


@pytest.fixture
def sample_graph():
    node1 = EntityNode(
        node_id="tenant:t1:entity:cls_order",
        tenant_id="t1",
        entity_id="cls_order",
        entity_type="class",
        name="Order",
        qualified_name="sales.Order",
        properties={"table": "orders"},
        chunk_ids=["chunk-1"],
    )
    node2 = EntityNode(
        node_id="tenant:t1:entity:fn_calculate",
        tenant_id="t1",
        entity_id="fn_calculate",
        entity_type="function",
        name="calculate_tax",
        qualified_name="sales.calculate_tax",
        chunk_ids=["chunk-1"],
    )
    edge = RelationEdge(
        edge_id="tenant:t1:rel:order->CALLS->calculate",
        tenant_id="t1",
        source_id=node1.node_id,
        target_id=node2.node_id,
        relationship_type="CALLS",
        weight=0.9,
    )
    return KnowledgeGraph(
        tenant_id="t1",
        nodes={node1.node_id: node1, node2.node_id: node2},
        edges={edge.edge_id: edge},
    )


def test_json_ld_export_and_tenant_security(sample_graph):
    # Default: include_tenant=False (Strict C15 Tenant Privacy)
    ld = to_json_ld(sample_graph, include_tenant=False)
    assert ld["@context"]["kg"] == "https://mdengine.dev/ontology#"
    assert "tenantId" not in ld
    assert "tenantId" not in ld["@graph"]["nodes"][0]
    assert "tenantId" not in ld["@graph"]["edges"][0]
    # Canonical IDs must have tenant:<tenant_id>: prefix completely stripped
    assert ld["@graph"]["nodes"][0]["@id"] == "entity:cls_order"
    assert ld["@graph"]["edges"][0]["source"] == "entity:cls_order"
    assert ld["@graph"]["edges"][0]["target"] == "entity:fn_calculate"
    assert ld["@graph"]["edges"][0]["@id"] == "rel:order->CALLS->calculate"
    # Byte-level check: internal tenant 't1' does not appear anywhere in serialized payload
    assert "t1" not in json.dumps(ld)

    # Explicit: include_tenant=True
    ld_tenant = to_json_ld(sample_graph, include_tenant=True)
    assert ld_tenant["tenantId"] == "t1"
    assert ld_tenant["@graph"]["nodes"][0]["tenantId"] == "t1"
    assert ld_tenant["@graph"]["nodes"][0]["@id"] == "tenant:t1:entity:cls_order"
    assert ld_tenant["@graph"]["edges"][0]["source"] == "tenant:t1:entity:cls_order"
    assert ld_tenant["@graph"]["edges"][0]["target"] == "tenant:t1:entity:fn_calculate"


def test_knowledge_graph_full_roundtrip_equality(sample_graph):
    # Add metadata to sample graph
    sample_graph.metadata = {"domain": "sales", "version": 2}

    # 1. Export to dict
    d = sample_graph.to_dict()
    assert isinstance(d, dict)

    # 2. Reconstruct from dict
    reconstructed = KnowledgeGraph.from_dict(d)

    # 3. Verify complete structural and property equality
    assert reconstructed.tenant_id == sample_graph.tenant_id
    assert reconstructed.nodes == sample_graph.nodes
    assert reconstructed.edges == sample_graph.edges
    assert reconstructed.metadata == sample_graph.metadata
    assert reconstructed == sample_graph

    # 4. Byte-for-byte serialization equality
    assert reconstructed.to_dict() == d
    assert json.dumps(reconstructed.to_dict(), sort_keys=True) == json.dumps(d, sort_keys=True)


def test_cytoscape_export(sample_graph):
    cy = to_cytoscape(sample_graph)
    assert "elements" in cy
    elements = cy["elements"]
    assert len(elements["nodes"]) == 2
    assert len(elements["edges"]) == 1

    node_data = elements["nodes"][0]["data"]
    assert "id" in node_data
    assert "label" in node_data
    assert "type" in node_data

    edge_data = elements["edges"][0]["data"]
    assert edge_data["label"] == "CALLS"
    assert edge_data["weight"] == 0.9


def test_cypher_statements_export(sample_graph):
    stmts = to_cypher_statements(sample_graph)
    assert len(stmts) == 3  # 2 node MERGE statements + 1 edge MERGE statement
    assert any("MERGE (n:EntityNode" in s for s in stmts)
    assert any("MERGE (s)-[r:`CALLS`" in s for s in stmts)


def test_graph_model_convenience_methods(sample_graph):
    ld = sample_graph.to_json_ld()
    assert "@context" in ld

    cy = sample_graph.to_cytoscape()
    assert "elements" in cy

    stmts = sample_graph.to_cypher_statements()
    assert len(stmts) == 3
